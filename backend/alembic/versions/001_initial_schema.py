"""Initial schema: students, filieres, teachers, rooms, courses, schedule, notifications."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "filieres",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("level", sa.String(40), nullable=False),
        sa.Column("desktop_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("name", "level", name="uq_filiere_name_level"),
    )
    op.create_index("ix_filieres_desktop_id", "filieres", ["desktop_id"], unique=True)

    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("desktop_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_rooms_desktop_id", "rooms", ["desktop_id"], unique=True)

    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subject", sa.String(160), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_number", sa.String(40), nullable=False),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("filiere_id", sa.Integer(), sa.ForeignKey("filieres.id"), nullable=False),
        sa.Column("level", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_students_student_number", "students", ["student_number"], unique=True)

    op.create_table(
        "schedule",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("desktop_id", sa.Integer(), nullable=True),
        sa.Column("filiere_id", sa.Integer(), sa.ForeignKey("filieres.id"), nullable=False),
        sa.Column("day", sa.String(20), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("subject", sa.String(160), nullable=False),
        sa.Column("teacher", sa.String(160), nullable=False),
        sa.Column("room", sa.String(80), nullable=True),
        sa.Column("group_tc", sa.String(120), nullable=True),
        sa.Column("week_date", sa.Date(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "filiere_id",
            "week_date",
            "day",
            "start_time",
            "subject",
            "group_tc",
            name="uq_schedule_slot",
        ),
    )
    op.create_index("ix_schedule_desktop_id", "schedule", ["desktop_id"], unique=True)
    op.create_index("ix_schedule_week_filiere", "schedule", ["week_date", "filiere_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=True),
        sa.Column("filiere_id", sa.Integer(), sa.ForeignKey("filieres.id"), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("schedule")
    op.drop_table("students")
    op.drop_table("courses")
    op.drop_table("rooms")
    op.drop_table("teachers")
    op.drop_table("filieres")
