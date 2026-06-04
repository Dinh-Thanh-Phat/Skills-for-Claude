# Daily Skill Evolution Log

Changelog written by the `daily-skill-evolution` remote routine (07:00 GMT+7 daily) on the `skill-evolution` branch.
Most recent at top.

<!-- Entries appended below by the routine -->

## 2026-06-04 (GMT+7)

Domains researched: AI chatbot/LLM security (adversarial testing), Frontend/Figma-to-code (design tokens), Playwright/web E2E (accessibility coverage update).

- CREATED: skills/llm-red-teaming — Adversarial LLM security testing using Garak (static probes), PyRIT (multi-turn Crescendo/TAP/Skeleton Key orchestration), and Promptfoo (CI-integrated red teaming). Covers direct injection, indirect RAG injection, and multi-turn escalation. Prompt injection is OWASP LLM Top-10 #1 in 2026; not covered by existing chatbot-tester (functional) or llm-production-observability (monitoring). Sources: https://genai.owasp.org/llmrisk/llm01-prompt-injection/, https://aisecurityandsafety.org/en/compare/garak-vs-pyrit/, https://appsecsanta.com/ai-security-tools/llm-red-teaming
- CREATED: skills/figma-design-tokens — Figma → Token Studio → Style Dictionary → CSS/Tailwind/TypeScript pipeline for React design systems. Covers W3C token JSON export, Style Dictionary transforms, GitHub Actions auto-sync, Tailwind integration, and component naming conventions. No existing skill covers Figma-to-React code workflows. Sources: https://medium.com/@alexdev82/how-we-built-a-reliable-design-token-pipeline-from-figma-to-react-fddf4725cdbe, https://docs.tokens.studio/transform-tokens/style-dictionary, https://www.superdevacademy.com/en/blogs/figma-to-react-workflow-2026
- UPDATED: skills/accessibility-testing — Corrected automated coverage figure from "~30-40%" to "~57%" per Deque Systems 2026 study; added source URL. Source: https://www.davidmello.com/software-testing/test-automation/playwright-accessibility-testing-axe-lighthouse-limitations

## 2026-06-03 (GMT+7)

Domains researched: Maestro/mobile (MCP integration), Odoo/ERP (Odoo 19 testing framework), QA test design.

- CREATED: skills/maestro-mcp-workflow — Maestro MCP server (slapglif/maestro-mcp) wires 47+ Maestro CLI tools into Claude Code; natural-language → YAML generation, live device interaction, UI-hierarchy debugging. Not covered by existing maestro-mobile skill (MCP paradigm is entirely new). Sources: https://github.com/slapglif/maestro-mcp, https://maestro.dev/blog/maestro-mcp-an-introduction, https://verygood.ventures/blog/maestro-mcp-claude-mobile-ui-test-automation/
- CREATED: skills/odoo-tour-testing — Odoo 19 three-layer test framework: Python TransactionCase/HttpCase, Tour-based browser integration tests (start_tour, watch=True debug mode, CSS trigger steps), and HOOT JS unit tests. Distinct from existing odoo-project-automation (XML-RPC task management). Sources: https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html, https://www.odoo.com/documentation/19.0/developer/reference/frontend/unit_testing/hoot.html, https://www.dixmit.com/en/blog/our-blog-1/testing-in-odoo-knowledge-and-best-practices-49
- SKIPPED QA test design — search returned general shift-left/risk-based practices already covered by behavioral-coverage-matrix, qa-test-plan, and smoke-test-gating skills.

## 2026-06-02 (GMT+7)

Domains researched: Playwright/web E2E (component testing), Google Workspace automation (Apps Script), QA test design (AI-assisted).

- CREATED: skills/playwright-component-testing — Playwright experimental CT (`@playwright/experimental-ct-react/vue/svelte`): `mount` fixture, `router` fixture for network mocking, `beforeMount` provider setup, CI integration. Not covered by any existing skill. Source: https://playwright.dev/docs/test-components, https://www.browserstack.com/guide/component-testing-react-playwright
- CREATED: skills/gapps-script-batch-ops — Google Apps Script batch operations for Sheets: `getValues()`/`setValues()` batch pattern, `UrlFetchApp.fetchAll()` for parallel HTTP, `flush()` discipline, quota table, cursor-based chunking for 6-min limit, Cloud Logging. Distinct from existing `gsheet-safe-write` (Python API) — covers in-Sheets Apps Script context. Source: https://developers.google.com/apps-script/guides/sheets, https://folderpal.io/articles/google-apps-script-quotas-and-workarounds-2026-breaking-limits-on-drive-automation
- SKIPPED QA test design — existing `behavioral-coverage-matrix`, `qa-generator`, `qa-test-generation` skills cover the space; AI-assisted equivalence partitioning search returned no actionable new technique.
- SKIPPED Maestro — already very comprehensive; no new content found.
- SKIPPED LLM testing — covered yesterday by `llm-production-observability`.

## 2026-06-01 (GMT+7)

Domains researched: Playwright/web E2E, Maestro/mobile, AI chatbot/LLM testing.

- CREATED: skills/playwright-deprecated-selectors — Documents the breaking removal of `_react`, `_vue`, and `:light` selector engines in recent Playwright versions, with migration patterns to role/testId/text locators. Source: https://playwright.dev/docs/release-notes, https://www.browserstack.com/guide/playwright-selectors-best-practices
- CREATED: skills/llm-production-observability — Three-pillar LLM quality strategy for production: offline golden-dataset evals as CI release gates, runtime input/output guardrails, and production tracing with embedding-distribution drift alerts. Extends existing chatbot-tester pipeline into post-deploy monitoring. Source: https://www.vervali.com/blog/ai-and-llm-application-testing-in-2026-the-definitive-guide/, https://medium.com/@falvarezpinto/evaluation-first-ai-product-engineering-golden-sets-drift-monitoring-and-release-gates-for-llm-2c3bfb3f1e7b, https://atalupadhyay.wordpress.com/2026/03/28/llm-observability-in-production-tracing-evals-cost-tracking-and-drift-detection/
- SKIPPED Maestro update — existing `maestro-mobile` skill already covers conditional platform logic (`condition: platform: iOS`), parallel execution, and Maestro Cloud. No new actionable content found.
