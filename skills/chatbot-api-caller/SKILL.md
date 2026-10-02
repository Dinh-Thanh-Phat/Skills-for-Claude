---
name: chatbot-api-caller
description: Send test questions to a chatbot API and record responses with timing metrics. Use when you need to call a chatbot endpoint with a batch of questions and measure performance. Supports REST, WebSocket, and GraphQL APIs with retry logic and rate limiting. Triggers on: "send questions to chatbot API", "call chatbot with test questions", "measure chatbot response time", "batch test chatbot API". Used as Step 3 in chatbot testing pipeline. Outputs JSON with responses, timing, and success/failure status for each question.
---

# Chatbot API Caller

Sends test questions to a chatbot API, measures response times, and records all results.

## Supported API Types

### REST API (most common)
```json
{
  "api_type": "rest",
  "endpoint": "https://api.example.com/chat",
  "method": "POST",
  "auth": {"type": "bearer", "token": "YOUR_TOKEN"},
  "request_template": {"message": "{{question}}", "session_id": "test-{{id}}"},
  "response_path": "data.response"
}
```

> ⚠️ Only **REST** is implemented in `chatbot_caller.py` below. The WebSocket and GraphQL
> blocks are **config shape only** — no code handles `api_type` yet; implement before use.

### WebSocket (config shape only — not implemented)
```json
{
  "api_type": "websocket",
  "endpoint": "wss://api.example.com/ws/chat",
  "send_template": {"type": "message", "content": "{{question}}"},
  "response_event": "bot_response",
  "response_path": "data.text"
}
```

### GraphQL (config shape only — not implemented)
```json
{
  "api_type": "graphql",
  "endpoint": "https://api.example.com/graphql",
  "query": "mutation SendMessage($msg: String!) { sendMessage(content: $msg) { response } }",
  "variables_template": {"msg": "{{question}}"},
  "response_path": "data.sendMessage.response"
}
```

## Output Format

File: `raw_responses.json`
```json
[
  {
    "question_id": "q001",
    "question": "What is the maximum file upload size?",
    "response": "The maximum file upload size is 50MB per file.",
    "response_time_ms": 1230,
    "timestamp": "2024-01-15T10:23:45.123Z",
    "success": true,
    "attempt": 1,
    "error": null
  },
  {
    "question_id": "q002",
    "question": "Why would a user need to upgrade?",
    "response": null,
    "response_time_ms": null,
    "timestamp": "2024-01-15T10:24:12.456Z",
    "success": false,
    "attempt": 3,
    "error": "Connection timeout after 3 attempts"
  }
]
```

## Python Implementation

Write this script as `chatbot_caller.py`:

```python
import json
import time
import asyncio
import aiohttp
import sys
from datetime import datetime, timezone
from pathlib import Path

class ChatbotAPICaller:
    def __init__(self, api_config: dict, rate_limit_ms: int = 1000, max_retries: int = 3, timeout_ms: int = 30000):
        self.config = api_config
        self.rate_limit_s = rate_limit_ms / 1000
        self.max_retries = max_retries
        self.timeout_s = timeout_ms / 1000

    def _build_request(self, question: str, question_id: str) -> dict:
        template = json.dumps(self.config.get("request_template", {"message": "{{question}}"}))
        # json.dumps(...)[1:-1] escapes quotes, backslashes AND newlines correctly
        body = template.replace("{{question}}", json.dumps(question)[1:-1]).replace("{{id}}", json.dumps(question_id)[1:-1])
        return json.loads(body)

    def _extract_response(self, data: dict) -> str:
        # Supports list indices, e.g. "choices.0.message.content"
        path = self.config.get("response_path", "response")
        result = data
        for key in path.split("."):
            if isinstance(result, list) and key.isdigit():
                result = result[int(key)] if int(key) < len(result) else ""
            elif isinstance(result, dict):
                result = result.get(key, "")
            else:
                return ""
        return str(result)

    async def _call_rest(self, session: aiohttp.ClientSession, question: str, qid: str) -> tuple:
        body = self._build_request(question, qid)
        auth = self.config.get("auth", {})
        headers = {"Content-Type": "application/json"}

        if auth.get("type") == "bearer":
            headers["Authorization"] = f"Bearer {auth['token']}"
        elif auth.get("type") == "api_key":
            headers[auth.get("header", "X-API-Key")] = auth["token"]

        endpoint = self.config["endpoint"]
        method = self.config.get("method", "POST").upper()

        start = time.monotonic()
        async with session.request(
            method, endpoint,
            json=body, headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout_s)
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return self._extract_response(data), elapsed_ms

    async def _call_with_retry(self, session: aiohttp.ClientSession, question: str, qid: str) -> dict:
        for attempt in range(1, self.max_retries + 1):
            try:
                response_text, elapsed_ms = await self._call_rest(session, question, qid)
                return {"response": response_text, "response_time_ms": elapsed_ms, "success": True, "attempt": attempt, "error": None}
            except Exception as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** (attempt - 1))
                else:
                    return {"response": None, "response_time_ms": None, "success": False, "attempt": attempt, "error": str(e)}

    async def run_all(self, questions: list, output_file: str = "raw_responses.json") -> list:
        results = []
        failed_count = 0

        async with aiohttp.ClientSession() as session:
            for i, q in enumerate(questions, 1):
                print(f"  [{i}/{len(questions)}] {q['question'][:60]}...")
                result = await self._call_with_retry(session, q["question"], q["id"])
                if not result["success"]:
                    failed_count += 1

                results.append({
                    "question_id": q["id"],
                    "question": q["question"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **result
                })

                # Stop early if > 50% failing — likely a config issue
                if i >= 4 and failed_count / i > 0.5:
                    raise RuntimeError(f"Over 50% of API calls failing. Check API config. Last error: {result.get('error')}")

                if i < len(questions):
                    await asyncio.sleep(self.rate_limit_s)

        Path(output_file).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
        success = sum(1 for r in results if r["success"])
        print(f"✓ {success}/{len(results)} successful → {output_file}")
        return results

    def run(self, questions_file: str, output_file: str = "raw_responses.json") -> list:
        questions = json.loads(Path(questions_file).read_text(encoding="utf-8"))  # Windows default cp1252 breaks Vietnamese
        return asyncio.run(self.run_all(questions, output_file))


if __name__ == "__main__":
    # Usage: python chatbot_caller.py questions.json chatbot_url [output.json]
    # API config read from api_config.json in current directory
    config = json.loads(Path("api_config.json").read_text(encoding="utf-8")) if Path("api_config.json").exists() else {
        "endpoint": sys.argv[2],
        "method": "POST",
        "request_template": {"message": "{{question}}"},
        "response_path": "response"
    }
    caller = ChatbotAPICaller(config)
    caller.run(sys.argv[1], sys.argv[3] if len(sys.argv) > 3 else "raw_responses.json")
```

## Dependencies
```bash
pip install aiohttp
```

## API Config File (api_config.json)

Create this file before running for custom chatbot APIs:
```json
{
  "endpoint": "https://your-chatbot.com/api/chat",
  "method": "POST",
  "auth": {
    "type": "bearer",
    "token": "your-api-token"
  },
  "request_template": {
    "message": "{{question}}"
  },
  "response_path": "choices.0.message.content"
}
```

## Streaming Response (SSE)

LLM chatbots often stream tokens as Server-Sent Events. Aggregate the stream until "done":

```python
async def _call_sse(session, question, qid):
    body = self._build_request(question, qid)
    async with session.post(endpoint, json=body, headers=headers) as resp:
        full = ""
        async for line in resp.content:
            line = line.decode().strip()
            if line.startswith("data: "):
                chunk = line[6:]
                if chunk == "[DONE]":
                    break
                full += json.loads(chunk).get("delta", {}).get("content", "")
        return full
```

## Multi-Turn Context (Conversation History)

Some questions only make sense after prior context. Maintain `session_id` across calls:

```python
session_id = f"test-session-{int(time.time())}"
for q in questions:
    body = {**self.config["request_template"], "session_id": session_id, "message": q["question"]}
    # send body — server retains context per session_id
```

For tests that explicitly want isolated questions, generate a NEW session_id per question.

## Key Principles
- Rate limiting is mandatory — respect `rate_limit_ms` between requests to avoid overwhelming the chatbot
- Always record timing from request start to full response received
- A failed question (all retries exhausted) appears in output with `success: false` — never silently skip it
- If > 50% of requests fail, stop early and report the API configuration issue to the user
- Use exponential backoff (1s, 2s, 4s) between retries — not fixed delays
