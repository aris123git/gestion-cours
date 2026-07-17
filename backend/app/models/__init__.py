"""SQLAlchemy ORM models for the online timetable database."""

from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Filiere(Base):
    __tablename__ = "filieres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    level = Column(String(40), nullable=False)  # L1, L2, L3, Master, Doctorat
    # Optional link to the desktop SQLite filiere id for sync
    desktop_id = Column(Integer, nullable=True, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    students = relationship("Student", back_populates="filiere")
    schedules = relationship("Schedule", back_populates="filiere")

    __table_args__ = (UniqueConstraint("name", "level", name="uq_filiere_name_level"),)


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(160), nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), nullable=False, unique=True)
    capacity = Column(Integer, nullable=False, default=0)
    desktop_id = Column(Integer, nullable=True, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Course(Base):
    """Catalogue entry for a subject (matière)."""

    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(160), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_number = Column(String(40), nullable=False, unique=True, index=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    filiere_id = Column(Integer, ForeignKey("filieres.id"), nullable=False)
    level = Column(String(40), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    filiere = relationship("Filiere", back_populates="students")
    notifications = relationship("Notification", back_populates="student", cascade="all, delete-orphan")


class Schedule(Base):
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True, index=True)
    # Stable id from the desktop SQLite `cours.id` — prevents duplicates on sync
    desktop_id = Column(Integer, nullable=True, unique=True, index=True)
    filiere_id = Column(Integer, ForeignKey("filieres.id"), nullable=False, index=True)
    day = Column(String(20), nullable=False)  # Lundi … Samedi
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    subject = Column(String(160), nullable=False)
    teacher = Column(String(160), nullable=False)
    room = Column(String(80), nullable=True)
    group_tc = Column(String(120), nullable=True)
    week_date = Column(Date, nullable=False, index=True)  # Monday of the week
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    filiere = relationship("Filiere", back_populates="schedules")

    __table_args__ = (
        Index("ix_schedule_week_filiere", "week_date", "filiere_id"),
        UniqueConstraint(
            "filiere_id",
            "week_date",
            "day",
            "start_time",
            "subject",
            "group_tc",
            name="uq_schedule_slot",
        ),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)
    filiere_id = Column(Integer, ForeignKey("filieres.id"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="notifications")
