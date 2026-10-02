---
name: chatbot-ui-automator
description: Automate chatbot testing through browser UI using Playwright — sends questions, waits for stable responses, measures response time, and captures screenshots. Use as a drop-in replacement for chatbot-api-caller when the chatbot has a web interface instead of (or in addition to) an API. No API keys needed. Triggers on: "test chatbot via browser", "automate chatbot UI", "send questions to chatbot web interface", "test chatbot without API", "chatbot UI automation", "Playwright chatbot testing". Outputs raw_responses.json in the same format as chatbot-api-caller so all downstream skills (response-evaluator, performance-analyzer, test-reporter) work unchanged.
---

# Chatbot UI Automator

Replaces `chatbot-api-caller` for web-based chatbots. Uses Playwright to control a real browser, type questions into the chat UI, and extract answers — identical output format, no API parsing required.

## Pipeline Position

```
gdrive-doc-reader → qa-generator → [chatbot-ui-automator] → response-evaluator → performance-analyzer → test-reporter
```

Drop-in replacement for `chatbot-api-caller`. Downstream skills need no changes.

## Output: raw_responses.json

Same schema as `chatbot-api-caller`:
```json
[
  {
    "question_id": "q001",
    "question": "Thuế suất TNDN là bao nhiêu?",
    "response": "Thuế suất thuế TNDN thông thường là 20%...",
    "response_time_ms": 3420,
    "timestamp": "2025-01-15T10:23:45.123Z",
    "success": true,
    "attempt": 1,
    "error": null,
    "screenshot": "screenshots/q001.png"
  }
]
```

---

## Python Implementation

Write this script as `chatbot_ui_automator.py`:

```python
import asyncio
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout


# ── 1. ELEMENT AUTO-DETECTION ────────────────────────────────────────────────

# Prefer semantic Playwright locators (role, label, placeholder) over CSS selectors —
# they survive UI refactors and match how users see the page.
INPUT_STRATEGIES = [
    # Semantic (most robust)
    lambda p: p.get_by_role("textbox"),
    lambda p: p.get_by_placeholder(re.compile(r"nhập|hỏi|type|message|chat", re.I)),
    # CSS fallback
    lambda p: p.locator("textarea").first,
    lambda p: p.locator('div[contenteditable="true"]').first,
    lambda p: p.locator('[data-testid*="input"]').first,
    lambda p: p.locator('.chat-input, .message-input, .input-box, #chat-input').first,
]

SEND_STRATEGIES = [
    lambda p: p.get_by_role("button", name=re.compile(r"gửi|send|submit", re.I)),
    lambda p: p.locator('button[type="submit"]').first,
    lambda p: p.locator('[aria-label*="send" i]').first,
    lambda p: p.locator('.send-button, .send-btn').first,
]

RESPONSE_STRATEGIES = [
    lambda p: p.locator('[data-role="assistant"]').last,
    lambda p: p.locator('.assistant-message, .bot-message, .chat-message').last,
    lambda p: p.locator('.message').last,
]


async def _first_visible(page: Page, strategies: list):
    """Try each strategy; return first locator that has a visible element."""
    for strategy in strategies:
        try:
            loc = strategy(page)
            if await loc.count() > 0 and await loc.is_visible():
                return loc
        except Exception:
            pass
    return None


async def find_input(page: Page, custom_selector: str = None) -> object:
    if custom_selector:
        return page.locator(custom_selector).first
    loc = await _first_visible(page, INPUT_STRATEGIES)
    if not loc:
        raise RuntimeError("Could not find chat input box. Set custom_selectors.input in config.")
    return loc


async def find_send_button(page: Page, custom_selector: str = None):
    if custom_selector:
        return page.locator(custom_selector).first
    return await _first_visible(page, SEND_STRATEGIES)  # None = use Enter


async def find_response_area(page: Page, custom_selector: str = None):
    if custom_selector:
        return page.locator(custom_selector).last
    loc = await _first_visible(page, RESPONSE_STRATEGIES)
    if not loc:
        raise RuntimeError("Could not find response area. Set custom_selectors.response in config.")
    return loc


# Same selectors as RESPONSE_STRATEGIES but WITHOUT .last — used to COUNT bubbles.
RESPONSE_GROUP_CSS = [
    '[data-role="assistant"]',
    '.assistant-message, .bot-message, .chat-message',
    '.message',
]


async def response_group(page: Page, custom_selector: str = None):
    """Locator matching ALL response bubbles (for counting before/after send)."""
    if custom_selector:
        return page.locator(custom_selector)
    for css in RESPONSE_GROUP_CSS:
        loc = page.locator(css)
        if await loc.count() > 0:
            return loc
    return page.locator(", ".join(RESPONSE_GROUP_CSS))  # nothing rendered yet


def _is_own_question(text: str, question: str) -> bool:
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    t, q = norm(text), norm(question)
    return bool(t) and (t == q or t.startswith(q[:40]))


async def wait_for_new_bot_bubble(group, before: int, question: str, timeout_s: int = 30):
    """Wait until a NEW bubble exists AND the last bubble is not our own question.

    Bot and user bubbles often share a CSS class (e.g. `.message`) — then `.last` right
    after send is the question we just typed; it is "stable" and would be recorded as the
    answer. Count-before + not-own-question avoids that.
    """
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        n = await group.count()
        if n > before:
            try:
                last_txt = (await group.last.inner_text()).strip()
            except Exception:
                last_txt = ""
            if last_txt and not _is_own_question(last_txt, question):
                return group.last
        await asyncio.sleep(0.25)
    raise RuntimeError("No new bot bubble appeared (only our own question?) — check custom_selectors.response")


# ── 2. RESPONSE STABILITY DETECTION ─────────────────────────────────────────
# networkidle is discouraged for SPAs (streaming chatbots never reach idle).
# Instead, poll for text stability — response is "done" when text stops changing.

async def wait_for_stable_response(
    page: Page,
    response_selector,
    stability_checks: int = 3,
    check_interval_ms: int = 500,
    timeout_s: int = 60,
) -> str:
    """
    Wait until the response element's text stops changing for `stability_checks` consecutive
    intervals. This handles streaming output correctly without relying on networkidle.
    """
    deadline = time.monotonic() + timeout_s
    previous_text = ""
    stable_count = 0

    # First: wait for the LAST matching bubble to have text (up to 15s).
    # querySelectorAll(...).pop() — querySelector() returns the FIRST (oldest) bubble,
    # which already has text after question 1, so the wait would pass instantly.
    try:
        await page.wait_for_function(
            "(sel) => { const els = document.querySelectorAll(sel); const el = els[els.length - 1]; return el && el.innerText.trim().length > 5; }",
            arg=await response_selector.evaluate("el => el.tagName.toLowerCase() + (el.id ? '#'+el.id : '') + (el.className ? '.'+el.className.split(' ')[0] : '')"),
            timeout=15_000,
        )
    except Exception:
        pass  # Fall through to stability polling

    while time.monotonic() < deadline:
        try:
            current_text = (await response_selector.inner_text()).strip()
        except Exception:
            await asyncio.sleep(check_interval_ms / 1000)
            continue

        if current_text == previous_text and current_text:
            stable_count += 1
            if stable_count >= stability_checks:
                return current_text
        else:
            stable_count = 0
        previous_text = current_text
        await asyncio.sleep(check_interval_ms / 1000)

    return previous_text  # Return whatever we have at timeout


def clean_response_text(text: str) -> str:
    """Remove common UI artifacts: timestamps, bot-name prefixes, trailing ellipsis."""
    text = re.sub(r'\d{1,2}:\d{2}(?:\s*[AP]M)?', '', text)
    text = re.sub(r'^(?:Bot|Assistant|AI|Trợ lý):\s*', '', text, flags=re.I)
    text = re.sub(r'\.{3,}$', '', text.strip())  # trailing typing indicator
    return re.sub(r'\n{3,}', '\n\n', text).strip()


# ── 3. SESSION & CORE INTERACTION ────────────────────────────────────────────

class ChatbotUIAutomator:
    def __init__(self, config: dict):
        self.url = config["chatbot_url"]
        self.headless = config.get("headless", True)
        self.typing_delay = config.get("typing_delay_ms", 30)
        self.response_timeout = config.get("response_timeout_s", 60)
        self.delay_between_q = config.get("delay_between_questions_s", 2)
        self.max_retries = config.get("max_retries", 3)
        self.save_screenshots = config.get("save_screenshots", True)
        self.custom_sel = config.get("custom_selectors", {})
        self.screenshot_dir = Path(config.get("screenshot_dir", "screenshots"))
        self.browser_type = config.get("browser", "chromium")
        if self.save_screenshots:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    async def _ask_once(self, page: Page, question: str, qid: str) -> dict:
        """Send one question and return result dict."""
        input_box = await find_input(page, self.custom_sel.get("input"))
        send_btn = await find_send_button(page, self.custom_sel.get("send_button"))

        # Count response bubbles BEFORE sending (see wait_for_new_bot_bubble).
        group = await response_group(page, self.custom_sel.get("response"))
        before = await group.count()

        # Type question
        await input_box.click()
        await input_box.fill("")  # clear
        await input_box.type(question, delay=self.typing_delay)

        t_start = time.monotonic()

        # Send
        if send_btn:
            await send_btn.click()
        else:
            await input_box.press("Enter")

        # Wait for a NEW bubble that is not our own question (no fixed sleep)
        response_loc = await wait_for_new_bot_bubble(
            group, before, question, timeout_s=min(30, self.response_timeout)
        )
        text = await wait_for_stable_response(
            page, response_loc,
            timeout_s=self.response_timeout,
        )
        elapsed_ms = int((time.monotonic() - t_start) * 1000)
        text = clean_response_text(text)

        screenshot_path = None
        if self.save_screenshots:
            screenshot_path = str(self.screenshot_dir / f"{qid}.png")
            await page.screenshot(path=screenshot_path)

        return {
            "response": text,
            "response_time_ms": elapsed_ms,
            "success": bool(text and len(text) > 5),
            "screenshot": screenshot_path,
        }

    async def _ask_with_retry(self, page: Page, question: str, qid: str) -> dict:
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = await self._ask_once(page, question, qid)
                if result["success"]:
                    result["attempt"] = attempt
                    result["error"] = None
                    return result
                # Empty response — retry
                last_error = "Empty or too-short response"
            except Exception as e:
                last_error = str(e)
                print(f"    Attempt {attempt} failed: {last_error}")
            if attempt < self.max_retries:
                await asyncio.sleep(2 ** (attempt - 1))  # 1s, 2s, 4s

        return {
            "response": None,
            "response_time_ms": None,
            "success": False,
            "attempt": self.max_retries,
            "error": f"Failed after {self.max_retries} attempts: {last_error}",
            "screenshot": None,
        }

    async def run_all(self, questions: list, output_file: str = "raw_responses.json") -> list:
        results = []
        failed = 0

        async with async_playwright() as pw:
            browser_launcher = getattr(pw, self.browser_type)
            browser = await browser_launcher.launch(headless=self.headless)
            context = await browser.new_context(viewport={"width": 1280, "height": 720})
            page = await context.new_page()

            print(f"Opening: {self.url}")
            await page.goto(self.url, wait_until="domcontentloaded")
            # Brief pause — let SPA render; don't use networkidle (chatbots keep connections open)
            await asyncio.sleep(2)

            for i, q in enumerate(questions, 1):
                qid = q.get("id", f"q{i:03d}")
                question_text = q["question"]
                print(f"  [{i}/{len(questions)}] {question_text[:60]}...")

                result = await self._ask_with_retry(page, question_text, qid)
                if not result["success"]:
                    failed += 1

                results.append({
                    "question_id": qid,
                    "question": question_text,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **result,
                })

                # Abort early if majority failing (likely a UI config issue)
                if i >= 4 and failed / i > 0.5:
                    await browser.close()
                    raise RuntimeError(
                        f"Over 50% of UI interactions failing. Check selectors or chatbot URL. "
                        f"Last error: {result.get('error')}"
                    )

                if i < len(questions):
                    await asyncio.sleep(self.delay_between_q)

            await browser.close()

        Path(output_file).write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        success = sum(1 for r in results if r["success"])
        print(f"✓ {success}/{len(results)} successful → {output_file}")
        return results

    def run(self, questions_file: str, output_file: str = "raw_responses.json") -> list:
        questions = json.loads(Path(questions_file).read_text(encoding="utf-8"))
        return asyncio.run(self.run_all(questions, output_file))


if __name__ == "__main__":
    # Usage: python chatbot_ui_automator.py questions.json chatbot_url [output.json] [config.json]
    if len(sys.argv) < 3:
        print("Usage: python chatbot_ui_automator.py <questions.json> <chatbot_url> [output.json] [config.json]")
        sys.exit(1)

    cfg_path = sys.argv[4] if len(sys.argv) > 4 else "ui_automator_config.json"
    config = json.loads(Path(cfg_path).read_text()) if Path(cfg_path).exists() else {}
    config["chatbot_url"] = sys.argv[2]

    automator = ChatbotUIAutomator(config)
    automator.run(
        questions_file=sys.argv[1],
        output_file=sys.argv[3] if len(sys.argv) > 3 else "raw_responses.json",
    )
```

---

## Config File (ui_automator_config.json)

```json
{
  "chatbot_url": "https://your-chatbot.com/chat",
  "headless": true,
  "browser": "chromium",
  "typing_delay_ms": 30,
  "response_timeout_s": 60,
  "delay_between_questions_s": 2,
  "max_retries": 3,
  "save_screenshots": true,
  "screenshot_dir": "./screenshots",
  "custom_selectors": {
    "input": null,
    "send_button": null,
    "response": null
  }
}
```

**`headless`**: `false` = show browser (useful for debugging why selectors fail).
**`custom_selectors`**: Override auto-detection. Set to CSS selector string if auto-detect fails.
**`response_timeout_s`**: Max seconds to wait for a complete response. Increase for slow LLM backends.
**`delay_between_questions_s`**: Pause between questions. Prevents rate-limiting and gives chatbot time to reset state.

---

## Auto-Detection Order

The skill tries selectors in priority order. If auto-detection fails, set `custom_selectors` in config.

### Input box
1. `getByRole("textbox")` — semantic, preferred
2. `getByPlaceholder` matching Vietnamese/English input hints
3. `textarea` elements
4. `contenteditable` divs
5. Common CSS class/id patterns

### Send button
1. `getByRole("button")` matching "gửi / send / submit"
2. `button[type="submit"]`
3. `[aria-label*="send"]`
4. Falls back to **Enter key** if no button found

### Response area
1. `[data-role="assistant"]` (semantic)
2. `.assistant-message`, `.bot-message`, `.chat-message` (last)
3. `.message` (last)

---

## Stability Detection (Streaming-Safe)

`networkidle` is unreliable for chatbots — streaming LLMs continuously write to the network. Instead:

1. Poll response element every 500ms
2. Count consecutive polls where text hasn't changed
3. Declare "stable" after 3 consecutive unchanged polls (~1.5s of silence)
4. Hard timeout at `response_timeout_s` — return whatever text exists

This works correctly for both streaming (word-by-word) and batch (single-shot) chatbot responses.

---

## Dependencies

```bash
pip install playwright
playwright install chromium
# (Optional) firefox and webkit:
playwright install firefox webkit
```

---

## Chatbot Needs Login

Add a `login_steps` block to config and run it once on page load:

```json
{
  "chatbot_url": "https://app.example.com/chat",
  "login_steps": {
    "url": "https://app.example.com/login",
    "email_selector": "[name=email]",
    "password_selector": "[name=password]",
    "submit_selector": "button[type=submit]",
    "post_login_wait_for": "text=Chat"
  }
}
```

```python
async def _do_login(self, page):
    if not self.cfg.get("login_steps"): return
    s = self.cfg["login_steps"]
    await page.goto(s["url"])
    await page.fill(s["email_selector"], os.environ["TEST_EMAIL"])
    await page.fill(s["password_selector"], os.environ["TEST_PASSWORD"])
    await page.click(s["submit_selector"])
    await page.wait_for_selector(s["post_login_wait_for"], timeout=30000)
```

## Citation / Source Extraction

Many RAG chatbots show citations in the response (links, footnotes). Extract them so the
evaluator can verify the chatbot used the right source:

```python
# Extract citation links from the response element
citations = await response_loc.locator('a, [data-citation]').all()
sources = []
for c in citations:
    text = await c.inner_text()
    href = await c.get_attribute('href')
    sources.append({'text': text, 'href': href})
result['citations'] = sources
```

## Debugging Tips

**If auto-detection fails:**
1. Set `"headless": false` to watch the browser
2. Open DevTools → find the input CSS selector
3. Set `custom_selectors.input` in config

**If response is cut off:**
- Increase `stability_check_interval` (default 500ms) or `stability_checks` count
- Increase `response_timeout_s` for slow backends

**If questions fail intermittently:**
- Increase `delay_between_questions_s` — chatbot may need time to reset session state
- Check if chatbot requires login — add a `login_steps` pre-run block

---

## Integration with chatbot-tester

In `run_chatbot_test.py`, choose API caller vs UI automator based on config:

```python
def get_caller_config(user_config: dict) -> str:
    if user_config.get("use_ui_automator") or not user_config.get("api_endpoint"):
        return "ui"  # use chatbot_ui_automator.py
    return "api"     # use chatbot_caller.py

# Step 3 dispatch
if caller_mode == "ui":
    subprocess.run(["python", "chatbot_ui_automator.py",
                    "test_questions.json", chatbot_url, "raw_responses.json"], check=True)
else:
    subprocess.run(["python", "chatbot_caller.py",
                    "test_questions.json", chatbot_url, "raw_responses.json"], check=True)
```

---

## Key Principles

- **Semantic locators first**: `getByRole`, `getByPlaceholder` survive UI refactors; CSS selectors break when class names change.
- **Never use `networkidle` for chatbots**: Streaming LLMs keep the connection alive — `networkidle` will timeout. Use text stability polling instead.
- **Screenshot on every question**: When a question fails, the screenshot shows exactly what the browser saw. This is the main debugging tool.
- **Abort at 50% failure**: If half the interactions fail, it's a config problem, not a chatbot quality issue — stop early and report.
- **Same output format as chatbot-api-caller**: The `raw_responses.json` schema must match exactly so `response-evaluator`, `performance-analyzer`, and `test-reporter` need zero changes.
