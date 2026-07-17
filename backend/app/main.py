"""
GestionCours FastAPI application entrypoint.

Student portal API + desktop admin sync.
Interactive docs: /docs  |  OpenAPI JSON: /openapi.json
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, schedule
from app.core.config import get_settings
from app.db.session import Base, engine
from app.schemas import HealthResponse

# Import models so metadata is registered
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Create tables on startup (Alembic preferred in production)
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "REST API for the GestionCours hybrid timetable system. "
            "Students authenticate with student number + password. "
            "The Windows desktop app syncs schedules via `POST /sync` using `X-API-Key`."
        ),
        lifespan=lifespan,
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
