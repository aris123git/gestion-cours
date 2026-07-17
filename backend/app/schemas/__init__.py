"""Pydantic request/response schemas."""

from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth ----------

class LoginRequest(BaseModel):
    student_number: str = Field(..., min_length=1, max_length=40)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    student_number: str = Field(..., min_length=1, max_length=40)
    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    filiere_id: int
    level: str = Field(..., min_length=1, max_length=40)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_number: str
    first_name: str
    last_name: str
    email: EmailStr
    filiere_id: int
    level: str
    filiere_name: Optional[str] = None
    created_at: Optional[datetime] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: StudentOut


# ---------- Filieres ----------

class FiliereOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    level: str


class FiliereSyncIn(BaseModel):
    desktop_id: int
    name: str
    level: str


# ---------- Schedule ----------

class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    desktop_id: Optional[int] = None
    filiere_id: int
    day: str
    start_time: time
    end_time: time
    subject: str
    teacher: str
    room: Optional[str] = None
    group_tc: Optional[str] = None
    week_date: date
    updated_at: Optional[datetime] = None
    filiere_name: Optional[str] = None
    filiere_level: Optional[str] = None


class ScheduleCreate(BaseModel):
    desktop_id: Optional[int] = None
    filiere_id: Optional[int] = None
    filiere_desktop_id: Optional[int] = None
    day: str
    start_time: time
    end_time: time
    subject: str
    teacher: str
    room: Optional[str] = None
    group_tc: Optional[str] = None
    week_date: date
    updated_at: Optional[datetime] = None


class ScheduleUpdate(BaseModel):
    day: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    subject: Optional[str] = None
    teacher: Optional[str] = None
    room: Optional[str] = None
    group_tc: Optional[str] = None
    week_date: Optional[date] = None
    filiere_id: Optional[int] = None
    updated_at: Optional[datetime] = None


# ---------- Sync ----------

class RoomSyncIn(BaseModel):
    desktop_id: int
    name: str
    capacity: int = 0


class SyncPayload(BaseModel):
    """Full sync payload sent by the desktop application."""

    filieres: list[FiliereSyncIn] = []
    rooms: list[RoomSyncIn] = []
    schedules: list[ScheduleCreate] = []
    deleted_desktop_ids: list[int] = []
    notify_students: bool = True


class SyncConflict(BaseModel):
    desktop_id: int
    reason: str
    server_updated_at: Optional[datetime] = None
    client_updated_at: Optional[datetime] = None


class SyncResult(BaseModel):
    created: int = 0
    updated: int = 0
    deleted: int = 0
    filieres_upserted: int = 0
    rooms_upserted: int = 0
    conflicts: list[SyncConflict] = []
    message: str = "Sync completed"


# ---------- Notifications ----------

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime
    filiere_id: Optional[int] = None


# ---------- Meta ----------

class HealthResponse(BaseModel):
    status: str
    version: str
