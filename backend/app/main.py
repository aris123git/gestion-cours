"""
GestionCours FastAPI application entrypoint.

Student portal API + desktop admin sync, backed by Supabase.
Interactive docs: /docs  |  OpenAPI JSON: /openapi.json
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, schedule
from app.core.config import get_settings
from app.schemas import HealthResponse


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "REST API for the GestionCours hybrid timetable system. "
            "Data is stored in Supabase. Students authenticate with student number + password. "
            "The Windows desktop app syncs schedules via `POST /sync` using `X-API-Key`."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(auth.router)
    application.include_router(schedule.router)
    application.include_router(admin.router)
    application.include_router(admin.sync_router)

    @application.get("/health", response_model=HealthResponse, tags=["Meta"])
    def health():
        return HealthResponse(status="ok", version=settings.app_version)

    return application


app = create_app()
