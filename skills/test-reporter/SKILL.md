---
name: test-reporter
description: >-
  Generate comprehensive self-contained HTML test reports for chatbot evaluation results with
  embedded charts, performance metrics, accuracy scores, and failed test details. Use when you
  need a professional shareable report from chatbot test data. Triggers on: "generate test
  report", "create chatbot test HTML report", "export test results report", "make performance
  report", "generate QA report for chatbot". Used as Step 6 (final step) in chatbot testing
  pipeline. Outputs a single self-contained HTML file (and optionally PDF).
---

# Test Reporter

Generates a professional, self-contained HTML report from chatbot test results.

## Report Structure

1. **Header** — Title, chatbot URL, date, PASS/FAIL badge
2. **Executive Summary** — 4 KPI cards: Questions, Pass Rate, Avg Score, Avg Response Time
3. **Performance Dashboard** — Response time chart + timing table (mean, p50, p95, p99)
4. **Accuracy Analysis** — Category chart + score distribution + pass/fail pie + breakdown table
5. **Failed Test Cases** — Table sorted by score ascending, with hallucination flags
6. **All Test Cases** — Collapsible full table of all questions + scores
7. **Raw Data** — Reference to metrics.json and evaluations.json

## Python Implementation

Write this script as `test_reporter.py`:

```python
import json
import base64
import sys
from pathlib import Path
from datetime import datetime

class TestReporter:
    def generate_report(
        self,
        metrics_file: str,
        evaluations_file: str,
        chatbot_url: str = "",
        output_file: str = "report.html",
        export_pdf: bool = False
    ) -> str:
        metrics = json.loads(Path(metrics_file).read_text())
        evaluations = json.loads(Path(evaluations_file).read_text())

        # Embed charts as base64
        charts = {}
        for key, path in metrics.get("charts", {}).items():
            if path and Path(path).exists():
                with open(path, "rb") as f:
                    charts[key] = base64.b64encode(f.read()).decode()

        html = self._build_html(metrics, evaluations, charts, chatbot_url)
        Path(output_file).write_text(html, encoding='utf-8')
        print(f"✓ Report saved → {output_file}")

        if export_pdf:
            self._export_pdf(output_file)

        return output_file

    def _chart_img(self, charts: dict, key: str, alt: str) -> str:
        if key in charts:
            return f'<img src="data:image/png;base64,{charts[key]}" alt="{alt}" style="max-width:100%;border-radius:8px;">'
        return f'<p style="color:#999;font-style:italic;">Chart not available: {alt}</p>'

    def _build_html(self, metrics: dict, evaluations: list, charts: dict, chatbot_url: str) -> str:
        summary = metrics["summary"]
        rt = metrics.get("response_time", {})
        thresholds = metrics.get("thresholds", {})
        overall_pass = thresholds.get("accuracy_passed", False) and thresholds.get("response_time_passed", True)
        status_color = "#27ae60" if overall_pass else "#e74c3c"
        status_text = "PASS" if overall_pass else "FAIL"

        # Failed questions rows
        failed_rows = ""
        for e in evaluations:
            if not e["pass"]:
                hallucination_badge = '<span style="background:#e74c3c;color:white;padding:2px 6px;border-radius:4px;font-size:11px;margin-left:4px;">HALLUCINATION</span>' if e.get("hallucination_detected") else ""
                failed_rows += f"""<tr>
<td style="max-width:200px;font-size:13px;">{e['question']}</td>
<td><span style="background:#3498db;color:white;padding:2px 6px;border-radius:4px;font-size:11px;">{e.get('category','?')}</span></td>
<td style="color:#e74c3c;font-weight:bold;">{e['scores']['overall']:.0f}</td>
<td style="max-width:200px;font-size:12px;color:#555;">{(e.get('actual_response') or 'No response')[:120]}...</td>
<td>{hallucination_badge}</td>
</tr>"""

        # All questions rows
        all_rows = ""
        for e in evaluations:
            score = e['scores']['overall']
            score_color = "#27ae60" if e["pass"] else "#e74c3c"
            all_rows += f"""<tr>
<td style="font-size:12px;">{e['question_id']}</td>
<td style="max-width:180px;font-size:12px;">{e['question']}</td>
<td style="max-width:140px;font-size:11px;color:#555;">{(e.get('expected_answer') or '')[:70]}...</td>
<td style="max-width:140px;font-size:11px;color:#555;">{(e.get('actual_response') or 'N/A')[:70]}...</td>
<td style="color:{score_color};font-weight:bold;">{score:.0f}</td>
<td><span style="background:{score_color};color:white;padding:2px 8px;border-radius:12px;font-size:11px;">{'PASS' if e['pass'] else 'FAIL'}</span></td>
</tr>"""

        no_failed = not any(not e["pass"] for e in evaluations)
        failed_section = '<p style="color:#27ae60;font-weight:bold;">All test cases passed!</p>' if no_failed else f"""<table>
<tr><th>Question</th><th>Category</th><th>Score</th><th>Response (truncated)</th><th>Issues</th></tr>
{failed_rows}
</table>"""

        cat_rows = "".join(
            f"<tr><td>{cat}</td><td>{data['avg_score']:.1f}</td><td>{data['pass_rate']:.0f}%</td><td>{data['count']}</td></tr>"
            for cat, data in metrics.get("accuracy_by_category", {}).items()
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Chatbot Test Report</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8f9fa;color:#333}}
.container{{max-width:1100px;margin:0 auto;padding:24px}}
.header{{background:white;border-radius:12px;padding:28px;margin-bottom:20px;border-left:6px solid {status_color};box-shadow:0 2px 8px rgba(0,0,0,.06)}}
h1{{font-size:24px;margin-bottom:8px}}
.badge{{display:inline-block;background:{status_color};color:white;padding:6px 16px;border-radius:20px;font-weight:bold;font-size:14px}}
.meta{{color:#666;font-size:13px;margin-top:10px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}}
.card{{background:white;border-radius:12px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
.card .val{{font-size:32px;font-weight:bold;margin-bottom:4px}}
.card .lbl{{color:#666;font-size:13px}}
.section{{background:white;border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
h2{{font-size:18px;margin-bottom:16px;color:#2c3e50;border-bottom:2px solid #f0f0f0;padding-bottom:8px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#f8f9fa;padding:10px 12px;text-align:left;font-weight:600;border-bottom:2px solid #e9ecef}}
td{{padding:10px 12px;border-bottom:1px solid #f0f0f0;vertical-align:top}}
tr:hover td{{background:#f8f9fa}}
.charts{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:16px}}
details summary{{cursor:pointer;padding:10px;background:#f8f9fa;border-radius:6px;font-weight:600}}
details[open] summary{{margin-bottom:12px}}
@media(max-width:768px){{.cards{{grid-template-columns:1fr 1fr}}.charts{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Chatbot Test Report &nbsp;<span class="badge">{status_text}</span></h1>
    <div class="meta">
      <strong>Chatbot:</strong> {chatbot_url or 'N/A'} &nbsp;|&nbsp;
      <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp;
      <strong>Questions:</strong> {summary['total_questions']}
    </div>
  </div>

  <div class="cards">
    <div class="card"><div class="val">{summary['total_questions']}</div><div class="lbl">Questions Tested</div></div>
    <div class="card"><div class="val" style="color:{'#27ae60' if thresholds.get('accuracy_passed') else '#e74c3c'}">{summary['pass_rate']:.0f}%</div><div class="lbl">Pass Rate {'✓' if thresholds.get('accuracy_passed') else '✗'}</div></div>
    <div class="card"><div class="val" style="color:{'#27ae60' if summary['avg_score']>=70 else '#e74c3c'}">{summary['avg_score']:.0f}</div><div class="lbl">Avg Score / 100</div></div>
    <div class="card"><div class="val" style="color:{'#27ae60' if thresholds.get('response_time_passed') else '#e74c3c'}">{rt.get('mean_ms','N/A')}ms</div><div class="lbl">Avg Response Time {'✓' if thresholds.get('response_time_passed') else '✗'}</div></div>
  </div>

  <div class="section">
    <h2>Performance Metrics</h2>
    <div class="charts">
      {self._chart_img(charts,'response_time_dist','Response Time Distribution')}
      {self._chart_img(charts,'pass_fail_breakdown','Pass/Fail Breakdown')}
    </div>
    <table>
      <tr><th>Metric</th><th>Mean</th><th>p50</th><th>p95</th><th>p99</th><th>Min</th><th>Max</th></tr>
      <tr><td><strong>Response Time</strong></td><td>{rt.get('mean_ms','N/A')}ms</td><td>{rt.get('p50_ms','N/A')}ms</td><td>{rt.get('p95_ms','N/A')}ms</td><td>{rt.get('p99_ms','N/A')}ms</td><td>{rt.get('min_ms','N/A')}ms</td><td>{rt.get('max_ms','N/A')}ms</td></tr>
    </table>
  </div>

  <div class="section">
    <h2>Accuracy Analysis</h2>
    <div class="charts">
      {self._chart_img(charts,'accuracy_by_category','Accuracy by Category')}
      {self._chart_img(charts,'score_distribution','Score Distribution')}
    </div>
    <table>
      <tr><th>Category</th><th>Avg Score</th><th>Pass Rate</th><th>Count</th></tr>
      {cat_rows}
    </table>
  </div>

  <div class="section">
    <h2>Failed Test Cases ({sum(1 for e in evaluations if not e['pass'])})</h2>
    {failed_section}
  </div>

  <div class="section">
    <details>
      <summary>All Test Cases ({len(evaluations)} total)</summary>
      <table style="margin-top:12px;">
        <tr><th>ID</th><th>Question</th><th>Expected</th><th>Actual</th><th>Score</th><th>Result</th></tr>
        {all_rows}
      </table>
    </details>
  </div>

  <div class="section">
    <h2>Raw Data</h2>
    <p>Full data files: <code>metrics.json</code>, <code>evaluations.json</code></p>
    <p style="color:#666;font-size:13px;margin-top:8px;">Hallucination rate: {summary['hallucination_rate']:.0f}% | API success rate: {summary['success_rate']:.0f}%</p>
  </div>
</div>
</body>
</html>"""

    def _export_pdf(self, html_file: str):
        pdf_file = html_file.replace('.html', '.pdf')
        import subprocess
        for cmd in ['chromium', 'google-chrome', 'chrome']:
            try:
                subprocess.run([cmd, '--headless', '--no-sandbox', f'--print-to-pdf={pdf_file}', html_file],
                               check=True, capture_output=True, timeout=30)
                print(f"✓ PDF exported → {pdf_file}")
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        try:
            from weasyprint import HTML
            HTML(filename=html_file).write_pdf(pdf_file)
            print(f"✓ PDF exported → {pdf_file}")
        except Exception as e:
            print(f"⚠️ PDF export failed: {e}. HTML report is still available.")


if __name__ == "__main__":
    reporter = TestReporter()
    reporter.generate_report(
        metrics_file=sys.argv[1],
        evaluations_file=sys.argv[2],
        chatbot_url=sys.argv[3] if len(sys.argv) > 3 else "",
        output_file=sys.argv[4] if len(sys.argv) > 4 else "report.html",
        export_pdf="--pdf" in sys.argv
    )
```

## Dependencies
```bash
# No extra deps required for HTML report
# Optional for PDF:
pip install weasyprint   # or use Chromium headless
```

## Run Comparison Section (Trend)

If `metrics.vs_prev` exists (from performance-analyzer comparison), add a "Trend vs previous run" card:

```python
def _trend_section(self, metrics: dict) -> str:
    vp = metrics.get('vs_prev')
    if not vp: return ''
    sign = lambda n: '🟢 ↑' if n > 0 else ('🔴 ↓' if n < 0 else '⏸ =')
    return f'''<div class="section">
    <h2>Trend vs Previous Run</h2>
    <table>
      <tr><th>Metric</th><th>Δ</th></tr>
      <tr><td>Pass rate</td><td>{sign(vp['pass_rate_delta'])} {vp['pass_rate_delta']:+.1f}%</td></tr>
      <tr><td>Avg score</td><td>{sign(vp['avg_score_delta'])} {vp['avg_score_delta']:+.1f}</td></tr>
      <tr><td>P95 latency</td><td>{sign(-vp['p95_delta_ms'])} {vp['p95_delta_ms']:+d}ms</td></tr>
    </table></div>'''
```

## Multi-Chatbot Comparison

When comparing several chatbots, write a separate `report-comparison.html` consuming each
chatbot's `metrics.json` and showing a side-by-side table — pass rate, avg score, p95,
hallucination rate, cost per question.

## CSV Export

```python
import csv
def export_csv(evaluations, path='evaluations.csv'):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['id', 'question', 'expected', 'actual', 'score', 'pass', 'category', 'hallucination'])
        for e in evaluations:
            w.writerow([e['question_id'], e['question'], e['expected_answer'], e['actual_response'],
                        e['scores']['overall'], e['pass'], e.get('category', ''), e.get('hallucination_detected', False)])
```

Useful for sharing with stakeholders who prefer spreadsheets over HTML.

## Key Principles
- HTML report must be self-contained — all charts embedded as base64, no external CDN
- Failed test cases section is the most prominent — that's what the user acts on
- Color coding is consistent throughout: `#27ae60` green (pass), `#e74c3c` red (fail)
- If PDF export fails, fall back gracefully — HTML is always the primary deliverable
- The report opens correctly in any modern browser without a server
