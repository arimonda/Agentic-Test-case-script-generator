"""
Real-Time Execution Report Generator.

Produces an HTML report tracking the AI agent's reasoning, token usage,
step-by-step execution results, locator healing events, and timing.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from models.schemas import StepStatus, TestCaseResult

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Execution Report — {test_name}</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --border: #334155;
            --text: #e2e8f0;
            --text-muted: #94a3b8;
            --green: #22c55e;
            --red: #ef4444;
            --yellow: #eab308;
            --blue: #3b82f6;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, var(--blue), var(--green));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ color: var(--text-muted); margin-bottom: 2rem; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .stat-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.2rem;
            text-align: center;
        }}
        .stat-card .value {{
            font-size: 2rem;
            font-weight: 700;
        }}
        .stat-card .label {{
            color: var(--text-muted);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .passed {{ color: var(--green); }}
        .failed {{ color: var(--red); }}
        .healed {{ color: var(--yellow); }}
        .step-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }}
        .step-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.8rem;
        }}
        .step-number {{
            font-weight: 700;
            font-size: 1.1rem;
        }}
        .badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge-passed {{ background: rgba(34,197,94,0.15); color: var(--green); }}
        .badge-failed {{ background: rgba(239,68,68,0.15); color: var(--red); }}
        .badge-healed {{ background: rgba(234,179,8,0.15); color: var(--yellow); }}
        .step-detail {{ color: var(--text-muted); font-size: 0.9rem; margin-bottom: 0.3rem; }}
        .locator-info {{
            background: var(--bg);
            border-radius: 8px;
            padding: 0.8rem;
            margin-top: 0.8rem;
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            font-size: 0.85rem;
        }}
        .screenshots {{
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
        }}
        .screenshots img {{
            max-width: 48%;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        .ai-section {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 2rem;
        }}
        .ai-section h2 {{ margin-bottom: 1rem; font-size: 1.3rem; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        th, td {{
            padding: 0.6rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{ color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{test_name}</h1>
        <p class="subtitle">{description} — Generated {timestamp}</p>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{total_steps}</div>
                <div class="label">Total Steps</div>
            </div>
            <div class="stat-card">
                <div class="value passed">{passed}</div>
                <div class="label">Passed</div>
            </div>
            <div class="stat-card">
                <div class="value failed">{failed}</div>
                <div class="label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="value healed">{healed}</div>
                <div class="label">Self-Healed</div>
            </div>
            <div class="stat-card">
                <div class="value">{duration}</div>
                <div class="label">Duration (s)</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_tokens}</div>
                <div class="label">AI Tokens</div>
            </div>
        </div>

        <h2 style="margin-bottom: 1rem;">Step-by-Step Results</h2>
        {step_cards}

        <div class="ai-section">
            <h2>AI Usage & Reasoning Log</h2>
            <table>
                <thead>
                    <tr>
                        <th>Step</th>
                        <th>Provider</th>
                        <th>Tokens</th>
                        <th>Latency</th>
                        <th>Reasoning</th>
                    </tr>
                </thead>
                <tbody>
                    {ai_log_rows}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

STEP_CARD_TEMPLATE = """\
<div class="step-card">
    <div class="step-header">
        <span class="step-number">Step {step_number}: {intent}</span>
        <span class="badge badge-{status_class}">{status}</span>
    </div>
    <div class="step-detail"><strong>Action:</strong> {action_type}</div>
    <div class="step-detail"><strong>Input:</strong> {input_data}</div>
    <div class="step-detail"><strong>Expected:</strong> {expected}</div>
    <div class="step-detail"><strong>Actual:</strong> {actual}</div>
    <div class="step-detail"><strong>Duration:</strong> {duration_ms:.0f} ms</div>
    {locator_html}
    {error_html}
</div>
"""


class ReportGenerator:
    """Generates HTML execution reports from test results."""

    def __init__(self, output_dir: str = "output/reports"):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        self._ai_log: list[dict[str, Any]] = []

    def log_ai_usage(
        self,
        step_number: int,
        provider: str,
        tokens: int,
        latency_ms: float,
        reasoning: str,
    ) -> None:
        """Record AI usage for a step (called during execution)."""
        self._ai_log.append({
            "step": step_number,
            "provider": provider,
            "tokens": tokens,
            "latency_ms": latency_ms,
            "reasoning": reasoning[:200],
        })

    def generate(self, test_result: TestCaseResult) -> str:
        """
        Generate the HTML report and return its file path.
        """
        tc = test_result.test_case
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build step cards
        step_cards = []
        for sr in test_result.step_results:
            step = sr.step_input
            status_class = sr.status.value.lower()

            locator_html = ""
            if sr.locators_used:
                primary = sr.locators_used.primary
                locator_html = (
                    f'<div class="locator-info">'
                    f"Primary: {primary.to_playwright()} "
                    f"(confidence: {primary.confidence:.0%})"
                    f"</div>"
                )

            error_html = ""
            if sr.error_message:
                error_html = (
                    f'<div class="step-detail" style="color: var(--red);">'
                    f"<strong>Error:</strong> {sr.error_message}</div>"
                )

            card = STEP_CARD_TEMPLATE.format(
                step_number=step.step_number,
                intent=step.intent,
                status_class=status_class,
                status=sr.status.value.upper(),
                action_type=step.action_type.value,
                input_data=step.input_data or "—",
                expected=step.expected_result,
                actual=sr.actual_result or "—",
                duration_ms=sr.duration_ms,
                locator_html=locator_html,
                error_html=error_html,
            )
            step_cards.append(card)

        # Build AI log rows
        ai_rows = []
        total_tokens = 0
        for entry in self._ai_log:
            total_tokens += entry["tokens"]
            ai_rows.append(
                f"<tr>"
                f"<td>{entry['step']}</td>"
                f"<td>{entry['provider']}</td>"
                f"<td>{entry['tokens']:,}</td>"
                f"<td>{entry['latency_ms']:.0f} ms</td>"
                f"<td>{entry['reasoning']}</td>"
                f"</tr>"
            )

        html = HTML_TEMPLATE.format(
            test_name=tc.name,
            description=tc.description,
            timestamp=timestamp,
            total_steps=len(test_result.step_results),
            passed=test_result.passed_steps,
            failed=test_result.failed_steps,
            healed=test_result.healed_steps,
            duration=f"{test_result.total_duration_ms / 1000:.1f}",
            total_tokens=f"{total_tokens:,}",
            step_cards="\n".join(step_cards),
            ai_log_rows="\n".join(ai_rows) if ai_rows else "<tr><td colspan='5'>No AI usage logged</td></tr>",
        )

        safe_name = tc.name.replace(" ", "_")[:50]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{safe_name}_{ts}.html"
        filepath = Path(self.output_dir) / filename

        filepath.write_text(html, encoding="utf-8")
        logger.info("Generated HTML report: %s", filepath)

        # Also save JSON version
        self._save_json_report(test_result, filepath.with_suffix(".json"))

        return str(filepath)

    def _save_json_report(self, test_result: TestCaseResult, filepath: Path) -> None:
        """Save a machine-readable JSON version of the report."""
        data = {
            "test_case": test_result.test_case.model_dump(mode="json"),
            "step_results": [sr.model_dump(mode="json") for sr in test_result.step_results],
            "summary": {
                "overall_status": test_result.overall_status.value,
                "passed": test_result.passed_steps,
                "failed": test_result.failed_steps,
                "healed": test_result.healed_steps,
                "total_duration_ms": test_result.total_duration_ms,
                "total_healing_attempts": test_result.total_healing_attempts,
            },
            "ai_usage": self._ai_log,
        }
        filepath.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.info("Generated JSON report: %s", filepath)
