---
name: voice-ai-agent-testing
description: >-
  Test and evaluate voice/speech AI agents (IVR bots, voice assistants, phone-call agents) — WER
  transcription accuracy, latency budgets (TTFT, endpointing), barge-in/interruption handling,
  and turn-detection regression testing. Use when validating a voice agent before production or
  diagnosing "feels laggy"/"talks over me"/"cuts me off" complaints. Triggers on: "voice agent
  testing", "voice AI evaluation", "barge-in testing", "turn detection", "IVR testing", "speech
  agent QA", "WER benchmark", "voice latency test", "interruption handling test",
  "deepeval voice metrics".
---

# Voice AI Agent Testing

Text-chatbot metrics (response relevancy, hallucination, judge scoring — see `response-evaluator`,
`llm-hallucination-detection`, `llm-judge-bias`) still apply to *what* a voice agent says. This skill
covers what's unique to the **audio channel**: transcription accuracy, conversational latency budgets,
and turn-taking (barge-in / interruption) — the failure modes that only show up once speech is involved.

## Metric 1 — Word Error Rate (WER): transcription accuracy

```
WER = (S + D + I) / N × 100
S = substitutions, D = deletions, I = insertions (vs. reference transcript), N = words in reference
```

| Condition | Target |
|---|---|
| Clean audio, production enterprise bar | < 5% |
| Clean audio, general benchmark | < 8% |
| Noisy audio / accented speech | < 15% |

Test with a corpus that spans accents, background noise (call center, street, car), and telephony
codec artifacts (8kHz μ-law) — a WER measured on clean 16kHz studio audio does not predict phone-line WER.

## Metric 2 — Latency budget (perceived responsiveness)

| Metric | Definition | Target |
|---|---|---|
| Time-to-first-token (TTFT) | Request → first LLM token | < 500 ms (Twilio bar: < 400 ms) |
| End-to-end response latency | User stops speaking → agent audio starts | < 500 ms natural, 500–1000 ms acceptable, > 1000 ms feels broken |
| P50 / P95 (cascading STT→LLM→TTS architectures) | Percentile response latency | P50 < 1.5 s, P95 < 5 s |
| Endpointing dead air (P95) | Silence after user stops talking before agent responds | as low as possible; > 800 ms and callers perceive an awkward pause |

Cascading architectures (separate STT, LLM, TTS services) accumulate latency at each hop — budget each
stage separately, don't just assert on the end-to-end number, or you can't tell which stage regressed.

## Metric 3 — Turn detection & barge-in (interruption handling)

Voice agents must detect when a caller starts talking over them (barge-in) and stop fast — this is the
#1 "feels unnatural" complaint and the hardest thing to get right.

| Metric | Target |
|---|---|
| Barge-in detection accuracy | ≥ 95% |
| Interruption response latency (speech onset → TTS suppressed) | < 200 ms |
| False positive rate (background noise mistaken for barge-in) | < 5% |
| False negative rate (missed real interruption) | < 5% |
| Clipped-word count (over-aggressive VAD cutting the agent off its own sentence) | track as a regression signal, not just a pass/fail |

Endpointing sensitivity is a tunable tradeoff, not a fixed constant — e.g. Nova Sonic-style turn-taking
configs offer ~1.5s / 1.75s / 2.0s wait thresholds before responding. Lower = snappier but more false
barge-ins on pauses/breaths; higher = safer but feels slow. Pick per use case (fast IVR menu vs.
reflective customer-support conversation) and pin the choice in a config, not tribal knowledge.

### The 4 barge-in scenarios that catch demo→production regressions

Test these explicitly — they cover the cases that pass in a quiet demo and fail in production:

1. **Interruption during the greeting** — caller starts talking before the agent finishes its opener.
2. **Interruption during a tool/API lookup** — agent is mid-sentence while waiting on a backend call;
   verify the interruption doesn't orphan the pending tool call or duplicate it on resume.
3. **Interruption during a long confirmation read-back** ("So that's 123 Main Street, apartment 4B,
   confirm?") — the longer the utterance, the more barge-in opportunities.
4. **Speech from a noisy room** — TV/traffic/crosstalk in the background; must not false-trigger.

## Testing methodology

| Layer | What it catches | How |
|---|---|---|
| Replay-based regression | Did a prompt/model/config change break a previously-passing call? | Store real (or synthesized) call recordings as a golden corpus; re-run through the pipeline on every change |
| Synthetic noise injection | Does the agent hold up outside the quiet demo environment? | Overlay babble noise, codec compression, packet loss onto test audio at fixed SNR levels |
| LLM-as-judge + manual expert spot-check | Semantic correctness of the *content* once transcribed | Same judge patterns as `response-evaluator`/`llm-judge-bias`, applied to the STT output — calibrate against human review, don't trust the judge blind |
| Task success rate (TSR) | Did the call actually accomplish its goal? | `successful completions / total interactions`, target ≥ 85% for production agents |

## Decision table — where to test

| Situation | Approach |
|---|---|
| Regression-testing prompt/model changes against known calls | Replay corpus, automated diff on transcript + judge score |
| Pre-launch robustness check | Synthetic noise injection across SNR levels + the 4 barge-in scenarios |
| Ongoing production quality | Sample live calls, score WER/latency/TSR on a rolling window, alert on drift |
| Load/concurrency (many simultaneous calls) | Pair with `llm-load-testing` for the underlying LLM hop; add concurrent-call capacity to the protocol |
| What the agent *says* is correct/on-brand | `response-evaluator`, `llm-judge-bias`, `llm-hallucination-detection` — this skill only covers the audio-channel layer |

Commercial/OSS platforms purpose-built for this (2026): Hamming, Cekura, Coval, Bluejay, Braintrust,
Cyara, Evalion, Roark, TestZeus — most combine replay corpora, synthetic noise injection, and
LLM-judge scoring out of the box, useful if building the harness in-house isn't worth the investment.

Already on DeepEval for other CI gates (see `skills/deepeval-llm-cicd`)? Its v4.1.10 voice metrics
(`VoiceNaturalnessMetric`, `SpeechIntelligibilityMetric`, `VoiceConsistencyMetric`,
`TurnTakingNaturalnessMetric`, `AgentResponsivenessMetric`, `AudioIntegrityMetric`,
`VoiceReliabilityMetric`) score recorded audio turns as a pytest-native `assert_test()` gate —
dependency-free acoustic analysis, not a WER/latency benchmark. Use them as the CI layer on top of
this skill's replay-corpus/noise-injection methodology, not a replacement for it.

## Sources

- https://hamming.ai/resources/voice-agent-evaluation-metrics-guide
- https://hamming.ai/resources/voice-agent-interruption-handling-runbook
- https://hamming.ai/resources/asr-accuracy-evaluation-for-voice-agents
- https://hamming.ai/resources/voice-agent-testing-guide
- https://www.cekura.ai/blogs/voice-ai-evaluation-metrics
- https://www.getmaxim.ai/articles/best-voice-agent-evaluation-tools-in-2026/
- https://www.speechmatics.com/company/articles-and-news/de-risk-your-voice-agent-11-best-voice-agent-testing-platforms
