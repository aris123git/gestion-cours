"""Schedule sync service — upsert / delete without duplicates (Supabase)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db.supabase import first_or_none, sb
from app.models import date_str, parse_datetime, time_str
from app.schemas import ScheduleCreate, SyncConflict, SyncPayload, SyncResult


def _resolve_filiere_id(item: ScheduleCreate) -> int | None:
    if item.filiere_id:
        return item.filiere_id
    if item.filiere_desktop_id is not None:
        row = first_or_none(
            sb()
            .table("filieres")
            .select("id")
            .eq("desktop_id", item.filiere_desktop_id)
            .limit(1)
            .execute()
        )
        return int(row["id"]) if row else None
    return None


def upsert_filieres(items: list) -> int:
    count = 0
    for item in items:
        existing = first_or_none(
            sb().table("filieres").select("*").eq("desktop_id", item.desktop_id).limit(1).execute()
        )
        if existing:
            sb().table("filieres").update({"name": item.name, "level": item.level}).eq(
                "id", existing["id"]
            ).execute()
        else:
            by_name = first_or_none(
                sb()
                .table("filieres")
                .select("*")
                .eq("name", item.name)
                .eq("level", item.level)
                .limit(1)
                .execute()
            )
            if by_name:
                sb().table("filieres").update({"desktop_id": item.desktop_id}).eq(
                    "id", by_name["id"]
                ).execute()
            else:
                sb().table("filieres").insert(
                    {"desktop_id": item.desktop_id, "name": item.name, "level": item.level}
                ).execute()
        count += 1
    return count


def upsert_rooms(items: list) -> int:
    count = 0
    for item in items:
        existing = first_or_none(
            sb().table("rooms").select("*").eq("desktop_id", item.desktop_id).limit(1).execute()
        )
        if existing:
            sb().table("rooms").update({"name": item.name, "capacity": item.capacity}).eq(
                "id", existing["id"]
            ).execute()
        else:
            by_name = first_or_none(
                sb().table("rooms").select("*").eq("name", item.name).limit(1).execute()
            )
            if by_name:
                sb().table("rooms").update(
                    {"desktop_id": item.desktop_id, "capacity": item.capacity}
                ).eq("id", by_name["id"]).execute()
            else:
                sb().table("rooms").insert(
                    {
                        "desktop_id": item.desktop_id,
                        "name": item.name,
                        "capacity": item.capacity,
                    }
                ).execute()
        count += 1
    return count


def _ensure_teacher_and_course(
    subject: str,
    teacher: str,
    seen_subjects: set[str],
    seen_teachers: set[str],
) -> None:
    if subject and subject not in seen_subjects:
        existing = first_or_none(
            sb().table("courses").select("id").eq("subject", subject).limit(1).execute()
        )
        if not existing:
            sb().table("courses").insert({"subject": subject}).execute()
        seen_subjects.add(subject)
    if teacher and teacher not in seen_teachers:
        existing = first_or_none(
            sb().table("teachers").select("id").eq("name", teacher).limit(1).execute()
        )
        if not existing:
            sb().table("teachers").insert({"name": teacher}).execute()
        seen_teachers.add(teacher)


def apply_sync(payload: SyncPayload) -> SyncResult:
    """
    Apply a desktop sync payload against Supabase:
    - Upsert filieres / rooms
    - Create or update schedules by desktop_id (never duplicates)
    - Delete schedules listed in deleted_desktop_ids
    - Detect conflicts when server copy is newer than client
    """
    result = SyncResult()
    result.filieres_upserted = upsert_filieres(payload.filieres)
    result.rooms_upserted = upsert_rooms(payload.rooms)

    affected_filiere_ids: set[int] = set()
    seen_subjects: set[str] = set()
    seen_teachers: set[str] = set()

    for item in payload.schedules:
        filiere_id = _resolve_filiere_id(item)
        if filiere_id is None:
            result.conflicts.append(
                SyncConflict(
                    desktop_id=item.desktop_id or 0,
                    reason="Unknown filière (desktop_id not found on server)",
                )
            )
            continue

        _ensure_teacher_and_course(item.subject, item.teacher, seen_subjects, seen_teachers)
        affected_filiere_ids.add(filiere_id)

        existing: dict[str, Any] | None = None
        if item.desktop_id is not None:
            existing = first_or_none(
                sb()
                .table("schedule")
                .select("*")
                .eq("desktop_id", item.desktop_id)
                .limit(1)
                .execute()
            )

        payload_row = {
            "desktop_id": item.desktop_id,
            "filiere_id": filiere_id,
            "day": item.day,
            "start_time": time_str(item.start_time),
            "end_time": time_str(item.end_time),
            "subject": item.subject,
            "teacher": item.teacher,
            "room": item.room,
            "group_tc": item.group_tc,
            "week_date": date_str(item.week_date),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if existing:
            if item.updated_at and existing.get("updated_at"):
                server_ts = parse_datetime(existing["updated_at"])
                client_ts = item.updated_at
                if server_ts and client_ts:
                    if server_ts.tzinfo is None:
                        server_ts = server_ts.replace(tzinfo=timezone.utc)
                    if client_ts.tzinfo is None:
                        client_ts = client_ts.replace(tzinfo=timezone.utc)
                    if server_ts > client_ts:
                        result.conflicts.append(
                            SyncConflict(
                                desktop_id=item.desktop_id or 0,
                                reason="Server version is newer; client data skipped",
                                server_updated_at=server_ts,
                                client_updated_at=item.updated_at,
                            )
                        )
                        continue

            sb().table("schedule").update(payload_row).eq("id", existing["id"]).execute()
            result.updated += 1
        else:
            sb().table("schedule").insert(payload_row).execute()
            result.created += 1

    if payload.deleted_desktop_ids:
        to_delete = (
            sb()
            .table("schedule")
            .select("id, filiere_id, desktop_id")
            .in_("desktop_id", payload.deleted_desktop_ids)
            .execute()
            .data
            or []
        )
        for row in to_delete:
            affected_filiere_ids.add(int(row["filiere_id"]))
            sb().table("schedule").delete().eq("id", row["id"]).execute()
            result.deleted += 1

    if payload.notify_students and (result.created or result.updated or result.deleted):
        for fid in affected_filiere_ids:
            filiere = first_or_none(
                sb().table("filieres").select("*").eq("id", fid).limit(1).execute()
            )
            label = f"{filiere['level']} — {filiere['name']}" if filiere else str(fid)
            students = (
                sb().table("students").select("id").eq("filiere_id", fid).execute().data or []
            )
            if students:
                sb().table("notifications").insert(
                    [
                        {
                            "student_id": s["id"],
                            "filiere_id": fid,
                            "title": "Emploi du temps mis à jour",
                            "message": (
                                f"L'emploi du temps de {label} a été modifié. "
                                "Consultez votre planning."
                            ),
                        }
                        for s in students
                    ]
                ).execute()

    result.message = (
        f"Sync OK — created={result.created}, updated={result.updated}, "
        f"deleted={result.deleted}, conflicts={len(result.conflicts)}"
    )
    return result
