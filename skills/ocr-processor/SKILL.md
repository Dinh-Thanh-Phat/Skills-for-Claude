---
name: ocr-processor
description: >-
  Extract text from scanned PDFs and images using multi-engine OCR (Tesseract → EasyOCR → Google
  Vision fallback). Automatically detects whether a PDF has a text layer or needs OCR. Supports
  Vietnamese + English, image preprocessing (deskew, denoise, binarization), batch processing,
  and quality scoring. Use whenever you need to read text from images or scan-based documents
  before feeding into the chatbot-tester pipeline. Triggers on: "OCR this PDF", "extract text
  from image", "read scanned document", "process Vietnamese scan", "convert image to text", "PDF
  has no text layer", "preprocess document for chatbot testing". Integrates as Step 0 before
  gdrive-doc-reader in the chatbot testing pipeline.
---

# OCR Processor

Converts scanned PDFs and images into clean, readable text. Sits before `gdrive-doc-reader` in the chatbot testing pipeline when source documents are image-based rather than text-based.

## Pipeline Position

```
[ocr-processor] → gdrive-doc-reader → qa-generator → chatbot-api-caller → response-evaluator → performance-analyzer → test-reporter
```

Use this skill when the Google Drive folder contains scanned PDFs, screenshots, or photos of documents instead of (or alongside) text PDFs.

## Output

File: `ocr_output.txt` — same format as `docs_content.txt` from gdrive-doc-reader, with `=== filename ===` section headers so downstream skills consume it identically.

Also writes `ocr_quality_report.json` with per-file confidence scores and flags.

---

## Python Implementation

Write this script as `ocr_processor.py`:

```python
import sys
import json
import time
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


# ── 1. PDF TYPE DETECTION ───────────────────────────────────────────────────

def is_scanned_pdf(pdf_path: str, text_chars_threshold: int = 50) -> bool:
    """Return True if PDF has no usable text layer (needs OCR)."""
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            total_chars = sum(
                len(page.extract_text() or "")
                for page in pdf.pages[:5]  # sample first 5 pages
            )
        return total_chars < text_chars_threshold
    except Exception:
        return True  # assume scanned if detection fails


def pdf_to_images(pdf_path: str, dpi: int = 300) -> list:
    """Convert PDF pages to PIL Image objects."""
    from pdf2image import convert_from_path
    return convert_from_path(pdf_path, dpi=dpi)


# ── 2. IMAGE PREPROCESSING ──────────────────────────────────────────────────

def preprocess_image(img: np.ndarray, config: dict = None) -> np.ndarray:
    """
    Apply preprocessing pipeline. Order matters:
    grayscale → denoise → upscale (if low DPI) → deskew → binarize → border_remove
    """
    cfg = config or {}

    # Grayscale
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    if cfg.get("denoise", True):
        img = cv2.fastNlMeansDenoising(img, h=10)

    # Upscale if image is small (low DPI scan)
    h, w = img.shape[:2]
    if cfg.get("upscale", True) and max(h, w) < 2000:
        scale = 2.0
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    # Contrast enhancement (CLAHE)
    if cfg.get("enhance_contrast", True):
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img = clahe.apply(img)

    # Deskew
    if cfg.get("deskew", True):
        img = _deskew(img)

    # Binarization (Otsu threshold)
    if cfg.get("binarize", True):
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Remove thin border artifacts
    if cfg.get("remove_border", True):
        border = 5
        img[0:border, :] = 255
        img[-border:, :] = 255
        img[:, 0:border] = 255
        img[:, -border:] = 255

    return img


def _deskew(img: np.ndarray) -> np.ndarray:
    """Straighten tilted images using Hough transform angle detection."""
    try:
        coords = np.column_stack(np.where(img < 128))
        if len(coords) < 10:
            return img
        angle = cv2.minAreaRect(coords.astype(np.float32))[-1]
        if angle < -45:
            angle += 90
        if abs(angle) < 0.5:
            return img  # skip tiny corrections
        (h, w) = img.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    except Exception:
        return img


# ── 3. OCR ENGINES ──────────────────────────────────────────────────────────

def ocr_tesseract(img: np.ndarray, languages: list = None) -> tuple:
    """Returns (text, avg_confidence). Primary engine."""
    import pytesseract
    lang_str = "+".join(languages or ["vie", "eng"])
    config = "--oem 3 --psm 3"  # LSTM engine, fully automatic page segmentation
    pil_img = Image.fromarray(img)

    data = pytesseract.image_to_data(pil_img, lang=lang_str, config=config,
                                     output_type=pytesseract.Output.DICT)
    texts = [data["text"][i] for i in range(len(data["text"]))
             if int(data["conf"][i]) > 0 and data["text"][i].strip()]
    confs = [int(data["conf"][i]) for i in range(len(data["conf"]))
             if int(data["conf"][i]) > 0 and data["text"][i].strip()]

    text = " ".join(texts)
    avg_conf = (sum(confs) / len(confs)) if confs else 0
    return text, avg_conf


def ocr_easyocr(img: np.ndarray, languages: list = None) -> tuple:
    """Returns (text, avg_confidence). Secondary engine (deep learning)."""
    import easyocr
    langs = languages or ["vi", "en"]
    # Map tesseract lang codes to easyocr codes
    lang_map = {"vie": "vi", "eng": "en", "vi": "vi", "en": "en"}
    langs = [lang_map.get(l, l) for l in langs]

    reader = easyocr.Reader(langs, gpu=False, verbose=False)
    results = reader.readtext(img, batch_size=4)
    # results: [(bbox, text, confidence), ...]
    if not results:
        return "", 0
    texts = [r[1] for r in results]
    confs = [r[2] for r in results]
    return " ".join(texts), (sum(confs) / len(confs)) * 100


def ocr_google_vision(img: np.ndarray, api_key: str = None) -> tuple:
    """Returns (text, confidence=95). Tertiary engine (cloud)."""
    import base64
    import requests
    _, buffer = cv2.imencode(".png", img)
    b64 = base64.b64encode(buffer).decode()
    endpoint = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    payload = {"requests": [{"image": {"content": b64},
                              "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]}]}
    resp = requests.post(endpoint, json=payload, timeout=30)
    resp.raise_for_status()
    annotation = resp.json()["responses"][0].get("fullTextAnnotation", {})
    text = annotation.get("text", "")
    return text, 95.0 if text else 0.0


# ── 4. ORCHESTRATION ─────────────────────────────────────────────────────────

class OCRProcessor:
    def __init__(self, config: dict = None):
        self.cfg = config or {}
        self.languages = self.cfg.get("languages", ["vie", "eng"])
        self.min_confidence = self.cfg.get("min_confidence", 60)
        self.google_api_key = self.cfg.get("google_vision_api_key")
        self.preprocess_cfg = self.cfg.get("preprocessing", {})
        self.max_workers = self.cfg.get("max_workers", 4)

    def _ocr_image(self, img_array: np.ndarray, filename: str) -> dict:
        """Try OCR engines in order until confidence threshold met."""
        processed = preprocess_image(img_array, self.preprocess_cfg)

        engines_tried = []
        text, confidence, engine_used = "", 0, "none"

        # Primary: Tesseract
        try:
            text, confidence = ocr_tesseract(processed, self.languages)
            engine_used = "tesseract"
            engines_tried.append({"engine": "tesseract", "confidence": round(confidence, 1)})
        except Exception as e:
            engines_tried.append({"engine": "tesseract", "error": str(e)})

        # Secondary: EasyOCR (if tesseract confidence too low)
        if confidence < self.min_confidence:
            try:
                text2, conf2 = ocr_easyocr(processed, self.languages)
                engines_tried.append({"engine": "easyocr", "confidence": round(conf2, 1)})
                if conf2 > confidence:
                    text, confidence, engine_used = text2, conf2, "easyocr"
            except Exception as e:
                engines_tried.append({"engine": "easyocr", "error": str(e)})

        # Tertiary: Google Vision (only if API key provided and still low confidence)
        if confidence < self.min_confidence and self.google_api_key:
            try:
                text3, conf3 = ocr_google_vision(processed, self.google_api_key)
                engines_tried.append({"engine": "google_vision", "confidence": round(conf3, 1)})
                if conf3 > confidence:
                    text, confidence, engine_used = text3, conf3, "google_vision"
            except Exception as e:
                engines_tried.append({"engine": "google_vision", "error": str(e)})

        quality = "good" if confidence >= 80 else "fair" if confidence >= self.min_confidence else "poor"
        if quality == "poor":
            log.warning(f"  ⚠ Low OCR quality ({confidence:.0f}%) for {filename} — consider re-scanning")

        return {
            "filename": filename,
            "text": _postprocess_text(text),
            "confidence": round(confidence, 1),
            "engine_used": engine_used,
            "quality": quality,
            "engines_tried": engines_tried,
            "char_count": len(text.strip())
        }

    def process_file(self, file_path: str) -> list:
        """Process a single file. Returns list of page results."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        results = []

        if suffix == ".pdf":
            if is_scanned_pdf(file_path):
                log.info(f"  PDF scan detected: {path.name}")
                images = pdf_to_images(file_path)
                for i, pil_img in enumerate(images, 1):
                    img_array = np.array(pil_img)
                    result = self._ocr_image(img_array, f"{path.name}:page{i}")
                    results.append(result)
            else:
                log.info(f"  PDF text-based: {path.name} — extracting directly")
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                results.append({
                    "filename": path.name,
                    "text": text,
                    "confidence": 100.0,
                    "engine_used": "pdfplumber",
                    "quality": "good",
                    "engines_tried": [],
                    "char_count": len(text.strip())
                })

        elif suffix in {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}:
            pil_img = Image.open(file_path).convert("RGB")
            img_array = np.array(pil_img)
            result = self._ocr_image(img_array, path.name)
            results.append(result)

        else:
            log.warning(f"  Skipping unsupported file type: {path.name}")

        return results

    def process_directory(self, input_dir: str, output_txt: str = "ocr_output.txt",
                          quality_report: str = "ocr_quality_report.json") -> dict:
        """Batch-process all supported files in a directory."""
        input_path = Path(input_dir)
        supported_exts = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
        files = sorted(f for f in input_path.iterdir() if f.suffix.lower() in supported_exts)

        if not files:
            raise FileNotFoundError(f"No supported files found in {input_dir}")

        log.info(f"Processing {len(files)} files with up to {self.max_workers} workers...")

        all_sections = []
        all_results = []
        start = time.monotonic()

        # Parallel processing per file
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self.process_file, str(f)): f for f in files}
            completed = 0
            for future in as_completed(futures):
                f = futures[future]
                completed += 1
                try:
                    page_results = future.result()
                    all_results.extend(page_results)
                    # Build docs_content.txt section
                    combined_text = "\n\n".join(r["text"] for r in page_results if r["text"].strip())
                    if combined_text.strip():
                        all_sections.append(f"=== {f.name} ===\n{combined_text}")
                    avg_conf = sum(r["confidence"] for r in page_results) / len(page_results)
                    log.info(f"  [{completed}/{len(files)}] ✓ {f.name} — {avg_conf:.0f}% confidence")
                except Exception as e:
                    log.error(f"  [{completed}/{len(files)}] ✗ {f.name} — {e}")
                    all_results.append({"filename": f.name, "error": str(e), "confidence": 0, "quality": "failed"})

        elapsed = time.monotonic() - start

        # Write output text (same format as docs_content.txt)
        Path(output_txt).write_text("\n\n".join(all_sections), encoding="utf-8")
        log.info(f"✓ OCR text → {output_txt}")

        # Quality report
        good = sum(1 for r in all_results if r.get("quality") == "good")
        fair = sum(1 for r in all_results if r.get("quality") == "fair")
        poor = sum(1 for r in all_results if r.get("quality") == "poor")
        failed = sum(1 for r in all_results if r.get("quality") == "failed")
        avg_conf = sum(r.get("confidence", 0) for r in all_results) / len(all_results) if all_results else 0

        report = {
            "summary": {
                "total_files": len(files),
                "total_pages": len(all_results),
                "avg_confidence": round(avg_conf, 1),
                "quality_breakdown": {"good": good, "fair": fair, "poor": poor, "failed": failed},
                "elapsed_seconds": round(elapsed, 1)
            },
            "files": all_results
        }
        Path(quality_report).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info(f"✓ Quality report → {quality_report}")
        log.info(f"  Avg confidence: {avg_conf:.0f}% | Good: {good} Fair: {fair} Poor: {poor} Failed: {failed}")

        if poor > 0 or failed > 0:
            log.warning(f"  ⚠ {poor + failed} pages with poor quality — check ocr_quality_report.json")

        return report


# ── 5. POST-PROCESSING ───────────────────────────────────────────────────────

def _postprocess_text(text: str) -> str:
    """Remove OCR artifacts and normalize text."""
    import re
    # Remove stray single characters on their own lines (common OCR noise)
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Keep if meaningful (more than 1 char, or empty line as paragraph break)
        if len(stripped) > 1 or stripped == "":
            cleaned.append(line)
    text = "\n".join(cleaned)
    # Collapse 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove form-feed characters
    text = text.replace("\x0c", "\n")
    return text.strip()


# ── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Usage: python ocr_processor.py <input_dir> [output.txt] [quality_report.json] [config.json]
    if len(sys.argv) < 2:
        print("Usage: python ocr_processor.py <input_dir_or_file> [output.txt] [quality_report.json] [config.json]")
        sys.exit(1)

    config = {}
    if len(sys.argv) > 4 and Path(sys.argv[4]).exists():
        config = json.loads(Path(sys.argv[4]).read_text())

    processor = OCRProcessor(config)
    input_path = sys.argv[1]

    if Path(input_path).is_file():
        results = processor.process_file(input_path)
        text = "\n\n".join(r["text"] for r in results)
        out = sys.argv[2] if len(sys.argv) > 2 else "ocr_output.txt"
        Path(out).write_text(text, encoding="utf-8")
        print(f"✓ Saved → {out}")
    else:
        processor.process_directory(
            input_path,
            output_txt=sys.argv[2] if len(sys.argv) > 2 else "ocr_output.txt",
            quality_report=sys.argv[3] if len(sys.argv) > 3 else "ocr_quality_report.json"
        )
```

---

## Config File (ocr_config.json)

```json
{
  "languages": ["vie", "eng"],
  "min_confidence": 60,
  "max_workers": 4,
  "google_vision_api_key": null,
  "preprocessing": {
    "denoise": true,
    "upscale": true,
    "enhance_contrast": true,
    "deskew": true,
    "binarize": true,
    "remove_border": true
  }
}
```

**`languages`**: Tesseract lang codes. Vietnamese = `vie`, English = `eng`. For mixed docs use `["vie", "eng"]`.
**`min_confidence`**: If primary engine scores below this (0-100), try fallback engines.
**`google_vision_api_key`**: Set to enable cloud OCR as tertiary fallback. Leave `null` to skip.
**`max_workers`**: Thread pool size for parallel file processing. Set to 1 for debugging.

---

## Dependencies

```bash
# Core OCR
pip install pytesseract pillow opencv-python-headless numpy

# PDF handling
pip install pdfplumber pdf2image

# Secondary OCR engine (optional but recommended)
pip install easyocr

# Google Vision (tertiary, optional)
pip install google-cloud-vision

# System: Tesseract binary + Vietnamese language pack
# Windows: download from https://github.com/UB-Mannheim/tesseract/wiki
#   → include Vietnamese (vie) during install, or copy vie.traineddata to tessdata/
# Linux:  sudo apt install tesseract-ocr tesseract-ocr-vie
# macOS:  brew install tesseract tesseract-lang
```

---

## Integration with chatbot-tester Pipeline

When `gdrive-doc-reader` downloads files that include scanned PDFs or images, run `ocr_processor.py` first:

```bash
# Step 0: OCR (only when source docs are scanned)
python ocr_processor.py ./downloaded_docs/ ocr_output.txt ocr_quality_report.json

# Step 1: QA generation uses OCR output instead of docs_content.txt
python qa_generator.py ocr_output.txt test_questions.json

# Steps 2-6 continue normally...
```

The `chatbot-tester` orchestrator should check for scanned content:
```python
# In run_chatbot_test.py — detect if OCR step is needed
from pathlib import Path
import pdfplumber

def needs_ocr(docs_dir: str) -> bool:
    for f in Path(docs_dir).glob("*.pdf"):
        try:
            with pdfplumber.open(f) as pdf:
                if sum(len(page.extract_text() or "") for page in pdf.pages[:3]) < 50:
                    return True
        except Exception:
            return True
    image_exts = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
    return any(f.suffix.lower() in image_exts for f in Path(docs_dir).iterdir())
```

---

## Quality Report Output (ocr_quality_report.json)

```json
{
  "summary": {
    "total_files": 5,
    "total_pages": 12,
    "avg_confidence": 84.2,
    "quality_breakdown": {"good": 9, "fair": 2, "poor": 1, "failed": 0},
    "elapsed_seconds": 18.4
  },
  "files": [
    {
      "filename": "invoice_scan.pdf:page1",
      "confidence": 91.3,
      "engine_used": "tesseract",
      "quality": "good",
      "char_count": 847,
      "engines_tried": [{"engine": "tesseract", "confidence": 91.3}]
    },
    {
      "filename": "blurry_photo.jpg",
      "confidence": 52.1,
      "engine_used": "easyocr",
      "quality": "poor",
      "char_count": 134,
      "engines_tried": [
        {"engine": "tesseract", "confidence": 31.4},
        {"engine": "easyocr", "confidence": 52.1}
      ]
    }
  ]
}
```

---

## Handwriting / Cursive Text

Tesseract is poor at handwriting. Override engine selection for handwritten pages:

```python
# Force Google Vision (best handwriting) or EasyOCR for known handwritten files
if 'handwritten' in path.name.lower() or self.cfg.get('force_handwriting'):
    text, conf = ocr_google_vision(processed, self.google_api_key)
    engine_used = 'google_vision'
```

For Vietnamese handwriting, Google Vision currently outperforms Tesseract by ~3× accuracy.

## Table Structure Extraction

Plain text OCR loses table layout. For table-heavy docs use Tesseract's `--psm 6` (single
uniform block) + post-process by column position, or use Camelot for PDF tables:

```python
import camelot
tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')  # 'stream' for borderless
for t in tables:
    rows = t.df.values.tolist()  # list of rows
```

## Multi-Column Layout (Newspaper / 2-Column PDF)

```python
# Detect columns by clustering text x-coordinates, then OCR each column separately
import pytesseract
data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
# Group by block_num; sort by left → text per column
```

For complex layouts, `pdfplumber.extract_text(layout=True)` may preserve column order
better than naive OCR.

## Key Principles

- **Detect before OCR**: Always check if a PDF has a text layer first — OCRing a text PDF wastes time and degrades quality.
- **Preprocessing beats engine choice**: A well-deskewed, denoised image in Tesseract beats a raw noisy image in any engine.
- **Confidence is a signal, not a guarantee**: High Tesseract confidence on a badly preprocessed image can still be wrong — always inspect `poor` quality files manually.
- **Vietnamese needs `vie` lang pack**: Without it, diacritics (ă, ê, ơ, ư, tones) will be garbled. Verify with `tesseract --list-langs` that `vie` appears.
- **Output format must match `docs_content.txt`**: Use `=== filename ===` headers so qa-generator and other downstream skills work without modification.
- **Never silently skip failed files**: Log errors and include them in the quality report with `quality: "failed"` so the pipeline knows what's missing.
