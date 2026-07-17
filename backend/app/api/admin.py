"""Admin / desktop sync endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_admin_api_key
from app.db.session import get_db
from app.models import Schedule
from app.schemas import ScheduleCreate, ScheduleOut, ScheduleUpdate, SyncPayload, SyncResult
from app.services.sync import apply_sync

router = APIRouter(prefix="/admin", tags=["Admin Sync"], dependencies=[Depends(require_admin_api_key)])


def _to_out(row: Schedule) -> ScheduleOut:
    return ScheduleOut(
        id=row.id,
        desktop_id=row.desktop_id,
        filiere_id=row.filiere_id,
        day=row.day,
        start_time=row.start_time,
        end_time=row.end_time,
        subject=row.subject,
        teacher=row.teacher,
        room=row.room,
        group_tc=row.group_tc,
        week_date=row.week_date,
        updated_at=row.updated_at,
        filiere_name=row.filiere.name if row.filiere else None,
        filiere_level=row.filiere.level if row.filiere else None,
    )


@router.post("/sync", response_model=SyncResult)
def sync_timetable(payload: SyncPayload, db: Session = Depends(get_db)):
    """
    Full sync from the desktop application.
    Uploads new schedules, updates modified ones, deletes removed ones.
    Uses desktop_id to avoid duplicates.
    """
    return apply_sync(db, payload)


# Also expose at /sync as requested in the API spec
sync_router = APIRouter(tags=["Admin Sync"], dependencies=[Depends(require_admin_api_key)])


@sync_router.post("/sync", response_model=SyncResult)
def sync_timetable_root(payload: SyncPayload, db: Session = Depends(get_db)):
    return apply_sync(db, payload)


@sync_router.put("/schedule", response_model=ScheduleOut)
def upsert_schedule(body: ScheduleCreate, db: Session = Depends(get_db)):
    """Create or update a single schedule entry (admin)."""
    result = apply_sync(
        db,
        SyncPayload(schedules=[body], notify_students=True),
    )
    if result.conflicts and not (result.created or result.updated):
        raise HTTPException(status_code=409, detail=result.conflicts[0].reason)

    row = None
    if body.desktop_id is not None:
        row = (
            db.query(Schedule)
            .options(joinedload(Schedule.filiere))
            .filter(Schedule.desktop_id == body.desktop_id)
            .first()
        )
    if not row:
        raise HTTPException(status_code=500, detail="Schedule upsert failed")
    return _to_out(row)


@sync_router.delete("/schedule/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Delete a schedule by server id."""
    row = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(row)
    db.commit()
    return None


@sync_router.patch("/schedule/{schedule_id}", response_model=ScheduleOut)
def patch_schedule(schedule_id: int, body: ScheduleUpdate, db: Session = Depends(get_db)):
    row = (
        db.query(Schedule)
        .options(joinedload(Schedule.filiere))
        .filter(Schedule.id == schedule_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Schedule not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return _to_out(row)
