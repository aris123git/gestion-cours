"""FastAPI authentication dependencies."""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.supabase import first_or_none, sb
from app.models import StudentRow

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_student(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> StudentRow:
    """Require a valid student JWT."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    result = (
        sb()
        .table("students")
        .select("*, filieres(name, level)")
        .eq("id", int(payload["sub"]))
        .limit(1)
        .execute()
    )
    row = first_or_none(result)
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Student not found")
    return StudentRow(row)


def require_admin_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> str:
    """Require the desktop admin API key for sync / admin endpoints."""
    settings = get_settings()
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin API key")
    return x_api_key
