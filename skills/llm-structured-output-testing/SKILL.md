---
name: llm-structured-output-testing
description: >-
  Test and validate LLM structured output quality using Pydantic schemas and the Instructor
  library — track schema pass-rate as a CI gate, monitor retry rate as a prompt-health signal,
  and design schemas for testability. Use when adding structured output to an LLM pipeline, when
  a structured-output prompt starts failing validation, when setting up CI gates for a new LLM
  feature, or when diagnosing why a model keeps needing retries. Triggers on: "structured
  output", "Pydantic LLM", "Instructor library", "schema validation LLM", "JSON schema LLM",
  "response_model", "validation error LLM", "schema pass rate", "structured output CI gate", "LLM
  output validation".
---

# LLM Structured Output Testing

Structured output forces an LLM to return data in a schema-validated shape. When the model generates tokens that violate the schema, the library either retries or raises. Testing this layer means tracking whether your prompts keep the model on-schema — and catching schema drift before it hits production.

> **Cross-ref:** `deepeval-llm-cicd` (semantic quality metrics — AnswerRelevancy, Faithfulness; structured output testing is the *schema* layer below that); `llm-hallucination-detection` (content accuracy — structured output testing is about *shape*, not meaning); `llm-production-observability` (runtime tracing — instrument pass-rate here; gate on it here in CI).

---

## 1 — Instructor + Pydantic: Core Pattern

[Instructor](https://python.useinstructor.com/) wraps the Anthropic (and 15+ other provider) client with automatic Pydantic validation and retry-with-feedback.

```python
import instructor
import anthropic
from pydantic import BaseModel, Field
from typing import Literal

client = instructor.from_anthropic(anthropic.Anthropic())

class BugReport(BaseModel):
    title: str = Field(description="Short one-line summary of the bug")
    severity: Literal["low", "medium", "high", "critical"]
    steps_to_reproduce: list[str]
    expected_behavior: str
    actual_behavior: str
    reasoning: str = Field(description="Why you classified severity this way")

# response is a validated BugReport — not a string
report = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    max_retries=2,          # retry up to 2× on validation failure, feeding error back
    messages=[{"role": "user", "content": raw_bug_text}],
    response_model=BugReport,
)

assert report.severity in ("low", "medium", "high", "critical")   # guaranteed
```

---

## 2 — Schema Design for Testability

**Put reasoning fields first.** LLMs generate left-to-right; committing to a `severity` before writing `reasoning` produces worse calibration.

```python
# Bad — model commits to severity before explaining why
class BadSchema(BaseModel):
    severity: Literal["low", "medium", "high"]
    reasoning: str

# Good — reasoning first forces chain-of-thought before the enum
class GoodSchema(BaseModel):
    reasoning: str
    severity: Literal["low", "medium", "high"]
```

**Other rules:**
- Make fields optional (`Optional[str]`) when the source text may not contain data — never let the model hallucinate a required field.
- One schema per task. Don't extract 50 fields in one call; split into focused schemas.
- Use `Literal[...]` enums instead of plain `str` for any categorical field — these map directly to constrained grammar and are enforced server-side by providers that support native structured output.
- Add `Field(description=...)` for ambiguous fields — it goes into the tool description, which the model reads.

---

## 3 — Schema Pass-Rate: the Key Test Metric

Schema pass-rate = proportion of calls that return a valid schema without hitting `max_retries`.

```python
# Measure pass-rate over an eval set
import json

def measure_pass_rate(eval_set: list[dict], model_cls, max_retries=0) -> dict:
    passed = failed = 0
    failures = []
    for item in eval_set:
        try:
            client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                max_retries=max_retries,        # set 0 to expose raw failure rate
                messages=[{"role": "user", "content": item["input"]}],
                response_model=model_cls,
            )
            passed += 1
        except Exception as e:
            failed += 1
            failures.append({"input": item["input"][:80], "error": str(e)})
    total = passed + failed
    return {"pass_rate": passed / total, "failures": failures}
```

**Thresholds (2026 consensus):**

| Pass-rate | Signal | Action |
|-----------|--------|--------|
| ≥ 98% | Healthy | No action |
| 90–97% | Watch | Investigate field-level failures |
| < 90% | Failing | Block PR; fix prompt or schema |

Run at `max_retries=0` to measure raw compliance (no auto-healing). Run at `max_retries=2` to measure what production sees.

---

## 4 — Retry Rate: Prompt-Health Signal

Each retry costs tokens and latency. Track retry rate as a leading indicator:

```python
import instructor
from instructor import patch

# Instrument retry count
client_instrumented = instructor.from_anthropic(
    anthropic.Anthropic(),
    hooks=instructor.Hooks(
        on_error=lambda e, n_attempts: print(f"retry #{n_attempts}: {e}"),
    )
)
```

**Retry rate interpretation:**

| Retry rate | Meaning | Fix |
|------------|---------|-----|
| < 2% | Normal model variance | None |
| 2–10% | Prompt/schema tension | Add `Field(description=...)`, clarify enum options |
| > 10% | Structural mismatch | Redesign schema or split into multiple calls |
| Consistent 2+ retries on same inputs | Prompt bug | Fix prompt; schema changes alone won't help |

> A 5-point drop in schema pass-rate often surfaces before semantic-eval scores catch the regression — use it as an early warning in CI.

---

## 5 — CI Gate Pattern (pytest)

```python
# tests/test_structured_output.py
import pytest
from pathlib import Path
import json

EVAL_SET = json.loads(Path("tests/fixtures/bug_reports.json").read_text())
PASS_RATE_THRESHOLD = 0.95   # block PRs below 95%

@pytest.mark.llm
def test_bug_report_schema_pass_rate():
    results = measure_pass_rate(EVAL_SET, BugReport, max_retries=0)
    failures = results["failures"]
    if failures:
        # Print field-level breakdown for diagnosis
        for f in failures[:5]:
            print(f"FAILED: {f['input']} → {f['error']}")
    assert results["pass_rate"] >= PASS_RATE_THRESHOLD, (
        f"Schema pass-rate {results['pass_rate']:.1%} below threshold "
        f"{PASS_RATE_THRESHOLD:.0%}. First failure: {failures[0] if failures else 'none'}"
    )
```

```yaml
# .github/workflows/llm-eval.yml
- name: Run schema pass-rate gate
  run: pytest tests/test_structured_output.py -m llm -v
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Run this gate on:**
- Every prompt change (even wording tweaks)
- Every model swap (e.g. Haiku → Sonnet)
- Every schema field addition or type change
- Every CI build against the main eval set

---

## 6 — Native Structured Output vs Tool Calling

Instructor automatically selects the best mode per provider:

| Mode | How it works | When used |
|------|-------------|-----------|
| **Native structured output** | Provider enforces grammar server-side; model cannot produce invalid tokens | Anthropic with `response_model`, OpenAI with `response_format` |
| **Tool calling** | Schema passed as a tool definition; model calls the tool | Fallback for providers without native structured output |
| **JSON mode** | `response_format: {type: "json_object"}` | Weaker — schema not enforced, only valid JSON guaranteed |

> Prefer native structured output when available — it eliminates the need for retries for schema violations entirely; retries are only triggered by Pydantic validator logic you add.

---

## 7 — Production Span Instrumentation

Tag every LLM call with structured output metrics so CI and production share the same signal:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("llm.structured_call") as span:
    try:
        result = client.messages.create(...)
        span.set_attribute("llm.schema_pass", True)
        span.set_attribute("llm.retry_count", 0)
    except instructor.exceptions.InstructorRetryException as e:
        span.set_attribute("llm.schema_pass", False)
        span.set_attribute("llm.retry_count", e.n_attempts)
        span.set_attribute("llm.failure_field", str(e.last_completion))
        raise
```

Alert when production `schema_pass` rate drops below the same threshold used in CI — schema drift in production (prompt cache mismatch, model update) surfaces here first.

---

## Sources

- https://python.useinstructor.com/integrations/anthropic/
- https://github.com/567-labs/instructor
- https://collinwilkins.com/articles/structured-output
- https://devopsboys.com/blog/llm-output-validation-instructor-pydantic-production-2026
- https://futureagi.com/blog/what-is-llm-input-output-validation-2026/
- https://techsy.io/en/blog/llm-structured-outputs-guide
