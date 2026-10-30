"""LLM adapter interface (SAD AD-2). Agents talk to a provider only through this module."""
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Protocol

from pydantic import BaseModel

from app.config import get_settings


class LLMUnavailableError(Exception):
    """The provider could not be reached or returned an error."""


@dataclass
class LLMRequest:
    task: str
    system: str
    prompt: str
    schema: type[BaseModel] | None = None
    # Structured copy of the agent input. Real providers ignore it; the offline mock builds its answer from it.
    payload: dict[str, Any] = field(default_factory=dict)
    strict: bool = False


class LLMProvider(Protocol):
    name: str

    def generate(self, request: LLMRequest) -> str:
        """Return the model's raw text (expected to be JSON)."""
        ...


@lru_cache
def _provider(kind: str) -> LLMProvider:
    settings = get_settings()
    if kind == "gemini":
        from app.agents.gemini import GeminiProvider

        return GeminiProvider(settings.gemini_api_key, settings.gemini_model, settings.llm_timeout_seconds)
    from app.agents.mock import MockProvider, OfflineProvider

    return OfflineProvider() if kind == "offline" else MockProvider()


def get_llm() -> LLMProvider:
    """FastAPI dependency; tests override it with fakes."""
    return _provider(get_settings().llm_provider)
