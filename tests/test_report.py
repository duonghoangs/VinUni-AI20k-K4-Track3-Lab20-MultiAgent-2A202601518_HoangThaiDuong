from multi_agent_research_lab.core.schemas import BenchmarkMetrics, ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report


def test_report_renders_markdown() -> None:
    report = render_markdown_report(
        [
            BenchmarkMetrics(
                run_name="baseline-1",
                latency_seconds=1.0,
                estimated_cost_usd=0.001,
                quality_score=7.0,
                citation_coverage=0.5,
            ),
            BenchmarkMetrics(
                run_name="multi-agent-1",
                latency_seconds=2.0,
                estimated_cost_usd=0.003,
                quality_score=8.0,
                citation_coverage=0.75,
            ),
        ]
    )
    assert "Benchmark Report" in report
    assert "baseline" in report
    assert "Failure mode" in report
    assert "Average comparison" in report
    assert "2.00x" in report


def test_benchmark_scores_grounded_answer() -> None:
    def runner(query: str) -> ResearchState:
        source = SourceDocument(
            title="Evidence",
            snippet="Relevant evidence",
            metadata={"source_id": "S1"},
        )
        return ResearchState(
            request=ResearchQuery(query=query),
            sources=[source],
            final_answer="# Answer\n\nThis grounded claim contains enough detail for scoring [S1].",
        )

    _, metrics = run_benchmark("baseline", "Explain grounded agents", runner)
    assert metrics.successful
    assert metrics.provider == "unknown"
    assert metrics.citation_coverage == 1.0
    assert metrics.failure_rate == 0.0
