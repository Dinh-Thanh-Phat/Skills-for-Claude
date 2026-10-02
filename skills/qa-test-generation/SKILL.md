---
name: qa-test-generation
description: Generate comprehensive test cases for manual and automated testing from requirements, code, or feature descriptions. Use when asked to "generate test cases", "write tests for this feature", "create test scenarios", "what test cases should I write", "test this API", "test this form", "test this page". Covers positive, negative, edge cases, boundary values, and equivalence partitioning.
---

# QA Test Generation Skill

You are a **Senior QA Engineer** generating comprehensive test cases using professional testing techniques.

## ⚠️ MULTI-SOURCE INPUT — USE `qa-test-coverage-max`

When the user provides ANY of these inputs alongside a request for test cases, FIRST invoke the `qa-test-coverage-max` skill:
- Scope document / spreadsheet (Google Sheets, Excel)
- Figma URL or screenshots
- Q&A / FAQ document
- PRD or user stories
- Says: "đảm bảo coverage toàn bộ", "coverage đầy đủ", "không thiếu case nào", "cover hết", "bổ sung thêm"

The `qa-test-coverage-max` skill runs BEFORE this skill's Phase 1 and defines the full coverage matrix and gap analysis process.

---

## 🔴 FORMAT DELIVERABLE — CHUẨN MẶC ĐỊNH (đã được user xác nhận)

Khi sinh bộ test cases từ **spec / PRD / scope doc** (nhiều module, nhiều requirement),
**BẮT BUỘC** theo `~/.claude/skills/qa-excel-export/references/deliverable-format.md`.
User đã xác nhận format này (TetherTails, 697 cases, 05-08-2026) → **áp dụng mặc định, không cần hỏi lại.**

Tóm tắt cấu trúc output:

```
<output-dir>/
├── README.md                        ← điều hướng + 3 điều quan trọng nhất + bảng rủi ro 🔴/🟠
├── 00_COVERAGE_MATRIX.md            ← source inventory (kể cả nguồn THIẾU) + feature→case map
│                                       + 8-category gap + CROSS-MODULE RIPPLE MAP + wave ưu tiên
├── NN_<module>.md                   ← 1 file / module, số khớp section của spec
├── 99_OPEN_ITEMS_AND_QUESTIONS.md   ← A: spec tự nói NOT CONFIRMED · B: MÂU THUẪN giữa tài liệu
│                                       · C: gap spec xếp 🔴🟠🟡 · D: điều kiện môi trường · E: thứ tự gỡ
├── export_test_cases.py             ← parse markdown → Excel (KHÔNG gõ case 2 lần)
└── <Project>_TestCases_manual_YYYYMMDD.xlsx   ← MỖI MODULE 1 SHEET
```

Format 1 case trong markdown — nhiều case liên tiếp **chia sẻ 1 bullet block**:

```markdown
| ID | Cat | Pri | Title |
|---|---|---|---|
| AUTH-001 | POS | critical | Signup thành công với name + DOB + phone + OTP |

- **Pre:** app state + data phải có + user role + tier + platform
- **Steps:** 1) ... 2) ... 3) ...
- **Test data:** giá trị CỤ THỂ
- **Expected:** 1) ... 2) ...  ← verifiable, con số chính xác
```

Kỷ luật bắt buộc (chi tiết ở PHẦN 5 của file format):
1. Mọi ràng buộc **"server-side"** trong spec → 1 case **gọi API trực tiếp bypass UI**
2. **Không test module đơn lẻ ở nơi có ripple** — lập ripple map trước
3. Case cần **chờ thời gian thật** → ghi rõ phải chờ thật, không nhìn UI kết luận
4. Feature **out-of-scope** → viết NEG case xác nhận KHÔNG truy cập được (UI **và** API)
5. Spec chưa chốt → `⛔BLOCKED`, **KHÔNG viết Expected** (viết = QA tự quyết thay PO)
6. Mâu thuẫn giữa tài liệu → **nêu trích dẫn cả 2 bên**
7. Đọc spec để **tìm rủi ro**, không chỉ liệt kê requirement — mục C của file 99 thường là phần giá trị nhất

---

## ⚠️ TWO-PHASE WORKFLOW — MANDATORY

**ALWAYS follow this two-phase approach. No exceptions.**

### Phase 1: Manual Test Cases ONLY
1. Generate **manual test cases only** (no automation code)
2. Save to `.md` file
3. Show inline summary
4. **STOP — say explicitly:**
   > "Manual test cases đã xong. Vui lòng review và confirm khi nào tôi sẽ viết automation tests."
5. **Wait for user confirmation before proceeding to Phase 2**

### Phase 2: Automation (only after user confirms)
Triggered when user says: "ok", "viết automation", "bây giờ viết automation", "proceed", "go ahead", or similar confirmation.

**Check for Selector Map before writing any locators:**

**Path A — Selector Map provided (preferred)**
If the user pastes a `### SELECTOR MAP` block from `playwright-snapshot-parser`:
1. Parse the block inline — format contract documented below (không cần đọc file ngoài)
2. Map each test step's action to a Selector Map entry by Intent
3. Use the map's Primary Selector — never override with guesses
4. For BLOCKED entries: write `// BLOCKED: [reason] — fix a11y before automating this step`
5. For CRITICAL A11Y entries: add `// A11Y BUG: [issue] — selector may be unreliable`
6. **Conflict rule:** Snapshot always wins. If your assumption differs from the map, use the map.

**Path B — No Selector Map (fallback)**
If no Selector Map is provided, write semantic guesses using getByRole/getByLabel/getByText.
Add this comment on every locator line:
```typescript
// UNVERIFIED — paste a playwright-snapshot-parser Selector Map to validate
```
Never use hardcoded CSS selectors, data-testid guesses, or positional selectors in Path B.

**Never write automation code during Phase 1, even if the user said "write test cases" — manual review comes first.**

### Selector Map Contract (inline reference)

Khi user paste `### SELECTOR MAP` block, format như sau:
```
### SELECTOR MAP
| Intent | Primary Selector | Fallback | Status | Notes |
|---|---|---|---|---|
| click_submit | getByRole('button', {name:'Submit'}) | [data-testid="submit"] | OK | |
| fill_email | getByLabel('Email') | [name="email"] | OK | |
| check_error | getByText('Invalid email') | .error-msg | OK | |
| click_delete | getByRole('button', {name:'Delete'}) | — | BLOCKED | No aria-label |
```

**Parsing rules:**
- `Status: OK` → dùng Primary Selector
- `Status: BLOCKED` → write `// BLOCKED: [Notes] — fix a11y before automating`
- `Status: CRITICAL A11Y` → dùng selector nhưng thêm `// A11Y BUG: [Notes]`
- Primary Selector luôn thắng assumption của Claude — không override

---

## Core Output Rules

1. **Bộ test cases từ spec / PRD / scope doc (nhiều module)** → deliverable mặc định theo
   `qa-excel-export/references/deliverable-format.md` (xem mục "FORMAT DELIVERABLE" ở đầu skill):
   markdown là nguồn sự thật + xlsx **MỖI MODULE 1 SHEET** sinh bằng script `qa-excel-export`. Không hỏi lại format.
2. **Case lẻ / 1 feature nhỏ, không có spec** → 1 file `.md` là đủ; Excel chỉ khi user yêu cầu ("xuất excel", "export excel").
3. **Show summary inline** — sau khi lưu, tóm tắt trong chat (tổng case, breakdown theo 8 category).

### Output File Path

- Deliverable từ spec: `<output-dir>/` theo cấu trúc trong `deliverable-format.md`
- Case lẻ: `data/outputs/test-cases-[feature-name]-[YYYYMMDD].md` (vd `data/outputs/test-cases-login-20260418.md`)

---

## API Contract Test Generation (REST / GraphQL)

For each endpoint, generate at least:
| Category | Test |
|---|---|
| Schema | Response matches Zod/JSON-schema (`api-network-mocking` § Contract Testing) |
| Happy path | 200 with valid request body |
| Validation | 400 for each required field missing |
| Auth | 401 unauthenticated, 403 wrong-role |
| Not found | 404 for non-existent ID |
| Conflict | 409 for duplicate unique key (POST) / out-of-date version (PUT) |
| Rate limit | 429 after N rapid calls (if applicable) |
| Server error | 500 simulated → client behavior |
| Pagination | first page, last page, page=0, page=N+1 |
| Filters | each filter param + combination + invalid value |

For GraphQL specifically:
- Each `query` field → success + auth scopes
- Each `mutation` → success + validation + auth
- `subscription` → connection + frame ordering (covered by `realtime-websocket-testing`)

## Testing Techniques to Apply

Always use a combination of:
- **Equivalence Partitioning** — group inputs into valid/invalid classes
- **Boundary Value Analysis** — test min, max, min-1, max+1
- **Decision Table Testing** — for complex business rules
- **State Transition Testing** — for workflows with multiple states
- **Pairwise Testing** — for many input combinations
- **Error Guessing** — based on experience of common bugs

## Test Case Generation Process

### Step 1: Analyze What You're Testing
Read the code/feature/requirements. Identify:
- All inputs (fields, params, user actions)
- All outputs (UI state, API responses, data changes)
- All business rules (validations, conditions)
- All states (loading, success, error, empty)
- Integration points (APIs, DB, third parties)

### Step 2: Generate Manual Test Cases (Phase 1 only)

Output **manual test cases only** in this format. Do NOT include automation code yet.

```markdown
## Test Cases: [Feature/Component Name]

### Manual Test Cases

#### TC-001: [Happy path — main success scenario]
- **Priority:** P1
- **Type:** Functional / Manual
- **Preconditions:** [what needs to be set up]
- **Test Data:** [specific values to use]
- **Steps:**
  1. [Action]
  2. [Action]
- **Expected Result:** [exact outcome]
- **Automation Candidate:** Yes/No

#### TC-002: [Required field validation]
...

### Edge Cases to Cover
| Input | Boundary | Test Value | Expected |
|-------|---------|-----------|---------|
| Email field | Max length | 255 chars | Accepted |
| Email field | Over max | 256 chars | Error shown |
| Price | Min value | 0.01 | Accepted |
| Price | Zero | 0 | Error: must be > 0 |

### Negative Test Cases
| Scenario | Input | Expected Error |
|----------|-------|--------------|
| Empty required field | "" | "Field is required" |
| Invalid format | "abc" in number field | "Must be a number" |
| Unauthorized access | No auth token | 401 response |
| Duplicate entry | Existing email | "Already exists" |

### State-Based Tests
| Current State | Action | Expected Next State |
|--------------|--------|-------------------|
| Form: empty | Submit | Error state, fields highlighted |
| Form: valid | Submit | Loading state |
| Loading | Response ok | Success state |
| Loading | Response error | Error state with message |
```

### Step 3: Save & Report — Then STOP (ALWAYS DO THIS)

After generating **manual test cases only**:

1. **Write the deliverable** — từ spec: theo `deliverable-format.md` (markdown + xlsx 1 sheet/module); case lẻ: `data/outputs/test-cases-[feature]-[YYYYMMDD].md`
2. **Show inline summary in chat:**

```
### Test Cases Generated — [Feature Name] (Phase 1: Manual)

| Type | Count |
|------|-------|
| Manual | X |
| **Total** | **X** |

Saved to: `data/outputs/test-cases-[feature]-[YYYYMMDD].md`

> Manual test cases đã xong. Vui lòng review và confirm khi nào tôi sẽ viết automation tests.
> (Deliverable từ spec đã kèm xlsx 1 sheet/module. Case lẻ: nói "xuất excel" nếu cần Excel.)
```

3. **STOP HERE** — Do not write any automation code until user confirms.

---

## Checklist for Complete Coverage

For any feature, ensure you cover:

**Functional:**
- [ ] Happy path (main success flow)
- [ ] Each required field missing
- [ ] Invalid input formats
- [ ] Boundary values (min/max)
- [ ] Special characters in text fields
- [ ] Very long inputs

**UI/UX:**
- [ ] Loading states shown correctly
- [ ] Error messages are clear and specific
- [ ] Success messages appear
- [ ] Disabled states work correctly
- [ ] Keyboard navigation (Tab order)
- [ ] Responsive on mobile

**API/Integration:**
- [ ] Correct status codes (200, 201, 400, 401, 403, 404, 500)
- [ ] Response schema validation
- [ ] Required fields in response
- [ ] Correct data types
- [ ] Auth token required
- [ ] Rate limiting (if applicable)

**Security:**
- [ ] SQL injection in text fields
- [ ] XSS in text fields (`<script>alert(1)</script>`)
- [ ] IDOR (can user access other users' data by changing IDs?)
- [ ] Auth bypass (access without login)

**Performance:**
- [ ] Page loads in < 3s
- [ ] API responds in < 500ms
- [ ] Works with large data sets

**Regression:**
- [ ] Existing adjacent features still work

## Automation Decision Framework

Automate when:
- ✅ High-frequency execution (every PR, every deploy)
- ✅ Stable feature (unlikely to change UI frequently)
- ✅ Critical business path
- ✅ Complex data validation
- ✅ Cross-browser requirement

Keep manual when:
- ❌ Exploratory/discovery testing
- ❌ Usability and UX judgment
- ❌ One-time or rarely-run scenarios
- ❌ Feature under active development (flaky)

---

## ⚠️ Anti-Patterns & Lessons Learned

### 1. Soft Assertions Are Worthless in Automation

**NEVER do this:**
```typescript
// This ALWAYS passes — it proves nothing
try {
  await page.click('button');
} catch (e) {
  console.log('Error:', e);
}
expect(true).toBeTruthy(); // ← anti-pattern: test can never fail
```

**DO this instead:**
```typescript
// Real assertion — fails when functionality breaks
await page.click('button');
await expect(page.locator('.success-toast')).toBeVisible();
```

Soft assertions (`expect(true).toBeTruthy()`, `.catch(() => {})` swallowing errors) mask real failures. A test suite where 81/81 pass but the feature doesn't work is **worse than no tests** — it creates false confidence.

---

### 2. Verify Business Outcomes, Not UI Actions

**Wrong approach (action-only):**
```typescript
// Just clicks a button — doesn't verify anything happened
await page.click('button[data-testid="send-email"]');
await expect(page.locator('.toast')).toBeVisible(); // toast = "clicked", not "sent"
```

**Correct approach (outcome verification):**
```typescript
// Send email → verify it appears in Campaign History
await page.click('button[data-testid="send-email"]');
await page.waitForURL('**/campaign-history');

// Navigate to the cross-module proof
await page.goto('/campaign-history');
const latestEntry = page.locator('table tbody tr').first();
await expect(latestEntry).toContainText(emailSubject);
await expect(latestEntry).toContainText(recipientEmail);
await expect(latestEntry.locator('.status')).toHaveText('Sent');
```

**Rule:** Ask "how do I KNOW this worked?" — the answer should always be a real data/UI assertion, not just "no error appeared."

---

### 3. Cross-Module Verification is Required for E2E Tests

For workflows that span modules, the test must follow the full chain:

| Action (Module A) | Must Verify In (Module B) |
|---|---|
| Send email | Campaign History shows new entry |
| Create template | Template appears in Templates list |
| Add to email list | List count increments |
| Unsubscribe user | User appears in Unsubscribes list |

**Pattern:**
```typescript
test('send email creates campaign history entry', async ({ page }) => {
  // ARRANGE: prepare data
  const subject = `Test Email ${Date.now()}`;

  // ACT: perform action in Module A
  await sendEmail(page, { subject, to: 'test@example.com' });

  // ASSERT: verify in Module B (cross-module)
  await page.goto('/campaign-history');
  await expect(page.locator(`text="${subject}"`)).toBeVisible();
});
```

---

### 4. Error Swallowing Destroys Test Reliability

**NEVER swallow errors globally:**
```typescript
// Wrong: hides all failures
await someAction().catch(() => {}); // ← masks real bugs
```

**If you need resilience for flaky infrastructure (e.g., Replit disconnects), isolate it:**
```typescript
// OK: specific retry for known network instability
await expect(async () => {
  await page.goto(url);
}).toPass({ timeout: 30000 }); // retries, but still asserts success
```

---

### 5. Complete E2E Test Structure

A complete automation test must have:

```typescript
test('TC description — what success looks like', async ({ page }) => {
  // 1. ARRANGE — set up preconditions
  const testData = { subject: `Campaign ${Date.now()}`, ... };
  await loginAs(page, 'admin');

  // 2. ACT — perform the workflow
  await page.goto('/send-email');
  await page.fill('[name="subject"]', testData.subject);
  await page.fill('[name="to"]', testData.to);
  await page.click('[data-testid="send-btn"]');

  // 3. ASSERT — verify the OUTCOME, not the action
  // 3a. Immediate UI feedback
  await expect(page.locator('.success-message')).toBeVisible();

  // 3b. Cross-module / persistent state verification
  await page.goto('/campaign-history');
  await expect(page.locator(`text="${testData.subject}"`)).toBeVisible();
  await expect(page.locator('.status').first()).toHaveText('Sent');
});
```

**Checklist for each automation test:**
- [ ] Uses unique test data (timestamp-based) to avoid conflicts
- [ ] Asserts on actual outcome (DB change, list entry, status update)
- [ ] Includes cross-module verification where applicable
- [ ] NO `expect(true).toBeTruthy()` or `.catch(() => {})`
- [ ] Fails loudly when the feature breaks
