---
name: chatbot-tester
description: Main orchestrator for automated AI chatbot testing pipeline. Use this skill whenever the user wants to test an AI chatbot's accuracy, performance, or quality — especially when given a Google Drive link with documentation and a chatbot URL. Triggers on: "test my chatbot", "evaluate chatbot accuracy", "run chatbot QA", "benchmark my AI assistant", "test bot with documents". Coordinates the full pipeline: read docs → generate questions → call chatbot → evaluate responses → analyze performance → generate report.
---

# Chatbot Tester — Main Orchestrator

This skill coordinates the full automated chatbot testing pipeline. Use it whenever someone wants to evaluate an AI chatbot's accuracy or performance against reference documentation.

## Input Contract

Minimum required:
- `chatbot_url`: The chatbot API endpoint or web URL
- `gdrive_link`: Google Drive folder or file link containing reference docs

Optional config (prompt the user or use defaults):
```json
{
  "num_questions": 20,
  "question_categories": ["factual", "reasoning", "edge_case"],
  "difficulty_mix": {"easy": 0.4, "medium": 0.4, "hard": 0.2},
  "rate_limit_ms": 1000,
  "max_retries": 3,
  "accuracy_threshold": 0.7,
  "response_time_threshold_ms": 3000,
  "output_dir": "./chatbot-test-results",
  "use_ui_automator": false,
  "resume": true
}
```

`chatbot_url` is used by BOTH Step 3 variants: `use_ui_automator: true` → `chatbot_ui_automator.py`
(web URL), otherwise `chatbot_caller.py` (JSON endpoint / `api_config.json`). There is no
separate `api_endpoint` key. `resume: true` (default) skips a step whose output file already
exists and is non-empty; set `false` to force a full re-run.

## Pipeline Steps

Execute each step in order. Each step outputs to `output_dir/`:

```
Step 0 (optional): ocr-processor → ocr_output.txt   [if source has scanned PDFs/images]
Step 1: gdrive-doc-reader    → docs_content.txt
Step 2: qa-generator         → test_questions.json
Step 3: chatbot-api-caller   → raw_responses.json   (or chatbot-ui-automator for web UI)
Step 4: response-evaluator   → evaluations.json
Step 5: performance-analyzer → metrics.json + charts/
Step 6: test-reporter        → report.html (+ report.pdf optional)
```

**Step-number → skill mapping (Agentic project `run.py`):** `--step 2` = qa-generator ·
`--step 3` = chatbot-api-caller / chatbot-ui-automator · `--step 3b` = response-evaluator
(skill Step 4) · `--step 4` = Excel export (not a skill in this chain).

> ⚠️ **Known limitations (not yet implemented):**
> - **Step 0 needs local files.** `ocr-processor` reads a local folder, but `gdrive-doc-reader`
>   extracts text in memory and saves no source files. Download scanned PDFs/images yourself,
>   OCR them, and merge `ocr_output.txt` into `docs_content.txt`.
> - **`qa_generator.py` has no CLI.** `qa-generator` provides template code only (no
>   `__main__`, no fixed args). The `qa_generator.py` step in the template below assumes you
>   wrote one taking `<docs_content.txt> <num_questions> <test_questions.json>`.

**Pre-flight: validate chatbot reachable** before running full batch:
```python
# Send 1 throwaway question through the real step-3 script; abort early if it fails
import json, subprocess
from pathlib import Path
pre_q, pre_out = output_dir / "preflight_q.json", output_dir / "preflight_resp.json"
pre_q.write_text(json.dumps([{"id": "preflight", "question": "ping"}]), encoding="utf-8")
subprocess.run(["python", "chatbot_caller.py", str(pre_q), chatbot_url, str(pre_out)], check=True)
r = json.loads(pre_out.read_text(encoding="utf-8"))[0]
if not r["success"] or not (r["response"] or "").strip() or "sorry" in r["response"].lower():
    raise RuntimeError(f"Chatbot pre-flight failed — aborting. Response: {str(r['response'])[:200]} / {r['error']}")
```

## Orchestration Protocol

### 1. Validate Inputs
Before starting, confirm:
- Chatbot URL is reachable (quick HEAD request)
- Google Drive link format is valid
- Output directory exists or can be created
- Required Python packages are installed

If anything is missing, stop and tell the user specifically what's wrong.

### 2. Run Each Step
For each step:
1. Invoke the corresponding skill / run the corresponding script
2. Verify the output file was created and is non-empty
3. If output missing or empty → retry once, then STOP with clear error message
4. Log progress: "Step N/6 complete: [step name]"

Never silently skip a failed step. Fail loud, fail early.

### 3. Error & Retry Logic
Implemented inside `run_pipeline()` below (subprocess per step, retry with `2 ** attempt`
backoff, raise `RuntimeError` after `max_retries`). There is no separate `run_step()` helper.

### 4. Progress Reporting
Print a status line after each step:
```
[1/6] ✓ gdrive-doc-reader — 3 docs, 12,450 words
[2/6] ✓ qa-generator — 20 questions generated
[3/6] ✓ chatbot-api-caller — 20/20 responses (18 success, 2 retry)
[4/6] ✓ response-evaluator — avg score: 73.2%
[5/6] ✓ performance-analyzer — avg: 1,230ms, p95: 2,890ms
[6/6] ✓ test-reporter — report saved to ./chatbot-test-results/report.html
```

## Python Script Template

Write `run_chatbot_test.py` to implement the pipeline:

```python
import json
import time
import subprocess
from pathlib import Path

def run_pipeline(chatbot_url: str, gdrive_link: str, config: dict) -> str:
    output_dir = Path(config.get("output_dir", "./chatbot-test-results"))
    output_dir.mkdir(parents=True, exist_ok=True)

    steps = [
        {
            "name": "gdrive-doc-reader",
            "script": "gdrive_reader.py",
            "args": [gdrive_link, str(output_dir / "docs_content.txt")],
            "output": output_dir / "docs_content.txt"
        },
        {
            "name": "qa-generator",
            "script": "qa_generator.py",
            "args": [str(output_dir / "docs_content.txt"), str(config.get("num_questions", 20)), str(output_dir / "test_questions.json")],
            "output": output_dir / "test_questions.json"
        },
        {
            "name": "chatbot-ui-automator" if config.get("use_ui_automator") else "chatbot-api-caller",
            "script": "chatbot_ui_automator.py" if config.get("use_ui_automator") else "chatbot_caller.py",
            "args": [str(output_dir / "test_questions.json"), chatbot_url, str(output_dir / "raw_responses.json")],
            "output": output_dir / "raw_responses.json"
        },
        {
            "name": "response-evaluator",
            "script": "response_evaluator.py",
            "args": [str(output_dir / "raw_responses.json"), str(output_dir / "test_questions.json"), str(output_dir / "evaluations.json")],
            "output": output_dir / "evaluations.json"
        },
        {
            "name": "performance-analyzer",
            "script": "performance_analyzer.py",
            "args": [str(output_dir / "raw_responses.json"), str(output_dir / "evaluations.json"), str(output_dir)],
            "output": output_dir / "metrics.json"
        },
        {
            "name": "test-reporter",
            "script": "test_reporter.py",
            "args": [str(output_dir / "metrics.json"), str(output_dir / "evaluations.json"), chatbot_url, str(output_dir / "report.html")],
            "output": output_dir / "report.html"
        },
    ]

    for i, step in enumerate(steps, 1):
        if config.get("resume", True) and step["output"].exists() and step["output"].stat().st_size > 0:
            print(f"[{i}/6] ↷ {step['name']} — output exists, skipped (resume)")
            continue
        print(f"[{i}/6] Running {step['name']}...")
        for attempt in range(config.get("max_retries", 3)):
            result = subprocess.run(
                ["python", step["script"]] + step["args"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and step["output"].exists():
                print(f"[{i}/6] ✓ {step['name']}")
                break
            if attempt == config.get("max_retries", 3) - 1:
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                raise RuntimeError(f"Step {step['name']} failed after {attempt+1} attempts")
            time.sleep(2 ** attempt)

    report_path = str(output_dir / "report.html")
    print(f"\n✅ Test complete! Report: {report_path}")
    return report_path

if __name__ == "__main__":
    import sys
    config = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8")) if len(sys.argv) > 3 else {}
    run_pipeline(sys.argv[1], sys.argv[2], config)
```

## Final Output Message

```
✅ Chatbot test complete!

📊 Results Summary:
  • Questions tested: 20
  • Accuracy: 73.2% (threshold: 70%) ✓
  • Avg response time: 1,230ms (threshold: 3,000ms) ✓
  • Success rate: 90%

📄 Report: ./chatbot-test-results/report.html
📁 Raw data: ./chatbot-test-results/
```

If accuracy < threshold or response time > threshold, add a warning:
```
⚠️ WARNING: Accuracy 58% is below threshold 70%
   See "Failed Test Cases" section in the report for details.
```

## Lesson Learned — Common Failure Modes

### 1. Chatbot trả về lỗi nhưng step3 vẫn báo "success"
"Success" chỉ nghĩa là request được gửi thành công, không nghĩa chatbot trả lời đúng.
Sau step3, luôn kiểm tra:
```python
error_responses = [r for r in raw if 'Sorry' in r.get('response','') or not r.get('response','').strip()]
if len(error_responses) > len(raw) * 0.5:
    print(f"WARNING: {len(error_responses)}/{len(raw)} responses are errors — chatbot may be down or out of credits")
```

### 2. Step3b evaluate → 0% accuracy sau khi step3 OK
Nguyên nhân thường gặp: chatbot hết OpenRouter credits → trả về lỗi dạng "Sorry, I could not process..."
Kiểm tra trước: ping chatbot với 1 câu test trước khi chạy full 50 câu.

### 3. Groq rate limit giữa chừng — mất evaluation
Script phải có resume capability: lưu progress sau mỗi call, skip câu đã evaluate khi re-run.
```python
# Khi resume: load evaluations.json hiện có, chỉ evaluate những câu chưa có
done_ids = {e['question_id'] for e in existing_evals}
pending  = [r for r in responses if r['question_id'] not in done_ids]
```

### 4. docs_content.txt scope mismatch khi tạo slug mới
Khi tạo slug cherry-pick câu từ slug khác (ví dụ: copy 50 câu từ incard_prod vào incard_50):
- docs_content.txt của slug mới phải là docs của SOURCE slug, không phải slug đích
- drive_map trong step4 phải merge từ source slug's config.json
```python
# Trong step4, luôn merge drive_map từ incard_prod nếu questions đến từ đó
prod_cfg = CHATBOTS_DIR / "incard_prod" / "config.json"
if prod_cfg.exists():
    drive_map.update(build_drive_map(json.loads(prod_cfg.read_text(encoding='utf-8'))))
```

### 5. Citation format sau enrichment
Sau mỗi lần chạy enrich/fix, luôn validate:
```python
import re
def audit_citations(qs):
    for q in qs:
        a, src = q['expected_answer'], q['source_doc']
        if not re.search(r'[-–]\s*' + re.escape(src) + r'\s*$', a):
            print(f"WARN [{q['id']}]: missing end-citation")
        if 'Dieu' in a or 'Khoan' in a:
            print(f"WARN [{q['id']}]: non-accented citation")
```

## Pipeline Scripts (Agentic project)
```bash
python run.py <slug> --step 2    # generate questions
python run.py <slug> --step 3    # test chatbot
python run.py <slug> --step 3b   # evaluate (resumes from last)
python run.py <slug> --step 4    # export Excel
python pipeline/enrich_citations.py <slug>  # add citations to existing answers
python pipeline/fix_citations.py <slug>     # fix format + re-enrich problematic
```

## Key Principles
- Never silently skip a step — a step may only be skipped when its output already exists and is valid (resume)
- Always report the final report path so user can open it immediately
- If any step fails, write a partial report with results so far and a clear error section
- Config is optional — always have sensible defaults so the user can start with just a URL and Drive link
- **Pre-flight check**: validate chatbot responds with 1 test question before running full batch
- **Resume by default**: every step must be idempotent and resume-capable
- **Drive link column**: step4 Excel phải có cột "Link Tài Liệu" với hyperlink đến Google Drive file tương ứng
