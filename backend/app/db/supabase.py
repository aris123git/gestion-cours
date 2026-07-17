"""Supabase client factory (service role — server only)."""

from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_supabase() -> Client:
    """Return a cached Supabase client using the service role key."""
    settings = get_settings()
    settings.require_supabase()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def sb() -> Client:
    """Shortcut used by route handlers and services."""
    return get_supabase()


def first_or_none(result: Any) -> dict | None:
    """Normalize PostgREST responses that return a list of rows."""
    data = getattr(result, "data", result)
    if not data:
        return None
    if isinstance(data, list):
        return data[0] if data else None
    return data
