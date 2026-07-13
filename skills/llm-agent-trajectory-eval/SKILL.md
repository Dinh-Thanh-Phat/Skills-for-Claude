---
name: llm-agent-trajectory-eval
description: Evaluate an LLM agent's full trajectory — the exact ordered sequence of messages and tool calls it produced — rather than only its final answer or isolated spans. Use LangChain's agentevals library for deterministic trajectory matching (strict/unordered/subset/superset) or LLM-as-judge trajectory scoring (Agent-as-a-Judge pattern), and know when trajectory eval beats trace/span metrics or single-turn judge scoring. Use when testing multi-step agents, tool-calling flows, or LangGraph/LangChain agents where the sequence of decisions matters, not just the outcome. Triggers on: "trajectory evaluation", "agent-as-judge", "agentevals", "evaluate agent trajectory", "tool call sequence testing", "LangGraph agent eval", "trajectory match evaluator".
---

# LLM Agent Trajectory Evaluation

An agent's final answer can be correct while the *path* it took to get there is wrong — extra tool calls, wrong tool order, or a dangerous intermediate action that happened not to break the output. Trajectory evaluation scores the **entire ordered sequence of messages and tool calls**, not just the endpoint or one isolated span.

This is the practical, code-level counterpart to the "Agent-as-a-Judge" research direction (2026): instead of an LLM judge that only reads a final answer, either a deterministic matcher or an LLM judge inspects the whole trajectory — which tools were called, in what order, with what arguments, and how the agent recovered from errors.

## How this differs from other eval approaches

| Approach | Unit scored | Needs a reference? | Skill |
|---|---|---|---|
| Final-answer LLM-as-judge | Last message only | No | `llm-judge-bias` (bias mitigation for that judge) |
| Component/span metrics | One tool call / retrieval / LLM call at a time | No | `llm-agent-trace-eval` (DeepEval `@observe`) |
| **Trajectory evaluation** | **Whole ordered message+tool-call sequence** | Optional (match mode needs one; LLM-judge mode doesn't) | **This skill** |
| Multi-agent dispatch correctness | Supervisor→sub-agent handoff seam | No | `llm-agent-handoff-testing` |

Use trajectory eval when the *order and completeness* of steps matters (e.g. "must call `check_inventory` before `place_order`", "must not call `delete_account` unless `confirm_deletion` was called first") — something a final-answer judge or a single span metric cannot see.

## Setup

```bash
pip install agentevals
# or: npm install agentevals @langchain/core
```

## Deterministic Trajectory Matching

Use when you have (or can hand-author) a reference trajectory and want an exact, reproducible pass/fail — no LLM call, no cost, no variance.

```python
from agentevals.trajectory.match import create_trajectory_match_evaluator

evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="strict"   # or "unordered" | "subset" | "superset"
)

result = evaluator(outputs=outputs, reference_outputs=reference_outputs)
```

Match modes:
- **`strict`** — tool calls must appear in the exact same order as the reference. Use for flows with a mandated sequence (payment before shipment, auth before data access).
- **`unordered`** — same set of tool calls, any order. Use when steps are logically independent (fetching weather and fetching stock price can happen in either order).
- **`subset`** — the agent's trajectory must not call any tool outside the reference set. Use to catch scope creep / unauthorized tool use.
- **`superset`** — the agent's trajectory must cover at least the reference tool calls (extra calls allowed). Use for "did it do the required steps" checks where extra exploration is acceptable.

## LLM-as-Judge Trajectory Scoring

Use when there's no fixed reference (open-ended tasks) or you want a semantic judgment of trajectory quality rather than exact matching.

```python
import json
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT

trajectory_evaluator = create_trajectory_llm_as_judge(
    prompt=TRAJECTORY_ACCURACY_PROMPT,
    model="openai:o3-mini",   # or any cross-family judge — see llm-judge-bias for selection rules
)

outputs = [
    {"role": "user", "content": "What is the weather in SF?"},
    {
        "role": "assistant",
        "content": "",
        "tool_calls": [{"function": {"name": "get_weather", "arguments": json.dumps({"city": "SF"})}}],
    },
    {"role": "tool", "content": "It's 80 degrees and sunny in SF."},
    {"role": "assistant", "content": "The weather in SF is 80 degrees and sunny."},
]

eval_result = trajectory_evaluator(outputs=outputs)
# eval_result: {"key": ..., "score": <0-1, mapped from a 0-5 rubric>, "comment": "..."}
```

Async variant for CI parallelism:

```python
from agentevals.trajectory.llm import create_async_trajectory_llm_as_judge

evaluator = create_async_trajectory_llm_as_judge(prompt=TRAJECTORY_ACCURACY_PROMPT, model="openai:o3-mini")
result = await evaluator(outputs=outputs)
```

Apply the cross-family judge-selection and anti-bias rules from `llm-judge-bias` here too — the trajectory judge is still an LLM judge and inherits the same verbosity/position/self-preference risks.

## Handling Long Trajectories

For agents with many tool calls, feeding the raw full trajectory to the judge burns context and dilutes signal. Extract only the decision-relevant turns (tool name + arguments + result summary) before scoring rather than passing every raw message. Prefer the deterministic `strict`/`subset` matchers over an LLM judge when the trajectory is long and the required tool sequence is well-defined — they're free, instant, and immune to judge drift.

## CI Pattern

```python
import pytest
from agentevals.trajectory.match import create_trajectory_match_evaluator

REQUIRED_SEQUENCE = create_trajectory_match_evaluator(trajectory_match_mode="subset")

@pytest.mark.parametrize("query,reference", [
    ("Book a flight to Paris", REFERENCE_BOOKING_TRAJECTORY),
])
def test_agent_stays_in_scope(query, reference):
    outputs = run_agent(query)
    result = REQUIRED_SEQUENCE(outputs=outputs, reference_outputs=reference)
    assert result["score"] == 1.0, f"Agent called unauthorized tools: {result.get('comment')}"
```

## Relationship to Other Skills

- `llm-agent-trace-eval` — DeepEval component/span-level scoring (one tool call, retriever, or LLM call at a time via `@observe`). Complementary: use span eval to find *which* step is broken, trajectory eval to confirm the *overall path* is correct/safe.
- `llm-judge-bias` — bias mitigation and judge-selection rules; apply them whenever using the LLM-as-judge trajectory mode here.
- `llm-agent-handoff-testing` — specifically the supervisor→sub-agent dispatch seam in multi-agent systems, not general tool-call sequencing within one agent.

## Sources
- https://docs.langchain.com/langsmith/trajectory-evals
- https://github.com/langchain-ai/agentevals
- https://arxiv.org/html/2410.10934v2 (Agent-as-a-Judge: Evaluate Agents with Agents)
- https://www.judgmentlabs.ai/blogs/agent-judge-solving-long-context-evaluations
