"""Tests API / allocation / export pour GestionCours."""
import os
import tempfile
import zipfile

import pytest

# Base de test isolée avant imports applicatifs
_TMP = tempfile.mkdtemp(prefix="gestioncours_test_")
os.environ["GESTION_COURS_DB"] = os.path.join(_TMP, "test.db")
os.environ["GESTION_COURS_EXPORTS"] = os.path.join(_TMP, "exports")

from config import ANNEE_COURANTE  # noqa: E402
from database import (  # noqa: E402
    ajouter_filiere,
    ajouter_salle,
    get_cours,
    get_salles,
    init_db,
    set_effectif,
    supprimer_salle,
    sync_tronc_commun,
)
from allocation import allouer_salles_par_jour, allouer_toute_la_semaine  # noqa: E402
from app import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    if os.path.exists(os.environ["GESTION_COURS_DB"]):
        os.remove(os.environ["GESTION_COURS_DB"])
    init_db()
    yield


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def _seed_basic():
    f1 = ajouter_filiere("L1", "INFO", 1)
    f2 = ajouter_filiere("L1", "GESTION", 1)
    set_effectif(ANNEE_COURANTE, f1, 40)
    set_effectif(ANNEE_COURANTE, f2, 35)
    return f1, f2


def test_meta(client):
    r = client.get("/api/meta")
    assert r.status_code == 200
    data = r.get_json()
    assert "jours" in data
    assert data["annee_universitaire"] == ANNEE_COURANTE


def test_filiere_crud_validation(client):
    r = client.post("/api/filieres", json={"nom": "", "annee": "L1"})
    assert r.status_code == 400

    r = client.post(
        "/api/filieres",
        json={"nom": "RIT", "annee": "L1", "effectif": 38, "etablissement": "IST"},
    )
    assert r.status_code == 200
    fid = r.get_json()["id"]

    r = client.post(
        "/api/filieres",
        json={"nom": "RIT", "annee": "L1", "effectif": 10, "etablissement": "IST"},
    )
    assert r.status_code == 409

    r = client.post("/api/filieres", json={"nom": "X", "effectif": "abc"})
    assert r.status_code == 400

    r = client.delete(f"/api/filieres/{fid}")
    assert r.status_code == 200


def test_cours_save_and_slot_unique(client):
    f1, _ = _seed_basic()
    payload = {
        "filiere_id": f1,
        "date_lundi": "2026-05-18",
        "jour": "Lundi",
        "creneau": "Matin",
        "matiere": "Algo",
        "enseignant": "Dupont",
    }
    r = client.post("/api/cours", json=payload)
    assert r.status_code == 200
    assert r.get_json()["ok"]

    # Même créneau = mise à jour, pas de doublon
    payload["matiere"] = "Algo 2"
    r = client.post("/api/cours", json=payload)
    assert r.status_code == 200
    cours = get_cours(f1, "2026-05-18", "Lundi", "Matin")
    assert cours.matiere == "Algo 2"

    r = client.post(
        "/api/cours",
        json={**payload, "jour": "Dimanche"},
    )
    assert r.status_code == 400


def test_enseignant_conflict(client):
    f1, f2 = _seed_basic()
    base = {
        "date_lundi": "2026-05-18",
        "jour": "Mardi",
        "creneau": "Matin",
        "matiere": "Maths",
        "enseignant": "Martin",
    }
    assert client.post("/api/cours", json={**base, "filiere_id": f1}).status_code == 200
    r = client.post("/api/cours", json={**base, "filiere_id": f2})
    assert r.status_code == 409
    assert r.get_json()["warning"] == "conflit_enseignant"

    r = client.post("/api/cours", json={**base, "filiere_id": f2, "force": True})
    assert r.status_code == 200


def test_tronc_commun_sync(client):
    f1, f2 = _seed_basic()
    r = client.post(
        "/api/cours",
        json={
            "filiere_id": f1,
            "filieres_tc": [f2],
            "date_lundi": "2026-05-18",
            "jour": "Mercredi",
            "creneau": "Après-midi",
            "matiere": "TC Anglais",
            "enseignant": "Smith",
        },
    )
    assert r.status_code == 200
    c1 = get_cours(f1, "2026-05-18", "Mercredi", "Après-midi")
    c2 = get_cours(f2, "2026-05-18", "Mercredi", "Après-midi")
    assert c1.groupe_tc and c1.groupe_tc == c2.groupe_tc

    # Retirer f2 du TC : f2 garde le même enseignant → conflit attendu, puis force
    r = client.post(
        "/api/cours",
        json={
            "filiere_id": f1,
            "filieres_tc": [],
            "date_lundi": "2026-05-18",
            "jour": "Mercredi",
            "creneau": "Après-midi",
            "matiere": "Anglais seul",
            "enseignant": "Smith",
        },
    )
    assert r.status_code == 409

    r = client.post(
        "/api/cours",
        json={
            "filiere_id": f1,
            "filieres_tc": [],
            "date_lundi": "2026-05-18",
            "jour": "Mercredi",
            "creneau": "Après-midi",
            "matiere": "Anglais seul",
            "enseignant": "Smith",
            "force": True,
        },
    )
    assert r.status_code == 200
    c1 = get_cours(f1, "2026-05-18", "Mercredi", "Après-midi")
    c2 = get_cours(f2, "2026-05-18", "Mercredi", "Après-midi")
    assert c1.groupe_tc is None
    assert c2 is not None
    assert c2.groupe_tc is None


def test_allocation_best_fit_and_report(client):
    f1, f2 = _seed_basic()
    # salles déjà seedées par init_db
    assert get_salles()

    client.post(
        "/api/cours",
        json={
            "filiere_id": f1,
            "date_lundi": "2026-05-18",
            "jour": "Jeudi",
            "creneau": "Matin",
            "matiere": "Physique",
            "enseignant": "A",
        },
    )
    client.post(
        "/api/cours",
        json={
            "filiere_id": f2,
            "date_lundi": "2026-05-18",
            "jour": "Jeudi",
            "creneau": "Matin",
            "matiere": "Chimie",
            "enseignant": "B",
        },
    )

    r = client.post(
        "/api/allouer",
        json={"date_lundi": "2026-05-18", "filiere_id": f1},
    )
    assert r.status_code == 200
    rapport = r.get_json()["rapport"]
    assert rapport["assigned"] >= 2
    c1 = get_cours(f1, "2026-05-18", "Jeudi", "Matin")
    assert c1.salle_id is not None


def test_supprimer_salle_nullify():
    f1, _ = _seed_basic()
    sid = ajouter_salle("TempRoom", 50)
    sync_tronc_commun(
        "2026-05-18", "Vendredi", "Matin", [f1], "Test", "Prof", None
    )
    from database import get_conn
    conn = get_conn()
    conn.execute("UPDATE cours SET salle_id=? WHERE filiere_id=?", (sid, f1))
    conn.commit()
    conn.close()
    supprimer_salle(sid)
    c = get_cours(f1, "2026-05-18", "Vendredi", "Matin")
    assert c.salle_id is None


def test_conflits_endpoint(client):
    f1, f2 = _seed_basic()
    base = {
        "date_lundi": "2026-05-18",
        "jour": "Samedi",
        "creneau": "Matin",
        "matiere": "Droit",
        "enseignant": "Conflict",
    }
    client.post("/api/cours", json={**base, "filiere_id": f1})
    client.post("/api/cours", json={**base, "filiere_id": f2, "force": True})
    r = client.get("/api/conflits?date_lundi=2026-05-18")
    assert r.status_code == 200
    assert len(r.get_json()["conflits"]) >= 1


def test_export_pdf_and_zip(client):
    f1, f2 = _seed_basic()
    client.post(
        "/api/cours",
        json={
            "filiere_id": f1,
            "date_lundi": "2026-05-18",
            "jour": "Lundi",
            "creneau": "Matin",
            "matiere": "Export",
            "enseignant": "Z",
        },
    )
    r = client.post(
        "/api/export-pdf",
        json={"mode": "one", "filiere_id": f1, "date_lundi": "2026-05-18"},
    )
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("application/pdf")
    assert r.data[:4] == b"%PDF"

    r = client.post(
        "/api/export-pdf",
        json={"mode": "zip", "date_lundi": "2026-05-18", "etablissement": "IST"},
    )
    assert r.status_code == 200
    assert "zip" in r.headers["Content-Type"]
    # ZIP valide
    path = os.path.join(_TMP, "out.zip")
    with open(path, "wb") as f:
        f.write(r.data)
    with zipfile.ZipFile(path) as zf:
        assert len(zf.namelist()) >= 1


def test_download_path_traversal(client):
    r = client.get("/api/export-pdf/download?path=/etc/passwd")
    assert r.status_code == 403


def test_effectif_validation(client):
    f1, _ = _seed_basic()
    r = client.put(f"/api/effectifs/{f1}", json={"effectif": -3})
    assert r.status_code == 400
    r = client.put(f"/api/effectifs/{f1}", json={"effectif": 42})
    assert r.status_code == 200


def test_allocation_clears_without_rooms():
    f1, _ = _seed_basic()
    # supprimer toutes les salles
    for s in list(get_salles()):
        supprimer_salle(s.id)
    sync_tronc_commun(
        "2026-05-18", "Lundi", "Après-midi", [f1], "SansSalle", "P", None
    )
    from database import get_conn
    # assigner une salle fantôme impossible — juste vérifier clear
    _, rapport = allouer_salles_par_jour("2026-05-18", "Lundi")
    assert rapport["failed"]
    assert any("Aucune salle" in f["reason"] for f in rapport["failed"])
