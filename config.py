import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "gestion_cours.db")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
CRENEAUX = [("Matin", "07:00", "12:00"), ("Après-midi", "13:00", "18:00")]
CRENEAUX_LABELS = ["Matin (7h-12h)", "Après-midi (13h-18h)"]

ANNEE_COURANTE = "2025-2026"
DATE_FORMAT = "%d/%m/%Y"