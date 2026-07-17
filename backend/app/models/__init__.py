"""Lightweight row helpers for Supabase JSON responses (no SQLAlchemy)."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Optional


def parse_time(value: Any) -> Optional[time]:
    if value is None:
        return None
    if isinstance(value, time):
        return value
    text = str(value)
    if len(text) == 5:
        text = f"{text}:00"
    return time.fromisoformat(text)


def parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value)[:10])


def parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def time_str(value: time | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value if len(value) > 5 else f"{value}:00"
    return value.strftime("%H:%M:%S")


def date_str(value: date | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value[:10]
    return value.isoformat()


class StudentRow:
    """Minimal student object used by auth dependencies."""

    def __init__(self, data: dict[str, Any]):
        self.id = int(data["id"])
        self.student_number = data["student_number"]
        self.first_name = data["first_name"]
        self.last_name = data["last_name"]
        self.email = data["email"]
        self.password_hash = data["password_hash"]
        self.filiere_id = int(data["filiere_id"])
        self.level = data["level"]
        self.created_at = parse_datetime(data.get("created_at"))
        filiere = data.get("filieres") or data.get("filiere")
        if isinstance(filiere, list):
            filiere = filiere[0] if filiere else None
        self.filiere_name = filiere.get("name") if isinstance(filiere, dict) else None
        self.filiere_level = filiere.get("level") if isinstance(filiere, dict) else None
