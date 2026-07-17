"""Authentication & student registration routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Filiere, Student
from app.schemas import FiliereOut, LoginRequest, LoginResponse, RegisterRequest, StudentOut

router = APIRouter(tags=["Authentication"])


def _student_out(student: Student) -> StudentOut:
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


def _login_response(student: Student) -> LoginResponse:
    token = create_access_token(student.id, {"student_number": student.student_number})
    return LoginResponse(access_token=token, student=_student_out(student))


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """
    Student self-registration.
    Creates an account (bcrypt password) and returns a JWT so the user is logged in immediately.
    """
    number = body.student_number.strip()
    email = str(body.email).strip().lower()

    if db.query(Student).filter(Student.student_number == number).first():
        raise HTTPException(status_code=400, detail="Ce numéro d'étudiant est déjà utilisé")
    if db.query(Student).filter(Student.email == email).first():
        raise HTTPException(status_code=400, detail="Cet e-mail est déjà utilisé")

    filiere = db.query(Filiere).filter(Filiere.id == body.filiere_id).first()
    if not filiere:
        raise HTTPException(status_code=400, detail="Filière introuvable")

    level = body.level.strip() or filiere.level
    student = Student(
        student_number=number,
        first_name=body.first_name.strip(),
        last_name=body.last_name.strip(),
        email=email,
        password_hash=hash_password(body.password),
        filiere_id=filiere.id,
        level=level,
    )
    db.add(student)
    db.commit()
    student = (
        db.query(Student)
        .options(joinedload(Student.filiere))
        .filter(Student.id == student.id)
        .first()
    )
    return _login_response(student)


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Student login with student number + password."""
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
    return _login_response(student)


@router.get("/public/filieres", response_model=list[FiliereOut], tags=["Public"])
def public_filieres(level: str | None = None, db: Session = Depends(get_db)):
    """List programmes for the registration form (no auth required)."""
    q = db.query(Filiere)
    if level:
        q = q.filter(Filiere.level == level)
    return q.order_by(Filiere.level, Filiere.name).all()
