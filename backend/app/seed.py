"""
Seed the database with demo filières, rooms, students and a sample week schedule.
Usage:
  cd backend && python -m app.seed
"""

from datetime import date, time, timedelta

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import Filiere, Room, Schedule, Student, Teacher, Course


def monday_this_week() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Student).filter(Student.student_number == "20250001").first():
            print("Seed already applied — skipping.")
            return

        filieres = [
            Filiere(desktop_id=1, name="Informatique", level="L1"),
            Filiere(desktop_id=2, name="Gestion", level="L1"),
            Filiere(desktop_id=3, name="Informatique", level="L2"),
            Filiere(desktop_id=4, name="Réseaux", level="L3"),
        ]
        db.add_all(filieres)
        db.flush()

        rooms = [
            Room(desktop_id=1, name="A101", capacity=40),
            Room(desktop_id=2, name="B205", capacity=60),
            Room(desktop_id=3, name="Labo Info", capacity=30),
        ]
        db.add_all(rooms)

        teachers = [
            Teacher(name="Dr. Dupont"),
            Teacher(name="Mme. Martin"),
            Teacher(name="M. Bernard"),
        ]
        db.add_all(teachers)

        courses = [
            Course(subject="Algorithmique"),
            Course(subject="Bases de données"),
            Course(subject="Mathématiques"),
            Course(subject="Réseaux"),
            Course(subject="Anglais"),
        ]
        db.add_all(courses)
        db.flush()

        students = [
            Student(
                student_number="20250001",
                first_name="Amina",
                last_name="Diallo",
                email="amina.diallo@univ.example",
                password_hash=hash_password("password123"),
                filiere_id=filieres[0].id,
                level="L1",
            ),
            Student(
                student_number="20250002",
                first_name="Karim",
                last_name="Ndiaye",
                email="karim.ndiaye@univ.example",
                password_hash=hash_password("password123"),
                filiere_id=filieres[2].id,
                level="L2",
            ),
        ]
        db.add_all(students)

        week = monday_this_week()
        sample = [
            # Lundi matin
            Schedule(
                desktop_id=1001,
                filiere_id=filieres[0].id,
                day="Lundi",
                start_time=time(7, 0),
                end_time=time(12, 0),
                subject="Algorithmique",
                teacher="Dr. Dupont",
                room="Labo Info",
                group_tc=None,
                week_date=week,
            ),
            Schedule(
                desktop_id=1002,
                filiere_id=filieres[0].id,
                day="Lundi",
                start_time=time(13, 0),
                end_time=time(18, 0),
                subject="Mathématiques",
                teacher="Mme. Martin",
                room="A101",
                week_date=week,
            ),
            Schedule(
                desktop_id=1003,
                filiere_id=filieres[0].id,
                day="Mardi",
                start_time=time(7, 0),
                end_time=time(12, 0),
                subject="Bases de données",
                teacher="M. Bernard",
                room="B205",
                week_date=week,
            ),
            Schedule(
                desktop_id=1004,
                filiere_id=filieres[0].id,
                day="Mercredi",
                start_time=time(13, 0),
                end_time=time(18, 0),
                subject="Anglais",
                teacher="Mme. Martin",
                room="A101",
                week_date=week,
            ),
            Schedule(
                desktop_id=1005,
                filiere_id=filieres[0].id,
                day="Jeudi",
                start_time=time(7, 0),
                end_time=time(12, 0),
                subject="Réseaux",
                teacher="Dr. Dupont",
                room="Labo Info",
                week_date=week,
            ),
            # L2 sample
            Schedule(
                desktop_id=2001,
                filiere_id=filieres[2].id,
                day="Lundi",
                start_time=time(7, 0),
                end_time=time(12, 0),
                subject="Bases de données",
                teacher="M. Bernard",
                room="B205",
                week_date=week,
            ),
        ]
        db.add_all(sample)
        db.commit()
        print("Seed complete.")
        print("  Demo student : 20250001 / password123  (L1 Informatique)")
        print("  Demo student : 20250002 / password123  (L2 Informatique)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
