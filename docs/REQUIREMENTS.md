# What each group of skills needs

Skills are plain instructions — **all 165 load without installing anything**. The tools below are only
needed when you actually run what a skill describes. `python install.py` prints which ones it found.

| Skills | Needs | Install |
|---|---|---|
| `playwright-*`, most web E2E skills | Node 18+, Playwright | `npm i -D @playwright/test` then `npx playwright install chromium` |
| `maestro-*` | Java 17+, Maestro CLI ≥ 2.11 | `curl -fsSL "https://get.maestro.mobile.dev" \| bash` (Windows: https://docs.maestro.dev/getting-started/installing-maestro) |
| `android-*`, Maestro on Android | Android platform-tools (`adb`) | Android Studio, or `winget install Google.PlatformTools` |
| `ios-*`, Maestro on iOS | macOS + Xcode | App Store |
| `gdrive-doc-reader`, `gsheet-formatter`, `gsheet-safe-write`, `qa-generator` (Drive input) | Google OAuth token at `~/.google-docs-token.json` | `python tools/google_auth.py client_secret.json` (steps inside the script) |
| `qa-generator`, `response-evaluator`, `chatbot-*` | Python 3.10+, `GROQ_API_KEY` or `ANTHROPIC_API_KEY` | `pip install groq anthropic python-dotenv openpyxl requests` |
| `deepeval-llm-cicd`, `llm-red-teaming`, `llm-structured-output-testing` | an LLM key (`OPENAI_API_KEY` / `ANTHROPIC_API_KEY`) | `pip install deepeval` — see each skill |
| `ocr-processor` | Tesseract (+ `vie.traineddata` for Vietnamese) | https://github.com/UB-Mannheim/tesseract/wiki |
| `beads`, `--with-beads`, `--with-qa-gates` stop hook | `bd` (+ Dolt) on PATH | https://github.com/gastownhall/beads/releases |
| `odoo-tour-testing` | an Odoo instance | — |

## API keys

Put keys in environment variables (or a `.env` next to your project — `.env` is git-ignored here).
Never commit them. The skills read `GROQ_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`.

## Plugins

`install.py` installs these Claude Code plugins (skip with `--skip-plugins`); several skills hand off to them:
`superpowers`, `playwright`, `skill-creator`, `context7`, `code-review`, `pr-review-toolkit`,
`commit-commands`, `frontend-design`, `claude-md-management`, `claude-code-setup`, `playwright-skill`.
If the `claude` CLI is not on PATH, install them later with `/plugin` inside Claude Code.
