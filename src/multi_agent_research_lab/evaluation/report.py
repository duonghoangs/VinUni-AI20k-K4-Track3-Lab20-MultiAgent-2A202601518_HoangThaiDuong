"""Benchmark report rendering."""

from statistics import fmean

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _average_comparison(metrics: list[BenchmarkMetrics]) -> list[str]:
    baseline = [item for item in metrics if item.run_name.startswith("baseline")]
    multi = [item for item in metrics if item.run_name.startswith("multi-agent")]
    if not baseline or len(baseline) != len(multi):
        return []

    baseline_latency = fmean(item.latency_seconds for item in baseline)
    multi_latency = fmean(item.latency_seconds for item in multi)
    baseline_quality = fmean(item.quality_score or 0.0 for item in baseline)
    multi_quality = fmean(item.quality_score or 0.0 for item in multi)
    baseline_citations = fmean(item.citation_coverage or 0.0 for item in baseline)
    multi_citations = fmean(item.citation_coverage or 0.0 for item in multi)
    baseline_cost = fmean(item.estimated_cost_usd or 0.0 for item in baseline)
    multi_cost = fmean(item.estimated_cost_usd or 0.0 for item in multi)
    latency_ratio = multi_latency / baseline_latency if baseline_latency else 0.0
    cost_ratio = multi_cost / baseline_cost if baseline_cost else 0.0

    return [
        "",
        "## Average comparison",
        "",
        f"- Quality: baseline `{baseline_quality:.2f}`, multi-agent `{multi_quality:.2f}` "
        f"(delta `{multi_quality - baseline_quality:+.2f}`).",
        f"- Citation coverage: baseline `{baseline_citations:.0%}`, multi-agent "
        f"`{multi_citations:.0%}` (delta `{(multi_citations - baseline_citations):+.0%}`).",
        f"- Latency: baseline `{baseline_latency:.2f}s`, multi-agent `{multi_latency:.2f}s` "
        f"(`{latency_ratio:.2f}x`).",
        f"- Estimated cost: baseline `${baseline_cost:.4f}`, multi-agent "
        f"`${multi_cost:.4f}` (`{cost_ratio:.2f}x`).",
    ]


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render comparable metrics plus explicit trade-off and failure analysis."""

    lines = [
        "# Benchmark Report",
        "",
        "Generated from matched queries and the bundled offline corpus.",
        "",
        "| Run | Provider | Query | Latency (s) | Cost | Tokens | Steps | Retries | "
        "Quality | Citations | Failures | Notes |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        citation = "" if item.citation_coverage is None else f"{item.citation_coverage:.0%}"
        failure = "" if item.failure_rate is None else f"{item.failure_rate:.0%}"
        lines.append(
            f"| {_cell(item.run_name)} | {_cell(item.provider)} | {_cell(item.query)} "
            f"| {item.latency_seconds:.2f} | {cost} "
            f"| {item.total_tokens} "
            f"| {item.iterations} | {item.retries} | {quality} | {citation} | {failure} "
            f"| {_cell(item.notes)} |"
        )
    lines.extend(_average_comparison(metrics))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Quality is a transparent structural score based on answer completeness, valid inline "
            "citations, citation coverage, source diversity, and successful completion. It is not "
            "a substitute for expert factual review.",
            "",
            "Multi-agent runs normally use more steps and may cost more. A higher score is useful "
            "only when the quality or traceability gain justifies that overhead.",
            "",
            "## Failure mode",
            "",
            "Primary risk: evidence or citation provenance can be lost during handoff. "
            "The workflow mitigates this with typed shared state, immutable source IDs, "
            "bounded routing, offline "
            "fallbacks, and citation validation before accepting writer output.",
            "",
            "## Trace evidence",
            "",
            "Visual evidence: [successful workflow trace](trace_evidence.svg). Per-run JSON traces "
            "are stored beside this report in `reports/traces/`.",
        ]
    )
    return "\n".join(lines) + "\n"
