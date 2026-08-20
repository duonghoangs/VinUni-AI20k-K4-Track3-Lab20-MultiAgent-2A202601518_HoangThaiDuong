"""OpenRouter client implemented through the OpenAI-compatible SDK."""

from dataclasses import dataclass
from time import sleep
from typing import Any

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    retries: int = 0


class LLMClient:
    """Small OpenRouter client with bounded retry, timeout, and usage accounting."""

    def __init__(self, settings: Settings | None = None, client: Any | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = client
        if self._client is None and self.settings.openrouter_api_key:
            from openai import OpenAI

            headers = {"X-OpenRouter-Title": self.settings.openrouter_app_name}
            if self.settings.openrouter_site_url:
                headers["HTTP-Referer"] = self.settings.openrouter_site_url
            self._client = OpenAI(
                api_key=self.settings.openrouter_api_key,
                base_url=self.settings.openrouter_base_url,
                default_headers=headers,
                timeout=float(self.settings.timeout_seconds),
                max_retries=0,
            )

    @property
    def available(self) -> bool:
        """Return whether a provider client is configured."""

        return self._client is not None

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return one completion, retrying transient provider failures."""

        if self._client is None:
            raise AgentExecutionError(
                "OPENROUTER_API_KEY is not configured; use the built-in offline fallback"
            )

        last_error: Exception | None = None
        for attempt in range(self.settings.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.settings.openrouter_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = str(response.choices[0].message.content or "").strip()
                if not content:
                    raise ValueError("OpenRouter returned an empty response")
                usage = getattr(response, "usage", None)
                input_tokens = getattr(usage, "prompt_tokens", None)
                output_tokens = getattr(usage, "completion_tokens", None)
                cost = self._estimate_cost(input_tokens, output_tokens)
                return LLMResponse(content, input_tokens, output_tokens, cost, retries=attempt)
            except Exception as exc:  # provider SDK exposes several transient error classes
                last_error = exc
                if attempt < self.settings.max_retries:
                    sleep(min(2**attempt, 4))

        message = str(last_error) if last_error else "unknown provider error"
        raise AgentExecutionError(f"LLM request failed: {message}") from last_error

    def _estimate_cost(self, input_tokens: int | None, output_tokens: int | None) -> float | None:
        if input_tokens is None and output_tokens is None:
            return None
        input_cost = (input_tokens or 0) * self.settings.openrouter_input_cost_per_million
        output_cost = (output_tokens or 0) * self.settings.openrouter_output_cost_per_million
        return (input_cost + output_cost) / 1_000_000
