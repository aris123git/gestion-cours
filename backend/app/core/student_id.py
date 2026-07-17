"""Shared validation helpers."""

from __future__ import annotations

import re

# Student INE / numéro d'étudiant IST Wayalghin: IST.W followed by digits
STUDENT_NUMBER_PATTERN = re.compile(r"^IST\.W\d+$")
STUDENT_NUMBER_HINT = "Le numéro doit commencer par IST.W suivi de chiffres (ex. IST.W20250001)"


def normalize_student_number(value: str) -> str:
    """Strip spaces and uppercase prefix letters for consistent storage."""
    raw = (value or "").strip().upper().replace(" ", "")
    # Keep dots as typed after uppercasing (IST.W...)
    return raw


def validate_student_number(value: str) -> str:
    """Return normalized number or raise ValueError with a French message."""
    number = normalize_student_number(value)
    if not STUDENT_NUMBER_PATTERN.fullmatch(number):
        raise ValueError(STUDENT_NUMBER_HINT)
    return number
