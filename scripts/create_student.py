#!/usr/bin/env python3
"""
Create a student account in the online database.

Usage:
  cd backend && python ../scripts/create_student.py \\
      --number 20250003 --first Jean --last Dupont \\
      --email jean@univ.example --filiere-id 1 --level L1 \\
      --password secret123
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Filiere, Student


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a student account")
    parser.add_argument("--number", required=True)
    parser.add_argument("--first", required=True)
    parser.add_argument("--last", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--filiere-id", type=int, required=True)
    parser.add_argument("--level", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        filiere = db.query(Filiere).filter(Filiere.id == args.filiere_id).first()
        if not filiere:
            raise SystemExit(f"Filière id={args.filiere_id} introuvable")
        if db.query(Student).filter(Student.student_number == args.number).first():
            raise SystemExit("Numéro d'étudiant déjà utilisé")
        student = Student(
            student_number=args.number,
            first_name=args.first,
            last_name=args.last,
            email=args.email,
            password_hash=hash_password(args.password),
            filiere_id=args.filiere_id,
            level=args.level,
        )
        db.add(student)
        db.commit()
        print(f"Étudiant créé: {args.number} → id={student.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
