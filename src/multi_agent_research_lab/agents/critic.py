"""Optional deterministic citation critic."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.agents.support import valid_citations
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Audit whether final answer contains citations from retrieved evidence."""

        citations = valid_citations(state.final_answer or "", state.sources)
        if not state.final_answer:
            finding = "Final answer is missing."
        elif not citations:
            finding = "Final answer has no valid citations."
            state.errors.append(finding)
        else:
            finding = f"Citation audit passed with {len(citations)} distinct source IDs."
        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=finding,
                metadata={"valid_citations": sorted(citations)},
            )
        )
        state.add_trace_event("critic", {"finding": finding})
        return state
