from types import SimpleNamespace

from multi_agent_research_lab.agents import (
    AnalystAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.cli import run_baseline_query
from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class FakeCompletions:
    def create(self, **_: object) -> SimpleNamespace:
        return SimpleNamespace(
            choices=[
                SimpleNamespace(message=SimpleNamespace(content="Grounded response [autogen]"))
            ],
            usage=SimpleNamespace(prompt_tokens=20, completion_tokens=10),
        )


def test_supervisor_routes_by_missing_state() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = SupervisorAgent(Settings(max_iterations=6)).run(state)
    assert result.next_route == "researcher"
    assert result.route_history == ["researcher"]


def test_supervisor_stops_at_iteration_limit() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain multi-agent systems"),
        iteration=1,
    )
    result = SupervisorAgent(Settings(max_iterations=1)).run(state)
    assert result.next_route == "done"
    assert result.errors == ["Stopped after max_iterations=1"]


def test_search_returns_ranked_offline_sources() -> None:
    sources = SearchClient().search("single agent versus multi agent architecture", 3)
    assert len(sources) == 3
    assert all(source.metadata.get("source_id") for source in sources)
    assert any("agent" in source.title.lower() for source in sources)
    assert all(
        source.metadata.get("document_class") == "public_reference_summary" for source in sources
    )


def test_llm_client_records_usage_and_cost() -> None:
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    settings = Settings(
        max_retries=0,
        openrouter_input_cost_per_million=1.0,
        openrouter_output_cost_per_million=2.0,
    )
    response = LLMClient(settings, fake_client).complete("system", "user")
    assert response.input_tokens == 20
    assert response.output_tokens == 10
    assert response.cost_usd == 0.00004


def test_baseline_runs_without_api_key() -> None:
    state = run_baseline_query(
        "Compare single-agent and multi-agent systems",
        llm_client=LLMClient(Settings(openrouter_api_key=None)),
    )
    assert state.final_answer
    assert state.sources
    assert state.trace[0]["name"] == "baseline"


def test_workflow_runs_end_to_end_offline() -> None:
    offline_llm = LLMClient(Settings(openrouter_api_key=None))
    workflow = MultiAgentWorkflow(
        researcher=ResearcherAgent(llm_client=offline_llm),
        analyst=AnalystAgent(llm_client=offline_llm),
        writer=WriterAgent(llm_client=offline_llm),
    )
    result = workflow.run(
        ResearchState(request=ResearchQuery(query="Compare agent coordination strategies"))
    )
    assert result.final_answer
    assert result.route_history == ["researcher", "analyst", "writer", "done"]
    assert result.sources
    assert not result.errors
