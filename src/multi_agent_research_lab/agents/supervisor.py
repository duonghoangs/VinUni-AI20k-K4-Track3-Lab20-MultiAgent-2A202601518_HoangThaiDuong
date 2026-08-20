"""Deterministic supervisor and workflow guardrails."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def run(self, state: ResearchState) -> ResearchState:
        """Select next worker from explicit state completeness checks."""

        if state.final_answer:
            route = "done"
        elif state.iteration >= self.settings.max_iterations:
            route = "done"
            message = f"Stopped after max_iterations={self.settings.max_iterations}"
            if message not in state.errors:
                state.errors.append(message)
        elif not state.sources or not state.research_notes:
            route = "researcher"
        elif not state.analysis_notes:
            route = "analyst"
        else:
            route = "writer"

        state.record_route(route)
        state.agent_results.append(
            AgentResult(
                agent=AgentName.SUPERVISOR, content=route, metadata={"iteration": state.iteration}
            )
        )
        state.add_trace_event("route", {"next": route, "iteration": state.iteration})
        return state
