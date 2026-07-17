"""Student-facing schedule and profile endpoints."""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_student
from app.db.session import get_db
from app.models import Filiere, Notification, Schedule, Student
from app.schemas import FiliereOut, NotificationOut, ScheduleOut, StudentOut

router = APIRouter(tags=["Student"])


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _schedule_to_out(row: Schedule) -> ScheduleOut:
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


@router.get("/student", response_model=StudentOut)
def get_student(current: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    """Return the authenticated student's profile."""
    student = (
        db.query(Student)
        .options(joinedload(Student.filiere))
        .filter(Student.id == current.id)
        .first()
    )
    return StudentOut(
        id=student.id,
        student_number=student.student_number,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email,
        filiere_id=student.filiere_id,
        level=student.level,
        filiere_name=student.filiere.name if student.filiere else None,
        created_at=student.created_at,
    )


@router.get("/schedule", response_model=list[ScheduleOut])
def get_schedule(
    week: Optional[date] = Query(None, description="Any date in the target week (defaults to current week)"),
    filiere_id: Optional[int] = Query(None),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search subject / teacher / room"),
    current: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Return schedule entries for a week.
    Defaults to the student's filière and the current week.
    """
    week_date = _monday_of(week or date.today())
    q = (
        db.query(Schedule)
        .options(joinedload(Schedule.filiere))
        .filter(Schedule.week_date == week_date)
    )

    target_filiere = filiere_id or current.filiere_id
    q = q.filter(Schedule.filiere_id == target_filiere)

    if level:
        q = q.join(Filiere).filter(Filiere.level == level)

    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            (Schedule.subject.ilike(like))
            | (Schedule.teacher.ilike(like))
            | (Schedule.room.ilike(like))
        )

    rows = q.order_by(Schedule.day, Schedule.start_time).all()
    return [_schedule_to_out(r) for r in rows]


@router.get("/schedule/week/{week_date}", response_model=list[ScheduleOut])
def get_schedule_week(
    week_date: date,
    filiere_id: Optional[int] = Query(None),
    current: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Return schedule for the week starting on (or containing) `week_date`."""
    monday = _monday_of(week_date)
    target = filiere_id or current.filiere_id
    rows = (
        db.query(Schedule)
        .options(joinedload(Schedule.filiere))
        .filter(Schedule.week_date == monday, Schedule.filiere_id == target)
        .order_by(Schedule.day, Schedule.start_time)
        .all()
    )
    return [_schedule_to_out(r) for r in rows]


@router.get("/notifications", response_model=list[NotificationOut])
def get_notifications(
    unread_only: bool = Query(False),
    current: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """List notifications for the authenticated student."""
    q = db.query(Notification).filter(Notification.student_id == current.id)
    if unread_only:
        q = q.filter(Notification.is_read.is_(False))
    rows = q.order_by(Notification.created_at.desc()).limit(50).all()
    return rows


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    current: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.student_id == current.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.get("/filieres", response_model=list[FiliereOut])
def list_filieres(
    level: Optional[str] = Query(None),
    current: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """List programmes (filières), optionally filtered by level."""
    q = db.query(Filiere)
    if level:
        q = q.filter(Filiere.level == level)
    return q.order_by(Filiere.level, Filiere.name).all()
