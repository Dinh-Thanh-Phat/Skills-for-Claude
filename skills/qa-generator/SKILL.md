---
name: qa-generator
description: Generate comprehensive test questions with expected answers from document content using Claude API or Groq API. Use when you need to create a test question bank from reference documents to evaluate a chatbot or AI system. Triggers on: "generate test questions from docs", "create QA pairs from document", "make test cases from content", "generate chatbot test questions". Used as Step 2 in chatbot testing pipeline. Outputs structured JSON with factual, reasoning, and edge case questions.
---

# QA Generator — Test Question Generator

Generates a diverse set of test questions with expected answers from document content.

## Question Categories

Generate 3 types of questions to test different capabilities:

### 1. Factual Questions (40% of total)
Test direct knowledge retrieval from documents.

### 2. Reasoning Questions (40% of total)
Test ability to synthesize and reason across information.

### 3. Edge Cases (20% of total)
Test boundary conditions, ambiguous scenarios, unusual inputs.

## Output Format

File: `test_questions.json`
```json
[
  {
    "id": "q001",
    "question": "Điều 8 Nghị định 174/2025 quy định mức giảm thuế GTGT là bao nhiêu?",
    "expected_answer": "Mức giảm thuế GTGT là 8% cho các hàng hóa, dịch vụ theo quy định. Điều 8, Khoản 1 - GTGT_ND_174_2025",
    "category": "factual",
    "difficulty": "easy",
    "source_doc": "GTGT_ND_174_2025",
    "keywords": ["thuế GTGT", "mức giảm", "8%"]
  }
]
```

### Citation Rule (MANDATORY)
`expected_answer` PHẢI kết thúc bằng: `"Điều X, Khoản Y - tên_file"` hoặc `"Phần [tên phần] - tên_file"`.

Format chuẩn:
```
[đáp án đầy đủ]. Điều X, Khoản Y - SOURCE_DOC_NAME
```

**KHÔNG chấp nhận:**
- Thiếu citation ở cuối
- Dùng `Dieu/Khoan` thay vì `Điều/Khoản`
- Citation ở giữa câu thay vì cuối câu

## Groq Implementation (cho pipeline hiện tại)

### ⚠️ Critical Rules (Lesson Learned)

#### 0. Post-generation quality audit — chạy trước khi lưu
```python
# Sau mỗi batch, LUÔN chạy audit. Không pass audit → tái sinh batch đó.
QUALITY_THRESHOLDS = {
    'min_body_chars': 50,      # Phần đáp án (không kể citation) phải ≥ 50 ký tự
    'max_fail_ratio': 0.2,     # Nếu >20% batch lỗi → regenerate toàn bộ batch
}

def audit_batch(qs: list, source_doc: str) -> list[str]:
    issues = []
    for q in qs:
        ans  = q.get('expected_answer', '').strip()
        body = re.sub(r'\s*(?:Điều|Phần|Khoản)\s+[\w\s,]+[-–]\s*\S+\s*$', '', ans).strip()

        # 1. Câu trả lời bắt đầu bằng câu hỏi (echo/repeat)
        q_start = q.get('question','')[:25].lower()
        if ans[:25].lower().startswith(q_start[:15]):
            issues.append(f"{q['id']}: REPEAT — answer echoes question")

        # 2. Quá ngắn (one-value: "Có", "8%", "Bộ Tài chính")
        if len(body) < QUALITY_THRESHOLDS['min_body_chars']:
            issues.append(f"{q['id']}: SHORT — body={len(body)} chars")

        # 3. Model không tìm thấy thông tin (hallucinated refusal)
        refuse_signals = ['không đề cập', 'không tìm thấy', 'không có thông tin',
                          'không được đề cập', 'không nêu rõ', 'not mentioned']
        if any(s in ans.lower() for s in refuse_signals):
            issues.append(f"{q['id']}: REFUSE — model could not find info")

        # 4. Có ký tự xuống dòng \\n trong answer
        if '\n' in ans:
            issues.append(f"{q['id']}: NEWLINE — strip with ans.replace('\\n',' ')")

        # 5. Format citation sai: Điều X.Y, Khoản A (uppercase)
        if re.search(r'Điều \d+\.\d+', ans):
            issues.append(f"{q['id']}: FORMAT — Dieu X.Y")
        if re.search(r'Khoản [A-Z]\b', ans):
            issues.append(f"{q['id']}: FORMAT — Khoan uppercase")

        # 6. Không có end-citation
        if not re.search(r'[-–]\s*' + re.escape(source_doc) + r'\s*$', ans.strip()):
            issues.append(f"{q['id']}: NO_CITATION")

    return issues
```

#### 1. Batch nhỏ — tối đa 5 câu/call
```python
BATCH_SIZE = 5  # KHÔNG bao giờ vượt quá 5 câu/call với Groq free tier
# Lý do: max_tokens=1500 chỉ đủ cho ~5 câu có citation đầy đủ
# Nếu hỏi 20+ câu → JSON bị truncate → parse lỗi → 0 câu
```

#### 2. Dùng response_format để tránh JSON truncation
```python
# Groq hỗ trợ Structured Outputs — dùng response_format thay vì parse regex
response = client.chat.completions.create(
    model=MODEL,
    messages=[...],
    response_format={"type": "json_object"},  # Đảm bảo output luôn là JSON hợp lệ
    max_tokens=800,
)
```

#### 3. Model selection
```python
# Groq models (llama-3.1-8b-instant + llama-3.3-70b-versatile SHUT DOWN 2026-08-16):
GENERATION_MODEL  = "openai/gpt-oss-20b"   # Bulk generation (nhanh, rẻ)
ENRICHMENT_MODEL  = "openai/gpt-oss-120b"  # Citation enrichment (chất lượng cao)
# KHÔNG dùng model nhỏ để enrich citations — nó leak prompt và tạo citation sai
# (measured on Llama 3.x 8b, re-verify với gpt-oss-20b)
```

> ⚠️ Trước mỗi lần chạy: check https://console.groq.com/docs/deprecations + `client.models.list()`
> — Groq shut down model với ~2 tháng báo trước, pipeline gãy âm thầm.

#### 4. Prompt bằng tiếng Anh cho Groq — bắt buộc anti-echo + anti-short
```python
# Small models (8b) follow English instructions better than Vietnamese
# Vietnamese prompts → model echos prompt into output (prompt leaking)
# (measured on Llama 3.x, re-verify với gpt-oss)
# Thêm 2 ràng buộc mới: không lặp câu hỏi, câu trả lời phải đủ dài
prompt = f"""You are a Vietnamese legal QA engineer.
Document: {source_doc}
{doc_text[:3000]}

Create {n_q} test questions in VIETNAMESE. Return ONLY a JSON array.
Each object: {{"question": str, "expected_answer": str, "category": str, "difficulty": str, "source_doc": "{source_doc}", "keywords": []}}

RULES for expected_answer:
- MUST end with citation: "Dieu X, Khoan Y - {source_doc}"
- MUST be ≥ 50 characters of actual content (not counting citation)
- Do NOT start the answer by repeating or restating the question
- Do NOT use \\n newlines inside the answer string
- If question is yes/no, still explain WHY with at least 2 sentences

No explanation outside JSON. JSON array only."""
```

**Presence penalty để giảm echo (Groq API):**
```python
# Research: presence_penalty giảm nguy cơ model lặp lại phrase từ prompt
response = client.chat.completions.create(
    model=MODEL,
    messages=[...],
    response_format={"type": "json_object"},
    max_tokens=800,
    presence_penalty=0.3,   # Giảm echo câu hỏi vào đáp án
    frequency_penalty=0.1,  # Giảm lặp từ trong đáp án
)
```

#### 5. Post-processing: normalize citation format + clean structural errors
```python
import re

def normalize_citations(text: str) -> str:
    """Fix all known citation issues from Groq small models + format errors."""
    # Strip newlines inside answer (model sometimes uses \n before citation)
    text = text.replace('\n', ' ').strip()

    replacements = [
        # Non-accented → accented
        (r'\bDieu\b',  'Điều'),
        (r'\bKhoan\b', 'Khoản'),
        (r'\bDiem\b',  'Điểm'),
        (r'\bPhan\b',  'Phần'),
        # Uppercase Khoản letter → Điểm lowercase  (e.g. "Khoản A" → "Điểm a")
        (r'\bKhoản ([A-Z])\b', lambda m: f'Điểm {m.group(1).lower()}'),
        # "Điều 1.2" → "Điều 1, Khoản 2"
        (r'Điều (\d+)\.(\d+)', r'Điều \1, Khoản \2'),
        # "Dieu 1.2" (unaccented + dot) → "Điều 1, Khoản 2"
        (r'\bDieu (\d+)\.(\d+)\b', r'Điều \1, Khoản \2'),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text) if not callable(repl) else re.sub(pattern, repl, text)
    return text
```

#### 6. Validate end-citation — không chấp nhận thiếu
```python
def has_valid_citation(answer: str, source_doc: str) -> bool:
    """Citation phải ở CUỐI answer dạng '- source_doc'."""
    return bool(re.search(r'[-–]\s*' + re.escape(source_doc) + r'\s*$', answer))

# Nếu thiếu → re-enrich bằng enrichment_model (70b), không giữ answer lỗi
```

#### 7. Rate limit: sleep + exponential backoff
```python
import time, random

SLEEP_BETWEEN_CALLS = 12  # giây — giữ dưới 30K TPM Groq free tier

def call_with_backoff(client, **kwargs):
    for attempt in range(4):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            if 'rate_limit' in str(e).lower() or '429' in str(e):
                wait = (2 ** attempt) + random.uniform(0, 1)  # exponential + jitter
                print(f"Rate limit, waiting {wait:.1f}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Max retries exceeded")
```

### Full Script Template (Groq)

```python
import io, sys, json, re, os, time, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

from pathlib import Path
from groq import Groq

BASE = Path('D:/HK8/Learning/DQ/Agentic')
GENERATION_MODEL  = "openai/gpt-oss-20b"   # llama-3.1-8b-instant shut down 2026-08-16
ENRICHMENT_MODEL  = "openai/gpt-oss-120b"  # llama-3.3-70b-versatile shut down 2026-08-16
BATCH_SIZE        = 5
MAX_DOC_CHARS     = 3000
SLEEP_S           = 12

def load_env():
    for line in (BASE / '.env').read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1); os.environ[k.strip()] = v.strip()

def normalize_citations(text):
    for pattern, repl in [
        (r'\bDieu\b', 'Điều'), (r'\bKhoan\b', 'Khoản'),
        (r'\bDiem\b', 'Điểm'), (r'\bPhan\b', 'Phần'),
    ]:
        text = re.sub(pattern, repl, text)
    return text

def has_valid_citation(answer, source_doc):
    return bool(re.search(r'[-–]\s*' + re.escape(source_doc) + r'\s*$', answer.strip()))

def call_groq(client, model, messages, max_tokens=800, use_json=True):
    kwargs = dict(model=model, messages=messages, max_tokens=max_tokens, temperature=0.1)
    if use_json:
        kwargs['response_format'] = {"type": "json_object"}
    for attempt in range(4):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            if '429' in str(e) or 'rate' in str(e).lower():
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"  Rate limit, retry in {wait:.1f}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Groq max retries exceeded")

def generate_batch(client, doc_name, doc_text, n_q):
    prompt = (
        f'Document name: {doc_name}\n'
        f'Content:\n{doc_text[:MAX_DOC_CHARS]}\n\n'
        f'Create {n_q} Vietnamese test questions. Return JSON: {{"questions": [...]}}\n'
        f'Each item: {{"question": "...", "expected_answer": "answer. Dieu X, Khoan Y - {doc_name}", '
        f'"category": "factual|reasoning|edge_case", "difficulty": "easy|medium|hard", '
        f'"source_doc": "{doc_name}", "keywords": []}}\n'
        f'Output ONLY the JSON object.'
    )
    resp = call_groq(client, GENERATION_MODEL, [{'role': 'user', 'content': prompt}])
    raw  = resp.choices[0].message.content.strip()
    data = json.loads(raw)
    qs   = data.get('questions', data) if isinstance(data, dict) else data
    for q in qs:
        q['expected_answer'] = normalize_citations(q.get('expected_answer', ''))
    return qs

def enrich_citation(client, q, doc_text):
    src = q['source_doc']
    prompt = (
        f'Document: {src}\n{doc_text[:MAX_DOC_CHARS]}\n\n'
        f'Q: {q["question"]}\nCurrent answer: {q["expected_answer"]}\n\n'
        f'Rewrite answer in Vietnamese ending with citation: "[answer]. Dieu X, Khoan Y - {src}"\n'
        f'Reply with ONLY the rewritten answer string.'
    )
    resp = call_groq(client, ENRICHMENT_MODEL,
                     [{'role': 'user', 'content': prompt}],
                     max_tokens=450, use_json=False)
    new = normalize_citations(resp.choices[0].message.content.strip().split('\n\n')[0])
    if len(new) > 15:
        q['expected_answer'] = new
    return q
```

## Claude API Implementation (alternative)

```python
import anthropic, json, re
from pathlib import Path

class QAGenerator:
    def __init__(self, model="claude-sonnet-4-6"):
        self.client = anthropic.Anthropic()
        self.model  = model

    def generate_questions(self, docs_file, num_questions=20, output_file="test_questions.json"):
        docs = Path(docs_file).read_text(encoding='utf-8')[:100_000]
        n_f  = int(num_questions * 0.4)
        n_r  = int(num_questions * 0.4)
        n_e  = num_questions - n_f - n_r

        prompt = f"""You are a QA engineer. Generate {num_questions} test questions from this documentation.

<documentation>{docs}</documentation>

Return ONLY a JSON array. Each object:
- "id": "q001"...
- "question": string
- "expected_answer": string — MUST end with citation: "Điều X, Khoản Y - [source_section]"
- "category": "factual"|"reasoning"|"edge_case"
- "difficulty": "easy"|"medium"|"hard"
- "source_doc": string (section/file name)
- "keywords": string[]

Distribution: {n_f} factual, {n_r} reasoning, {n_e} edge_case.
Rules: answerable from docs only; citation mandatory at end of expected_answer."""

        resp = self.client.messages.create(
            model=self.model, max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )
        qs = json.loads(re.search(r'\[[\s\S]*\]', resp.content[0].text).group())
        Path(output_file).write_text(json.dumps(qs, indent=2, ensure_ascii=False), encoding='utf-8')
        return qs
```

## Validation Checklist (run after generation)

```python
def validate_questions(qs: list, source_doc: str = "") -> list[str]:
    issues = []
    for q in qs:
        a = q.get('expected_answer', '')
        if not a: issues.append(f"{q['id']}: missing expected_answer")
        if not has_valid_citation(a, source_doc or q.get('source_doc','')): 
            issues.append(f"{q['id']}: missing end-citation")
        if 'Dieu' in a or 'Khoan' in a:
            issues.append(f"{q['id']}: non-accented citation (run normalize_citations)")
        if len(a) < 20:
            issues.append(f"{q['id']}: answer too short ({len(a)} chars)")
    return issues
```

## Dependencies
```bash
pip install anthropic groq
```

## Key Principles

### Generation
- **Batch size ≤ 5** khi dùng Groq free tier — tránh JSON truncation do token budget
- **`response_format={"type":"json_object"}`** — buộc Groq output JSON hợp lệ
- **Model split**: 8b-instant cho generation, 70b-versatile cho enrichment/fix
- **Prompt bằng tiếng Anh** với Groq — tránh small model echo prompt vào output
- **Anti-echo instruction**: thêm "Do NOT start the answer by repeating the question" vào prompt
- **Anti-short instruction**: thêm "MUST be ≥ 50 characters of actual content" vào prompt
- **presence_penalty=0.3 + frequency_penalty=0.1** — giảm repetition trong Groq calls

### Post-processing (bắt buộc sau mỗi batch)
- **normalize_citations()** sau mọi answer: accented, newline strip, `Điều X.Y`, `Khoản A`
- **audit_batch()** — phát hiện: REPEAT, SHORT (<50 chars body), REFUSE signals, NEWLINE, FORMAT
- **Threshold**: >20% batch lỗi → regenerate toàn bộ batch đó thay vì enrich từng câu
- **Validate end-citation** trước khi lưu — `- source_doc` phải ở cuối string

### Dedup similar questions

Even with batches, the same fact can produce near-duplicate questions. Dedup by similarity
of the question text before saving:

```python
from rapidfuzz import fuzz
def dedup_questions(qs, threshold=85):
    kept = []
    for q in qs:
        if not any(fuzz.ratio(q['question'], k['question']) > threshold for k in kept):
            kept.append(q)
    return kept
```

### Enforce difficulty distribution

The 40/40/20 mix is requested in the prompt but small models drift. Enforce post-hoc:

```python
desired = {'easy': 0.4, 'medium': 0.4, 'hard': 0.2}
buckets = {k: [q for q in qs if q['difficulty'] == k] for k in desired}
target = {k: int(len(qs) * v) for k, v in desired.items()}
final = []
for k, n in target.items():
    final += buckets[k][:n]   # take first N of each (or random.sample)
```

If a bucket is short, regenerate just that difficulty.

### Re-enrichment (70b)
- **Guard against REFUSE**: nếu answer chứa "không đề cập / không tìm thấy" → mark failed, KHÔNG lưu
- **Max tokens 500** khi enrich để tránh cắt giữa chừng (lesson: 300 tokens quá nhỏ cho câu dài)
- **Exponential backoff + jitter** khi gặp rate limit 429
- **docs_content.txt scope**: khi cherry-pick câu hỏi từ slug khác → phải reference đúng docs_content.txt của slug nguồn
