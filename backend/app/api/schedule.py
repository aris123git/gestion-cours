"""Student-facing schedule and profile endpoints."""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_student
from app.db.supabase import first_or_none, sb
from app.models import StudentRow, parse_date, parse_datetime, parse_time
from app.schemas import FiliereOut, NotificationOut, ScheduleOut, StudentOut

router = APIRouter(tags=["Student"])


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _schedule_to_out(row: dict[str, Any]) -> ScheduleOut:
    filiere = row.get("filieres") or {}
    if isinstance(filiere, list):
        filiere = filiere[0] if filiere else {}
    return ScheduleOut(
        id=int(row["id"]),
        desktop_id=row.get("desktop_id"),
        filiere_id=int(row["filiere_id"]),
        day=row["day"],
        start_time=parse_time(row["start_time"]),
        end_time=parse_time(row["end_time"]),
        subject=row["subject"],
        teacher=row["teacher"],
        room=row.get("room"),
        group_tc=row.get("group_tc"),
        week_date=parse_date(row["week_date"]),
        updated_at=parse_datetime(row.get("updated_at")),
        filiere_name=filiere.get("name") if filiere else None,
        filiere_level=filiere.get("level") if filiere else None,
    )


@router.get("/student", response_model=StudentOut)
def get_student(current: StudentRow = Depends(get_current_student)):
    """Return the authenticated student's profile."""
    return StudentOut(
        id=current.id,
        student_number=current.student_number,
        first_name=current.first_name,
        last_name=current.last_name,
        email=current.email,
        filiere_id=current.filiere_id,
        level=current.level,
        filiere_name=current.filiere_name,
        created_at=current.created_at,
    )


@router.get("/schedule", response_model=list[ScheduleOut])
def get_schedule(
    week: Optional[date] = Query(None, description="Any date in the target week (defaults to current week)"),
    filiere_id: Optional[int] = Query(None),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search subject / teacher / room"),
    current: StudentRow = Depends(get_current_student),
):
    """
    Return schedule entries for a week.
    Defaults to the student's filière and the current week.
    """
    week_date = _monday_of(week or date.today())
    target_filiere = filiere_id or current.filiere_id

    query = (
        sb()
        .table("schedule")
        .select("*, filieres(name, level)")
        .eq("week_date", week_date.isoformat())
        .eq("filiere_id", target_filiere)
    )

    if level:
        # Filter via embedded filiere — fetch then filter in Python for simplicity
        rows = query.order("day").order("start_time").execute().data or []
        rows = [r for r in rows if (r.get("filieres") or {}).get("level") == level]
    else:
        rows = query.order("day").order("start_time").execute().data or []

    if search:
        needle = search.strip().lower()
        rows = [
            r
            for r in rows
            if needle in (r.get("subject") or "").lower()
            or needle in (r.get("teacher") or "").lower()
            or needle in (r.get("room") or "").lower()
        ]

    return [_schedule_to_out(r) for r in rows]


@router.get("/schedule/week/{week_date}", response_model=list[ScheduleOut])
def get_schedule_week(
    week_date: date,
    filiere_id: Optional[int] = Query(None),
    current: StudentRow = Depends(get_current_student),
):
    """Return schedule for the week starting on (or containing) `week_date`."""
    monday = _monday_of(week_date)
    target = filiere_id or current.filiere_id
    rows = (
        sb()
        .table("schedule")
        .select("*, filieres(name, level)")
        .eq("week_date", monday.isoformat())
        .eq("filiere_id", target)
        .order("day")
        .order("start_time")
        .execute()
        .data
        or []
    )
    return [_schedule_to_out(r) for r in rows]


@router.get("/notifications", response_model=list[NotificationOut])
def get_notifications(
    unread_only: bool = Query(False),
    current: StudentRow = Depends(get_current_student),
):
    """List notifications for the authenticated student."""
    query = sb().table("notifications").select("*").eq("student_id", current.id)
    if unread_only:
        query = query.eq("is_read", False)
    rows = query.order("created_at", desc=True).limit(50).execute().data or []
    return [
        NotificationOut(
            id=int(r["id"]),
            title=r["title"],
            message=r["message"],
            is_read=bool(r["is_read"]),
            created_at=parse_datetime(r["created_at"]),
            filiere_id=r.get("filiere_id"),
        )
        for r in rows
    ]


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    current: StudentRow = Depends(get_current_student),
):
    result = (
        sb()
        .table("notifications")
        .update({"is_read": True})
        .eq("id", notification_id)
        .eq("student_id", current.id)
        .execute()
    )
    row = first_or_none(result)
    if not row:
        # Confirm it doesn't exist / wrong owner
        existing = (
            sb()
            .table("notifications")
            .select("id")
            .eq("id", notification_id)
            .eq("student_id", current.id)
            .limit(1)
            .execute()
        )
        if not first_or_none(existing):
            raise HTTPException(status_code=404, detail="Notification not found")
        row = first_or_none(
            sb().table("notifications").select("*").eq("id", notification_id).limit(1).execute()
        )
    return NotificationOut(
        id=int(row["id"]),
        title=row["title"],
        message=row["message"],
        is_read=bool(row["is_read"]),
        created_at=parse_datetime(row["created_at"]),
        filiere_id=row.get("filiere_id"),
    )


@router.get("/filieres", response_model=list[FiliereOut])
def list_filieres(
    level: Optional[str] = Query(None),
    current: StudentRow = Depends(get_current_student),
):
    """List programmes (filières), optionally filtered by level."""
    query = sb().table("filieres").select("id, name, level")
    if level:
        query = query.eq("level", level)
    rows = query.order("level").order("name").execute().data or []
    return [FiliereOut(id=int(r["id"]), name=r["name"], level=r["level"]) for r in rows]
