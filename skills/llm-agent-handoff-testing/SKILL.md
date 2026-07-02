---
name: llm-agent-handoff-testing
description: Evaluate multi-agent LLM systems at the handoff (dispatch) level — the moment work crosses from a supervisor to a sub-agent — instead of only grading the final answer. Use when testing Claude Agent SDK sub-agents (Task tool), OpenAI Agents SDK handoff(), LangGraph edges, CrewAI delegation, or AutoGen turns, and a multi-agent run fails but it's unclear whether the supervisor picked the wrong sub-agent, the sub-agent drifted out of scope, or the supervisor misread the result. Triggers on: "multi-agent evaluation", "agent handoff testing", "sub-agent dispatch eval", "Task tool evaluation", "DispatchCorrectness", "ScopeFidelity", "supervisor agent testing", "evaluate Claude sub-agents".
---

# LLM Agent Handoff Testing

Grading only the final answer of a multi-agent run tells you *that* something broke, not *where*. In 2026 the
working pattern is to grade the seams — each **handoff** — not just the outcome.

## The Handoff Is the Cross-Framework Unit

A handoff is the moment work crosses from one agent to another, with whatever context the receiver needs to
continue. Every multi-agent framework has one, under a different name:

| Framework | Handoff primitive |
|---|---|
| Claude Agent SDK / Claude Code | `Task` tool dispatch to a sub-agent type |
| OpenAI Agents SDK | `handoff()` |
| LangGraph | an edge between nodes |
| CrewAI | delegation |
| AutoGen | a turn |

For Claude specifically: the supervisor decides three things at dispatch time — **which sub-agent type** to call
(`research-agent`, `refactor-agent`, `validator-agent`), **the prompt that scopes the work**, and the
**`allowed_tools` subset** the child can use. The child runs to completion in its own context window with its
own turn budget, then returns a single string result the supervisor reads and acts on. Three things can break
independently: the dispatch itself, the sub-agent's adherence to scope, and the supervisor's integration of the
result — so grade all three separately.

## Four Rubrics (as CustomLLMJudge Metrics)

| Rubric | Question it answers | Starting threshold |
|---|---|---|
| `DispatchCorrectness` | Did the supervisor pick the right sub-agent/receiver for this job? | ≥ 0.85 |
| `ScopeFidelity` | Did the receiver stay within the scope/prompt it was handed, without wandering into the supervisor's job or another sub-agent's job? | ≥ 0.90 **per receiver type** |
| `ResultIntegration` | Did the supervisor correctly read and act on what the sub-agent returned (not ignore it, not misquote it)? | ≥ 0.80 |
| `RecoveryOnError` | When a sub-agent failed, timed out, or returned a low-confidence result, did the supervisor detect it and recover (retry, re-scope, escalate to the user) instead of silently proceeding? | ≥ 0.85 |

Run these alongside your existing single-agent metrics (`TaskCompletionMetric`, tool-correctness, etc. — see
`llm-agent-trace-eval`) — they answer a different question and are not a replacement.

## Building the Test Set

Don't synthesize handoff test cases from scratch first — mine real production dispatches. 40–200 is enough to
start. For each one, capture:

1. The supervisor's input (what the user/upstream asked).
2. The dispatch decision the supervisor made (which sub-agent, what scoped prompt, what tools).
3. The sub-agent run that resulted (its trace, or at minimum its final returned string).
4. The supervisor's next turn after the dispatch returned (what it did with the result).

Wrap each as a test case and score all four rubrics against it with an LLM judge, alongside whatever
trace/task-completion metrics you already run.

```python
# Pseudocode — adapt to your eval SDK (DeepEval, Confident AI, or a custom judge harness)
handoff_case = {
    "supervisor_input": "Find and fix the flaky login test",
    "dispatch": {"sub_agent": "test-debugger", "prompt": "Diagnose flakiness in tests/login.spec.ts, do not fix unrelated tests", "allowed_tools": ["Read", "Bash", "Grep"]},
    "sub_agent_result": "...",       # what the child returned
    "supervisor_next_turn": "...",   # what the supervisor did with it
}

for rubric in ["DispatchCorrectness", "ScopeFidelity", "ResultIntegration", "RecoveryOnError"]:
    score = judge_llm.score(rubric, handoff_case)
    assert score >= THRESHOLDS[rubric], f"{rubric} failed: {score}"
```

## CI Gate Discipline

- **Fail on the failing axis, not one aggregate score.** A blended pass/fail hides which layer regressed.
- **Bind thresholds to prompt versions.** Tie each threshold to the supervisor system-prompt version *and* the
  sub-agent definition version being tested, so a regression localizes to one prompt change instead of a vague
  "the agent got worse."
- **Track ScopeFidelity per receiver type**, not as one global number — a `validator-agent` scope violation and a
  `refactor-agent` scope violation are different bugs with different fixes.
- **Cluster failures back to a prompt.** When several handoff cases fail the same rubric, group them (by
  sub-agent type or by failure text similarity) before filing one fix — usually one supervisor-prompt or
  sub-agent-prompt edit resolves a whole cluster at once, not one case at a time.

## Relationship to Other Skills

- `llm-agent-trace-eval` — component/span-level eval **inside one agent's own run** (tool calls, retrieval
  steps, LLM completions). Use that when there's a single agent with tool use; use **this** skill when there are
  two or more agents and work crosses between them.
- `deepeval-llm-cicd` — answer-level quality gates (relevancy/faithfulness/hallucination) on a single LLM
  output; orthogonal to handoff correctness.
- `ai-agent-eval-platforms` — SaaS/OSS platforms (Braintrust, Latitude, Langfuse) for team-wide experiment
  tracking; this skill is the methodology you'd run on top of any of them.

## Sources

- [Evaluating LLM Agent Handoffs 2026: The Cross-Framework Unit — Future AGI](https://futureagi.com/blog/evaluating-llm-agent-handoffs-2026/)
- [Evaluating Claude Sub-Agents: The Dispatch Is the Unit (2026) — Future AGI](https://futureagi.com/blog/evaluating-claude-sub-agents-2026/)
- [Evaluating OpenAI Agents SDK: The Handoff Is the Test (2026) — Future AGI](https://futureagi.com/blog/evaluating-openai-agents-sdk-2026/)
