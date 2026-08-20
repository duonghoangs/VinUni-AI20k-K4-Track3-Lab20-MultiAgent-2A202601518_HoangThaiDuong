"""LangGraph orchestration for the research agent team."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(
        self,
        supervisor: SupervisorAgent | None = None,
        researcher: ResearcherAgent | None = None,
        analyst: AnalystAgent | None = None,
        writer: WriterAgent | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.supervisor = supervisor or SupervisorAgent(self.settings)
        self.researcher = researcher or ResearcherAgent()
        self.analyst = analyst or AnalystAgent()
        self.writer = writer or WriterAgent()

    def build(self) -> Any:
        """Create and compile nodes, worker returns, conditional routing, and stop."""

        graph = StateGraph(ResearchState)
        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("researcher", self._researcher_node)
        graph.add_node("analyst", self._analyst_node)
        graph.add_node("writer", self._writer_node)
        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges(
            "supervisor",
            self._route,
            {"researcher": "researcher", "analyst": "analyst", "writer": "writer", "done": END},
        )
        graph.add_edge("researcher", "supervisor")
        graph.add_edge("analyst", "supervisor")
        graph.add_edge("writer", "supervisor")
        return graph.compile(name="multi-agent-research")

    def run(self, state: ResearchState) -> ResearchState:
        """Execute compiled graph with a bounded recursion guard."""

        try:
            result = self.build().invoke(
                state,
                config={"recursion_limit": self.settings.max_iterations * 3 + 3},
            )
        except Exception as exc:
            raise AgentExecutionError(f"Multi-agent workflow failed: {exc}") from exc
        return result if isinstance(result, ResearchState) else ResearchState.model_validate(result)

    def _supervisor_node(self, state: ResearchState) -> dict[str, Any]:
        return self.supervisor.run(state.model_copy(deep=True)).model_dump()

    def _researcher_node(self, state: ResearchState) -> dict[str, Any]:
        return self.researcher.run(state.model_copy(deep=True)).model_dump()

    def _analyst_node(self, state: ResearchState) -> dict[str, Any]:
        return self.analyst.run(state.model_copy(deep=True)).model_dump()

    def _writer_node(self, state: ResearchState) -> dict[str, Any]:
        return self.writer.run(state.model_copy(deep=True)).model_dump()

    @staticmethod
    def _route(state: ResearchState) -> str:
        return state.next_route or "done"
