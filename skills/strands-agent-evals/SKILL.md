---
name: strands-agent-evals
description: Evaluation SDK for agents built on AWS's Strands Agents framework — deterministic tool-fault chaos injection (Timeout/NetworkError/TruncateFields/CorruptValues), OpenTelemetry trace-based evaluators (HelpfulnessEvaluator, TrajectoryEvaluator) against Session objects, and ExperimentGenerator for auto-synthesizing test cases from a tool-context description. Use when testing a Strands-framework agent's resilience to tool failures or scoring its multi-turn trajectory. Distinct from the framework-agnostic ai-chaos-testing (prompt/context-level behavioral chaos) and llm-agent-trajectory-eval (LangChain agentevals). Triggers on: "strands agents evals", "strands-agents-evals", "ChaosPlugin", "ChaosExperiment", "strands chaos testing", "strands trace evaluator", "ExperimentGenerator strands".
---

# Strands Agent Evals SDK

`pip install strands-agents-evals` — evaluation framework specifically for agents built on
[Strands Agents](https://strandsagents.com) (AWS's open-source agent SDK). Installs a
`strands-evals` CLI for CI runs. Three distinct capabilities; use whichever fits the question
you're actually asking about the agent.

## 1. Deterministic Tool-Fault Chaos Injection

Injects failures into specific tool calls via Strands' plugin system, without touching task
code. This is **mechanism-based** fault injection (the tool literally times out / returns a
corrupted response) — contrast with `ai-chaos-testing`'s **prompt/context-based** disturbance
(fake conversation history, policy-violating instructions in the input text). Use this skill
when the question is "does my agent recover when a tool it depends on fails," and
`ai-chaos-testing` when the question is "does my agent stay in its behavioral lane under a
misleading prompt."

Available effects: `Timeout`, `NetworkError`, `ExecutionError`, `ValidationError` (cancel the
tool call outright) and `TruncateFields`, `RemoveFields`, `CorruptValues` (corrupt the tool's
response instead of failing it).

```python
from strands import Agent
from strands_evals import Case
from strands_evals.chaos import (
    ChaosCase, ChaosExperiment, ChaosPlugin,
    Timeout, NetworkError, TruncateFields,
)

base_cases = [Case(name="flight_search", input="Find flights to Tokyo")]

# Map specific tools to specific failure modes
effect_maps = {
    "search_timeout": {"tool_effects": {"search_tool":   [Timeout()]}},
    "db_truncate":    {"tool_effects": {"database_tool": [TruncateFields(max_length=20)]}},
}

# include_no_effect_baseline=True keeps a clean-run case in the matrix for comparison
chaos_cases = ChaosCase.expand(base_cases, effect_maps, include_no_effect_baseline=True)

def task(case):
    agent = Agent(tools=[search_tool, database_tool], plugins=[ChaosPlugin()])
    return {"output": str(agent(case.input))}

report = ChaosExperiment(cases=chaos_cases, evaluators=[...]).run_evaluations(task=task)
```

## 2. Trace-Based Evaluation (OpenTelemetry Session Objects)

Scores the agent from its actual execution trace (tool calls, conversation turns) rather than
final output alone. `HelpfulnessEvaluator` runs a "seven-level helpfulness assessment from user
perspective"; `TrajectoryEvaluator` scores tool-call parameter accuracy and selection
appropriateness — the same problem `llm-agent-trajectory-eval` solves via LangChain's
`agentevals`, but wired directly into Strands' own OTel spans instead of an external tracing
adapter.

```python
from strands import Agent
from strands_evals import Case, Experiment
from strands_evals.evaluators import HelpfulnessEvaluator
from strands_evals.telemetry import StrandsEvalsTelemetry
from strands_evals.mappers import StrandsInMemorySessionMapper

telemetry = StrandsEvalsTelemetry().setup_in_memory_exporter()

def user_task_function(case: Case) -> dict:
    telemetry.memory_exporter.clear()
    agent = Agent(trace_attributes={"session.id": case.session_id}, callback_handler=None)
    response = agent(case.input)

    spans = telemetry.memory_exporter.get_finished_spans()
    session = StrandsInMemorySessionMapper().map_to_session(spans, session_id=case.session_id)
    return {"output": str(response), "trajectory": session}

experiment = Experiment(cases=test_cases, evaluators=[HelpfulnessEvaluator()])
report = experiment.run_evaluations(user_task_function)
report.run_display()
```

## 3. Auto-Generating Test Cases from a Tool-Context Description

`ExperimentGenerator` synthesizes an experiment (test suite) from a free-form description of
the agent's available tools — skips manual case authoring for initial coverage:

```python
from strands_evals.generators import ExperimentGenerator
from strands_evals.evaluators import TrajectoryEvaluator

tool_context = """
Available tools:
- calculator(expression: str) -> float: Evaluate mathematical expressions
- web_search(query: str) -> str: Search the web for information
- file_read(path: str) -> str: Read file contents
"""

generator = ExperimentGenerator[str, str](str, str)
experiment = await generator.from_context_async(
    context=tool_context,
    num_cases=10,
    evaluator=TrajectoryEvaluator,
    task_description="Math and research assistant with tool usage",
    num_topics=3,
)
experiment.to_file("generated_experiment", "json")
```

Generated experiments serialize to JSON — commit them for reproducible CI gates rather than
regenerating on every run (regeneration reintroduces LLM non-determinism into what should be a
fixed regression suite).

## CI Usage

```bash
strands-evals validate experiments/customer_service.json
strands-evals run experiments/customer_service.json \
  --agent my_pkg.agents:build_agent \
  --display
```

## When to Reach for Which Skill

| Question | Skill |
|---|---|
| Does the agent survive its tools failing/corrupting responses? | `strands-agent-evals` (chaos) |
| Does the agent stay in policy under a misleading/injected prompt? | `ai-chaos-testing` |
| Is the agent's tool-call *sequence* correct (LangChain agent)? | `llm-agent-trajectory-eval` |
| Is a Strands agent's trace/trajectory helpful and well-ordered? | `strands-agent-evals` (trace eval) |
| Need to bootstrap an initial test suite with no cases written yet? | `strands-agent-evals` (`ExperimentGenerator`) |

## Sources
- https://github.com/strands-agents/evals
- https://raw.githubusercontent.com/strands-agents/evals/main/README.md
- https://techwithibrahim.medium.com/top-7-ai-agent-evaluation-frameworks-to-know-in-2026-786828662571
