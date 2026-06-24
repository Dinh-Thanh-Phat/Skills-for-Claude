---
name: llm-simulation-flywheel
description: |
  Synthetic-conversation regression testing for LLM chatbots: generate hundreds of realistic multi-turn
  conversations using an LLM to simulate user behavior, evaluate outcomes with LLM-as-judge, and iterate
  rapidly before shipping. Use when you need regression testing for a customer-support or task-completion
  chatbot, when manual golden-set evaluation is too slow or doesn't scale, or when you want to validate
  prompt/context changes without waiting for real user traffic.
  Triggers on: "chatbot simulation testing", "synthetic conversation generation", "LLM conversation simulator",
  "simulation flywheel", "chatbot regression testing", "simulate user behavior llm", "llm chatbot eval",
  "doordash simulation", "multi-turn synthetic testing".
---

# LLM Simulation Flywheel

A testing pattern for LLM-powered chatbots that replaces slow manual evaluation with an automated loop:
**simulate → evaluate → iterate → repeat**. Pioneered publicly by DoorDash (March 2026), where it cut
hallucination rates by ~90% through context engineering validated pre-production.

---

## Why A Simulation Flywheel

Traditional chatbot testing hits a wall because:
- **Golden sets age fast** — prompt changes invalidate curated examples within days.
- **Manual review is slow** — human review of 200 conversations can take days; automated simulation runs them in under 5 minutes.
- **Single-turn evals miss failures** — chatbot bugs often appear only in conversation turn 3–5, when context accumulates.
- **Real traffic lags** — you can't wait for production users to expose a regression.

The flywheel fixes all four: generates fresh scenarios from historical data, evaluates automatically, and runs before any change ships.

---

## Architecture (Four Components)

### 1. Scenario Extraction Pipeline

Mine your historical conversation logs to extract:
- **Customer intents** (e.g., "cancel order", "request refund", "track delivery")
- **Conversation flows** per intent (typical turn sequences)
- **Edge cases** (complaint escalations, unusual timing, ambiguous requests)
- **Failure patterns** (past hallucinations, wrong policies applied)

Output: a scenario library of `(intent, context_seed, expected_policy)` tuples.

```python
# Pseudocode — adapt to your transcript format
from collections import defaultdict

def extract_scenarios(transcripts: list[dict]) -> list[dict]:
    scenarios = []
    for t in transcripts:
        scenario = {
            "intent": classify_intent(t["turns"]),
            "context_seed": t["turns"][:2],      # first 2 turns as seed
            "expected_outcome": t["resolution"],  # e.g., "refund_issued"
            "edge_case": t.get("escalated", False),
        }
        scenarios.append(scenario)
    return scenarios
```

### 2. LLM User Simulator

A second LLM plays the customer role. Key design decisions:

- **Dynamic adaptation**: the simulator reads the bot's LAST response before generating the next customer turn — it reacts naturally, including pushback, frustration, and clarifying questions.
- **Persona grounding**: seed the simulator with the extracted context to reflect realistic customer behavior for that intent, not generic chat.
- **Behavioral diversity**: instruct the simulator to vary tone across scenarios (patient, impatient, confused, adversarial).

```python
USER_SIM_PROMPT = """
You are simulating a customer contacting support with this intent: {intent}.
Context from a real past conversation: {context_seed}

The support bot just said: {bot_response}

Reply as a realistic customer would — including natural pushback, questions, or escalation
if the bot's answer was incomplete. Stay in character. 1–3 sentences.
"""
```

### 3. Backend Mocking Layer

The chatbot under test often calls real APIs (order lookups, refund workflows, inventory checks).
Replace these with deterministic mocks for simulation:

```python
# Mock returns predictable data tied to the scenario
MOCK_ORDER_DB = {
    "scenario_cancel_001": {"status": "delivered", "eligible_refund": False},
    "scenario_refund_002": {"status": "in_transit", "eligible_refund": True},
}

def mock_order_lookup(order_id: str) -> dict:
    return MOCK_ORDER_DB.get(order_id, {"status": "unknown", "eligible_refund": False})
```

This makes simulations deterministic and fast — no real API latency, no test pollution.

### 4. LLM-as-Judge Evaluation

Evaluate each completed conversation with a binary policy judge (not a 1–5 rubric):

**Why binary over rubric:**
- Calibration is faster — reviewers agree more on "did the bot follow the refund policy?" than "rate helpfulness 1–5".
- Disagreements are diagnosable — "the bot gave the right answer but cited the wrong policy" is actionable.
- More reliable LLM judgments — binary avoids the verbosity/length bias of rubric scoring.

```python
JUDGE_PROMPT = """
Read this customer support conversation:

{conversation_transcript}

Policy being tested: {policy_description}

Did the support bot follow the policy correctly? Answer with:
- PASS — bot followed the policy correctly throughout
- FAIL — bot violated or ignored the policy (explain which turn and why)

Answer:
"""

def evaluate_conversation(transcript: str, policy: str, judge_llm) -> dict:
    verdict = judge_llm.complete(
        JUDGE_PROMPT.format(conversation_transcript=transcript, policy_description=policy)
    )
    return {
        "passed": verdict.startswith("PASS"),
        "explanation": verdict,
    }
```

---

## Running the Flywheel

```python
import concurrent.futures

def run_flywheel(scenarios, chatbot, simulator_llm, judge_llm, max_turns=8):
    results = []

    def run_one(scenario):
        conversation = []
        # Seed with context from real transcript
        bot_response = chatbot.respond(scenario["context_seed"])
        conversation.append({"role": "bot", "text": bot_response})

        for _ in range(max_turns - 1):
            user_turn = simulator_llm.complete(
                USER_SIM_PROMPT.format(
                    intent=scenario["intent"],
                    context_seed=scenario["context_seed"],
                    bot_response=bot_response,
                )
            )
            conversation.append({"role": "user", "text": user_turn})
            bot_response = chatbot.respond(conversation)
            conversation.append({"role": "bot", "text": bot_response})

            if is_conversation_resolved(bot_response):
                break

        verdict = evaluate_conversation(
            transcript=format_transcript(conversation),
            policy=scenario["expected_outcome"],
            judge_llm=judge_llm,
        )
        return {**scenario, "verdict": verdict, "transcript": conversation}

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(run_one, scenarios))

    pass_rate = sum(1 for r in results if r["verdict"]["passed"]) / len(results)
    return results, pass_rate
```

DoorDash's scale: **200+ conversations in under 5 minutes** using parallelism.

---

## CI Gate Integration

```yaml
# .github/workflows/chatbot-regression.yml
- name: Run simulation flywheel
  run: python run_flywheel.py --scenarios scenarios/library.json --output results.json

- name: Assert pass rate
  run: |
    PASS_RATE=$(python -c "import json; d=json.load(open('results.json')); print(d['pass_rate'])")
    python -c "rate=$PASS_RATE; assert rate >= 0.90, f'Pass rate {rate:.1%} below 90% threshold'"
```

**Recommended thresholds:**
- PR check: ≥ 90% pass rate on core policy scenarios
- Pre-release: ≥ 95% pass rate on full scenario library including edge cases

---

## What This Is NOT

| Concern | Answer |
|---|---|
| Does this replace golden-set evals? | No — complement them. Golden sets catch regressions on known cases; flywheel finds unknown failure modes. |
| Does this replace real user feedback? | No — use production tracing (see `llm-production-observability`) to close the loop on real traffic patterns. |
| Does binary judging miss nuance? | For policy compliance: no. For subjective quality (tone, helpfulness): supplement with a rubric judge for those dimensions. |

---

## Sources

- [A Simulation and Evaluation Flywheel to Develop LLM Chatbots — DoorDash Engineering Blog](https://careersatdoordash.com/blog/doordash-simulation-evaluation-flywheel-to-develop-llm-chatbots-at-scale/)
- [DoorDash Builds LLM Conversation Simulator to Test Customer Support Chatbots at Scale — InfoQ](https://www.infoq.com/news/2026/03/doordash-llm-chatbot-simulator/)
- [How DoorDash Built a Testing System to Evaluate LLMs — ByteByteGo](https://blog.bytebytego.com/p/how-doordash-built-a-testing-system)
- [Chatbot Testing in 2026: A Complete Guide to LLM Agents — Cekura](https://www.cekura.ai/blogs/complete-chatbot-testing-guide-ai-agents)
