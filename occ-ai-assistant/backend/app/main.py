"""OCC AI Assistant FastAPI application — Phase 2."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.routers import analysis, dashboard, health, incidents, teams
from app.seed import seed_if_empty


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        inserted = seed_if_empty(db)
        if inserted:
            print(f"Seeded {inserted} MOCK sample incidents")
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        description="Enterprise OCC incident & bridge platform (Phase 2 — AI analysis)",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    prefix = settings.api_prefix
    application.include_router(health.router, prefix=prefix)
    application.include_router(incidents.router, prefix=prefix)
    application.include_router(analysis.router, prefix=prefix)
    application.include_router(teams.router, prefix=prefix)
    application.include_router(dashboard.router, prefix=prefix)
    return application


app = create_app()
