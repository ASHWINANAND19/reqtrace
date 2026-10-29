"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.routers import admin, auth, inputs, projects, srs
from app.seed import seed_admin


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        seed_admin(db)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name, docs_url="/api/docs", openapi_url="/api/openapi.json", lifespan=lifespan
    )
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(projects.router)
    app.include_router(inputs.router)
    app.include_router(srs.router)

    @app.get("/api/health", tags=["system"])
    def health() -> dict:
        return {"status": "ok", "llm_provider": settings.llm_provider}

    return app


app = create_app()
