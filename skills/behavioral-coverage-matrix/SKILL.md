---
name: behavioral-coverage-matrix
description: Framework tạo test cases bao phủ TẤT CẢ scenarios có thể xảy ra — dùng trước khi viết bất kỳ test nào
triggers:
  - viết test cases cho admin panel / CMS
  - coverage > 90%
  - "bao phủ toàn bộ trường hợp"
  - test design cho CRUD feature
  - test matrix
  - đảm bảo không bỏ sót scenario
  - behavior inventory
  - coverage baseline
  - coverage gap
  - what behaviors to test
  - test coverage map
scope: Mọi tác vụ tạo test cases từ đầu cho bất kỳ feature UI nào
---

# Behavioral Coverage Matrix — Framework

## Nguyên tắc cốt lõi

> Coverage = **% behaviors trong behavior inventory được verify**, không phải % test cases pass.

Không có behavior inventory → không thể đo coverage → không thể đạt target có hệ thống.

---

## Bước 0 — Định nghĩa "coverage" với user

**PHẢI HỎI TRƯỚC KHI LÀM:**
```
"Coverage > 90% ở đây nghĩa là:
 A) % test cases PASS?
 B) % behaviors/scenarios được test?
 C) % UI elements có test?
 
 Nếu là B — tôi cần list tất cả behaviors trước, bạn confirm xong mới viết test."
```

---

## Bước 1 — Scan UI thực tế (KHÔNG dùng assumptions)

**Với mỗi section/feature, mở browser và liệt kê:**

```
□ Trang list có gì?
  - Columns: [tên từng cột]
  - Actions toolbar: [Sort? Filter? Per-page? Search? Bulk select?]
  - Row actions: [View? Edit? Delete?]
  - Empty state: có message không?
  - Pagination: có không? Dạng gì?

□ Form Create/Edit có gì?
  - Fields: [tên, type, required?]
  - Validation rules: [required, format, maxlength?]
  - Save behavior: [redirect đến đâu? Message gì?]
  - Cancel behavior: [redirect đến đâu?]

□ Auth behavior?
  - Role nào được phép: [admin, editor, viewer]
  - Role nào bị 403/redirect?

□ Special behaviors?
  - Versioning? (Draft/Published)
  - Soft delete hay hard delete?
  - Bulk operations?
```

---

## Bước 2 — Build Behavior Inventory theo State Transition

Dựa trên [State Transition Testing](https://testsigma.com/blog/state-transition-testing/) — mỗi feature có các **states** và **transitions** giữa chúng:

### Template cho Admin CMS collection

```
FEATURE: [Tên collection]
STATES: Empty | Has-Data | Creating | Editing | Deleting | Filtered | Searched | Sorted | Paginated

BEHAVIORS TO TEST:
```

### A. List Page Behaviors (trang danh sách)

| ID | Behavior | Input | Expected State |
|----|----------|-------|----------------|
| L-01 | Page loads | navigate to URL | Shows table with correct columns |
| L-02 | Sort ASC | click column header ↑ | First row changes (ASC order) |
| L-03 | Sort DESC | click same header ↓ | First row changes (DESC, ≠ ASC) |
| L-04 | Per-page = 10 | select "10" | count ≤ 10 rows |
| L-05 | Per-page = 25 | select "25" | count ≤ 25 rows |
| L-06 | Search match | type valid keyword | Shows matching rows only |
| L-07 | Search no match | type "XYZNONEXISTENT" | Shows 0 rows / empty state |
| L-08 | Clear search | clear search box | Full list restored |
| L-09 | Filter panel opens | click Filters | Panel/dialog appears |
| L-10 | Filter by field | apply filter | Only matching rows shown |
| L-11 | Clear filter | clear filter | Full list restored |
| L-12 | Pagination page 2 | click "2" | Different rows from page 1 |
| L-13 | Bulk select all | click header checkbox | All rows checked, Delete button appears |
| L-14 | Bulk deselect | uncheck header | All rows unchecked |
| L-15 | Bulk delete | select + delete | Selected rows removed |
| L-16 | Empty collection | no data exists | Empty state message shown |

### B. Create Flow Behaviors

| ID | Behavior | Input | Expected |
|----|----------|-------|----------|
| C-01 | Form accessible | click "Create" button | Form page loads |
| C-02 | Required fields empty → save | submit empty | Validation errors shown |
| C-03 | Required fields empty → individual | leave 1 required field empty | That field shows error |
| C-04 | Valid data → save | fill all required, submit | Redirect to detail/list + success |
| C-05 | Slug auto-generates | type in Title | Slug field updates automatically |
| C-06 | Cancel → no data saved | click Cancel | Back to list, no new record |
| C-07 | Duplicate unique field | same slug/email | Error: "already exists" |
| C-08 | Special chars in fields | `<script>`, `"`, `'` | Saved safely, no XSS |
| C-09 | Max-length fields | exceed maxlength | Truncated or error shown |
| C-10 | New record appears in list | create successfully | Record visible in list page |

### C. Edit/Detail Behaviors

| ID | Behavior | Input | Expected |
|----|----------|-------|----------|
| E-01 | Detail page loads | click record | All fields populated |
| E-02 | Edit and save | change field value, save | Change persists after reload |
| E-03 | Edit required → empty | clear required field, save | Validation error shown |
| E-04 | Cancel edit | change then cancel | Original value restored |
| E-05 | Versions tab (if versioned) | click Versions tab | Version history shown |
| E-06 | Publish draft (if versioned) | change status → Publish | Status updates to Published |

### D. Delete Behaviors

| ID | Behavior | Input | Expected |
|----|----------|-------|----------|
| D-01 | Delete confirmation | click Delete | Confirmation dialog/prompt appears |
| D-02 | Confirm delete | confirm | Record removed from list |
| D-03 | Cancel delete | cancel | Record still exists |

### E. Auth/Permission Behaviors

| ID | Behavior | Role | Expected |
|----|----------|------|----------|
| A-01 | Unauthenticated access | no session | Redirect to /login |
| A-02 | Admin can CRUD | admin role | Full access |
| A-03 | Restricted role → create | non-admin | 403 or button hidden |
| A-04 | Session persists | reload | Still logged in |
| A-05 | Logout | click logout | Redirect to /login |

### F. Global/Settings Behaviors (nếu có)

| ID | Behavior | Expected |
|----|----------|----------|
| G-01 | Settings page loads | All fields visible |
| G-02 | Edit and save | Change persists |
| G-03 | Required field validation | Error shown |

---

## Bước 3 — Equivalence Partitioning cho inputs

Mỗi input field phải có test cho TẤT CẢ partitions:

```
Partition rules (theo EP + BVA):
┌─────────────────────┬──────────────────────────────┐
│ Input type          │ Partitions cần test           │
├─────────────────────┼──────────────────────────────┤
│ Text field          │ Valid, Empty, Too-long, HTML  │
│ Number field        │ Valid, Zero, Negative, Max+1  │
│ Email field         │ Valid, Invalid format, Empty  │
│ Search box          │ Match, No-match, Empty, Spec  │
│ Sort column         │ ASC, DESC (verify order diff) │
│ Per-page selector   │ 10, 25, 50, boundary (max)   │
│ Checkbox            │ Checked, Unchecked            │
│ Dropdown            │ Each option + empty/default  │
└─────────────────────┴──────────────────────────────┘
```

---

## Bước 4 — Coverage Gap Report TRƯỚC khi viết code

```
BEHAVIOR INVENTORY: [tên feature]
Total behaviors identified: N

Covered by existing tests: M
  - List behaviors: x/16
  - Create behaviors: y/10
  - Edit behaviors: z/6
  - Delete behaviors: w/3
  - Auth behaviors: v/5

NOT COVERED (gaps):
  - L-07: Search no match
  - L-12: Pagination page 2
  - C-07: Duplicate unique field
  ...

Coverage = M/N × 100 = X%
To reach 90%: need [N×0.9 - M] more test cases
```

---

## Bước 5 — Assertion rules (tránh happy path bias)

Mỗi test PHẢI verify **state change**, không chỉ **action executed**:

```typescript
// ❌ Happy path bias — không verify gì cả
await page.click('button[sort]');
// test passes ngay cả khi sort không hoạt động

// ✅ State change verification
const before = await firstRowText();
await page.click('button[sort-asc]');
const afterAsc = await firstRowText();
await page.click('button[sort-desc]');
const afterDesc = await firstRowText();
expect(afterAsc).not.toBe(afterDesc); // actual behavior verified

// ❌ Visibility only
await expect(searchBox).toBeVisible();

// ✅ Behavior verification  
await searchBox.fill('XYZNONEXISTENT');
const count = await rows.count();
expect(count).toBe(0); // actual empty state verified
```

---

## Checklist trước khi submit test suite

- [ ] Có behavior inventory không? (list đầy đủ behaviors)
- [ ] Mỗi behavior có ≥1 test không?
- [ ] Có test negative path không? (empty, no-match, invalid, 403)
- [ ] Có test boundary không? (per-page limit, max chars)
- [ ] Assertions verify STATE CHANGE, không chỉ visibility?
- [ ] Auth behaviors được test không?
- [ ] Coverage% = behaviors_covered / total_behaviors × 100 đã tính chưa?

---

## Quick Reference — CMS Collection Template

Mỗi collection cần TỐI THIỂU các test này để đạt ~85%+ coverage:

```
1.  List loads với đúng columns
2.  Create với data hợp lệ → redirect đến detail
3.  Create với required fields trống → validation error
4.  Edit và save → persist sau reload
5.  Delete với confirm → xóa khỏi list
6.  Sort ASC ≠ Sort DESC (verify row order thay đổi)
7.  Per-page 10 → count ≤ 10 rows
8.  Search no match → 0 rows
9.  Unauthenticated → redirect /login
10. Role restriction → 403 hoặc button ẩn (nếu có)
```

10 tests × N collections = baseline coverage inventory.

---

## Cross-Ref With Other Coverage Skills

| Skill | Role |
|---|---|
| **this — `behavioral-coverage-matrix`** | State-transition + behavior inventory, coverage formula |
| `qa-test-coverage-max` | 8-category matrix (POS/NEG/UI/EDGE/SEC/PERF/A11Y/Platform) — apply per behavior |
| `state-ripple-verify` | Each behavior in the inventory needs ripple assertions |
| `qa-test-generation` | Writes the actual test cases from the inventory |

Workflow: **inventory (this) → 8-category coverage (qa-test-coverage-max) → write tests (qa-test-generation)**

**Research sources:**
- [State Transition Testing — Testsigma](https://testsigma.com/blog/state-transition-testing/)
- [CRUD Testing Guide — AccelaTest](https://accelatest.com/crud-testing-guide/)
- [Admin Module Test Cases — SampleTestCases](https://sampletestcases.com/admin-module-test-cases/)
- [EP & BVA — SoftwareTestingHelp](https://www.softwaretestinghelp.com/what-is-boundary-value-analysis-and-equivalence-partitioning/)
