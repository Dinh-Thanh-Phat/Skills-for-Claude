---
name: response-evaluator
description: Evaluate chatbot response accuracy by comparing actual responses to expected answers using Claude API for semantic scoring. Use when you need to grade chatbot answers for accuracy, relevance, completeness, and hallucination detection. Triggers on: "evaluate chatbot responses", "score chatbot accuracy", "grade AI answers", "check for hallucination in responses", "compare chatbot output to expected". Used as Step 4 in chatbot testing pipeline. Outputs JSON with scores and detailed evaluation for each response.
---

# Response Evaluator

Evaluates chatbot responses against expected answers using Claude-as-judge semantic grading.

## Evaluation Dimensions

Each response is scored on 4 dimensions (0-100):

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Correctness** | 40% | Facts match expected answer |
| **Completeness** | 25% | Covers all key points |
| **Relevance** | 25% | Stays on topic, no off-topic content |
| **Clarity** | 10% | Clear and understandable |

**Overall Score** = weighted average. Pass threshold default: **70**.

## Hallucination Detection

Flag a response as hallucinated if it:
- States specific facts not in expected answer or source docs
- Makes up numbers, dates, or names not grounded in docs
- Contradicts the expected answer on factual claims
- Presents uncertain information as definite fact

## Output Format

File: `evaluations.json`
```json
[
  {
    "question_id": "q001",
    "question": "What is the maximum file upload size?",
    "expected_answer": "Maximum 50MB per file, 500MB total per session.",
    "actual_response": "You can upload files up to 50MB each.",
    "scores": {
      "correctness": 90,
      "completeness": 70,
      "relevance": 100,
      "clarity": 95,
      "overall": 87.0
    },
    "pass": true,
    "hallucination_detected": false,
    "hallucination_details": null,
    "evaluation_reasoning": "Response correctly states 50MB per file limit. However, omits the 500MB total session limit.",
    "category": "factual",
    "difficulty": "easy"
  }
]
```

## Python Implementation

Write this script as `response_evaluator.py`:

```python
import json
import re
import sys
from pathlib import Path
import anthropic

class ResponseEvaluator:
    def __init__(self, model: str = "claude-sonnet-4-6", pass_threshold: int = 70):
        self.client = anthropic.Anthropic()
        self.model = model
        self.pass_threshold = pass_threshold

    def _build_grading_prompt(self, question: str, expected: str, actual: str) -> str:
        return f"""You are a QA evaluator grading a chatbot's response. Be strict but fair.

QUESTION: {question}

EXPECTED ANSWER (ground truth from documentation):
{expected}

CHATBOT'S ACTUAL RESPONSE:
{actual}

Evaluate on 4 dimensions (0-100 each):
1. Correctness (40% weight): Do stated facts match expected answer? Deduct for wrong facts.
2. Completeness (25% weight): Are all key points from expected answer covered?
3. Relevance (25% weight): Is the response on-topic? Does it avoid irrelevant tangents?
4. Clarity (10% weight): Is the response clear and easy to understand?

Also check for hallucinations: facts, numbers, names in the response NOT in the expected answer that appear fabricated or contradictory.

Return ONLY a valid JSON object:
{{
  "scores": {{
    "correctness": <0-100>,
    "completeness": <0-100>,
    "relevance": <0-100>,
    "clarity": <0-100>
  }},
  "hallucination_detected": <true|false>,
  "hallucination_details": "<specific hallucinated items, or null>",
  "evaluation_reasoning": "<2-3 sentences explaining the scores>"
}}"""

    def evaluate_one(self, question: str, expected: str, actual: str) -> dict:
        if not actual or actual.strip() == "":
            return {
                "scores": {"correctness": 0, "completeness": 0, "relevance": 0, "clarity": 0, "overall": 0},
                "pass": False,
                "hallucination_detected": False,
                "hallucination_details": None,
                "evaluation_reasoning": "No response received from chatbot."
            }

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": self._build_grading_prompt(question, expected, actual)}]
        )

        raw = response.content[0].text
        match = re.search(r'\{[\s\S]*\}', raw)
        if not match:
            raise ValueError(f"Invalid JSON from evaluator: {raw[:200]}")

        result = json.loads(match.group())
        scores = result["scores"]
        overall = (
            scores["correctness"] * 0.40 +
            scores["completeness"] * 0.25 +
            scores["relevance"] * 0.25 +
            scores["clarity"] * 0.10
        )
        result["scores"]["overall"] = round(overall, 1)
        result["pass"] = overall >= self.pass_threshold
        return result

    def evaluate_all(self, responses_file: str, questions_file: str, output_file: str = "evaluations.json") -> list:
        responses = json.loads(Path(responses_file).read_text())
        questions = {q["id"]: q for q in json.loads(Path(questions_file).read_text())}

        results = []
        for i, resp in enumerate(responses, 1):
            q = questions.get(resp["question_id"], {})
            print(f"  [{i}/{len(responses)}] Evaluating: {resp['question'][:50]}...")

            if not resp.get("success"):
                eval_result = {
                    "scores": {"correctness": 0, "completeness": 0, "relevance": 0, "clarity": 0, "overall": 0},
                    "pass": False,
                    "hallucination_detected": False,
                    "hallucination_details": None,
                    "evaluation_reasoning": f"API call failed: {resp.get('error')}"
                }
            else:
                eval_result = self.evaluate_one(resp["question"], q.get("expected_answer", ""), resp.get("response", ""))

            results.append({
                "question_id": resp["question_id"],
                "question": resp["question"],
                "expected_answer": q.get("expected_answer", ""),
                "actual_response": resp.get("response", ""),
                "category": q.get("category", "unknown"),
                "difficulty": q.get("difficulty", "unknown"),
                **eval_result
            })

        Path(output_file).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')

        passed = sum(1 for r in results if r["pass"])
        avg_score = sum(r["scores"]["overall"] for r in results) / len(results)
        hallucinations = sum(1 for r in results if r.get("hallucination_detected"))

        print(f"✓ Evaluated {len(results)} responses → {output_file}")
        print(f"  Passed: {passed}/{len(results)} ({passed/len(results)*100:.0f}%)")
        print(f"  Avg score: {avg_score:.1f} | Hallucinations: {hallucinations}")
        return results


if __name__ == "__main__":
    evaluator = ResponseEvaluator()
    evaluator.evaluate_all(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "evaluations.json")
```

## Dependencies
```bash
pip install anthropic
```

## Multi-Turn Evaluation

For conversational tests where context matters across turns, evaluate each turn with the
full history available to the judge:

```python
def _build_grading_prompt_multi(history, expected, actual):
    history_str = "\n".join(f"User: {h['user']}\nBot: {h['bot']}" for h in history)
    return f"""... 
CONVERSATION HISTORY:
{history_str}

LATEST EXPECTED: {expected}
LATEST ACTUAL: {actual}
..."""
```

## Language Mismatch Detection

Test for chatbot answering in the wrong language (common bug for multi-lingual bots):

```python
from langdetect import detect  # pip install langdetect
def language_check(question: str, actual: str) -> dict:
    q_lang = detect(question)
    a_lang = detect(actual) if actual else q_lang
    return {'language_match': q_lang == a_lang, 'q_lang': q_lang, 'a_lang': a_lang}
```

Add to eval output. Wrong language often means hard score=0 regardless of content.

## Cost Tracking

Capture token usage / API cost in evaluation so the report can show $/test:

```python
resp = self.client.messages.create(...)
result['eval_cost_usd'] = (
    resp.usage.input_tokens * 0.003 / 1000 +
    resp.usage.output_tokens * 0.015 / 1000
)
```

(Rates above for Sonnet — update for the model in use.)

## Key Principles
- Use Claude as judge — simple string matching misses nuance. "50MB" and "fifty megabytes" are equivalent; "50MB" and "500MB" are critically different
- Always evaluate failed API calls as score=0 — they count against accuracy
- Hallucination detection is separate from the score — a response can score 80 but still hallucinate
- When in doubt about hallucination, flag it — false positives are better than missed hallucinations
- Pass threshold default is 70 — below this the chatbot failed the question
