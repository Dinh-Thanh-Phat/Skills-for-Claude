# Daily Skill Evolution Log

Changelog written by the `daily-skill-evolution` remote routine (07:00 GMT+7 daily) on the `skill-evolution` branch.
Most recent at top.

<!-- Entries appended below by the routine -->

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
