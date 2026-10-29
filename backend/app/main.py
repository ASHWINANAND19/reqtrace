"""FastAPI application entry point."""
from fastapi import FastAPI

from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, docs_url="/api/docs", openapi_url="/api/openapi.json")

    @app.get("/api/health", tags=["system"])
    def health() -> dict:
        return {"status": "ok", "llm_provider": settings.llm_provider}

    return app


app = create_app()
