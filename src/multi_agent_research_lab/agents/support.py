"""Shared evidence formatting and deterministic offline fallbacks."""

import re

from multi_agent_research_lab.core.schemas import SourceDocument

_CITATION_RE = re.compile(r"\[([^\[\]]+)\]")


def source_id(source: SourceDocument) -> str:
    return str(source.metadata.get("source_id", source.title))


def evidence_block(sources: list[SourceDocument], max_chars: int = 12_000) -> str:
    blocks: list[str] = []
    used = 0
    for source in sources:
        label = "synthetic benchmark evidence" if source.metadata.get("is_synthetic") else "source"
        block = f"[{source_id(source)}] {source.title} ({label})\n{source.snippet.strip()}"
        remaining = max_chars - used
        if remaining <= 0:
            break
        blocks.append(block[:remaining])
        used += len(block)
    return "\n\n".join(blocks)


def concise_excerpt(text: str, max_chars: int = 360) -> str:
    compact = " ".join(text.split())
    sentences = re.split(r"(?<=[.!?])\s+", compact)
    excerpt = " ".join(sentences[:2]).strip()
    if len(excerpt) <= max_chars:
        return excerpt
    return excerpt[: max_chars - 1].rstrip() + "…"


def offline_research_notes(sources: list[SourceDocument]) -> str:
    lines = ["Evidence ledger:"]
    for source in sources:
        kind = "synthetic" if source.metadata.get("is_synthetic") else "public/embedded"
        lines.append(
            f"- [{source_id(source)}] ({kind}) {source.title}: {concise_excerpt(source.snippet)}"
        )
    return "\n".join(lines)


def offline_analysis_notes(sources: list[SourceDocument]) -> str:
    public_count = sum(not bool(source.metadata.get("is_synthetic")) for source in sources)
    synthetic_count = len(sources) - public_count
    lines = [
        "Evidence assessment:",
        f"- Evidence set: {public_count} public/embedded sources and "
        f"{synthetic_count} synthetic benchmark sources.",
        "- Public-reference summaries support scoped architectural claims; they do not prove "
        "universal superiority.",
        "- Synthetic evidence may illustrate benchmark behavior but must remain explicitly "
        "labeled.",
        "- Prefer conditional conclusions that compare quality gains against cost, latency, and "
        "coordination failures.",
        "- Preserve source IDs through synthesis; repeated agent agreement is not independent "
        "evidence.",
    ]
    return "\n".join(lines)


def offline_answer(
    query: str,
    sources: list[SourceDocument],
    analysis_notes: str | None = None,
    *,
    title: str = "Research Answer",
) -> str:
    if not sources:
        return f"# {title}\n\nNo evidence was retrieved for: {query}"

    lead = sources[0]
    second = sources[1] if len(sources) > 1 else lead
    evidence_lines = [
        f"- **{source.title}.** {concise_excerpt(source.snippet)} [{source_id(source)}]"
        for source in sources
    ]
    source_lines = []
    for source in sources:
        marker = " — synthetic benchmark evidence" if source.metadata.get("is_synthetic") else ""
        source_lines.append(f"- [{source_id(source)}] {source.title}{marker}")

    analysis = analysis_notes or offline_analysis_notes(sources)
    return "\n".join(
        [
            f"# {title}",
            "",
            "## Executive summary",
            "",
            f"For **{query}**, available evidence favors a conditional conclusion. "
            f"{concise_excerpt(lead.snippet)} [{source_id(lead)}]",
            "",
            "A robust decision must compare outcome quality with coordination cost, latency, and "
            f"failure propagation rather than assuming more agents are always better "
            f"[{source_id(second)}].",
            "",
            "## Evidence review",
            "",
            *evidence_lines,
            "",
            "## Analysis and trade-offs",
            "",
            analysis,
            "",
            "## Recommendations",
            "",
            f"1. Start with a measurable single-agent baseline [{source_id(lead)}].",
            "2. Add specialized agents only for distinct retrieval, analysis, or "
            "verification work "
            f"[{source_id(second)}].",
            "3. Track citation coverage, failure rate, latency, token usage, and handoff defects.",
            "4. Treat retrieved text as untrusted data and retain provenance through every "
            "handoff.",
            "",
            "## Limitations",
            "",
            "This answer uses a bounded offline corpus. Public-reference entries are embedded "
            "summaries, while synthetic entries are benchmark material rather than real "
            "publications. "
            "Conclusions require validation against deployment-specific tasks.",
            "",
            "## Sources",
            "",
            *source_lines,
        ]
    )


def valid_citations(text: str, sources: list[SourceDocument]) -> set[str]:
    allowed = {source_id(source) for source in sources}
    return set(_CITATION_RE.findall(text)) & allowed
