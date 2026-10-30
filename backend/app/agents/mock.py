"""Offline providers: a deterministic mock for tests and demos without a key, and an always-failing one
for demonstrating LLM-outage handling (TC-45)."""
import json
from collections.abc import Callable
from typing import Any

from app.agents.llm import LLMRequest, LLMUnavailableError

MockBuilder = Callable[[dict[str, Any]], dict[str, Any]]
_BUILDERS: dict[str, MockBuilder] = {}


def register_mock(task: str) -> Callable[[MockBuilder], MockBuilder]:
    """Each agent module registers how the mock answers its task, next to the agent itself."""

    def decorator(builder: MockBuilder) -> MockBuilder:
        _BUILDERS[task] = builder
        return builder

    return decorator


class MockProvider:
    name = "mock"

    def generate(self, request: LLMRequest) -> str:
        builder = _BUILDERS.get(request.task)
        if builder is None:
            raise LLMUnavailableError(f"mock provider has no answer for task '{request.task}'")
        return json.dumps(builder(request.payload))


class OfflineProvider:
    name = "offline"

    def generate(self, request: LLMRequest) -> str:
        raise LLMUnavailableError("LLM provider is offline")
