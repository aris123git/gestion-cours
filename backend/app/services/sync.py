"""Schedule sync service — upsert / delete without duplicates."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Course, Filiere, Notification, Room, Schedule, Student, Teacher
from app.schemas import ScheduleCreate, SyncConflict, SyncPayload, SyncResult


def _resolve_filiere_id(db: Session, item: ScheduleCreate) -> int | None:
    if item.filiere_id:
        return item.filiere_id
    if item.filiere_desktop_id is not None:
        filiere = db.query(Filiere).filter(Filiere.desktop_id == item.filiere_desktop_id).first()
        return filiere.id if filiere else None
    return None


def upsert_filieres(db: Session, items: list) -> int:
    count = 0
    for item in items:
        existing = db.query(Filiere).filter(Filiere.desktop_id == item.desktop_id).first()
        if existing:
            existing.name = item.name
            existing.level = item.level
        else:
            # Avoid unique constraint clash on (name, level)
            by_name = (
                db.query(Filiere)
                .filter(Filiere.name == item.name, Filiere.level == item.level)
                .first()
            )
            if by_name:
                by_name.desktop_id = item.desktop_id
            else:
                db.add(Filiere(desktop_id=item.desktop_id, name=item.name, level=item.level))
        count += 1
    db.flush()
    return count


def upsert_rooms(db: Session, items: list) -> int:
    count = 0
    for item in items:
        existing = db.query(Room).filter(Room.desktop_id == item.desktop_id).first()
        if existing:
            existing.name = item.name
            existing.capacity = item.capacity
        else:
            by_name = db.query(Room).filter(Room.name == item.name).first()
            if by_name:
                by_name.desktop_id = item.desktop_id
                by_name.capacity = item.capacity
            else:
                db.add(Room(desktop_id=item.desktop_id, name=item.name, capacity=item.capacity))
        count += 1
    db.flush()
    return count


def _ensure_teacher_and_course(
    db: Session,
    subject: str,
    teacher: str,
    seen_subjects: set[str],
    seen_teachers: set[str],
) -> None:
    if subject and subject not in seen_subjects:
        if not db.query(Course).filter(Course.subject == subject).first():
            db.add(Course(subject=subject))
            db.flush()
        seen_subjects.add(subject)
    if teacher and teacher not in seen_teachers:
        if not db.query(Teacher).filter(Teacher.name == teacher).first():
            db.add(Teacher(name=teacher))
            db.flush()
        seen_teachers.add(teacher)


def apply_sync(db: Session, payload: SyncPayload) -> SyncResult:
    """
    Apply a desktop sync payload:
    - Upsert filieres / rooms
    - Create or update schedules by desktop_id (never duplicates)
    - Delete schedules listed in deleted_desktop_ids
    - Detect conflicts when server copy is newer than client
    """
    result = SyncResult()
    try:
        result.filieres_upserted = upsert_filieres(db, payload.filieres)
        result.rooms_upserted = upsert_rooms(db, payload.rooms)

        affected_filiere_ids: set[int] = set()
        seen_subjects: set[str] = set()
        seen_teachers: set[str] = set()

        for item in payload.schedules:
            filiere_id = _resolve_filiere_id(db, item)
            if filiere_id is None:
                result.conflicts.append(
                    SyncConflict(
                        desktop_id=item.desktop_id or 0,
                        reason="Unknown filière (desktop_id not found on server)",
                    )
                )
                continue

            _ensure_teacher_and_course(
                db, item.subject, item.teacher, seen_subjects, seen_teachers
            )
            affected_filiere_ids.add(filiere_id)

            existing: Schedule | None = None
            if item.desktop_id is not None:
                existing = db.query(Schedule).filter(Schedule.desktop_id == item.desktop_id).first()

            if existing:
                # Conflict detection: server newer than client
                if item.updated_at and existing.updated_at:
                    server_ts = existing.updated_at
                    if server_ts.tzinfo is None:
                        server_ts = server_ts.replace(tzinfo=timezone.utc)
                    client_ts = item.updated_at
                    if client_ts.tzinfo is None:
                        client_ts = client_ts.replace(tzinfo=timezone.utc)
                    if server_ts > client_ts:
                        result.conflicts.append(
                            SyncConflict(
                                desktop_id=item.desktop_id or 0,
                                reason="Server version is newer; client data skipped",
                                server_updated_at=existing.updated_at,
                                client_updated_at=item.updated_at,
                            )
                        )
                        continue

                existing.filiere_id = filiere_id
                existing.day = item.day
                existing.start_time = item.start_time
                existing.end_time = item.end_time
                existing.subject = item.subject
                existing.teacher = item.teacher
                existing.room = item.room
                existing.group_tc = item.group_tc
                existing.week_date = item.week_date
                existing.updated_at = datetime.now(timezone.utc)
                result.updated += 1
            else:
                db.add(
                    Schedule(
                        desktop_id=item.desktop_id,
                        filiere_id=filiere_id,
                        day=item.day,
                        start_time=item.start_time,
                        end_time=item.end_time,
                        subject=item.subject,
                        teacher=item.teacher,
                        room=item.room,
                        group_tc=item.group_tc,
                        week_date=item.week_date,
                    )
                )
                result.created += 1

        if payload.deleted_desktop_ids:
            to_delete = (
                db.query(Schedule)
                .filter(Schedule.desktop_id.in_(payload.deleted_desktop_ids))
                .all()
            )
            for row in to_delete:
                affected_filiere_ids.add(row.filiere_id)
                db.delete(row)
                result.deleted += 1

        if payload.notify_students and (result.created or result.updated or result.deleted):
            for fid in affected_filiere_ids:
                filiere = db.query(Filiere).filter(Filiere.id == fid).first()
                label = f"{filiere.level} — {filiere.name}" if filiere else str(fid)
                students = db.query(Student).filter(Student.filiere_id == fid).all()
                for student in students:
                    db.add(
                        Notification(
                            student_id=student.id,
                            filiere_id=fid,
                            title="Emploi du temps mis à jour",
                            message=f"L'emploi du temps de {label} a été modifié. Consultez votre planning.",
                        )
                    )

        db.commit()
        result.message = (
            f"Sync OK — created={result.created}, updated={result.updated}, "
            f"deleted={result.deleted}, conflicts={len(result.conflicts)}"
        )
        return result
    except Exception:
        db.rollback()
        raise
