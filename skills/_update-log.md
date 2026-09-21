# Skills Update Log

Lịch sử thay đổi các skills — được ghi tự động bởi skill-updater.

---

## 2026-04-28 — Chatbot Pipeline Lesson Learned

**Skills updated:** `qa-generator`, `chatbot-tester`

### Lessons từ session incard_50:

| Vấn đề | Root Cause | Fix được đưa vào skill |
|---|---|---|
| JSON truncation (0 câu) | Hỏi 20-50 câu/call vượt max_tokens | Batch ≤ 5 câu/call + `response_format={"type":"json_object"}` |
| Prompt leak vào output | Small model echo prompt tiếng Việt | Prompt bằng tiếng Anh; hướng dẫn "output ONLY" |
| Citation format lộn xộn (`Dieu/Khoan`) | llama-8b không nhất quán dấu | Post-process `normalize_citations()` bắt buộc |
| Citation ở giữa câu, không ở cuối | Detection chỉ check `Điều` anywhere | Validate end-citation `- source_doc` regex |
| 48/50 docs "not found" khi enrich | docs_content.txt của slug mới chỉ có 5 docs | Merge với incard_prod/docs_content.txt; document scope rule |
| Groq rate limit giữa chừng mất progress | Không có resume | Script phải idempotent + resume-capable |
| Step3 báo "50/50 success" nhưng 0% | Chatbot hết OpenRouter credits | Pre-flight check: test 1 câu trước khi chạy full batch |
| drive_map thiếu 48/50 links trong Excel | Config của slug mới khác source slug | Merge drive_map từ incard_prod config trong step4 |

### Web Research Sources:
- [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs) — `response_format` + `strict: true`
- [Exponential Backoff for LLM](https://hackernoon.com/openais-rate-limit-a-guide-to-exponential-backoff-for-llm-evaluation) — tenacity + jitter
- [LLM Prompt Injection Prevention - OWASP](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)

---

## 2026-05-24 — Test Data Accumulation Root Cause Fix

**Feedback:** Projects (HVS, Incard CMS, Inapps, etc.) accumulate test data across CI runs because inline end-of-test-body cleanup is skipped when tests fail mid-way.

**Root cause identified via web search:** Cleanup at end of test body is NOT guaranteed. Only `test.afterEach()` and `test.afterAll()` run regardless of test outcome in Playwright.

**Skills fixed:**

| Skill | Chỗ sửa | Thay đổi |
|---|---|---|
| `test-data-lifecycle` | Strategy A | Removed misleading "always runs even if test fails" comment; promoted `test.afterEach()` as ONLY correct pattern; marked inline cleanup as ❌ ANTI-PATTERN; added Strategy D (globalSetup pre-run prefix sweep) |
| `test-data-lifecycle` | Decision Matrix | "delete after adding" → "delete in test.afterEach()" |
| `qa-e2e-complete` | Main test template | Wrapped in `test.describe()` with `test.afterEach()` cleanup block + rule callout |
| `playwright-test-workflow` | Step 4 | Added Step 4b: mandatory afterEach cleanup for data-creating tests |
| `playwright-test-workflow` | Output Checklist | Added: every data-creating test must have afterEach hook |
| `playwright-test-workflow` | Scenario A table | Added step 6a: add afterEach cleanup |

---

## 2026-04-28 (session 2) — Answer Quality Fix Lessons

**Skills updated:** `qa-generator`
**Scripts updated:** `pipeline/fix_citations.py`, `pipeline/fix_all_answers.py`

### Lessons từ incard_50 answer quality scan (31/50 vấn đề):

| Loại lỗi | Root Cause | Fix được đưa vào skill |
|---|---|---|
| OCR errors ("6 phần", "nhém", "găn với") | Small model (8b) hallucinate OCR-like characters | `pipeline/fix_all_answers.py` Phase 1: specific string replacement dict per question id |
| FORMAT: `Điều X.Y`, `Khoản A` uppercase | Model dùng dot notation thay vì "Điều X, Khoản Y"; uppercase cho điểm | `normalize_citations()` mở rộng: `Điều (\d+)\.(\d+)` → `Điều \1, Khoản \2`; `Khoản [A-Z]` → `Điểm [a-z]` |
| REPEAT: model lặp lại câu hỏi đầu answer | LLM echo câu hỏi làm "đề bài" cho câu trả lời | Thêm `presence_penalty=0.3` + negative prompt instruction "Do NOT restate the question" |
| SHORT: "Có", "8%", "Bộ Tài chính" | Model không expand yes/no hoặc single-value | Thêm vào prompt: "MUST be ≥ 50 chars of actual content"; detect bằng `audit_batch()` |
| NEWLINE `\n` giữa answer trước citation | Model dùng line break trước citation dòng mới | `normalize_citations()` gọi `.replace('\n', ' ')` đầu tiên |
| Re-enrich trả về "Không đề cập đến" | 70b model không tìm thấy info trong doc → trả về refusal | Guard: check `REFUSE_SIGNALS` trước khi save answer mới; giữ old answer nếu refuse |
| Audit false positive với source_doc có "Dieu" | `'Dieu' in ans` match cả "DieuUocQuocTe" trong source_doc name | Audit scan cần exclude source_doc name khi check non-accented citations |

### New function added to qa-generator skill:
- `audit_batch()` — 6-signal quality gate chạy sau mỗi generation batch
- Threshold: >20% fail → regenerate toàn bộ batch

### Web Research Sources:
- [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs) — strict mode vs best-effort
- [Pydantic Validation for LLM](https://www.freecodecamp.org/news/how-to-keep-llm-outputs-predictable-using-pydantic-validation/) — type-safe answer schema
- [Preventing Citation Hallucination](https://www.inra.ai/blog/citation-accuracy) — multi-layer: schema + regex + semantic check
- [LLM Repetition via Presence Penalty](https://www.promptingguide.ai/introduction/settings) — presence_penalty giảm echo

<!-- Các thay đổi sẽ được append vào đây -->

---

## 2026-05-26 — Fix stale reference + project name recognition

**Skills updated:** `skill-updater`, `qa-session-start`

| Skill | Chỗ sửa | Thay đổi |
|---|---|---|
| `skill-updater` | Bảng Bước 1 (Detect Skill) | Dòng `returns-processor` đổi từ "*(chưa có — cần tạo)*" → `` `returns-processor` `` — skill đã tồn tại từ session trước |
| `qa-session-start` | Trigger conditions | Thêm trigger: "user mention tên project mà không kèm đủ context" |
| `qa-session-start` | Quy trình | Thêm Bước 0: Project name → lookup slug → đọc knowledge/[slug].md → present context → chờ user confirm mục tiêu |
| `odoo-project-automation` | description (frontmatter) | Thêm "DO NOT use khi user mention HVS trong context test/Playwright — đó là HVS Playwright project, dùng qa-session-start" |
| `qa-session-start` | Project Name Map | Thêm disambiguation block: HVS = Playwright project tại D:\HK8\Learning\DQ\HVS, KHÔNG phải Odoo HaiVan Ship |

## 2026-06-10 — Lessons from InCard Social Agents session

| Skill | Loại | Thay đổi |
|---|---|---|
| `expensive-irreversible-ops` | **NEW (P0)** | Trước khi auto bất kỳ op tốn credit / đăng thật / tạo data không xóa được: verify teardown TRƯỚC, retries=0, chạy 1 lần validated, KHÔNG retry-loop. Sinh ra từ lỗi đốt AI credit ~4 lần + tạo orphan agents không xóa được |
| `synthetic-click-limits` | **NEW** | Nhận diện control chỉ nhận trusted click (kebab ⋯ menu, overlay button): sau 2 lần fail → đổi sang keyboard/dispatchEvent/URL trực tiếp/manual, đừng grind. Phân biệt với selector bug (banner vs card, overlay sibling, hover-reveal) |
| `timeout-discipline` | update | Thêm: phải nâng `test.setTimeout()` cùng lúc với action/expect timeout — `test.slow()` (90s) giết test trước khi wait 240s xong |
| `playwright-diagnosis-first` | update | Thêm: N test fail cùng 1 dòng helper/POM → fix helper TRƯỚC, không debug từng test (vd continue() hỏng làm 7/7 wizard fail). Helper-bug smells: locator 0 elements rồi hang, `^anchor` getByText lệch do whitespace/icon/CSS uppercase |

## 2026-09-21 — Repo audit: misplaced + stale skills

**Feedback:** User asked to scan for skills needing update trong repo Duy (`D:\HK8\Learning\DQ\phat\phat`).

| Vấn đề | Fix |
|---|---|
| `.claude/skills/fe-component-builder/`, `.claude/skills/figma-to-code/` bị tạo nhầm trong repo Duy (Python/FastAPI agent, không phải FE project); `figma-to-code` hard-code "React + Tailwind" sai ngữ cảnh | Move cả 2 sang `~/.claude/skills/` (global) — nơi hợp lý hơn cho skill FE generic; xoá khỏi repo Duy |
| `skills/maestro-speed-optimization.md` (project-local flat file) bị lag phía sau bản global — thiếu cảnh báo phân biệt với `maestro-element-harvest`, thiếu phần "ĐO trước khi tin optimization" | Overwrite bằng nội dung `~/.claude/skills/maestro-speed-optimization/SKILL.md` |
| `skills/maestro-android-windows-gotchas.md`, `maestro-test-scaling.md`, `maestro-auth-state-strategy/` chỉ là flat knowledge file, không phải skill invoke-được, không có bản global tương ứng | Giữ nguyên (khớp memory reference_maestro-*) — không phải bug, đã xác nhận là chủ ý |

## 2026-09-21 (session 2) — Web scan for new/updated skills

**Research domains:** Playwright, Maestro mobile, LLM agent testing (theo focus domains của `daily-skill-evolution`).

| Domain | Finding | Quyết định |
|---|---|---|
| Playwright | Playwright 1.63 released 2026-09-04: test locks, cross-frame locators (no-selector `frameLocator()`), `Locator.visible()`, `test.step()` subtitle/params, selective trace snapshots + aria trace viewer mode, `ariaSnapshotJSON()`, `--add-reporter` | **CREATED** `playwright-1.63-new-apis` — theo đúng format của 1.60/1.61/1.62 |
| Maestro mobile | MCP server, MaestroGPT self-healing, Studio redesign (contextual autocomplete Apr 2026), Android 15/16, iOS 26 | **SKIP** — đã cover đủ bởi `maestro-mcp-workflow`, `maestro-studio`, `android-16-qa-gate`, `ios-26-test-gotchas` |
| LLM agent testing | Trace/span-level eval, tool-calling correctness, 5-10 run semantic-similarity distribution testing | **SKIP** — đã cover bởi `llm-agent-trace-eval`, `llm-agent-trajectory-eval`; ngưỡng "nhiều lượt đo" đã khớp `feedback_chatbot-measure-8-runs-not-3` |

## 2026-09-21 (session 3) — Outdated-skill audit (~150 skills scanned)

**Method:** general-purpose agent grep'd toàn bộ `~/.claude/skills` cho version pin / "as of" claim / tên model cụ thể, đọc kỹ các skill nghi ngờ.

**UPDATED (model-name pins đã lỗi thời, thay bằng "current frontier/cross-family" thay vì tên cứng):**

| Skill | Chỗ sửa | Thay đổi |
|---|---|---|
| `llm-judge-bias` | Bảng "Cross-Family Judge Selection" + "Frontier vs Small Judge" + bias table | Xoá hard-code "GPT-4o/GPT-4", "Gemini 1.5 Pro/Ultra", "Claude Haiku" cụ thể → thay bằng mô tả theo family ("model đời hiện tại của family khác"). Nguyên tắc cross-family vẫn giữ nguyên, chỉ tên model là lỗi thời |
| `deepeval-llm-cicd` | "Controlling the Judge Model" | "DeepEval defaults to GPT-4o" → "defaults to whichever OpenAI model current version ships — check deepeval docs/version thay vì assume tên cố định" |
| `qa-preflight` | Checklist API/Chatbot Pipeline | "Model version đúng không? (GPT-4 vs GPT-3.5)" → ví dụ generic "model đời mới/mắc hơn vs đời rẻ hơn" |
| `multimodal-chatbot-testing` | Layer 1 MLLM-as-a-Judge | "GPT-4V/GPT-4o" (GPT-4V đã deprecated/merge vào GPT-4o) → "current vision-capable model (OpenAI/Gemini/Claude)" |

**Checked, KHÔNG stale (để khỏi re-flag lần sau):** `playwright-1.60/61/62/63-new-apis` (mỗi bản scope đúng version của nó, không mâu thuẫn nhau), `playwright-cli-agent`/`playwright-mcp-server` (claim "1.62+ bundles CLI/MCP" vẫn đúng dưới 1.63), `playwright-deprecated-selectors` vs `safe-locators` (bổ trợ, không mâu thuẫn), `ios-26-test-gotchas`, `android-16-qa-gate`, `maestro-mobile`.

## 2026-09-21 (session 4) — Outdated-skill audit: generic dev catalog (D:\...\phat\phat\skills\, ~270 file)

**Kết luận:** catalog này được maintain khá tốt — Next.js 16/Turbopack, React 19, Expo SDK 54, Swift 6.2, Laravel version table đều đúng/hiện hành. Chỉ 1 lỗi thật:

| Skill | Vấn đề | Đã sửa |
|---|---|---|
| `expo-expo-api-routes.md:146` | Code example gọi OpenAI hard-code `model: "gpt-4"` (model đã deprecated) trong route mẫu duy nhất | Đổi thành `"gpt-4o"` + comment "illustrative — dùng model hiện hành, gpt-4 đã deprecated" |

**User quyết định (đã hỏi):** KHÔNG set lịch tự động quét outdated 2 tháng/lần — chỉ chạy khi user yêu cầu trực tiếp ("quét skill"). Ghi nhớ preference này, đừng tự đề xuất lại lịch định kỳ trừ khi user đổi ý.

## 2026-09-21 (session 5) — Domain còn lại: Test design & QA process

**Research:** test case design techniques 2026, QA metrics, test automation tool trends 2026.

| Finding | Quyết định |
|---|---|
| 5 kỹ thuật thiết kế test (equivalence/boundary/state-transition/pairwise/error-guessing) | **SKIP** — đã cover bởi `behavioral-coverage-matrix`, `pairwise-combinatorial-testing` |
| QA metrics (flake rate, defect escape rate, mean-time-to-detect, automation ROI) | **SKIP** — đã cover đủ bởi `qa-suite-health-metrics` (đúng 5 metric) |
| AI-assisted failure triage / self-healing tools | **SKIP** — đã cover bởi `test-failure-triage`, `self-healing-test-automation` |

**Kết luận full sweep hôm nay (4 domain: Playwright, Maestro, LLM/chatbot, QA process):** không còn skill mới nào đáng tạo thêm. Đã tạo `playwright-1.63-new-apis` + fix 5 skill outdated (4 QA catalog + 1 dev catalog) trong các session trước cùng ngày.

## 2026-09-21 (session 6) — Maestro đào sâu lại: 2 version bị bỏ sót (2.9.0, 2.10.0)

User hỏi lại riêng "Maestro có gì mới đặc biệt không" — lần trước chỉ check các tool-level feature (MCP, Studio, MaestroGPT) mà bỏ sót 2 bản CLI mới nhất chưa release lúc đó. Fetch trực tiếp `maestro.dev/blog/changelog` phát hiện:

| Version | Date | Finding |
|---|---|---|
| 2.10.0 | 9 Sep 2026 | `--device-os` nhận full path `system-images;<api>;<tag>;<abi>` thay vì chỉ bare API level; `--android-api-level`/`--ios-version`/`--os-version` deprecated |
| 2.9.0 | 31 Aug 2026 | 4 command mới: `setDarkMode`/`toggleDarkMode`/`assertDarkMode`/`assertLightMode` — switch+assert theme NGAY TRONG 1 flow (iOS/Android/Web) |

Grep xác nhận `maestro-mobile/SKILL.md` (skill chính, có version timeline table) hoàn toàn không có 2 version này lẫn từ khóa "dark"/"device-os full path". **UPDATED `maestro-mobile`**: thêm section Dark Mode Testing + section Android system image targeting + 2 dòng vào version timeline table + nguồn.

2.7.0/2.8.0 (AI-agent Cloud debug, swipe point-in-element) đã cover đầy đủ từ trước — không đổi gì thêm ở đó.

## 2026-09-21 (session 7) — Structural fix: lesson lặp lại vì rải rác, không phải vá từng project

**User complaint:** đã diagnose đúng nguyên nhân slow (per-flow login/clearState, ad-hoc element dump, full-section rerun) trên TetherTails + Soundwise — nhưng đây là **lặp lại** của lesson đã tự rút ra 84 ngày trước (`feedback_maestro-element-discovery-efficiency`). Fix skill đã tồn tại (`maestro-element-harvest`, `maestro-auth-state-strategy`, `feedback_test-rerun-discipline`) nhưng không được áp dụng lại vì chúng là skill vệ tinh, không ai bắt buộc đọc trước khi bắt đầu project mới. User yêu cầu: đừng vá từng project, làm fix áp dụng TỰ ĐỘNG trên mọi project.

**Fix structural:**
| File | Thay đổi |
|---|---|
| `maestro-mobile/SKILL.md` | Thêm section "🚦 MANDATORY gate" NGAY ĐẦU file (trước Quick Start) — bắt buộc 3 bước (harvest 1 lần / group theo auth-state / canary-only rerun) kèm bằng chứng cụ thể từ TetherTails+Soundwise, không skip được nếu >5 flow hoặc >1 account |
| `qa-preflight/SKILL.md` | Mirror checklist ngắn vào section Maestro Mobile — bắt case đi thẳng vào test execution mà bỏ qua `maestro-mobile` |

**Meta-lesson lưu vào memory (`feedback_bake-fix-into-entry-skill-not-scatter`):** khi 1 lesson chỉ nằm ở skill vệ tinh → sẽ bị bỏ qua lặp lại nhiều project. Phải bake enforcement vào ENTRY-POINT skill (skill có trigger khớp cách task thực sự được gọi), viết ở đầu file với bằng chứng cụ thể, không chỉ "xem thêm X".

## 2026-09-21 (session 8) — 3 issue thêm: root cause + fix mechanical (không phải thiếu skill)

**User complaint:** (1) luôn viết POS-only dù đã có memory+skill nhắc full case, (2) chạy "full" nhưng dừng giữa chừng, (3) đã có creds/đã chạy được trước đó nhưng retest lại hỏi/claim blocked. Yêu cầu: tìm root cause áp dụng được trên MỌI project, không vá từng cái.

**Root cause đã confirm bằng cách đọc lại memory cũ:**
- (1)+(2) **CÙNG 1 root cause** — `feedback_automation-must-cover-all-cases-not-happy-path` đã ghi nhận đây là pattern tái diễn 01-Jul VÀ 09-Sep, ĐÃ có hard-block ở `qa-router` + `qa-coverage-gate.py` hook (deterministic, không skip được) — nhưng hook chỉ CHÈN cảnh báo vào context, không verify output thật. Tôi vẫn có thể đọc cảnh báo rồi tự quyết "đủ để báo cáo có vẻ ổn" và dừng sớm — đây là lỗi ÁP DỤNG, prose-level checklist không có bằng chứng cơ học.
- (3) **Structural gap thật**: registry (`~/.claude/shared-context/registry.md`, 14 project) và knowledge system KHÔNG có TetherTails/TetherTails Portal/Soundwise — nên `qa-session-start` không lookup được, dù ACCOUNTS.md/ELEMENT_MAP*/matrix_run_*.log đã có sẵn trên đĩa.

**Fix mechanical (khác lần trước — không chỉ thêm text nhắc):**
| File | Thay đổi |
|---|---|
| `qa-router/SKILL.md` | Thêm hard-block MỚI: checklist 8-category phải là **bd issue riêng từng category** tạo TRƯỚC khi chạy case đầu — không chỉ để "trong đầu"/prose. `bd list --status=open` là bằng chứng cơ học không lờ được, khác cảnh báo hook (chỉ là text) |
| `registry.md` | Thêm 3 slug: `tethertails`, `tethertails-portal`, `soundwise` |
| `knowledge/tethertails.md`, `tethertails-portal.md`, `soundwise.md` | Tạo mới — trỏ thẳng ACCOUNTS.md/ELEMENT_MAP*/matrix_run_*.log/execution_results*.json đã có sẵn |
| `qa-session-start/SKILL.md` | Thêm 3 dòng vào Project Name → Slug map |
| `qa-preflight/SKILL.md` | Thêm "Rule P0 #2" — bắt buộc tra registry + grep ACCOUNTS/README/credentials/.env/ELEMENT_MAP TRƯỚC KHI hỏi user hoặc báo blocked |

**Lưu ý cho lần sau:** (1)+(2) chưa có fix triệt để — hook + hard-block đã là mức mạnh nhất khả thi hiện có mà vẫn tái diễn; bd-issue-per-category là nỗ lực tiếp theo, cần theo dõi có còn tái diễn không sau fix này.

## 2026-09-21 (session 9) — Đào transcript thô TetherTails + Soundwise (2 agent nền, ~1.7GB text)

User yêu cầu đọc lại conversation lúc làm TetherTails + Soundwise, tự đánh giá cần update gì. 2 agent grep transcript JSONL gốc (extract user-text only, loại boilerplate/compaction noise), cross-check với MEMORY.md để tránh báo lại pattern đã biết.

**TetherTails — 3 finding mới:**
| Finding | Fix |
|---|---|
| User hỏi 3 lần riêng biệt (24-Aug/27-Aug/03-Sep) "có lưu automation script để lần sau chạy không" — chưa từng được fix triệt để | Thêm mục #0 vào `maestro-mobile` MANDATORY gate: check flows đã lưu trên đĩa TRƯỚC khi viết flow mới (khác với #1 harvest-element — đây là persistence CROSS-SESSION, không phải trong 1 session) |
| "Đã nói rất nhiều lần" — staging không charge tiền, multi-account cần account thứ 2 không phải máy thứ 2, destructive/RPC được phép trên staging — 3 fact này KHÔNG có ở đâu trong memory | Thêm section "Staging environment facts" vào `knowledge/tethertails.md` |
| Voice note chỉ người tạo mới thấy — mention 1 lần, chưa verify lại | Ghi vào `knowledge/tethertails.md` mục "Unverified — needs reconfirm" |

**Soundwise — 5 finding mới:**
| Finding | Fix |
|---|---|
| Nav-away-back báo PASS persistence (profile bio) nhưng thực ra là bug — chỉ lộ ra khi force-stop+relaunch thật | **NEW** `lesson_android-persistence-needs-cold-relaunch` — áp dụng CHUNG mọi Android app, không riêng Soundwise |
| `uiautomator dump` trả stale content khi đang transition/đang phát audio (không chỉ miss popup) | Thêm "second trigger condition" vào `lesson_uiautomator_diff_misses_popup_windows` |
| Device khoá/dozing chặn adb input, không tự phát hiện được | Thêm vào `knowledge/soundwise.md` — dumpsys power/window check + mitigate bằng screen_off_timeout |
| User hỏi 2 lần "đã lưu automation scripts chưa" | Thêm "Deliverable convention" vào `knowledge/soundwise.md` — verify bằng `ls` trước khi báo done |
| Brand list thiếu Herr Professor/Arika/Relax Change | Thêm vào `project_soundwise-whitelabel-qa.md` (low priority, chỉ backfill fact) |

**Không tìm thấy pattern mới nào khác sau khi loại các finding đã biết** (happy-path-only, partial-run, per-flow relogin, ad-hoc dump, full-section rerun, prod-no-delete, two-pass-verify) — 2 agent confirm rõ ràng, không manufacture finding để lấp chỗ trống.
