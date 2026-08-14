---
name: llm-load-testing
description: >-
  Load testing LLM APIs for streaming performance — TTFT, inter-token latency, throughput SLOs.
  Use when you need to verify an AI chatbot or LLM API can handle concurrent users within latency
  targets, or before production launch of a streaming AI feature. Triggers on: "LLM load test",
  "chatbot performance test", "TTFT benchmark", "streaming API load", "time to first token", "LLM
  throughput", "SSE load test", "concurrent LLM users", "k6 LLM", "locust LLM", "LLM performance
  SLO".
---

# LLM Load Testing

LLM API performance differs from standard REST APIs: the response streams token-by-token. TTFT (Time to First Token) dominates perceived responsiveness; total latency is secondary. Standard load tools need adaptation for SSE/streaming endpoints.

## Key Metrics

| Metric | Abbrev | Meaning | Chat SLO | RAG SLO |
|--------|--------|---------|----------|---------|
| Time to First Token | TTFT | Latency from request → first byte of response | < 500 ms | < 50 ms |
| Inter-Token Latency | ITL | Time between consecutive tokens | < 200 ms | < 50 ms |
| Tokens per Second | TPS | Output throughput per request | — | — |
| End-to-End Latency | E2E | Total time from request to last token | — | — |
| Concurrent Requests | — | Users actively streaming simultaneously | — | — |

> A TTFT > 1 s under load = users perceive the app as broken. Add network distance: a "300 ms TTFT" measured us-east-1 to us-east-1 becomes 600–900 ms from Southeast Asia.

## Tool Selection for Streaming Endpoints

| Tool | SSE Support | Best For |
|------|-------------|----------|
| **Gatling** | Native | Best choice — built-in SSE, Scala/Java DSL, precise percentile reporting |
| **Locust** | Custom (geventhttpclient) | ML teams in Python; cap at ~500 concurrent for SSE |
| **k6** | Via `xk6-sse` extension | Go-based, very efficient; needs custom build |

## Locust — LLM Streaming Load Test

```python
# locustfile.py
import json
import time
from locust import HttpUser, task, between

class LLMStreamingUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def chat_completion(self):
        prompt = self._sample_prompt()   # sample from real log distribution
        start = time.perf_counter()
        first_token_time = None
        token_count = 0

        with self.client.post(
            "/v1/chat/completions",
            json={"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}], "stream": True},
            headers={"Authorization": f"Bearer {API_KEY}"},
            stream=True,
            catch_response=True,
        ) as response:
            for line in response.iter_lines():
                if not line or line == b"data: [DONE]":
                    continue
                if line.startswith(b"data: "):
                    if first_token_time is None:
                        first_token_time = time.perf_counter()
                        ttft_ms = (first_token_time - start) * 1000
                        # Custom metric — Locust events
                        self.environment.events.request.fire(
                            request_type="SSE", name="TTFT",
                            response_time=ttft_ms, response_length=0
                        )
                    token_count += 1

            e2e_ms = (time.perf_counter() - start) * 1000
            if e2e_ms > 30_000:
                response.failure(f"E2E latency {e2e_ms:.0f}ms exceeds 30s")
            else:
                response.success()

    def _sample_prompt(self):
        # Sample from real prompt lengths — don't use fixed short prompts
        import random
        lengths = [50, 80, 120, 200, 350]   # token counts representative of production
        n = random.choice(lengths)
        return " ".join(["test"] * n)
```

Run:
```bash
locust -f locustfile.py --headless -u 50 -r 5 -t 10m --host https://api.example.com \
  --html report.html --csv results
```

## Gatling — Native SSE Support

```scala
// LLMLoadSimulation.scala
import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class LLMStreamingSimulation extends Simulation {
  val httpProtocol = http
    .baseUrl("https://api.example.com")
    .header("Authorization", s"Bearer ${System.getenv("API_KEY")}")

  val scn = scenario("LLM Chat Load")
    .exec(
      http("chat_stream")
        .post("/v1/chat/completions")
        .body(StringBody("""{"model":"gpt-4o","messages":[{"role":"user","content":"Explain RAG in 3 sentences."}],"stream":true}"""))
        .asJson
        .check(status.is(200))
        // Capture first byte time — Gatling measures TTFB natively
    )

  setUp(
    scn.inject(
      rampUsersPerSec(1).to(20).during(60.seconds),   // ramp up
      constantUsersPerSec(20).during(600.seconds),     // sustained load
    )
  ).protocols(httpProtocol)
   .assertions(
     global.responseTime.percentile(95).lt(2000),      // E2E p95 < 2s
     global.failedRequests.percent.lt(1),              // < 1% errors
   )
}
```

## k6 with xk6-sse Extension

```javascript
// k6-llm-test.js  (requires: xk6 build --with github.com/phymbert/xk6-sse)
import sse from 'k6/x/sse';
import { check } from 'k6';

export const options = {
  vus: 50,
  duration: '10m',
  thresholds: {
    'ttft': ['p(95)<500'],           // 95% TTFT under 500ms
    'http_req_failed': ['rate<0.01'],
  },
};

export default function () {
  const start = Date.now();
  let firstToken = null;

  const response = sse.open('https://api.example.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${__ENV.API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: 'gpt-4o', messages: [{ role: 'user', content: 'Ping' }], stream: true }),
  }, function (client) {
    client.on('event', (event) => {
      if (firstToken === null && event.data !== '[DONE]') {
        firstToken = Date.now() - start;
        // Record as custom metric
      }
    });
  });
}
```

## Load Test Protocol

```
1. Warm-up run    — 10 users, 2 minutes (fills cache, JIT, connection pools)
2. Ramp test      — ramp from 1 → target concurrency over 60s
3. Sustained load — hold target concurrency for 10 minutes
4. Soak test      — hold target concurrency for 60 minutes (catches memory leaks)

Concurrency targets (typical):
  MVP launch:      20–50 concurrent
  Growth phase:    100–200 concurrent
  Enterprise:      500+ (use Gatling)

Sample prompt distribution: pull from production logs, not synthetic.
Run 3× across different times of day (provider rate limits vary).
```

## Interpreting Results

| Observation | Diagnosis |
|-------------|-----------|
| TTFT high, ITL fine | Slow prompt processing / token-classification overhead |
| ITL spikes at p99 | Provider throttling or memory-bandwidth pressure in decode |
| TTFT grows linearly with concurrency | Queuing at the inference server — need horizontal scaling |
| TTFT fine, E2E high | Long output sequences draining throughput |
| High error rate > 5 users | Rate limit hit — add request queue / backpressure |

## CI Gate Integration

```yaml
# .github/workflows/llm-perf.yml
name: LLM Performance Gate
on:
  push:
    paths: ['prompts/**', 'system_prompt.txt']  # run when prompt/model changes

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Locust
        run: pip install locust
      - name: Run 2-min load test
        env:
          API_KEY: ${{ secrets.LLM_API_KEY }}
        run: |
          locust -f locustfile.py --headless -u 20 -r 2 -t 2m \
            --host ${{ vars.LLM_API_URL }} --csv ci_results
      - name: Assert TTFT p95 < 500ms
        run: python assert_slos.py ci_results_stats.csv
```

```python
# assert_slos.py
import csv, sys
with open(sys.argv[1]) as f:
    for row in csv.DictReader(f):
        if row['Name'] == 'TTFT':
            p95 = float(row['95%'])
            assert p95 < 500, f"TTFT p95={p95:.0f}ms exceeds 500ms SLO"
```

## Key Principles

- Always measure **TTFT separately** from E2E — they diagnose different failure modes
- Use real prompt-length distributions, not "Hello" — short prompts hide prefill latency
- Account for geographic distance — test from a node close to your users' region
- Streaming endpoints need SSE-aware tools; total-time-only metrics are misleading for UX
- A clean perf baseline before launch makes degradation regressions detectable later

## Sources

- https://gatling.io/blog/load-testing-an-llm-api
- https://latitude.so/blog/ultimate-guide-llm-load-testing
- https://medium.com/@hiteshpara762/how-i-load-tested-a-conversational-ai-chatbot-agent-with-a-streaming-endpoint-c8e26e7a091b
- https://blog.premai.io/load-testing-llms-tools-metrics-realistic-traffic-simulation-2026/
- https://github.com/phymbert/xk6-sse
