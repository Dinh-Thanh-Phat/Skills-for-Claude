---
name: performance-analyzer
description: >-
  Analyze chatbot performance metrics including response times (p50/p95/p99), accuracy
  distribution by category/difficulty, and success rates. Generates statistical summaries and PNG
  visualizations using matplotlib. Use when you need performance charts or percentile
  calculations from chatbot test results. Triggers on: "analyze chatbot performance", "calculate
  response time percentiles", "generate performance metrics", "create accuracy charts", "p95
  response time chatbot". Used as Step 5 in chatbot testing pipeline. Outputs JSON metrics and
  PNG charts.
---

# Performance Analyzer

Computes performance metrics and generates visualizations from chatbot test results.

## Metrics Computed

### Response Time Metrics
- Mean, Median (p50), p95, p99, Min, Max, Standard deviation (all in ms)

### Accuracy Metrics
- Overall pass rate (%), Average score (0-100)
- Score by category: factual / reasoning / edge_case
- Score by difficulty: easy / medium / hard
- Hallucination rate (% responses with hallucinations)

### Reliability Metrics
- API success rate (%)
- Retry rate

## Output: metrics.json
```json
{
  "summary": {
    "total_questions": 20,
    "success_rate": 90.0,
    "pass_rate": 75.0,
    "avg_score": 78.3,
    "hallucination_rate": 10.0
  },
  "response_time": {
    "mean_ms": 1230, "median_ms": 1100,
    "p50_ms": 1100, "p95_ms": 2890, "p99_ms": 3200,
    "min_ms": 450, "max_ms": 3500, "std_ms": 620
  },
  "accuracy_by_category": {
    "factual": {"avg_score": 82.1, "pass_rate": 80.0, "count": 8},
    "reasoning": {"avg_score": 75.4, "pass_rate": 75.0, "count": 8},
    "edge_case": {"avg_score": 68.2, "pass_rate": 62.5, "count": 4}
  },
  "accuracy_by_difficulty": {
    "easy": {"avg_score": 88.5, "pass_rate": 93.3, "count": 7},
    "medium": {"avg_score": 75.2, "pass_rate": 70.0, "count": 9},
    "hard": {"avg_score": 58.1, "pass_rate": 50.0, "count": 4}
  },
  "failed_questions": [
    {"question_id": "q002", "question": "...", "score": 45.2}
  ],
  "thresholds": {
    "accuracy_threshold": 70,
    "response_time_threshold_ms": 3000,
    "accuracy_passed": true,
    "response_time_passed": true
  },
  "charts": {
    "response_time_dist": "charts/response_time_distribution.png",
    "accuracy_by_category": "charts/accuracy_by_category.png",
    "score_distribution": "charts/score_distribution.png",
    "pass_fail_breakdown": "charts/pass_fail_breakdown.png"
  }
}
```

## Python Implementation

Write this script as `performance_analyzer.py`:

```python
import json
import sys
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class PerformanceAnalyzer:
    def __init__(self, accuracy_threshold: float = 70.0, response_time_threshold_ms: int = 3000):
        self.accuracy_threshold = accuracy_threshold
        self.rt_threshold = response_time_threshold_ms

    def analyze(self, responses_file: str, evaluations_file: str, output_dir: str = ".") -> dict:
        responses = json.loads(Path(responses_file).read_text())
        evaluations = json.loads(Path(evaluations_file).read_text())

        charts_dir = Path(output_dir) / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)

        # Response time metrics
        times = [r["response_time_ms"] for r in responses if r.get("success") and r.get("response_time_ms")]
        rt_metrics = {}
        if times:
            arr = np.array(times)
            rt_metrics = {
                "mean_ms": round(float(np.mean(arr))),
                "median_ms": round(float(np.median(arr))),
                "p50_ms": round(float(np.percentile(arr, 50))),
                "p95_ms": round(float(np.percentile(arr, 95))),
                "p99_ms": round(float(np.percentile(arr, 99))),
                "min_ms": round(float(np.min(arr))),
                "max_ms": round(float(np.max(arr))),
                "std_ms": round(float(np.std(arr)))
            }

        scores = [e["scores"]["overall"] for e in evaluations]
        passed = [e for e in evaluations if e["pass"]]
        hallucinations = [e for e in evaluations if e.get("hallucination_detected")]
        failed = [e for e in evaluations if not e["pass"]]
        avg_score = sum(scores) / len(scores) if scores else 0

        # By category
        by_cat = {}
        for cat in ["factual", "reasoning", "edge_case"]:
            cat_evals = [e for e in evaluations if e.get("category") == cat]
            if cat_evals:
                by_cat[cat] = {
                    "avg_score": round(sum(e["scores"]["overall"] for e in cat_evals) / len(cat_evals), 1),
                    "pass_rate": round(sum(1 for e in cat_evals if e["pass"]) / len(cat_evals) * 100, 1),
                    "count": len(cat_evals)
                }

        # By difficulty
        by_diff = {}
        for diff in ["easy", "medium", "hard"]:
            diff_evals = [e for e in evaluations if e.get("difficulty") == diff]
            if diff_evals:
                by_diff[diff] = {
                    "avg_score": round(sum(e["scores"]["overall"] for e in diff_evals) / len(diff_evals), 1),
                    "pass_rate": round(sum(1 for e in diff_evals if e["pass"]) / len(diff_evals) * 100, 1),
                    "count": len(diff_evals)
                }

        chart_paths = self._generate_charts(times, evaluations, by_cat, str(charts_dir))

        metrics = {
            "summary": {
                "total_questions": len(evaluations),
                "success_rate": round(sum(1 for r in responses if r.get("success")) / len(responses) * 100, 1),
                "pass_rate": round(len(passed) / len(evaluations) * 100, 1) if evaluations else 0,
                "avg_score": round(avg_score, 1),
                "hallucination_rate": round(len(hallucinations) / len(evaluations) * 100, 1) if evaluations else 0
            },
            "response_time": rt_metrics,
            "accuracy_by_category": by_cat,
            "accuracy_by_difficulty": by_diff,
            "failed_questions": [
                {"question_id": e["question_id"], "question": e["question"][:80], "score": e["scores"]["overall"]}
                for e in sorted(failed, key=lambda x: x["scores"]["overall"])[:10]
            ],
            "thresholds": {
                "accuracy_threshold": self.accuracy_threshold,
                "response_time_threshold_ms": self.rt_threshold,
                "accuracy_passed": avg_score >= self.accuracy_threshold,
                "response_time_passed": rt_metrics.get("p95_ms", 0) <= self.rt_threshold
            },
            "charts": chart_paths
        }

        out_path = Path(output_dir) / "metrics.json"
        out_path.write_text(json.dumps(metrics, indent=2), encoding='utf-8')
        print(f"✓ Metrics → {out_path}")
        print(f"  Avg score: {avg_score:.1f} | P95: {rt_metrics.get('p95_ms', 'N/A')}ms")
        return metrics

    def _generate_charts(self, times, evaluations, by_cat, charts_dir) -> dict:
        plt.style.use('seaborn-v0_8-whitegrid')
        paths = {}

        # 1. Response time distribution
        if times:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.hist(times, bins=20, color='steelblue', edgecolor='white', alpha=0.85)
            ax.axvline(np.percentile(times, 50), color='green', linestyle='--', label=f'p50: {int(np.percentile(times, 50))}ms')
            ax.axvline(np.percentile(times, 95), color='orange', linestyle='--', label=f'p95: {int(np.percentile(times, 95))}ms')
            ax.axvline(np.percentile(times, 99), color='red', linestyle='--', label=f'p99: {int(np.percentile(times, 99))}ms')
            ax.set_xlabel('Response Time (ms)')
            ax.set_ylabel('Count')
            ax.set_title('Response Time Distribution')
            ax.legend()
            path = f"{charts_dir}/response_time_distribution.png"
            fig.savefig(path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            paths["response_time_dist"] = path

        # 2. Accuracy by category
        if by_cat:
            fig, ax = plt.subplots(figsize=(8, 5))
            cats = list(by_cat.keys())
            cat_scores = [by_cat[c]["avg_score"] for c in cats]
            colors = ['#2ecc71' if s >= 70 else '#e74c3c' for s in cat_scores]
            bars = ax.bar(cats, cat_scores, color=colors, edgecolor='white')
            ax.axhline(70, color='gray', linestyle='--', alpha=0.7, label='Pass threshold (70)')
            ax.set_ylim(0, 100)
            ax.set_ylabel('Average Score')
            ax.set_title('Accuracy by Question Category')
            for bar, score in zip(bars, cat_scores):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{score:.0f}', ha='center', fontsize=12)
            path = f"{charts_dir}/accuracy_by_category.png"
            fig.savefig(path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            paths["accuracy_by_category"] = path

        # 3. Score distribution
        all_scores = [e["scores"]["overall"] for e in evaluations]
        if all_scores:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.hist(all_scores, bins=10, range=(0, 100), color='steelblue', edgecolor='white', alpha=0.85)
            ax.axvline(70, color='red', linestyle='--', label='Pass threshold (70)')
            ax.set_xlabel('Score (0-100)')
            ax.set_ylabel('Number of Questions')
            ax.set_title('Score Distribution')
            ax.legend()
            path = f"{charts_dir}/score_distribution.png"
            fig.savefig(path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            paths["score_distribution"] = path

        # 4. Pass/Fail pie
        passed_count = sum(1 for e in evaluations if e["pass"])
        failed_count = len(evaluations) - passed_count
        if evaluations:
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.pie(
                [passed_count, failed_count],
                labels=[f'Pass ({passed_count})', f'Fail ({failed_count})'],
                colors=['#2ecc71', '#e74c3c'],
                autopct='%1.0f%%', startangle=90,
                textprops={'fontsize': 13}
            )
            ax.set_title('Pass / Fail Breakdown')
            path = f"{charts_dir}/pass_fail_breakdown.png"
            fig.savefig(path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            paths["pass_fail_breakdown"] = path

        return paths


if __name__ == "__main__":
    analyzer = PerformanceAnalyzer()
    analyzer.analyze(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ".")
```

## Dependencies
```bash
pip install numpy matplotlib
```

## Token / Cost Aggregation

When responses include token counts, aggregate cost per run for the report:

```python
total_input  = sum(r.get('usage', {}).get('input_tokens', 0)  for r in responses)
total_output = sum(r.get('usage', {}).get('output_tokens', 0) for r in responses)
total_eval_cost = sum(e.get('eval_cost_usd', 0) for e in evaluations)

metrics['cost'] = {
    'total_input_tokens':  total_input,
    'total_output_tokens': total_output,
    'eval_cost_usd':       round(total_eval_cost, 4),
    'avg_cost_per_question_usd': round(total_eval_cost / max(len(responses), 1), 4),
}
```

## Run-to-Run Comparison (Regression Detection)

If `metrics-prev.json` exists, compute deltas so the reporter can flag regressions:

```python
from pathlib import Path
prev_path = Path(output_dir) / 'metrics-prev.json'
if prev_path.exists():
    prev = json.loads(prev_path.read_text())
    metrics['vs_prev'] = {
        'pass_rate_delta':   round(metrics['summary']['pass_rate']   - prev['summary']['pass_rate'],   1),
        'avg_score_delta':   round(metrics['summary']['avg_score']   - prev['summary']['avg_score'],   1),
        'p95_delta_ms':      metrics['response_time'].get('p95_ms', 0) - prev['response_time'].get('p95_ms', 0),
    }

# After this run completes — rotate so the next run can compare:
# Path(output_dir) / 'metrics.json'  →  Path(output_dir) / 'metrics-prev.json'
```

The reporter's "Trend vs Previous Run" section consumes `metrics.vs_prev` directly.

## Key Principles
- Always compute p95 and p99, not just mean — mean hides tail latency problems
- Charts use consistent color coding: green=#2ecc71 (pass ≥70), red=#e74c3c (fail <70)
- Failed questions must be sorted by score ascending (worst first) for the reporter
- If no successful API calls, skip response time metrics but still compute accuracy (all zeros)
- Close all matplotlib figures after saving (`plt.close(fig)`) to avoid memory leaks
