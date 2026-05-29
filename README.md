# Skills-for-Claude

Personal Claude Code skill library — 85+ custom skills for QA automation, testing, and development workflows.

## Quick Setup (New Machine)

### Windows (PowerShell)

```powershell
git clone https://github.com/Dinh-Thanh-Phat/Skills-for-Claude.git
cd Skills-for-Claude
.\setup.ps1
```

### Mac / Linux / Git Bash

```bash
git clone https://github.com/Dinh-Thanh-Phat/Skills-for-Claude.git
cd Skills-for-Claude
bash setup.sh
```

After setup, **restart Claude Code** to activate skills and hooks.

---

## What Gets Installed

| Source | Destination | Description |
|--------|-------------|-------------|
| `skills/` | `~/.claude/skills/` | 85+ custom skills |
| `hooks/fix-flat-skill.py` | `~/.claude/hooks/` | Auto-converts flat skill .md to dir format |
| `shared-context/memories/_shared.md` | `~/.claude/shared-context/memories/` | Global behaviour rules |
| `config/settings.template.json` | `~/.claude/settings.json` | Hooks + plugins config (if no settings.json exists) |

---

## Manual Settings Merge

If you already have `~/.claude/settings.json`, merge the following sections from `config/settings.template.json`:

1. **`hooks`** — critical for skill structure and `bd prime` on session start
2. **`enabledPlugins`** — official Claude Code plugins
3. **`extraKnownMarketplaces`** — adds `playwright-skill` marketplace

---

## Post-Install: Additional Tools

Some skills depend on external tools. Install as needed:

### beads (bd) — issue tracker

```bash
npm install -g beads-cli
```

Windows: ensure `bd.exe` is in PATH:
```
C:/Users/<user>/AppData/Roaming/npm/bd.exe
```

### Dolt — version-controlled database (used by beads)

Download from https://github.com/dolthub/dolt/releases or:
```powershell
winget install DoltHub.Dolt
```

Add to PATH: `C:/Program Files/dolt/bin`

### Playwright

```bash
npm install -D @playwright/test
npx playwright install chromium
```

### Python dependencies (for chatbot testing pipeline)

```bash
pip install playwright pdfplumber openpyxl requests python-dotenv
python -m playwright install chromium
```

### OCR (for ocr-processor skill)

- **Tesseract**: https://github.com/UB-Mannheim/tesseract/wiki
- After install, add Vietnamese language pack:
  ```
  C:/Program Files/Tesseract-OCR/tessdata/vie.traineddata
  ```
  Download from: https://github.com/tesseract-ocr/tessdata

---

## Skill Categories

### QA & Testing Orchestration
- `qa-router` — entry point for all QA tasks (routes to right skill)
- `qa-session-start` / `qa-session-close` — session lifecycle
- `qa-preflight` — environment check before running tests
- `qa-test-generation` — generate test cases from requirements
- `qa-test-coverage-max` — maximum coverage from multi-source inputs
- `qa-e2e-complete` — full E2E test suites
- `qa-bug-report` — professional bug reports
- `qa-regression` — regression test management
- `behavioral-coverage-matrix` — behavior inventory before test writing

### Playwright E2E
- `playwright-diagnosis-first` — diagnose before fixing
- `playwright-snapshot-parser` — parse aria snapshots for selectors
- `playwright-test-workflow` — complete test creation workflow
- `playwright-page-object-model` — POM pattern enforcement
- `playwright-network-interception` — mock APIs, intercept requests
- `playwright-flaky-test-detection` — detect and fix flaky tests
- `playwright-link-audit` — broken link checker
- `playwright-artifact-cleanup` — prevent disk overflow
- `playwright-reporter-discipline` — correct reporter usage

### Mobile Testing
- `maestro-mobile` — Maestro YAML flows for iOS + Android
- `android-adb` — ADB device management
- `ios-xcrun` — iOS simulator management

### Assertions & Test Quality
- `fail-loud` — enforce hard assertions
- `outcome-verification` — verify business outcomes not just UI
- `cross-module-verify` — multi-module workflow testing
- `soft-assertion-ban` — ban `expect(A || B)` patterns
- `skip-vs-fail` — when to skip vs fail tests
- `test-isolation` — prevent test interdependencies
- `flaky-test-prevention` — systematic flakiness prevention

### Test Data & Lifecycle
- `test-data-lifecycle` / `test-data-lifecycle-strategy` — cleanup strategies
- `otp-untestable-flows` — OTP/email verification strategy
- `test-auth-strategy` — authentication test patterns
- `auth-session-testing` — session management testing

### Diagnosis & Debugging
- `ask-when-stuck` — stop and ask after 1-2 failures
- `test-diagnosis-before-code` — diagnose before writing tests
- `playwright-diagnosis-first` — full diagnosis workflow
- `test-failure-triage` — quick failure categorization
- `test-debug-checklist` — quick reference for debugging
- `systematic-debugging` (via superpowers)

### Chatbot Testing Pipeline
- `chatbot-tester` — main orchestrator
- `gdrive-doc-reader` — read docs from Google Drive
- `qa-generator` — generate test questions from docs
- `chatbot-api-caller` — call chatbot API with questions
- `chatbot-ui-automator` — test via browser UI
- `response-evaluator` — evaluate chatbot answers
- `performance-analyzer` — p50/p95/p99 metrics
- `ocr-processor` — OCR for scanned PDFs

### Frontend & UI
- `fe-component-builder` — React components from descriptions
- `figma-to-code` — implement UI from Figma designs
- `accessibility-testing` — WCAG / axe-core testing
- `visual-regression-testing` — screenshot comparison
- `responsive-viewport-testing` — multi-viewport testing
- `ui-error-classification` — classify UI errors

### Data & Files
- `file-aggregation-comparison` — compare/merge Excel/CSV files
- `gsheet-formatter` — format Google Sheets via API
- `gsheet-safe-write` — safe Google Sheets write protocol
- `demo-slide-builder` — build .pptx presentations

### Project Management
- `beads` — Dolt-powered issue tracker
- `openspec-explore/propose/apply/archive` — spec management
- `odoo-project-automation` — Odoo task/bug management

### Skill Management
- `skill-creator` — create new skills
- `skill-updater` — update existing skills
- `skill-discovery` — find skills for a task
- `using-superpowers` (via superpowers plugin)

---

## Directory Structure

```
Skills-for-Claude/
├── README.md
├── setup.ps1                    # Windows setup
├── setup.sh                     # Mac/Linux/Git Bash setup
├── skills/                      # All skills (→ ~/.claude/skills/)
│   ├── accessibility-testing/
│   │   └── SKILL.md
│   └── ... (85+ skills)
├── hooks/                       # Claude hooks (→ ~/.claude/hooks/)
│   └── fix-flat-skill.py
├── shared-context/              # Global context (→ ~/.claude/shared-context/)
│   └── memories/
│       └── _shared.md
├── config/
│   └── settings.template.json  # Settings template
└── project-example/            # Example project .claude/ structure
    └── .claude/
        └── skills/
            ├── fe-component-builder/
            ├── figma-to-code/
            └── openspec-*/
```

---

## Project-Level Skills

Skills in `project-example/.claude/skills/` are intended for specific projects:

| Skill | Purpose |
|-------|---------|
| `fe-component-builder` | React component generation |
| `figma-to-code` | Figma design → React code |
| `openspec-explore` | Explore API specs |
| `openspec-propose` | Propose spec changes |
| `openspec-apply-change` | Apply spec changes |
| `openspec-archive-change` | Archive spec changes |

Copy to `<your-project>/.claude/skills/` as needed.

---

## Updating Skills

After pulling changes:
```bash
git pull
.\setup.ps1 --force    # Windows
bash setup.sh --force  # Mac/Linux
```
