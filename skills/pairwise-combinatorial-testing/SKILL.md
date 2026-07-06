---
name: pairwise-combinatorial-testing
description: Pairwise (all-pairs) combinatorial test design — generate a minimal test set that covers every 2-way interaction between input parameters instead of testing every combination. Use when a feature has 4+ independent input parameters/config flags/dropdowns and exhaustive combination testing would explode the suite size (e.g. browser × OS × role × plan × locale). Triggers on "pairwise testing", "all-pairs testing", "combinatorial test design", "too many test combinations", "config matrix explosion", "PICT", "allpairspy".
---

# Pairwise / Combinatorial Test Design

Most multi-parameter defects are triggered by the interaction of just **two** parameters at a time — empirically 60–95% of interaction bugs. Exhaustive testing of every combination grows multiplicatively (5 params × 5 values each = 3,125 combinations); pairwise testing guarantees every **pair** of values appears in at least one test case, typically cutting the suite by 90%+ while still catching almost all interaction defects.

Not a replacement for full coverage on critical paths — use it as a **coverage optimization strategy** for the combinatorial config space around a flow, then add explicit test cases for payment, auth, and destructive actions regardless of what pairwise selects.

## When to reach for this vs. `behavioral-coverage-matrix`

| Technique | Answers | Skill |
|---|---|---|
| Equivalence Partitioning / BVA | What values to test for **one** field | `behavioral-coverage-matrix` |
| State Transition | What sequences of **actions** to test | `behavioral-coverage-matrix` |
| **Pairwise / combinatorial** | What **combinations** of 3+ independent parameters to test | this skill |

Use pairwise once you've identified the independent parameters (from EP/BVA) and need to combine them efficiently — the two techniques compose, they don't compete.

## Step 1 — Model the parameters

List every independent parameter and its representative values (already partitioned via EP/BVA — 2-5 values per parameter, not every raw value):

```
Browser:      Chrome, Firefox, Safari, Edge
OS:           Windows, macOS, Linux
User role:    Admin, Editor, Viewer
Plan:         Free, Pro, Enterprise
Locale:       en-US, vi-VN, ja-JP
```

Exhaustive = 4×3×3×3×3 = 324 combinations. Pairwise typically needs ~15-25.

## Step 2 — Generate pairs with a tool (don't hand-craft)

Manual pairwise generation is error-prone past 3-4 parameters. Use a dedicated tool.

### PICT (Microsoft, cross-platform CLI, free)

```
# model.txt
Browser:   Chrome, Firefox, Safari, Edge
OS:        Windows, macOS, Linux
Role:      Admin, Editor, Viewer
Plan:      Free, Pro, Enterprise
Locale:    en-US, vi-VN, ja-JP
```

```bash
pict model.txt                  # order:2 (pairwise) by default
pict model.txt /o:3              # 3-way coverage instead of pairwise
pict model.txt /r:42             # deterministic random seed for reproducible output
pict model.txt /e:seedrows.txt   # force specific rows to always be included
```

Constraints — exclude combinations that can't occur in the real system:

```
IF [OS] = "Linux" THEN [Browser] <> "Safari";
IF [Plan] = "Free" THEN [Role] <> "Admin";
```

Sub-models for a subset of parameters that need higher-order coverage than the rest:

```
{ Browser, OS } @ 3
```

### allpairspy (Python, when you want pairs generated in-process)

```python
from allpairspy import AllPairs

parameters = [
    ["Chrome", "Firefox", "Safari", "Edge"],   # Browser
    ["Windows", "macOS", "Linux"],              # OS
    ["Admin", "Editor", "Viewer"],              # Role
    ["Free", "Pro", "Enterprise"],              # Plan
]

def is_valid(row):
    # row is a partial combination in parameter order; reject impossible states
    if len(row) >= 2 and row[1] == "Linux" and row[0] == "Safari":
        return False
    return True

for i, combo in enumerate(AllPairs(parameters, filter_func=is_valid)):
    print(f"{i:2d}: {combo}")
```

`filter_func` is checked incrementally as each parameter is added — encode the same "impossible in production" rules here that you'd put in PICT's `IF/THEN` constraints.

> ⚠️ **allpairspy + `filter_func` can silently drop *unrelated* pairs.** The greedy generator rejects
> partial rows that fail the filter and does **not** backfill, so a pair with nothing to do with your
> constraint can end up uncovered. Verified example: the model above with the Safari+Linux filter drops
> the `Chrome`+`Pro` pair — 2-way coverage is no longer guaranteed. **After generating with a filter,
> always assert full coverage (snippet below), or use PICT instead** — PICT applies `IF/THEN` constraints
> without losing all-pairs coverage. Unconstrained allpairspy *does* give full 2-way coverage.

```python
# Coverage guard — run this after any filtered generation; fail the build if a pair was dropped
from itertools import combinations

def assert_pairwise_coverage(rows, params, excluded=frozenset()):
    missing = []
    for a, b in combinations(range(len(params)), 2):
        for va in params[a]:
            for vb in params[b]:
                if (a, b, va, vb) in excluded:      # pairs you intentionally removed via constraints
                    continue
                if not any(r[a] == va and r[b] == vb for r in rows):
                    missing.append((va, vb))
    assert not missing, f"pairwise coverage broken, missing pairs: {missing}"
```

## Step 3 — Turn generated rows into test cases

Each output row of the tool = one test case. Feed rows straight into a parameterized Playwright test instead of writing them by hand:

```typescript
const pairwiseRows = [
  { browser: 'chromium', role: 'Admin', plan: 'Free' },
  { browser: 'firefox', role: 'Editor', plan: 'Pro' },
  { browser: 'webkit', role: 'Viewer', plan: 'Enterprise' },
  // ...rest of the PICT/allpairspy output
];

for (const row of pairwiseRows) {
  test(`checkout renders for ${row.browser}/${row.role}/${row.plan}`, async ({ page }) => {
    // seed role + plan via API, then assert the checkout flow for this combination
  });
}
```

## Step 4 — Layer critical-path cases back in

Pairwise selection can skip a specific combination that matters for business or security reasons (e.g. Enterprise+Admin+Safari might not be selected). After generating pairs, explicitly re-add:

- The exact combination(s) support tickets are filed against
- Payment / auth / destructive-action flows on their own dedicated matrix, not left to chance pairwise selection
- Any combination excluded by a constraint you're not 100% sure is correct — verify the constraint against the real system before trusting the reduced set

## Anti-patterns

```
❌ Hand-picking "representative" combinations by eye — misses non-obvious pairs, not reproducible.
❌ Treating pairwise output as exhaustive — it guarantees 2-way coverage only, not 3-way+ interaction bugs.
❌ Feeding un-partitioned raw values (every possible string) into the tool — partition with EP/BVA first,
   pairwise multiplies whatever parameter/value counts you give it.
❌ Skipping constraints — an unconstrained model generates "impossible in production" test cases
   (e.g. Free plan + Admin role, if that combination can't exist) and wastes CI time asserting on unreachable states.
❌ Trusting allpairspy's all-pairs guarantee when filter_func is set — the greedy filter can drop
   unrelated pairs. Assert coverage with the guard snippet after filtered runs, or switch to PICT.
```

## Sources
- [Pairwise Testing: Complete Guide to Combinatorial Test Case Design](https://mastersoftwaretesting.com/testing-fundamentals/types-of-testing/specialized-testing/pairwise-testing)
- [PICT model/constraint/sub-model documentation](https://raw.githubusercontent.com/microsoft/pict/main/doc/pict.md)
- [allpairspy README (parameters, OrderedDict, filter_func)](https://github.com/thombashi/allpairspy)
- [Understanding Pairwise and Combinatorial Testing](https://insightsbyricktechblog.wordpress.com/2025/03/13/understanding-pairwise-and-combinatorial-testing-a-simple-guide/)
