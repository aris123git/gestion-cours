from dataclasses import dataclass
from typing import Optional

@dataclass
class Salle:
    id: Optional[int]
    nom: str
    capacite: int

@dataclass
class Filiere:
    id: Optional[int]
    annee: str
    nom: str

@dataclass
class Cours:
    id: Optional[int]
    filiere_id: int
    date_lundi: str
    jour: str
    creneau: str
    matiere: str
    enseignant: str
    salle_id: Optional[int] = None
    groupe_tc: Optional[str] = None

@dataclass
class Effectif:
    annee_universitaire: str
    filiere_id: int
    effectif: int