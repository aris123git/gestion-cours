"""Authentication routes."""

from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token, verify_password
from app.db.supabase import first_or_none, sb
from app.models import StudentRow
from app.schemas import LoginRequest, LoginResponse, StudentOut

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """
    Student login with student number + password.
    Returns a JWT and the student profile.
    """
    result = (
        sb()
        .table("students")
        .select("*, filieres(name, level)")
        .eq("student_number", body.student_number.strip())
        .limit(1)
        .execute()
    )
    row = first_or_none(result)
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Numéro d'étudiant ou mot de passe incorrect",
        )

    student = StudentRow(row)
    token = create_access_token(student.id, {"student_number": student.student_number})
    profile = StudentOut(
        id=student.id,
        student_number=student.student_number,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email,
        filiere_id=student.filiere_id,
        level=student.level,
        filiere_name=student.filiere_name,
        created_at=student.created_at,
    )
    return LoginResponse(access_token=token, student=profile)
