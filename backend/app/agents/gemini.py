"""Google Gemini provider (free tier). Network-bound, so it is mocked in automated tests."""
from google import genai
from google.genai import types

from app.agents.llm import LLMRequest, LLMUnavailableError


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout_seconds: int):
        if not api_key:
            raise LLMUnavailableError("GEMINI_API_KEY is not set")
        self.model = model
        self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_seconds * 1000))

    def generate(self, request: LLMRequest) -> str:
        config = types.GenerateContentConfig(
            system_instruction=request.system,
            response_mime_type="application/json",
            response_schema=request.schema,
            temperature=0.1 if request.strict else 0.4,
        )
        try:
            response = self.client.models.generate_content(
                model=self.model, contents=request.prompt, config=config
            )
        except Exception as exc:  # network, quota, auth: all mean "unavailable" to the caller
            raise LLMUnavailableError(str(exc)) from exc
        return response.text or ""
