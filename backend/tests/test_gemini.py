from types import SimpleNamespace

import pytest

from app.agents.gemini import GeminiProvider
from app.agents.llm import LLMRequest, LLMUnavailableError


class FakeModels:
    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.calls = []

    def generate_content(self, model, contents, config):
        self.calls.append(model)
        outcome = self.outcomes[model]
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(text=outcome)


def provider(outcomes, models):
    p = GeminiProvider("test-key", models, 5)
    p.client = SimpleNamespace(models=FakeModels(outcomes))
    return p


REQUEST = LLMRequest(task="srs", system="s", prompt="p")


def test_first_model_answers():
    p = provider({"a": '{"ok": 1}'}, "a,b")
    assert p.generate(REQUEST) == '{"ok": 1}'
    assert p.client.models.calls == ["a"]


def test_falls_back_when_model_busy_or_retired():
    p = provider({"a": RuntimeError("404 no longer available"), "b": RuntimeError("503 busy"), "c": "{}"}, "a, b ,c")
    assert p.generate(REQUEST) == "{}"
    assert p.client.models.calls == ["a", "b", "c"]


def test_all_models_failing_is_unavailable():
    p = provider({"a": RuntimeError("503 busy")}, "a")
    with pytest.raises(LLMUnavailableError, match="503"):
        p.generate(REQUEST)


def test_missing_key_is_unavailable():
    with pytest.raises(LLMUnavailableError):
        GeminiProvider("", "a", 5)


def test_misconfigured_provider_returns_friendly_503(client, analyst):
    from app.agents.llm import get_llm

    def broken():
        raise LLMUnavailableError("GEMINI_API_KEY is not set")

    client.app.dependency_overrides[get_llm] = broken
    pid = client.post("/api/projects", json={"name": "P"}, headers=analyst).json()["id"]
    client.post(f"/api/projects/{pid}/inputs/text", json={"content": "The system shall work."}, headers=analyst)
    response = client.post(f"/api/projects/{pid}/srs/generate", headers=analyst)
    assert response.status_code == 503 and "work is saved" in response.json()["detail"]
