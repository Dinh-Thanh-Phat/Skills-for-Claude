# Daily Skill Evolution Log

Changelog written by the `daily-skill-evolution` remote routine (07:00 GMT+7 daily) on the `skill-evolution` branch.
Most recent at top.

<!-- Entries appended below by the routine -->

## 2026-06-21 (GMT+7)

Domains researched: Maestro/mobile (Maestro 2.0 web browser testing), Playwright/web E2E (1.61 already covered on 06-19; WebSocket patterns — skipped), AI chatbot/LLM testing (skipped — no new actionable content found).

- CREATED: skills/maestro-web-testing — Maestro 2.0 Beta web browser (desktop) testing: same YAML syntax as mobile flows with `url:` header instead of `appId:`, identical commands (`tapOn`, `inputText`, `assertVisible`, `clearState`), Maestro Studio web support, composing mobile+web flows with `runFlow`, decision table (Maestro web vs Playwright), and known beta limitations (Chromium-only, locale fixed en-US, no multi-tab, no WebSocket/HAR). Distinct from maestro-mobile (iOS/Android only), maestro-mcp-workflow (MCP integration), and all Playwright skills.  Sources: https://docs.maestro.dev/get-started/supported-platform/web-browser, https://maestro.dev/insights/automate-web-ui-tests-maestro, https://maestro.dev/blog/introducing-maestro-2-0-0, https://dev.to/leading-edje/maestro-a-single-framework-for-mobile-and-web-e2e-testing-b98
- SKIPPED Playwright 1.61 — already fully covered by skills/playwright-1.61-new-apis (created 2026-06-19).
- SKIPPED Playwright WebSocket testing — `playwright-network-interception` covers network patterns; 1.61 WebSocket HAR capture encoded in playwright-1.61-new-apis; no additional distinct skill warranted.
- SKIPPED AI chatbot/LLM testing — searches returned no new actionable technique not already in llm-judge-bias (06-19), llm-agent-trace-eval (06-15), deepeval-llm-cicd, rag-evaluation-ragas, or ai-agent-eval-platforms.

## 2026-06-20 (GMT+7)

Domains researched: Playwright/web E2E (MCP server for AI agents, Clock API for time control), QA test design (AI test generation trends — skipped, too general).

- CREATED: skills/playwright-mcp-server — Official Microsoft Playwright MCP server (`@playwright/mcp`): snapshot mode (accessibility tree, default) vs vision mode (`--caps=vision`, screenshots), ~40 tools (browser_navigate, browser_click, browser_snapshot, browser_network_requests, browser_storage_state_save, etc.), element ref system (`ref=e42`), Claude Desktop/VS Code/Cursor setup JSON, inline vs file snapshot-response-mode, session persistence. Distinct from playwright-agentic-apis (1.59 in-process APIs) and maestro-mcp-workflow (Maestro's MCP server). Sources: https://playwright.dev/docs/getting-started-mcp, https://github.com/microsoft/playwright-mcp, https://playwright.dev/mcp/vision-mode, https://testdino.com/blog/playwright-mcp, https://bug0.com/blog/playwright-mcp-servers-ai-testing
- CREATED: skills/playwright-clock-testing — Playwright Clock API for time-sensitive tests: `setFixedTime` (freeze Date.now() only, timers run naturally), `install + fastForward` (jump time without firing intermediate timers — for session expiry, auto-logout), `install + runFor` (advance time AND fire all intermediate setInterval/setTimeout — for countdown timers, polling), `pauseAt + resume` (freeze at exact instant). Includes decision table, time format reference, and the critical rule: install clock before page.goto(). No existing skill covered time control. Sources: https://playwright.dev/docs/clock, https://github.com/microsoft/playwright/blob/main/docs/src/clock.md, https://qaskills.sh/blog/playwright-clock-time-control-testing-guide
- SKIPPED QA test design (AI test generation / shift-left) — search returned high-level 2026 trend reports (72% AI adoption stats, "shift-everywhere" framing) without new actionable technique distinct from existing qa-generator, qa-test-generation, behavioral-coverage-matrix skills.

## 2026-06-19 (GMT+7)

Domains researched: Playwright/web E2E (1.61 new APIs), AI chatbot/LLM testing (LLM-as-a-Judge bias mitigation), QA test design (ephemeral preview environments — skipped, insufficient actionable depth).

- CREATED: skills/playwright-1.61-new-apis — Playwright 1.61 (June 2026) seven new capabilities: WebAuthn passkeys via `browserContext.credentials` virtual authenticator (register+seed without hardware, Chromium-only); Web Storage API (`page.localStorage`/`page.sessionStorage` with `setItem`/`getItem`/`items()`); three new video retention modes (`'on-all-retries'`, `'retain-on-first-failure'`, `'retain-on-failure-and-retries'`); `expect.soft.poll()` for combined polling+soft-assertions; `failOnFlakyTests` config to fail CI when tests only pass on retry; `apiResponse.securityDetails()`/`apiResponse.serverAddr()` for security assertions; HAR and trace now capture WebSocket frames. Not covered by playwright-1.60-new-apis (locator.drop, tracing.startHar, test.abort, ARIA boxes) or playwright-agentic-apis (1.59 APIs). Sources: https://github.com/microsoft/playwright/releases/tag/v1.61.0, https://www.corbado.com/blog/passkeys-e2e-playwright-testing-webauthn-virtual-authenticator, https://changjoon-baek.medium.com/overcoming-passkey-verification-in-test-automation-fc7fc6748bd6
- CREATED: skills/llm-judge-bias — LLM-as-a-Judge bias mitigation for AI eval pipelines: the 5 bias types with measured impact (verbosity/length +15–30 pts, self-preference/family +10–25%, position bias ~60% first-choice, format bias, calibration drift), cross-family judge selection table (never judge your own family's output), frontier vs small-judge cost tiers, four anti-bias techniques (rubric-based scoring with explicit anti-verbosity language, length normalization, pairwise position swap, human calibration with Pearson r ≥ 0.70 threshold), real-time guardrail implementation with Claude Haiku. Distinct from response-evaluator (implementation code for chatbot QA scoring) — this covers bias awareness, judge selection, and calibration methodology. Sources: https://futureagi.com/blog/llm-as-judge-best-practices-2026, https://futureagi.com/blog/evaluating-llm-judge-bias-mitigation-2026/, https://medium.com/@jiminlee-ai/understanding-llm-as-a-judge-benefits-biases-and-best-practices-4b4d5cc3cbcd, https://arxiv.org/pdf/2412.05579
- SKIPPED ephemeral/preview environments (QA domain) — search returned general platform-level content (Bunnyshell, Northflank per-PR environments + BASE_URL pattern); not enough Playwright-specific actionable detail to meet quality bar without duplicating test-isolation and existing CI guidance.

## 2026-06-16 (GMT+7)

Domains researched: Maestro/mobile (AI assertion commands), QA test design / Playwright (AI self-healing test automation).

- CREATED: skills/maestro-ai-assertions — Maestro's three LLM-powered assertion commands: `assertWithAI` (natural-language visual validation — good for OTP/CAPTCHA/dynamic content), `extractTextWithAI` (extracts on-screen text to `${aiOutput}` variable for use in subsequent steps), `assertNoDefectsWithAI` (visual smoke test detecting clipped text / overlapping elements, outputs HTML+JSON report). Distinct from maestro-mcp-workflow (which lists them in a table but does not document syntax or decision guide) and from maestro-mobile (standard YAML flows). Sources: https://docs.maestro.dev/reference/commands-available/assertwithai, https://docs.maestro.dev/reference/commands-available/extracttextwithai, https://docs.maestro.dev/api-reference/commands/assertnodefectswithai, https://deepwiki.com/mobile-dev-inc/Maestro/6.5-ai-features-and-mcp-server
- CREATED: skills/self-healing-test-automation — AI self-healing for E2E/Playwright suites: the 6 failure categories with ~% breakdown (selector ~28%, timing ~30%, runtime ~15%, test data ~12%, visual ~10%, interaction ~5%), rule-based locator fallback chain (Tier 1, covers 40–70% of selector failures) vs LLM intent-resolution (Tier 2, reaches 75–90%+), Detection→Diagnosis→Remediation pipeline, Playwright healing fixture pattern using Anthropic SDK, and guard rails (always review healed locators; never self-heal timing failures). Distinct from flaky-test-prevention (prevention + root cause diagnosis) and playwright-flaky-test-detection (diagnosis workflow); this covers automated AI repair mechanisms. Sources: https://www.qawolf.com/blog/self-healing-test-automation-types, https://getautonoma.com/blog/ai-self-healing-test-automation, https://software-testing-tutorials-automation.com/2026/02/implement-playwright-self-healing-locators-enterprise-framework.html, https://wopee.io/blog/self-healing-in-sw-test-automation/
- SKIPPED Maestro general best practices — general YAML patterns (launchApp, tapOn, runFlow composition) already thoroughly covered by maestro-mobile; no new June 2026 commands found beyond the AI assertion layer.

## 2026-06-15 (GMT+7)

Domains researched: AI chatbot/LLM testing (agent trace/span evaluation, multi-turn metrics), Maestro/mobile (iOS regression CI strategy — skipped, already covered by maestro-mobile skill).

- CREATED: skills/llm-agent-trace-eval — DeepEval `@observe` decorator for component-level agent evaluation: trace (end-to-end) vs span (per tool-call / retriever / LLM completion) architecture, ArgumentCorrectnessMetric and ContextualRelevancyMetric on individual spans, `deepeval.collect_traces()` context manager, pytest CI integration for per-tool assertions. Distinct from deepeval-llm-cicd (which covers end-to-end LLMTestCase with `tools_called` but not the trace/span instrumentation layer). Sources: https://www.confident-ai.com/blog/llm-agent-evaluation-complete-guide, https://deepeval.com/docs/evaluation-component-level-llm-evals, https://deepeval.com/docs/evaluation-llm-tracing, https://deepeval.com/guides/guides-ai-agent-evaluation-metrics
- SKIPPED multi-turn chatbot metrics — deepeval-llm-cicd already covers ConversationalTestCase, KnowledgeRetentionMetric, RoleAdherenceMetric, ConversationCompletenessMetric; would be a duplicate.
- SKIPPED Maestro/mobile — maestro.dev iOS regression blog covers smoke-on-PR / full-regression-nightly patterns already implied in maestro-mobile; no new YAML commands or APIs found.

## 2026-06-14 (GMT+7)

Domains researched: Playwright/web E2E (API testing via request fixture), QA test design (property-based testing — skipped duplicate, Testcontainers — skipped as backend infra), AI chatbot/LLM testing (multi-turn DeepEval — skipped duplicate in deepeval-llm-cicd), Maestro/mobile (skipped — no new June 2026 content beyond existing skills).

- CREATED: skills/playwright-api-testing — Playwright `request` fixture and `APIRequestContext` for testing REST and GraphQL APIs directly (no browser), with CRUD `test.step` patterns, Bearer token auth, browser↔API shared storage state, hybrid API-setup+UI-validation pattern, and GraphQL request structure. No existing skill covers Playwright's built-in API testing mode (api-network-mocking covers intercepting browser calls; this covers hitting endpoints directly). Sources: https://playwright.dev/docs/api-testing, https://getautonoma.com/blog/playwright-api-testing-guide, https://testdino.com/blog/playwright-api-testing, https://www.browserstack.com/guide/playwright-api-test, https://qaskills.sh/blog/playwright-apirequestcontext-storagestate-guide
- SKIPPED property-based testing — skills/property-based-testing-api (created 2026-06-06) covers fast-check and Hypothesis with API invariant patterns; would be a duplicate.
- SKIPPED LLM multi-turn evaluation — skills/deepeval-llm-cicd (updated 2026-06-10) already covers ConversationalTestCase, KnowledgeRetentionMetric, RoleAdherenceMetric, ConversationCompletenessMetric, ConversationalSynthesizer; would be a duplicate.
- SKIPPED Maestro/mobile — web search returned general best practices (reusable flows, Accessibility IDs, real device cloud) already covered by maestro-mobile, maestro-mcp-workflow, maestro-real-ios-device; no new June 2026 content.
- SKIPPED Testcontainers — backend Docker integration test infrastructure; does not fall within QA/testing domains 1–4 in the runbook scope.

## 2026-06-13 (GMT+7)

Domains researched: AI chatbot/LLM testing (streaming performance/load testing), QA test design (contract testing — skipped duplicate), Maestro/mobile (skipped — no new June 2026 content).

- CREATED: skills/llm-load-testing — LLM streaming load testing: TTFT/ITL/TPS metrics and SLOs (chat: TTFT<500ms, ITL<200ms; RAG: TTFT<50ms), tool comparison (Gatling native SSE, Locust Python, k6+xk6-sse), Locust SSE streaming implementation, Gatling simulation with p95 assertions, load test protocol (warm-up→ramp→sustained→soak), diagnostic table (TTFT vs ITL patterns), CI gate with Locust 2-min smoke run. Not covered by existing llm-production-observability (monitoring/tracing) or performance-analyzer (Playwright results). Sources: https://gatling.io/blog/load-testing-an-llm-api, https://latitude.so/blog/ultimate-guide-llm-load-testing, https://medium.com/@hiteshpara762/how-i-load-tested-a-conversational-ai-chatbot-agent-with-a-streaming-endpoint-c8e26e7a091b, https://blog.premai.io/load-testing-llms-tools-metrics-realistic-traffic-simulation-2026/
- SKIPPED QA test design (contract testing) — skills/pact-contract-testing already created 2026-06-11; would be a duplicate.
- SKIPPED Maestro/mobile — parallel sharding (06-09), GraalJS (06-07), iOS real device (06-06) already in existing skills; search returned no new June 2026 content.
- SKIPPED AI chatbot multi-turn eval — skills/deepeval-llm-cicd updated 2026-06-10 with ConversationCompletenessMetric / KnowledgeRetentionMetric; would be a duplicate.

## 2026-06-12 (GMT+7)

Domains researched: AI chatbot/LLM testing (agent eval platforms), Playwright/web E2E (visual regression SaaS tools), Maestro/mobile (skipped — no new June 2026 content beyond existing skills).

- CREATED: skills/ai-agent-eval-platforms — 2026 comparison of commercial/OSS platforms for evaluating multi-turn AI agents: Braintrust (experiment-first, sandboxed Python scorers, merge-blocking CI gate), Latitude (agent-native causal trace, multi-turn simulation testing, GEPA auto-generates regression tests from production failures), Langfuse (open-source self-hosted, annotation workflows). Distinct from deepeval-llm-cicd (metric library) and llm-production-observability (tracing/guardrails) — covers the SaaS platform layer for team experiment tracking and production session scoring. Sources: https://latitude.so/blog/best-ai-agent-evaluation-platforms-2026-comprehensive-comparison, https://latitude.so/blog/agent-first-comparison-guide-vs-braintrust, https://www.digitalapplied.com/blog/ai-agent-eval-frameworks-testing-guide-2026, https://laminar.sh/article/2026-04-23-top-6-agent-observability-platforms
- UPDATED: skills/visual-regression-testing — Added "Beyond Native Playwright: Visual Testing SaaS Tools (2026)" section: decision guide (Chromatic for Storybook, Percy for CI/BrowserStack, Applitools for enterprise/Figma), Applitools 2026 differentiator (Figma plugin in Eyes 10.22 Jan 2026), Percy DOM-snapshot mechanism, and Percy+Playwright integration code example. Existing skill covered native Playwright only; no SaaS comparison existed. Sources: https://bug0.com/knowledge-base/visual-regression-testing-tools, https://www.pkgpulse.com/guides/chromatic-vs-percy-vs-applitools-visual-regression-2026, https://delta-qa.com/en/blog/applitools-vs-percy-comparison-2026/
- SKIPPED Maestro/mobile — search returned no new June 2026 features beyond GraalJS (06-07), parallel sharding (06-09), and real iOS device (06-06) already in existing skills.

## 2026-06-11 (GMT+7)

Domains researched: Playwright/web E2E (1.60 new APIs), QA test design (contract testing with Pact), Maestro/mobile (skipped — no new content found beyond existing skills).

- CREATED: skills/playwright-1.60-new-apis — Playwright 1.60 (May 2026) six new APIs: `locator.drop()` for synthetic file/data drag-and-drop on upload zones, `tracing.startHar()`/`tracing.stopHar()` for HAR recording as first-class tracing API, `test.abort()` for runtime test guardrails from fixtures/hooks, ARIA bounding boxes via `ariaSnapshot({ boxes: true })`, `errorContext` for ARIA-snapshot-enriched assertion failure diagnostics, and JSON pretty-print in Trace Viewer. Not covered by `playwright-agentic-apis` (1.59-specific). Sources: https://www.testdino.com/blog/playwright-1-60-release, https://github.com/microsoft/playwright/releases/tag/v1.60.0, https://playwright.dev/docs/release-notes
- CREATED: skills/pact-contract-testing — Consumer-driven contract testing with Pact for microservices API compatibility: consumer writes tests to generate JSON contracts, provider verifies against real API, Pact Broker/PactFlow stores and versions contracts, `can-i-deploy` blocks unsafe deployments in CI/CD, `record-deployment` tracks production state. No existing skill covers contract testing. Sources: https://docs.pact.io/, https://www.sqaexperts.com/consumerdriven-contract-testing-with-pact-microservices-qa-guide-for-2026, https://totalshiftleft.ai/blog/contract-testing-for-microservices, https://qaskills.sh/blog/pact-contract-testing-complete-guide-2026
- SKIPPED Maestro/mobile — web search returned general best practices already covered by `maestro-mobile` (runFlow composition, env.yaml, real device testing, AI commands). No new June 2026 content found.

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
