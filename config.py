import os
import sys


def resource_dir():
    """Dossier des ressources empaquetées (templates, static, logos)."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def app_dir():
    """Dossier writable (à côté du .exe) pour la base et les exports."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = app_dir()
RESOURCE_DIR = resource_dir()
DB_PATH = os.environ.get("GESTION_COURS_DB") or os.path.join(BASE_DIR, "gestion_cours.db")
EXPORT_DIR = os.environ.get("GESTION_COURS_EXPORTS") or os.path.join(BASE_DIR, "exports")

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
CRENEAUX = [("Matin", "07:00", "12:00"), ("Après-midi", "13:00", "18:00")]
CRENEAUX_LABELS = ["Matin (7h-12h)", "Après-midi (13h-18h)"]

ANNEE_COURANTE = "2025-2026"
DATE_FORMAT = "%d/%m/%Y"
