"""Admin / desktop sync endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_admin_api_key
from app.db.supabase import first_or_none, sb
from app.models import date_str, parse_date, parse_datetime, parse_time, time_str
from app.schemas import ScheduleCreate, ScheduleOut, ScheduleUpdate, SyncPayload, SyncResult
from app.services.sync import apply_sync

router = APIRouter(prefix="/admin", tags=["Admin Sync"], dependencies=[Depends(require_admin_api_key)])


def _to_out(row: dict[str, Any]) -> ScheduleOut:
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


@router.post("/sync", response_model=SyncResult)
def sync_timetable(payload: SyncPayload):
    """
    Full sync from the desktop application.
    Uploads new schedules, updates modified ones, deletes removed ones.
    Uses desktop_id to avoid duplicates.
    """
    return apply_sync(payload)


# Also expose at /sync as requested in the API spec
sync_router = APIRouter(tags=["Admin Sync"], dependencies=[Depends(require_admin_api_key)])


@sync_router.post("/sync", response_model=SyncResult)
def sync_timetable_root(payload: SyncPayload):
    return apply_sync(payload)


@sync_router.put("/schedule", response_model=ScheduleOut)
def upsert_schedule(body: ScheduleCreate):
    """Create or update a single schedule entry (admin)."""
    result = apply_sync(
        SyncPayload(schedules=[body], notify_students=True),
    )
    if result.conflicts and not (result.created or result.updated):
        raise HTTPException(status_code=409, detail=result.conflicts[0].reason)

    row = None
    if body.desktop_id is not None:
        row = first_or_none(
            sb()
            .table("schedule")
            .select("*, filieres(name, level)")
            .eq("desktop_id", body.desktop_id)
            .limit(1)
            .execute()
        )
    if not row:
        raise HTTPException(status_code=500, detail="Schedule upsert failed")
    return _to_out(row)


@sync_router.delete("/schedule/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int):
    """Delete a schedule by server id."""
    existing = first_or_none(
        sb().table("schedule").select("id").eq("id", schedule_id).limit(1).execute()
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Schedule not found")
    sb().table("schedule").delete().eq("id", schedule_id).execute()
    return None


@sync_router.patch("/schedule/{schedule_id}", response_model=ScheduleOut)
def patch_schedule(schedule_id: int, body: ScheduleUpdate):
    existing = first_or_none(
        sb()
        .table("schedule")
        .select("*, filieres(name, level)")
        .eq("id", schedule_id)
        .limit(1)
        .execute()
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Schedule not found")

    patch: dict[str, Any] = {}
    for field, value in body.model_dump(exclude_unset=True).items():
        if field in ("start_time", "end_time"):
            patch[field] = time_str(value)
        elif field == "week_date":
            patch[field] = date_str(value)
        else:
            patch[field] = value

    if patch:
        sb().table("schedule").update(patch).eq("id", schedule_id).execute()

    row = first_or_none(
        sb()
        .table("schedule")
        .select("*, filieres(name, level)")
        .eq("id", schedule_id)
        .limit(1)
        .execute()
    )
    return _to_out(row)
