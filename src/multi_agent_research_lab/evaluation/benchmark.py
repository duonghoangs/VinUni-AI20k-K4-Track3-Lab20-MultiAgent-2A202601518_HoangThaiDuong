"""Reproducible single-agent versus multi-agent measurements."""

from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.agents.support import valid_citations
from multi_agent_research_lab.core.schemas import BenchmarkMetrics, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure runtime and deterministic output-quality indicators."""

    started = perf_counter()
    try:
        state = runner(query)
    except Exception as exc:
        state = ResearchState(request=ResearchQuery(query=query), errors=[str(exc)])
    latency = perf_counter() - started
    citation_coverage = calculate_citation_coverage(state)
    successful = bool(state.final_answer) and not state.errors
    providers = sorted(
        {
            str(result.metadata["provider"])
            for result in state.agent_results
            if result.metadata.get("provider")
        }
    )
    metrics = BenchmarkMetrics(
        run_name=run_name,
        query=query,
        provider="+".join(providers) or "unknown",
        latency_seconds=latency,
        estimated_cost_usd=state.estimated_cost_usd,
        total_tokens=state.input_tokens + state.output_tokens,
        iterations=state.iteration,
        retries=state.retries,
        successful=successful,
        quality_score=calculate_quality_score(state, citation_coverage),
        citation_coverage=citation_coverage,
        failure_rate=0.0 if successful else 1.0,
        notes="; ".join(state.errors),
    )
    return state, metrics


def calculate_citation_coverage(state: ResearchState) -> float:
    """Approximate grounded-claim coverage using substantive answer lines."""

    if not state.final_answer:
        return 0.0
    allowed = valid_citations(state.final_answer, state.sources)
    claim_lines = [
        line.strip()
        for line in state.final_answer.splitlines()
        if len(line.strip()) >= 50 and not line.lstrip().startswith("#")
    ]
    if not claim_lines:
        return 0.0
    grounded = sum(any(f"[{citation}]" in line for citation in allowed) for line in claim_lines)
    return grounded / len(claim_lines)


def calculate_quality_score(state: ResearchState, citation_coverage: float) -> float:
    """Return transparent 0-10 structural quality score, not an LLM judge score."""

    answer = state.final_answer or ""
    valid = valid_citations(answer, state.sources)
    length_score = min(len(answer.split()) / 300, 1.0) * 3
    citation_score = citation_coverage * 3
    diversity_score = min(len(valid) / 4, 1.0) * 2
    structure_score = 1.0 if "##" in answer else 0.0
    reliability_score = 1.0 if answer and not state.errors else 0.0
    return round(
        length_score + citation_score + diversity_score + structure_score + reliability_score, 2
    )
