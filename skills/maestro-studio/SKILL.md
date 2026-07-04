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

## ⚡ Element discovery for an AI agent (no browser clicking)

Studio's Inspector/Flow Builder/MaestroGPT are **browser UI** at `localhost:9999` — an autonomous
agent (Claude Code, CI, headless) **cannot click them**. Use the **scriptable CLI equivalents**
instead — same on-device hierarchy, no human interaction:

```bash
# Dump the CURRENT screen's full hierarchy (JSON) — the agent-friendly Inspector
maestro hierarchy > screen.json
# Then grep resource-id / text to pick selectors:
grep -oE '"resource-id"[: ]+"[^"]+"' screen.json | sort -u   # RN testIDs land here
grep -oE '"(text|hintText)"[: ]+"[^"]+"' screen.json | sort -u
```

**Do NOT use `adb shell uiautomator dump` for React Native / Expo apps** — it often returns a
near-empty tree (RN renders to a canvas; only native chrome shows). `maestro hierarchy` pulls the
a11y tree Maestro actually uses, so RN `testID`s appear (mapped to `id:`). If a container shows no
children even in `maestro hierarchy` (a known Maestro issue), fall back to `text:`/relative selectors
or a screenshot.

### One WARM session — never re-login per dump
Login/`clearState` is the bottleneck (~30–40s each). Don't pay it for every element lookup:

1. Drive the app to the target screen **once** (one flow with login).
2. Leave it parked — run `maestro hierarchy` repeatedly as you navigate via **small attach flows
   that do NOT `launchApp`/`clearState`** (they act on the running app):
   ```yaml
   appId: com.example.app
   ---
   - tapOn: { id: "clients-add" }   # no launchApp → attaches to current session
   - takeScreenshot: "create-form"
   ```
3. Or use **Studio REPL** (when a human is driving): type single YAML commands that execute
   instantly on-device — experiment without rerunning the whole flow.

### Verify your fix with a CANARY, not the whole folder
After changing one flow, run **that one flow** (`maestro test flows/x.yaml`), not
`maestro test flows/` — a full-suite rerun for a one-line fix wastes minutes. See
`maestro-speed-optimization`.

### Ask the human about app-specific behaviour early
If a capability isn't discoverable in 1–2 probes (e.g. "where is Delete?", "what's the appointment
flow?"), **ask the person who knows the app** instead of probing N ways. Blind exploration is the
biggest time sink — cross-ref `ask-when-stuck`.

---

## Maestro Studio Desktop (Beta) — No CLI Required

A separate, native **desktop app** (macOS Apple Silicon & Intel, Windows, Linux) — distinct from the
`maestro studio` browser IDE above. It's a fully self-contained IDE: no Maestro CLI install, no terminal, no
`ANDROID_HOME`/Xcode toolchain setup. Free even though Studio itself isn't open source.

**Install:**
- Windows: download `MaestroStudio.exe`, run the setup wizard.
- macOS: download `MaestroStudio.dmg`, drag into Applications.
- Linux: download `MaestroStudio.AppImage`, `chmod +x`, run.

**What it gives you that the CLI-launched browser Studio doesn't:**
- Instantly connect a device (Android, iOS, **or Web**) without first installing/configuring the Maestro CLI.
- Same Element Inspector, visual Flow Builder, and MaestroGPT as browser Studio, but as a standalone app —
  useful for testers/PMs who need to build and run flows without a dev environment.

**Redesign (April 2026) — Contextual Autocomplete:** Desktop Studio now autocompletes commands,
arguments, and *selectors* as you type, pulled live from your connected device's current screen — not
just static YAML keyword completion. Typing `tapOn:` suggests real `id:`/`text:` values visible on
screen right now, so you stop tabbing back to Inspector to copy a selector by hand, and commands you
didn't know existed surface exactly when they're relevant. Cuts both new-user ramp-up (no need to
memorize Maestro syntax up front) and the repetitive selector-lookup loop for experienced authors.

**When to prefer Desktop over `maestro studio` (browser/CLI-launched):**

| Situation | Use |
|---|---|
| Team already has Maestro CLI + flows in a repo, needs CI | CLI + browser Studio (this skill's main sections) |
| Non-developer tester needs to build/run flows with zero setup | Studio Desktop |
| Testing a web app alongside mobile in one tool, no CLI installed | Studio Desktop |

---

## Studio vs MCP vs CLI

| Situation | Use |
|---|---|
| Discovering element IDs on a live device | Studio — Element Inspector |
| Recording a happy-path flow quickly | Studio — Flow Builder |
| Generating complex YAML from English | Studio — MaestroGPT |
| Zero-install flow authoring (no CLI/terminal) | Studio Desktop (beta) |
| Driving Maestro from Claude Code | `maestro-mcp-workflow` skill |
| Running flows in CI without a UI | `maestro test` CLI |
| AI assertions in YAML (`assertWithAI`) | `maestro-ai-assertions` skill |

---

## Sources

- [Maestro Studio overview — maestro.dev insights](https://maestro.dev/insights/end-to-end-ui-testing-for-mobile-apps-with-maestro)
- [How AI Improves Mobile UI Test Automation — maestro.dev](https://maestro.dev/insights/how-ai-improves-mobile-ui-test-automation)
- [Maestro Mobile Testing Guide 2026 — qaskills.sh](https://qaskills.sh/blog/maestro-mobile-testing-guide-2026)
- [GitHub — mobile-dev-inc/Maestro](https://github.com/mobile-dev-inc/maestro)
- [Maestro Studio Desktop — Beta (docs.maestro.dev)](https://docs.maestro.dev/getting-started/maestro-studio-desktop)
- [Maestro Studio Desktop Beta — Product Hunt](https://www.producthunt.com/products/maestro-studio-beta)
- [New Maestro Studio — Redesigned, with Contextual Autocomplete (maestro.dev, Apr 2026)](https://maestro.dev/blog/new-maestro-studio)
