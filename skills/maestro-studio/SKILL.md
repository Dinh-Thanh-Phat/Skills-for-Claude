---
name: maestro-studio
description: |
  Maestro Studio — the browser-based visual IDE for building and debugging Maestro mobile test flows.
  Use when you want to: inspect UI elements on a live device/emulator without reading source code,
  record interactions as YAML automatically, or use MaestroGPT (the built-in AI assistant) to
  generate YAML from plain English or diagnose failing flows.
  Triggers on: "maestro studio", "maestroGPT", "maestro element inspector", "maestro flow builder",
  "maestro visual IDE", "maestro record interactions", "maestro ai yaml generator", "maestro debug studio".
---

# Maestro Studio

Maestro Studio is the **browser-based visual IDE** that connects directly to a running emulator,
simulator, or physical device. It has three integrated tools that work together for rapid flow
development — distinct from the `maestro-mcp-workflow` skill (which wires the CLI into Claude Code).

Launch it:

```bash
maestro studio
# Opens http://localhost:9999 in the browser; connects to the first detected device
```

---

## Tool 1 — Element Inspector

Highlights any UI component on the live device screen and reveals its selectable attributes.

**What you get per element:**
- `id` (resource-id / accessibility id) — preferred stable selector
- `text` — visible label
- `hint` / `contentDescription` — accessibility attributes
- Bounds (x, y, width, height) — for swipe target calculation

**Workflow:**
1. Tap any element in the Studio preview panel.
2. Studio highlights it and shows the attribute panel on the right.
3. Copy the `id:` or `text:` value directly into your YAML.

**Why it matters:** Eliminates the need to read app source code or run `adb uiautomator dump` to discover element IDs. Especially useful when element IDs aren't documented and the app is a third-party binary.

---

## Tool 2 — Flow Builder

Records your live interactions with the device and converts them to Maestro YAML in real time.

**How to use:**
1. Click **Record** in Studio.
2. Interact normally with the device (tap, swipe, type).
3. Studio emits the corresponding YAML commands line by line.
4. Click **Stop** when the sequence is complete.
5. Copy or export the generated YAML to your `flows/` directory.

**Output example** for tapping a login button and entering credentials:

```yaml
- tapOn:
    id: "com.example.app:id/login_button"
- tapOn:
    id: "com.example.app:id/email_input"
- inputText: "test@example.com"
- tapOn:
    id: "com.example.app:id/password_input"
- inputText: "secret"
- tapOn:
    text: "Sign in"
```

**Refinement rule:** Replace `text:` selectors that contain dynamic content (e.g., timestamps, usernames) with `id:` selectors found via the inspector before committing.

---

## Tool 3 — MaestroGPT (Built-in AI Assistant)

An AI assistant embedded in Studio that understands both the Maestro command set and the **current live screen state**. Grounded suggestions, not hallucinated YAML.

### Generate a flow from plain English

Type a description in the MaestroGPT chat panel:

> "Test the checkout flow: add item to cart, proceed to checkout, enter a coupon code SAVE10, assert it is invalid, then remove the coupon and verify the original price is restored."

MaestroGPT:
1. Reads the current UI hierarchy from the connected device.
2. Matches element IDs visible on screen to your description.
3. Outputs valid YAML using exact IDs from the hierarchy — no guessing.

Teams report cutting test creation time from **several hours to 10–15 minutes**.

### Debug a failing flow

Paste the failure output and ask:

> "The flow fails at 'tapOn: checkout__confirm-button'. Here's the error log: [paste]. Fix the selector."

MaestroGPT reads the live hierarchy, identifies the correct element, and proposes the corrected YAML.

---

## Recommended Studio Workflow

```
1. INSPECT   → Tap each screen element; collect stable id: values
2. RECORD    → Record the happy path; get baseline YAML
3. REFINE    → Replace fragile text: selectors with id: from inspector
4. GENERATE  → Use MaestroGPT for complex logic (conditionals, loops, assertions)
5. VALIDATE  → maestro validate flows/my-flow.yaml
6. RUN       → maestro test flows/my-flow.yaml
```

---

## Studio vs MCP vs CLI

| Situation | Use |
|---|---|
| Discovering element IDs on a live device | Studio — Element Inspector |
| Recording a happy-path flow quickly | Studio — Flow Builder |
| Generating complex YAML from English | Studio — MaestroGPT |
| Driving Maestro from Claude Code | `maestro-mcp-workflow` skill |
| Running flows in CI without a UI | `maestro test` CLI |
| AI assertions in YAML (`assertWithAI`) | `maestro-ai-assertions` skill |

---

## Sources

- [Maestro Studio overview — maestro.dev insights](https://maestro.dev/insights/end-to-end-ui-testing-for-mobile-apps-with-maestro)
- [How AI Improves Mobile UI Test Automation — maestro.dev](https://maestro.dev/insights/how-ai-improves-mobile-ui-test-automation)
- [Maestro Mobile Testing Guide 2026 — qaskills.sh](https://qaskills.sh/blog/maestro-mobile-testing-guide-2026)
- [GitHub — mobile-dev-inc/Maestro](https://github.com/mobile-dev-inc/maestro)
