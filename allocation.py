"""Allocation automatique des salles (best-fit + rapport)."""
from collections import defaultdict
import sqlite3

from config import ANNEE_COURANTE, DB_PATH, JOURS
from database import get_effectif, get_salles, get_tous_cours_par_jour


def allouer_salles_par_jour(date_lundi, jour):
    """
    Alloue les salles pour un jour donné.

    - Priorité aux plus gros effectifs
    - Best-fit : plus petite salle suffisante
    - Groupes TC partagent une salle
    - Retourne un rapport {assigned, failed, cleared}
    """
    rapport = {"assigned": 0, "failed": [], "cleared": 0, "jour": jour}
    salles = get_salles()
    cours_jour = [
        c for c in get_tous_cours_par_jour(date_lundi, jour)
        if (c.matiere or "").strip()
    ]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if not cours_jour:
        conn.close()
        return {}, rapport

    # Sans salles : vider les allocations existantes
    if not salles:
        ids = []
        for c in cours_jour:
            cur.execute("UPDATE cours SET salle_id = NULL WHERE id = ?", (c.id,))
            ids.append(c.id)
            rapport["cleared"] += 1
            rapport["failed"].append({
                "cours_id": c.id,
                "filiere_id": c.filiere_id,
                "matiere": c.matiere,
                "creneau": c.creneau,
                "effectif": get_effectif(ANNEE_COURANTE, c.filiere_id),
                "reason": "Aucune salle configurée",
            })
        conn.commit()
        conn.close()
        return {cid: None for cid in ids}, rapport

    # Best-fit : plus petite capacité d'abord
    salles_sorted = sorted(salles, key=lambda s: s.capacite)

    par_creneau = defaultdict(list)
    for cours in cours_jour:
        par_creneau[cours.creneau].append(cours)

    allocation = {}

    for creneau, cours_list in par_creneau.items():
        groupes = defaultdict(list)
        for c in cours_list:
            key = c.groupe_tc if c.groupe_tc else f"alone_{c.id}"
            groupes[key].append(c)

        jobs = []
        for key, cours_groupe in groupes.items():
            effectif_total = sum(
                get_effectif(ANNEE_COURANTE, c.filiere_id) for c in cours_groupe
            )
            jobs.append((effectif_total, cours_groupe, key))

        jobs.sort(key=lambda x: x[0], reverse=True)

        salles_occupees = set()
        for effectif, cours_groupe, key in jobs:
            salle_choisie = None
            reason = None

            if effectif <= 0:
                reason = "Effectif nul ou manquant"
            else:
                candidates = [
                    s for s in salles_sorted
                    if s.id not in salles_occupees and s.capacite >= effectif
                ]
                if candidates:
                    salle_choisie = candidates[0]  # plus petite suffisante
                else:
                    reason = "Aucune salle assez grande"

            if salle_choisie:
                salles_occupees.add(salle_choisie.id)
                for c in cours_groupe:
                    allocation[c.id] = salle_choisie.id
                    rapport["assigned"] += 1
            else:
                for c in cours_groupe:
                    allocation[c.id] = None
                    rapport["failed"].append({
                        "cours_id": c.id,
                        "filiere_id": c.filiere_id,
                        "matiere": c.matiere,
                        "creneau": creneau,
                        "effectif": effectif,
                        "reason": reason or "Échec allocation",
                    })

    for cours_id, salle_id in allocation.items():
        cur.execute("UPDATE cours SET salle_id = ? WHERE id = ?", (salle_id, cours_id))

    conn.commit()
    conn.close()
    return allocation, rapport


def allouer_toute_la_semaine(date_lundi):
    """Alloue les salles pour tous les jours. Retourne un rapport agrégé."""
    total = {"assigned": 0, "failed": [], "cleared": 0, "jours": {}}
    for jour in JOURS:
        _, rapport = allouer_salles_par_jour(date_lundi, jour)
        total["assigned"] += rapport["assigned"]
        total["cleared"] += rapport["cleared"]
        total["failed"].extend(rapport["failed"])
        total["jours"][jour] = {
            "assigned": rapport["assigned"],
            "failed": len(rapport["failed"]),
        }
    return total
