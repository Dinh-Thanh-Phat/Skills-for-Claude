---
name: qa-suite-health-metrics
description: >-
  Track and act on the 5 key test suite health metrics — flake rate, defect escape rate, pass
  rate, mean time to detect, and duration trend — with formulas, thresholds, and collection from
  Playwright JSON reports. Use when establishing QA KPIs, setting up a test health dashboard, or
  diagnosing systemic test suite degradation. Triggers on: "test suite health", "flake rate",
  "defect escape rate", "QA metrics", "test KPIs", "test dashboard", "suite performance", "DORA
  metrics QA", "escaped defects", "test pass rate".
---

# QA Suite Health Metrics

Five numbers that tell you whether your test suite is healthy or silently degrading. Collect them from CI, display as trends, and act when thresholds are crossed.

> **Cross-ref:** `flaky-test-prevention` (how to eliminate flaky tests once flake rate is high); `mutation-testing-stryker` (mutation score as a coverage quality gate); `qa-test-plan` (per-release risk matrix and coverage planning).

---

## The 5 Suite Health Metrics

### 1. Flake Rate

**What:** Tests that failed on first run but passed on retry — false alarms that erode trust in CI results.

```
flake_rate = (flaky_test_runs / total_test_runs) × 100
```

| Color | Threshold | Action |
|-------|-----------|--------|
| Green | < 1% | Healthy — monitor weekly |
| Yellow | 1–3% | Schedule flake-hunt session within the sprint |
| Red | > 3% | Freeze new test additions; fix flaky tests first |

---

### 2. Defect Escape Rate (DER)

**What:** Bugs that reach production despite testing — measures how effective your test suite actually is.

```
DER = (escaped_defects / (caught_defects + escaped_defects)) × 100
```

*Escaped defects* = bugs reported by users or found in production monitoring.
*Caught defects* = bugs caught by tests (unit, integration, E2E) before release.

| Color | Threshold | Action |
|-------|-----------|--------|
| Green | < 10% | Test suite is catching defects well |
| Yellow | 10–20% | Review behavioral coverage gaps with `behavioral-coverage-matrix` |
| Red | > 20% | Coverage audit required; add E2E tests for escaped defect paths |

---

### 3. First-Run Pass Rate

**What:** % of tests that pass on the very first attempt (not counting retries). Different from "pass rate including retries."

```
pass_rate = (expected_passes / (expected_passes + unexpected_fails)) × 100
```

| Color | Threshold | Action |
|-------|-----------|--------|
| Green | > 95% | Healthy |
| Yellow | 90–95% | Identify and prioritize failing tests |
| Red | < 90% | Suite is unreliable; block release until resolved |

---

### 4. Mean Time to Detect (MTTD)

**What:** Average time from a code commit to the test pipeline surfacing the failure.

```
MTTD = Σ(time_failure_detected - time_commit_pushed) / number_of_failures
```

| Test level | Target MTTD | Red threshold |
|------------|-------------|---------------|
| Unit / integration | < 5 min | > 15 min |
| E2E smoke | < 20 min | > 45 min |
| Full E2E regression | < 45 min | > 90 min |

Slow MTTD → add sharding, split long tests, or move coverage to a faster layer.

---

### 5. Suite Duration Trend

**What:** Weekly average of total test suite runtime. An upward trend indicates the suite is becoming a CI bottleneck.

```
duration_delta_% = ((this_week_avg - last_week_avg) / last_week_avg) × 100
```

Alert if week-over-week growth > 20% — likely caused by new tests without balancing parallel workers or sharding.

---

## Collecting from Playwright JSON Reporter

The Playwright JSON reporter writes `test-results/results.json`. Parse it to extract metrics 1, 3, and 5:

```typescript
// scripts/suite-health.ts
import results from '../test-results/results.json';

const { stats } = results;
const total = stats.expected + stats.unexpected + stats.flaky + stats.skipped;

const flakeRate = total > 0
  ? (stats.flaky / total) * 100
  : 0;

const passRate = (stats.expected + stats.unexpected) > 0
  ? (stats.expected / (stats.expected + stats.unexpected)) * 100
  : 0;

const durationMin = stats.duration / 1000 / 60;

console.log(`Flake rate: ${flakeRate.toFixed(2)}%`);
console.log(`Pass rate:  ${passRate.toFixed(2)}%`);
console.log(`Duration:   ${durationMin.toFixed(1)} min`);

// Exit non-zero for CI gate
if (flakeRate > 3 || passRate < 90) process.exit(1);
```

Enable the JSON reporter in `playwright.config.ts`:

```typescript
reporter: [
  ['list'],
  ['json', { outputFile: 'test-results/results.json' }],
  ['html', { outputFolder: 'test-results/html-report' }],
],
```

> **Warning:** Never pass `--reporter=json` on the CLI — it overrides ALL config reporters. See `playwright-reporter-discipline`.

---

## DORA Metric Alignment

| DORA Metric | QA equivalent |
|-------------|---------------|
| Change Failure Rate | Defect Escape Rate (DER) |
| Mean Time to Recover (MTTR) | Time from escaped defect detected → fix deployed |
| Deployment Frequency | Release cadence (how often your regression suite runs) |
| Lead Time for Changes | MTTD (how quickly tests surface regressions) |

Tracking MTTD + DER maps directly onto DORA-style engineering health reporting.

---

## Dashboard: One-Page Weekly Review

Track these 5 numbers weekly as a team. The simplest implementation:

```markdown
## Suite Health — Week of <date>

| Metric | This Week | Last Week | Status |
|--------|-----------|-----------|--------|
| Flake Rate | 0.8% | 1.2% | ✅ Green |
| Defect Escape Rate | 8% | 11% | ✅ Green |
| First-Run Pass Rate | 96.2% | 94.8% | ✅ Green |
| MTTD (E2E smoke) | 18 min | 22 min | ✅ Green |
| Suite Duration | 28 min | 24 min | ⚠️ +17% |
```

Review in < 5 minutes; act only when a metric hits Yellow/Red.

---

## Sources

- [QA Metrics That Matter — QASphere 2026](https://qasphere.com/blog/qa-metrics-guide/)
- [DevOps Metrics Dashboard for QA: DORA Metrics, Test Stability — yrkan.com](https://yrkan.com/blog/devops-metrics-dashboard-qa/)
- [Six Metrics to Gauge the Real Impact of Test Coverage — QA Wolf](https://www.qawolf.com/blog/six-metrics-to-gauge-the-real-impact-of-test-coverage)
- [Flaky Test Rate — minware](https://www.minware.com/guide/metrics/flaky-test-rate)
- [Test Metrics & KPIs: Measure QA Success 2026 — TestUnity](https://blog.testunity.com/test-metrics-kpis-measure-qa-success/)
