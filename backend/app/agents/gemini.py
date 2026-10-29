"""Google Gemini provider (free tier)."""
import logging

from google import genai
from google.genai import types

from app.agents.llm import LLMRequest, LLMUnavailableError

log = logging.getLogger(__name__)


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, models: str, timeout_seconds: int):
        if not api_key:
            raise LLMUnavailableError("GEMINI_API_KEY is not set")
        # GEMINI_MODEL may list fallbacks, e.g. "gemini-3-flash-preview,gemini-3.1-flash-lite" (NFR-03)
        self.models = [m.strip() for m in models.split(",") if m.strip()]
        self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_seconds * 1000))

    def generate(self, request: LLMRequest) -> str:
        config = types.GenerateContentConfig(
            system_instruction=request.system,
            response_mime_type="application/json",
            response_schema=request.schema,
            temperature=0.1 if request.strict else 0.4,
        )
        last_error: Exception | None = None
        for model in self.models:
            try:
                response = self.client.models.generate_content(model=model, contents=request.prompt, config=config)
                return response.text or ""
            except Exception as exc:  # network, quota, model busy or retired: try the next model
                log.warning("gemini model %s failed: %s", model, str(exc)[:200])
                last_error = exc
        raise LLMUnavailableError(str(last_error))
