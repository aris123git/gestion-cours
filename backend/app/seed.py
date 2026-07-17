"""
Seed Supabase with demo filières, rooms, students and a sample week schedule.
Usage:
  cd backend && python -m app.seed

Requires SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY (and the schema applied).
"""

from datetime import date, timedelta

from app.core.security import hash_password
from app.db.supabase import first_or_none, sb


def monday_this_week() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


def seed() -> None:
    client = sb()

    if first_or_none(
        client.table("students").select("id").eq("student_number", "20250001").limit(1).execute()
    ):
        print("Seed already applied — skipping.")
        return

    filiere_rows = (
        client.table("filieres")
        .insert(
            [
                {"desktop_id": 1, "name": "Informatique", "level": "L1"},
                {"desktop_id": 2, "name": "Gestion", "level": "L1"},
                {"desktop_id": 3, "name": "Informatique", "level": "L2"},
                {"desktop_id": 4, "name": "Réseaux", "level": "L3"},
            ]
        )
        .execute()
        .data
    )

    client.table("rooms").insert(
        [
            {"desktop_id": 1, "name": "A101", "capacity": 40},
            {"desktop_id": 2, "name": "B205", "capacity": 60},
            {"desktop_id": 3, "name": "Labo Info", "capacity": 30},
        ]
    ).execute()

    client.table("teachers").insert(
        [
            {"name": "Dr. Dupont"},
            {"name": "Mme. Martin"},
            {"name": "M. Bernard"},
        ]
    ).execute()

    client.table("courses").insert(
        [
            {"subject": "Algorithmique"},
            {"subject": "Bases de données"},
            {"subject": "Mathématiques"},
            {"subject": "Réseaux"},
            {"subject": "Anglais"},
        ]
    ).execute()

    # Map by desktop_id for stable references
    by_desktop = {f["desktop_id"]: f["id"] for f in filiere_rows}
    l1_info = by_desktop[1]
    l2_info = by_desktop[3]

    client.table("students").insert(
        [
            {
                "student_number": "20250001",
                "first_name": "Amina",
                "last_name": "Diallo",
                "email": "amina.diallo@univ.example",
                "password_hash": hash_password("password123"),
                "filiere_id": l1_info,
                "level": "L1",
            },
            {
                "student_number": "20250002",
                "first_name": "Karim",
                "last_name": "Ndiaye",
                "email": "karim.ndiaye@univ.example",
                "password_hash": hash_password("password123"),
                "filiere_id": l2_info,
                "level": "L2",
            },
        ]
    ).execute()

    week = monday_this_week().isoformat()
    client.table("schedule").insert(
        [
            {
                "desktop_id": 1001,
                "filiere_id": l1_info,
                "day": "Lundi",
                "start_time": "07:00:00",
                "end_time": "12:00:00",
                "subject": "Algorithmique",
                "teacher": "Dr. Dupont",
                "room": "Labo Info",
                "week_date": week,
            },
            {
                "desktop_id": 1002,
                "filiere_id": l1_info,
                "day": "Lundi",
                "start_time": "13:00:00",
                "end_time": "18:00:00",
                "subject": "Mathématiques",
                "teacher": "Mme. Martin",
                "room": "A101",
                "week_date": week,
            },
            {
                "desktop_id": 1003,
                "filiere_id": l1_info,
                "day": "Mardi",
                "start_time": "07:00:00",
                "end_time": "12:00:00",
                "subject": "Bases de données",
                "teacher": "M. Bernard",
                "room": "B205",
                "week_date": week,
            },
            {
                "desktop_id": 1004,
                "filiere_id": l1_info,
                "day": "Mercredi",
                "start_time": "13:00:00",
                "end_time": "18:00:00",
                "subject": "Anglais",
                "teacher": "Mme. Martin",
                "room": "A101",
                "week_date": week,
            },
            {
                "desktop_id": 1005,
                "filiere_id": l1_info,
                "day": "Jeudi",
                "start_time": "07:00:00",
                "end_time": "12:00:00",
                "subject": "Réseaux",
                "teacher": "Dr. Dupont",
                "room": "Labo Info",
                "week_date": week,
            },
            {
                "desktop_id": 2001,
                "filiere_id": l2_info,
                "day": "Lundi",
                "start_time": "07:00:00",
                "end_time": "12:00:00",
                "subject": "Bases de données",
                "teacher": "M. Bernard",
                "room": "B205",
                "week_date": week,
            },
        ]
    ).execute()

    print("Seed complete.")
    print("  Demo student : 20250001 / password123  (L1 Informatique)")
    print("  Demo student : 20250002 / password123  (L2 Informatique)")


if __name__ == "__main__":
    seed()
