# Daily Skill Evolution Log

Changelog written by the `daily-skill-evolution` remote routine (07:00 GMT+7 daily) on the `skill-evolution` branch.
Most recent at top.

<!-- Entries appended below by the routine -->

## 2026-06-10 (GMT+7)

Domains researched: QA test design (skipped — general BVA/decision-table content already covered), Maestro/mobile (skipped — flaky-test and self-healing content already covered by maestro-mobile), AI chatbot/LLM testing (DeepEval multi-turn evaluation).

- UPDATED: skills/deepeval-llm-cicd — Added "Multi-Turn (Conversational) Evaluation" section: `ConversationalTestCase` with `Turn` objects, `KnowledgeRetentionMetric` / `RoleAdherenceMetric` / `ConversationCompletenessMetric` for chatbot context-retention testing, and `ConversationalSynthesizer` for auto-generating user turns. Not previously covered — skill had only single-turn `LLMTestCase`. Sources: https://deepeval.com/docs/evaluation-multiturn-test-cases, https://deepeval.com/guides/guides-multi-turn-evaluation-metrics, https://www.confident-ai.com/blog/multi-turn-llm-evaluation-in-2026
- SKIPPED QA test design — boundary value analysis / decision table / AI-assisted test generation returned only general content already covered by behavioral-coverage-matrix, qa-generator, qa-test-generation.
- SKIPPED Maestro/mobile — flaky-test self-healing content from maestro.dev duplicates existing maestro-mobile skill (animations, retry layers, smart sync). Nothing new actionable found.

## 2026-06-09 (GMT+7)

Domains researched: Maestro/mobile (parallel sharding), AI chatbot/LLM testing (RAGAS RAG evaluation), QA test design (skipped — recent coverage sufficient).

- CREATED: skills/rag-evaluation-ragas — RAGAS 4-core metrics for RAG pipeline evaluation: context precision, context recall, faithfulness, answer relevancy; diagnostic decision table (which metric failing → which layer is broken); production confusion matrix (TP/FP/FN/TN for retrieval); chunking fix patterns for low context recall; CI gate thresholds; DeepEval integration for pytest runner. Distinct from deepeval-llm-cicd (covers DeepEval API wrappers only, not RAGAS framework or diagnostic interpretation). Sources: https://datavlab.ai/post/rag-evaluation-methods-metrics-2026-guide, https://www.invra.co/en/rag-evaluation-with-ragas-measuring-faithfulness-context-precision-and-recall-in-production/, https://blog.premai.io/rag-evaluation-metrics-frameworks-testing-2026/
- UPDATED: skills/maestro-mobile — Added "Parallel Testing & Sharding" section: `maestro test --shards N` to distribute flows across N devices; `${MAESTRO_SHARD_INDEX}` and `${MAESTRO_DEVICE_UDID}` built-in variables for artifact isolation; `clearState: true` + unique-per-device test data pattern to prevent concurrent account conflicts; Maestro Cloud CI guidance. Not previously covered (2026-06-07 update added GraalJS only). Sources: https://maestro.dev/insights/parallel-testing-android-ios, https://docs.maestro.dev/maestro-flows/flow-control-and-logic/specify-and-start-devices
- SKIPPED AI chatbot/LLM testing (DeepEval) — deepeval-llm-cicd already thoroughly covers DeepEval including RAG metrics, agent metrics, and judge model control (updated 2026-06-08). No new angle found.
- SKIPPED QA test design — property-based-testing-api (2026-06-06) and mutation-testing-stryker (2026-06-05) cover advanced techniques; general BDD/shift-left content already in behavioral-coverage-matrix and qa-test-plan.

## 2026-06-08 (GMT+7)

Domains researched: AI chatbot/LLM testing (DeepEval agent metrics, judge model cost control), Playwright/web E2E (composable fixtures vs POM, 2026 consensus), Maestro/mobile (accessibility testing — skipped).

- UPDATED: skills/deepeval-llm-cicd — Added "Agent Evaluation Metrics" section (TaskCompletionMetric, ToolCorrectnessMetric for agentic systems) and "Controlling the Judge Model" section (GPT-4o-mini for per-PR speed vs GPT-4o for release gates). Existing skill covered RAG and chatbot eval well but had no agent-specific metrics or model-swapping guidance. Sources: https://github.com/confident-ai/deepeval, https://labelyourdata.com/articles/llm-as-a-judge, https://calmops.com/testing/llm-evaluation-frameworks-deepeval-2026/
- UPDATED: skills/playwright-page-object-model — Added "Composable Fixtures as an Alternative (2026)" section with test.extend() TypeScript pattern, full fixture example with setup/teardown, and a clear fixtures-vs-POM decision guide. 2026 community consensus: fixtures preferred for new small-to-medium suites; POM retained for 200+ spec teams or Selenium migrations. Sources: https://playwright.dev/docs/test-fixtures, https://getautonoma.com/blog/playwright-best-practices-2026, https://dzone.com/articles/playwright-fixtures-vs-pom
- SKIPPED Maestro accessibility — search returned general mobile a11y advice (touch targets, WCAG contrast, TalkBack/VoiceOver) not specific to Maestro YAML commands. Existing maestro-mobile skill already covers label: and id: selectors (the same accessibility-layer primitives). No actionable Maestro-specific additions found.

## 2026-06-07 (GMT+7)

Domains researched: Maestro/mobile (GraalJS JS engine migration), Playwright/web E2E (blob reporter for shard merging), AI chatbot/LLM testing (DeepEval — checked for novelty).

- UPDATED: skills/maestro-mobile — Added GraalJS vs Rhino migration section: `jsEngine: graaljs` frontmatter opt-in, `MAESTRO_USE_GRAALJS=true` env var (local only), ES5 vs ECMAScript 2022 comparison table. Maestro 2.0+ defaults to GraalJS; Rhino is being deprecated. Sources: https://github.com/mobile-dev-inc/Maestro/issues/2049, https://github.com/mobile-dev-inc/maestro-docs/blob/main/advanced/javascript/graaljs-support.md
- UPDATED: skills/test-parallelization — Added blob reporter config (`reporter: process.env.CI ? 'blob' : 'html'`) required for shard report merging, full GitHub Actions shard+merge workflow (upload per shard, merge-multiple artifact download, merge-reports step), and 2026 optimal shard count table (4–6 shards × 2–4 workers = ~80% time reduction). Existing skill had the `merge-reports` CLI command but not the blob reporter config needed to enable it. Sources: https://playwright.dev/docs/test-sharding, https://qaskills.sh/blog/playwright-parallel-testing-best-practices-2026, https://bug0.com/blog/playwright-test-sharding-guide
- SKIPPED AI chatbot/LLM testing — DeepEval already covered thoroughly by skills/deepeval-llm-cicd (created 2026-06-06); no new angle found worth adding.

## 2026-06-06 (GMT+7)

Domains researched: Maestro/mobile (real iOS device testing), AI chatbot/LLM testing (DeepEval CI/CD evaluation), QA test design (property-based testing for APIs).

- CREATED: skills/maestro-real-ios-device — community tool `maestro-runner` (devicelab-dev) adds real physical iOS device support to Maestro via XCTest driver + auto port forwarding; 3.6× faster than maestro-ios-device, supports parallel multi-device runs; existing YAML flows unchanged. Not covered by maestro-mobile (simulators/Android only). Sources: https://github.com/devicelab-dev/maestro-runner, https://blog.devicelab.dev/went-in-to-support-maestro-for-physical-devices-came-out-with-even-more/
- CREATED: skills/deepeval-llm-cicd — DeepEval (Confident AI) pytest-native LLM quality CI/CD framework: assert_test() gates PRs on AnswerRelevancy / Faithfulness / Hallucination / ContextualRecall metrics; parallel eval (-n 4); GitHub Actions integration; RAG eval pipeline. Distinct from llm-red-teaming (security) and llm-production-observability (runtime monitoring). Sources: https://deepeval.com/docs/evaluation-unit-testing-in-ci-cd, https://deepeval.com/guides/guides-regression-testing-in-cicd
- CREATED: skills/property-based-testing-api — Property-based testing with fast-check (JS/TS) and Hypothesis (Python): auto-generates 100s of inputs from invariants (idempotency, schema compliance, referential integrity, ordering, error handling), shrinks failures to minimal case. API migration playbook included. 35–50% higher edge-case defect detection than example-only tests. No existing skill covered this technique. Sources: https://www.sachith.co.uk/property%E2%80%91based-testing-for-apis-migration-playbook-practical-guide-jun-4-2026/, https://fast-check.dev/

## 2026-06-05 (GMT+7)

Domains researched: Playwright/web E2E (1.59 new APIs), AI chatbot/LLM testing (red-teaming), QA test design (mutation testing).

- CREATED: skills/playwright-agentic-apis — Playwright 1.59 (April 2026) new agentic APIs: `locator.normalize()` to canonicalize brittle selectors to ARIA/testId form, `page.pickLocator()` for interactive element discovery, `page.screencast` for precise annotated video recording with chapter overlays and live frame streaming, `browserContext.setStorageState()` for mid-test auth switching. Not covered by any existing skill. Sources: https://github.com/microsoft/playwright/releases/tag/v1.59.0, https://testdino.com/blog/playwright-release-guide, https://bug0.com/blog/whats-new-playwright-1-59
- CREATED: skills/mutation-testing-stryker — StrykerJS mutation testing for JS/TS: validates tests actually catch bugs beyond code coverage, incremental CI mode (--incremental flag) for PR pipelines with nightly full runs, mutation score thresholds (break at 55%, target 80%), AI-assisted survivor killing workflow, supported runners (Vitest/Jest/Mocha). No existing mutation testing skill in repo. Sources: https://github.com/stryker-mutator/stryker-js, https://stryker-mutator.io/docs/stryker-js/incremental/, https://oneuptime.com/blog/post/2026-01-25-mutation-testing-with-stryker/view
- UPDATED: skills/llm-red-teaming — Added DeepTeam framework (50+ vulns, 20+ attack vectors, OWASP ASI 2026/NIST/MITRE aligned) alongside existing Garak/PyRIT/Promptfoo tools; added bias testing coverage matrix (gender/race/religion/socioeconomic probing) and structured toxicity/PII leakage sections not previously covered. Sources: https://github.com/confident-ai/deepteam, https://datavlab.ai/post/red-teaming-llms-practitioner-guide-2026

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
