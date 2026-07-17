"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GestionCours API"
    app_version: str = "2.0.0"
    debug: bool = False

    # Supabase (replaces local PostgreSQL / SQLAlchemy)
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    # Optional anon key if you later call Supabase from the SPA
    supabase_anon_key: str = ""

    # JWT (student sessions issued by this API)
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12  # 12 hours

    # Admin sync API key (desktop application authenticates with this)
    admin_api_key: str = "desktop-admin-sync-key-change-me"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def require_supabase(self) -> None:
        if not self.supabase_url or not self.supabase_service_role_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. "
                "See supabase/README.md"
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
