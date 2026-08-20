from multi_agent_research_lab.cli import doctor_status
from multi_agent_research_lab.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.openrouter_model.startswith("openai/")
    assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert settings.max_iterations >= 1


def test_doctor_reports_offline_readiness() -> None:
    status = doctor_status()
    assert status["Model"].startswith("openai/")
    assert status["Offline corpus"].startswith("ready")
    assert "sk-" not in " ".join(status.values())
