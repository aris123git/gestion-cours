"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models import Student
from app.schemas import LoginRequest, LoginResponse, StudentOut

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Student login with student number + password.
    Returns a JWT and the student profile.
    """
    student = (
        db.query(Student)
        .options(joinedload(Student.filiere))
        .filter(Student.student_number == body.student_number.strip())
        .first()
    )
    if not student or not verify_password(body.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Numéro d'étudiant ou mot de passe incorrect",
        )

    token = create_access_token(student.id, {"student_number": student.student_number})
    profile = StudentOut(
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
    return LoginResponse(access_token=token, student=profile)
