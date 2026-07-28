"""
Gestion des cours — application web moderne.
Lance avec : python app.py
"""
import os
import time
from flask import Flask, render_template, request, jsonify, send_file

from config import JOURS, CRENEAUX, CRENEAUX_LABELS, ANNEE_COURANTE, RESOURCE_DIR
from database import (
    init_db, get_filieres, get_filieres_avec_effectif, ajouter_filiere, supprimer_filiere,
    set_effectif, get_effectif, get_salles, ajouter_salle, supprimer_salle, modifier_salle,
    get_cours, sauvegarder_cours, supprimer_cours, supprimer_cours_filiere_semaine,
    get_grille_filiere, get_stats_semaine, copier_semaine, rechercher_conflits_enseignant,
    get_matieres_semaine, get_enseignants_pour_matiere, get_dernier_enseignant_filiere_matiere,
    get_tous_enseignants, get_toutes_matieres, get_etablissements, get_types_cours,
    get_filieres_tc_groupe, get_salle_by_id, sync_tronc_commun, rechercher_conflits_semaine,
)
from models import Cours
from allocation import allouer_salles_par_jour, allouer_toute_la_semaine
from export_pdf import export_all_filieres, export_all_filieres_zip, export_une_filiere
from utils import get_lundi_week_courante, get_semaine_precedente, get_semaine_suivante, format_date_fr

app = Flask(
    __name__,
    template_folder=os.path.join(RESOURCE_DIR, "templates"),
    static_folder=os.path.join(RESOURCE_DIR, "static"),
)
app.config["JSON_AS_ASCII"] = False

init_db()

CRENEAU_IDS = {c[0] for c in CRENEAUX}


def etab_id_from_name(nom):
    mapping = {"IST": 1, "UBS": 2}
    return mapping.get(nom, 1)


def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _as_int(value, default=None):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return None


def _validate_slot(jour, creneau):
    if jour not in JOURS:
        return f"Jour invalide : {jour}"
    if creneau not in CRENEAU_IDS:
        return f"Créneau invalide : {creneau}"
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/meta")
def api_meta():
    return jsonify({
        "jours": JOURS,
        "creneaux": [{"id": c[0], "label": CRENEAUX_LABELS[i], "debut": c[1], "fin": c[2]}
                     for i, c in enumerate(CRENEAUX)],
        "annees": ["L1", "L2", "L3", "Master", "Doctorat"],
        "annee_universitaire": ANNEE_COURANTE,
        "etablissements": get_etablissements(),
        "types_cours": get_types_cours(),
        "semaine_courante": get_lundi_week_courante(),
    })


@app.route("/api/semaine")
def api_semaine():
    date = request.args.get("date", get_lundi_week_courante())
    direction = request.args.get("dir")
    if direction == "prev":
        date = get_semaine_precedente(date)
    elif direction == "next":
        date = get_semaine_suivante(date)
    elif direction == "today":
        date = get_lundi_week_courante()
    return jsonify({
        "date_lundi": date,
        "label": format_date_fr(date),
    })


@app.route("/api/filieres")
def api_filieres():
    annee = request.args.get("annee") or None
    etablissement = request.args.get("etablissement") or None
    return jsonify(get_filieres_avec_effectif(annee, etablissement))


@app.route("/api/filieres", methods=["POST"])
def api_ajouter_filiere():
    data = _json_body()
    nom = (data.get("nom") or "").strip()
    annee = data.get("annee") or "L1"
    effectif = _as_int(data.get("effectif"), 0)
    etab = data.get("etablissement") or "IST"
    if not nom:
        return jsonify({"error": "Nom requis"}), 400
    if effectif is None or effectif < 0:
        return jsonify({"error": "Effectif invalide"}), 400
    fid = ajouter_filiere(annee, nom, etab_id_from_name(etab))
    if not fid:
        return jsonify({"error": "Cette filière existe déjà"}), 409
    set_effectif(ANNEE_COURANTE, fid, effectif)
    return jsonify({"id": fid, "ok": True})


@app.route("/api/filieres/<int:filiere_id>", methods=["DELETE"])
def api_supprimer_filiere(filiere_id):
    supprimer_filiere(filiere_id)
    return jsonify({"ok": True})


@app.route("/api/grille")
def api_grille():
    filiere_id = request.args.get("filiere_id", type=int)
    date_lundi = request.args.get("date_lundi") or get_lundi_week_courante()
    if not filiere_id:
        return jsonify({"error": "filiere_id requis"}), 400
    grille = get_grille_filiere(filiere_id, date_lundi)
    stats = get_stats_semaine(date_lundi, filiere_id)
    return jsonify({"grille": grille, "stats": stats, "date_lundi": date_lundi})


@app.route("/api/stats")
def api_stats():
    date_lundi = request.args.get("date_lundi") or get_lundi_week_courante()
    filiere_id = request.args.get("filiere_id", type=int)
    return jsonify(get_stats_semaine(date_lundi, filiere_id))


@app.route("/api/cours", methods=["POST"])
def api_sauver_cours():
    data = _json_body()
    filiere_id = _as_int(data.get("filiere_id"))
    date_lundi = data.get("date_lundi")
    jour = data.get("jour")
    creneau = data.get("creneau")
    matiere = (data.get("matiere") or "").strip()
    enseignant = (data.get("enseignant") or "").strip()
    filieres_tc = data.get("filieres_tc") or []
    force = bool(data.get("force", False))
    clear_tc = bool(data.get("clear_tc_group", False))

    if not all([filiere_id, date_lundi, jour, creneau]):
        return jsonify({"error": "Champs manquants"}), 400
    err = _validate_slot(jour, creneau)
    if err:
        return jsonify({"error": err}), 400

    if not matiere and not enseignant:
        existant = get_cours(filiere_id, date_lundi, jour, creneau)
        if existant:
            supprimer_cours(existant.id, clear_tc_group=clear_tc or bool(existant.groupe_tc))
            allouer_salles_par_jour(date_lundi, jour)
        return jsonify({"ok": True, "deleted": True})

    if not matiere or not enseignant:
        return jsonify({"error": "Matière et enseignant requis"}), 400

    existant = get_cours(filiere_id, date_lundi, jour, creneau)
    try:
        filieres_tc = [int(x) for x in filieres_tc]
    except (TypeError, ValueError):
        return jsonify({"error": "filieres_tc invalide"}), 400

    conflits = rechercher_conflits_enseignant(
        date_lundi, jour, creneau, enseignant,
        exclude_cours_id=existant.id if existant else None,
    )
    if filieres_tc:
        ignore = set(filieres_tc) | {filiere_id}
        conflits = [c for c in conflits if c["filiere_id"] not in ignore]

    if conflits and not force:
        return jsonify({"warning": "conflit_enseignant", "conflits": conflits}), 409

    targets = list(dict.fromkeys([filiere_id, *filieres_tc]))
    groupe_tc = f"TC_{int(time.time())}" if len(targets) > 1 else None

    if len(targets) > 1:
        ids = sync_tronc_commun(
            date_lundi, jour, creneau, targets, matiere, enseignant, groupe_tc
        )
    else:
        # Retirer d'un éventuel ancien TC
        if existant and existant.groupe_tc:
            sync_tronc_commun(
                date_lundi, jour, creneau, [filiere_id], matiere, enseignant, None
            )
            ids = [get_cours(filiere_id, date_lundi, jour, creneau).id]
        else:
            if existant:
                existant.matiere = matiere
                existant.enseignant = enseignant
                existant.groupe_tc = None
                sauvegarder_cours(existant)
                ids = [existant.id]
            else:
                nouveau = Cours(None, filiere_id, date_lundi, jour, creneau, matiere, enseignant, None, None)
                ids = [sauvegarder_cours(nouveau)]

    _, alloc = allouer_salles_par_jour(date_lundi, jour)
    grille = get_grille_filiere(filiere_id, date_lundi)
    return jsonify({
        "ok": True,
        "ids": ids,
        "grille": grille,
        "stats": get_stats_semaine(date_lundi, filiere_id),
        "allocation": alloc,
    })


@app.route("/api/cours/<int:cours_id>", methods=["DELETE"])
def api_delete_cours(cours_id):
    date_lundi = request.args.get("date_lundi")
    jour = request.args.get("jour")
    clear_tc = request.args.get("clear_tc", "1") != "0"
    ok = supprimer_cours(cours_id, clear_tc_group=clear_tc)
    if not ok:
        return jsonify({"error": "Cours introuvable"}), 404
    if date_lundi and jour:
        allouer_salles_par_jour(date_lundi, jour)
    return jsonify({"ok": True})


@app.route("/api/suggestions/matieres")
def api_matieres():
    filiere_id = request.args.get("filiere_id", type=int)
    date_lundi = request.args.get("date_lundi")
    if filiere_id and date_lundi:
        return jsonify(get_matieres_semaine(filiere_id, date_lundi) or get_toutes_matieres())
    return jsonify(get_toutes_matieres())


@app.route("/api/suggestions/enseignants")
def api_enseignants():
    matiere = request.args.get("matiere", "").strip()
    filiere_id = request.args.get("filiere_id", type=int)
    if matiere:
        profs = get_enseignants_pour_matiere(matiere)
        dernier = ""
        if filiere_id:
            dernier = get_dernier_enseignant_filiere_matiere(filiere_id, matiere)
        return jsonify({"enseignants": profs, "dernier": dernier})
    return jsonify({"enseignants": get_tous_enseignants(), "dernier": ""})


@app.route("/api/tronc-commun/<int:filiere_id>")
def api_tc_info():
    date_lundi = request.args.get("date_lundi")
    jour = request.args.get("jour")
    creneau = request.args.get("creneau")
    cours = get_cours(filiere_id, date_lundi, jour, creneau)
    ids = []
    if cours and cours.groupe_tc:
        ids = get_filieres_tc_groupe(cours.groupe_tc, date_lundi, jour, creneau)
    return jsonify({"filiere_ids": ids, "groupe_tc": cours.groupe_tc if cours else None})


@app.route("/api/salles")
def api_salles():
    salles = get_salles()
    return jsonify([{"id": s.id, "nom": s.nom, "capacite": s.capacite} for s in salles])


@app.route("/api/salles", methods=["POST"])
def api_ajouter_salle():
    data = _json_body()
    nom = (data.get("nom") or "").strip()
    capacite = _as_int(data.get("capacite"), 0)
    if not nom or capacite is None or capacite <= 0:
        return jsonify({"error": "Nom et capacité valides requis"}), 400
    sid = ajouter_salle(nom, capacite)
    if not sid:
        return jsonify({"error": "Salle déjà existante"}), 409
    return jsonify({"id": sid, "ok": True})


@app.route("/api/salles/<int:salle_id>", methods=["PUT"])
def api_modifier_salle(salle_id):
    data = _json_body()
    nom = (data.get("nom") or "").strip()
    capacite = _as_int(data.get("capacite"), 0)
    if not nom or capacite is None or capacite <= 0:
        return jsonify({"error": "Nom et capacité valides requis"}), 400
    if not modifier_salle(salle_id, nom, capacite):
        return jsonify({"error": "Salle introuvable ou nom déjà utilisé"}), 409
    return jsonify({"ok": True})


@app.route("/api/salles/<int:salle_id>", methods=["DELETE"])
def api_supprimer_salle(salle_id):
    supprimer_salle(salle_id)
    return jsonify({"ok": True})


@app.route("/api/effectifs")
def api_effectifs():
    etab = request.args.get("etablissement") or None
    filieres = get_filieres(etablissement=etab)
    return jsonify([
        {
            "id": f.id,
            "annee": f.annee,
            "nom": f.nom,
            "etablissement": f.etablissement,
            "effectif": get_effectif(ANNEE_COURANTE, f.id),
        }
        for f in filieres
    ])


@app.route("/api/effectifs/<int:filiere_id>", methods=["PUT"])
def api_set_effectif(filiere_id):
    data = _json_body()
    effectif = _as_int(data.get("effectif"))
    if effectif is None or effectif < 0:
        return jsonify({"error": "Effectif invalide"}), 400
    if not get_filiere_by_id_safe(filiere_id):
        return jsonify({"error": "Filière introuvable"}), 404
    set_effectif(ANNEE_COURANTE, filiere_id, effectif)
    return jsonify({"ok": True})


def get_filiere_by_id_safe(filiere_id):
    from database import get_filiere_by_id
    return get_filiere_by_id(filiere_id)


@app.route("/api/allouer", methods=["POST"])
def api_allouer():
    data = _json_body()
    date_lundi = data.get("date_lundi") or get_lundi_week_courante()
    rapport = allouer_toute_la_semaine(date_lundi)
    filiere_id = _as_int(data.get("filiere_id"))
    payload = {
        "ok": True,
        "rapport": rapport,
        "message": (
            f"{rapport['assigned']} salle(s) allouée(s)"
            + (f", {len(rapport['failed'])} échec(s)" if rapport["failed"] else "")
        ),
    }
    if filiere_id:
        payload["grille"] = get_grille_filiere(filiere_id, date_lundi)
        payload["stats"] = get_stats_semaine(date_lundi, filiere_id)
    return jsonify(payload)


@app.route("/api/conflits")
def api_conflits():
    date_lundi = request.args.get("date_lundi") or get_lundi_week_courante()
    filiere_id = request.args.get("filiere_id", type=int)
    return jsonify({
        "date_lundi": date_lundi,
        "conflits": rechercher_conflits_semaine(date_lundi, filiere_id),
    })


@app.route("/api/reinitialiser", methods=["POST"])
def api_reinitialiser():
    data = _json_body()
    filiere_id = _as_int(data.get("filiere_id"))
    date_lundi = data.get("date_lundi")
    if not filiere_id or not date_lundi:
        return jsonify({"error": "Paramètres manquants"}), 400
    supprimer_cours_filiere_semaine(filiere_id, date_lundi)
    allouer_toute_la_semaine(date_lundi)
    return jsonify({"ok": True, "grille": get_grille_filiere(filiere_id, date_lundi),
                    "stats": get_stats_semaine(date_lundi, filiere_id)})


@app.route("/api/copier-semaine", methods=["POST"])
def api_copier_semaine():
    data = _json_body()
    filiere_id = _as_int(data.get("filiere_id"))
    date_source = data.get("date_source")
    date_cible = data.get("date_cible")
    if not all([filiere_id, date_source, date_cible]):
        return jsonify({"error": "Paramètres manquants"}), 400
    if date_source == date_cible:
        return jsonify({"error": "Source et cible identiques"}), 400
    count = copier_semaine(filiere_id, date_source, date_cible)
    allouer_toute_la_semaine(date_cible)
    return jsonify({
        "ok": True,
        "copied": count,
        "grille": get_grille_filiere(filiere_id, date_cible),
        "stats": get_stats_semaine(date_cible, filiere_id),
    })


@app.route("/api/export-pdf", methods=["POST"])
def api_export_pdf():
    data = _json_body()
    date_lundi = data.get("date_lundi") or get_lundi_week_courante()
    mode = data.get("mode", "all")  # all | one | zip
    filiere_id = _as_int(data.get("filiere_id"))
    etablissement = data.get("etablissement") or None
    type_cours = (data.get("type_cours") or "").strip() or None

    if mode == "one":
        if not filiere_id:
            return jsonify({"error": "filiere_id requis"}), 400
        path = export_une_filiere(filiere_id, date_lundi, type_cours=type_cours)
        if not path:
            return jsonify({"error": "Export échoué"}), 500
        return send_file(path, as_attachment=True, download_name=os.path.basename(path))

    if mode == "zip" or data.get("as_zip"):
        zip_path, resultats = export_all_filieres_zip(
            date_lundi, etablissement=etablissement, type_cours=type_cours
        )
        if not zip_path:
            return jsonify({"error": "Aucun PDF à exporter"}), 404
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=os.path.basename(zip_path),
            mimetype="application/zip",
        )

    resultats = export_all_filieres(
        date_lundi, etablissement=etablissement, type_cours=type_cours
    )
    nb_ok = sum(1 for r in resultats if r[1])
    return jsonify({
        "ok": True,
        "count": nb_ok,
        "files": [
            {
                "filiere": f"{f.annee} {f.nom}",
                "etablissement": getattr(f, "etablissement", None),
                "path": path,
            }
            for f, ok, path in resultats if ok
        ],
    })


@app.route("/api/export-pdf/download")
def api_download_pdf():
    path = request.args.get("path")
    if not path:
        return jsonify({"error": "Fichier introuvable"}), 404
    from config import EXPORT_DIR
    real = os.path.realpath(path)
    export_root = os.path.realpath(EXPORT_DIR)
    if not (real == export_root or real.startswith(export_root + os.sep)):
        return jsonify({"error": "Accès refusé"}), 403
    if not os.path.isfile(real):
        return jsonify({"error": "Fichier introuvable"}), 404
    return send_file(real, as_attachment=True, download_name=os.path.basename(real))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
