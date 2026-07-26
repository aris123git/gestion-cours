import sqlite3
from config import DB_PATH
from models import Salle, Filiere, Cours, Effectif


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS filieres (
                    id INTEGER PRIMARY KEY,
                    annee TEXT NOT NULL,
                    nom TEXT NOT NULL,
                    UNIQUE(annee, nom)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS salles (
                    id INTEGER PRIMARY KEY,
                    nom TEXT UNIQUE NOT NULL,
                    capacite INTEGER NOT NULL
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS effectifs (
                    annee_universitaire TEXT NOT NULL,
                    filiere_id INTEGER NOT NULL,
                    effectif INTEGER NOT NULL,
                    PRIMARY KEY (annee_universitaire, filiere_id),
                    FOREIGN KEY (filiere_id) REFERENCES filieres(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS cours (
                    id INTEGER PRIMARY KEY,
                    filiere_id INTEGER NOT NULL,
                    date_lundi TEXT NOT NULL,
                    jour TEXT NOT NULL,
                    creneau TEXT NOT NULL,
                    matiere TEXT NOT NULL,
                    enseignant TEXT NOT NULL,
                    salle_id INTEGER,
                    groupe_tc TEXT,
                    FOREIGN KEY (filiere_id) REFERENCES filieres(id),
                    FOREIGN KEY (salle_id) REFERENCES salles(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS matiere_enseignant (
                    filiere_id INTEGER NOT NULL,
                    matiere TEXT NOT NULL,
                    enseignant TEXT NOT NULL,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (filiere_id, matiere),
                    FOREIGN KEY (filiere_id) REFERENCES filieres(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS matieres_semaine (
                    filiere_id INTEGER NOT NULL,
                    date_lundi TEXT NOT NULL,
                    matiere TEXT NOT NULL,
                    PRIMARY KEY (filiere_id, date_lundi, matiere)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS enseignants_par_matiere (
                    matiere TEXT NOT NULL,
                    enseignant TEXT NOT NULL,
                    PRIMARY KEY (matiere, enseignant)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS etablissements (
                    id INTEGER PRIMARY KEY,
                    nom TEXT UNIQUE NOT NULL
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS types_cours (
                    id INTEGER PRIMARY KEY,
                    nom TEXT UNIQUE NOT NULL
                )''')

    c.execute("INSERT OR IGNORE INTO etablissements (id, nom) VALUES (1, 'IST')")
    c.execute("INSERT OR IGNORE INTO etablissements (id, nom) VALUES (2, 'UBS')")
    c.execute("INSERT OR IGNORE INTO types_cours (id, nom) VALUES (1, 'Jour')")
    c.execute("INSERT OR IGNORE INTO types_cours (id, nom) VALUES (2, 'Soir')")
    c.execute("INSERT OR IGNORE INTO types_cours (id, nom) VALUES (3, 'En ligne')")

    for stmt in (
        "ALTER TABLE filieres ADD COLUMN etablissement_id INTEGER",
        "ALTER TABLE salles ADD COLUMN etablissement_id INTEGER",
        "ALTER TABLE cours ADD COLUMN type_cours_id INTEGER",
    ):
        try:
            c.execute(stmt)
        except sqlite3.OperationalError:
            pass

    c.execute("UPDATE filieres SET etablissement_id = 1 WHERE etablissement_id IS NULL")

    # Dédupliquer les créneaux avant l'index unique
    c.execute("""
        DELETE FROM cours WHERE id NOT IN (
            SELECT MIN(id) FROM cours
            GROUP BY filiere_id, date_lundi, jour, creneau
        )
    """)
    c.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_cours_slot
        ON cours(filiere_id, date_lundi, jour, creneau)
    """)

    # Salles par défaut si la table est vide
    c.execute("SELECT COUNT(*) FROM salles")
    if c.fetchone()[0] == 0:
        for nom, cap in (
            ("Amphi A", 120),
            ("Amphi B", 80),
            ("Salle 101", 45),
            ("Salle 102", 40),
            ("Salle 201", 30),
            ("Labo Info", 25),
        ):
            c.execute(
                "INSERT INTO salles (nom, capacite, etablissement_id) VALUES (?, ?, 1)",
                (nom, cap),
            )

    conn.commit()
    conn.close()
    print("Base de données initialisée avec succès")

# ========== FILIERES ==========
def ajouter_filiere(annee, nom, etablissement_id=1):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO filieres (annee, nom, etablissement_id) VALUES (?, ?, ?)", 
                  (annee, nom, etablissement_id))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_filieres(annee=None, etablissement=None):
    conn = get_conn()
    c = conn.cursor()
    
    query = """
        SELECT f.id, f.annee, f.nom, e.nom
        FROM filieres f
        LEFT JOIN etablissements e ON f.etablissement_id = e.id
        WHERE 1=1
    """
    params = []
    
    if annee:
        query += " AND f.annee = ?"
        params.append(annee)
    
    if etablissement:
        query += " AND e.nom = ?"
        params.append(etablissement)
    
    query += " ORDER BY f.annee, f.nom"
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [Filiere(id=r[0], annee=r[1], nom=r[2], etablissement=r[3]) for r in rows]

def get_filiere_by_id(id_):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT f.id, f.annee, f.nom, e.nom
        FROM filieres f
        LEFT JOIN etablissements e ON f.etablissement_id = e.id
        WHERE f.id = ?
    """, (id_,))
    r = c.fetchone()
    conn.close()
    if r:
        return Filiere(id=r[0], annee=r[1], nom=r[2], etablissement=r[3])
    return None

def supprimer_filiere(filiere_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM cours WHERE filiere_id = ?", (filiere_id,))
    c.execute("DELETE FROM effectifs WHERE filiere_id = ?", (filiere_id,))
    c.execute("DELETE FROM matiere_enseignant WHERE filiere_id = ?", (filiere_id,))
    c.execute("DELETE FROM matieres_semaine WHERE filiere_id = ?", (filiere_id,))
    c.execute("DELETE FROM filieres WHERE id = ?", (filiere_id,))
    conn.commit()
    conn.close()

# ========== SALLES ==========
def ajouter_salle(nom, capacite):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO salles (nom, capacite) VALUES (?, ?)", (nom, capacite))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_salles():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, nom, capacite FROM salles ORDER BY capacite, nom")
    rows = c.fetchall()
    conn.close()
    return [Salle(id=r[0], nom=r[1], capacite=r[2]) for r in rows]

def supprimer_salle(id_):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE cours SET salle_id = NULL WHERE salle_id = ?", (id_,))
    c.execute("DELETE FROM salles WHERE id = ?", (id_,))
    conn.commit()
    conn.close()

def get_salle_by_id(salle_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, nom, capacite FROM salles WHERE id = ?", (salle_id,))
    r = c.fetchone()
    conn.close()
    if r:
        return Salle(id=r[0], nom=r[1], capacite=r[2])
    return None

# ========== EFFECTIFS ==========
def set_effectif(annee_univ, filiere_id, effectif):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO effectifs (annee_universitaire, filiere_id, effectif) VALUES (?, ?, ?)",
              (annee_univ, filiere_id, effectif))
    conn.commit()
    conn.close()

def get_effectif(annee_univ, filiere_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT effectif FROM effectifs WHERE annee_universitaire = ? AND filiere_id = ?", (annee_univ, filiere_id))
    r = c.fetchone()
    conn.close()
    return r[0] if r else 0

# ========== COURS ==========
def supprimer_cours_filiere_semaine(filiere_id, date_lundi):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM cours WHERE filiere_id = ? AND date_lundi = ?", (filiere_id, date_lundi))
    c.execute("DELETE FROM matieres_semaine WHERE filiere_id = ? AND date_lundi = ?", (filiere_id, date_lundi))
    conn.commit()
    conn.close()

def sauvegarder_cours(cours: Cours):
    conn = get_conn()
    c = conn.cursor()
    if cours.id:
        c.execute("""UPDATE cours SET matiere=?, enseignant=?, salle_id=?, groupe_tc=?
                     WHERE id=?""", (cours.matiere, cours.enseignant, cours.salle_id, cours.groupe_tc, cours.id))
    else:
        c.execute("""INSERT INTO cours (filiere_id, date_lundi, jour, creneau, matiere, enseignant, salle_id, groupe_tc)
                     VALUES (?,?,?,?,?,?,?,?)""",
                  (cours.filiere_id, cours.date_lundi, cours.jour, cours.creneau,
                   cours.matiere, cours.enseignant, cours.salle_id, cours.groupe_tc))
        cours.id = c.lastrowid

    if (cours.matiere or "").strip() and (cours.enseignant or "").strip():
        c.execute(
            "INSERT OR REPLACE INTO matiere_enseignant (filiere_id, matiere, enseignant, last_used) VALUES (?,?,?, CURRENT_TIMESTAMP)",
            (cours.filiere_id, cours.matiere, cours.enseignant),
        )
        c.execute(
            "INSERT OR IGNORE INTO matieres_semaine (filiere_id, date_lundi, matiere) VALUES (?,?,?)",
            (cours.filiere_id, cours.date_lundi, cours.matiere),
        )
        c.execute(
            "INSERT OR IGNORE INTO enseignants_par_matiere (matiere, enseignant) VALUES (?,?)",
            (cours.matiere, cours.enseignant),
        )

    conn.commit()
    conn.close()
    return cours.id

def get_cours(filiere_id, date_lundi, jour, creneau):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT id, matiere, enseignant, salle_id, groupe_tc
                 FROM cours WHERE filiere_id=? AND date_lundi=? AND jour=? AND creneau=?""",
              (filiere_id, date_lundi, jour, creneau))
    r = c.fetchone()
    conn.close()
    if r:
        return Cours(id=r[0], filiere_id=filiere_id, date_lundi=date_lundi, jour=jour, creneau=creneau,
                     matiere=r[1], enseignant=r[2], salle_id=r[3], groupe_tc=r[4])
    return None

def get_tous_cours_semaine(date_lundi):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT id, filiere_id, jour, creneau, matiere, enseignant, salle_id, groupe_tc
                 FROM cours WHERE date_lundi=? ORDER BY filiere_id, jour, creneau""", (date_lundi,))
    rows = c.fetchall()
    conn.close()
    cours_list = []
    for r in rows:
        cours_list.append(Cours(id=r[0], filiere_id=r[1], date_lundi=date_lundi, jour=r[2],
                                creneau=r[3], matiere=r[4], enseignant=r[5], salle_id=r[6], groupe_tc=r[7]))
    return cours_list

def get_tous_cours_par_jour(date_lundi, jour):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, filiere_id, jour, creneau, matiere, enseignant, salle_id, groupe_tc
        FROM cours
        WHERE date_lundi = ? AND jour = ?
        ORDER BY filiere_id, creneau
    """, (date_lundi, jour))
    rows = c.fetchall()
    conn.close()
    return [Cours(id=r[0], filiere_id=r[1], date_lundi=date_lundi, jour=r[2],
                  creneau=r[3], matiere=r[4], enseignant=r[5], salle_id=r[6], groupe_tc=r[7])
            for r in rows]

def get_matieres_semaine(filiere_id, date_lundi):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT matiere FROM matieres_semaine WHERE filiere_id=? AND date_lundi=? ORDER BY rowid",
              (filiere_id, date_lundi))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_enseignants_pour_matiere(matiere):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT enseignant FROM enseignants_par_matiere WHERE matiere = ? ORDER BY enseignant", (matiere,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_dernier_enseignant_filiere_matiere(filiere_id, matiere):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT enseignant FROM matiere_enseignant WHERE filiere_id=? AND matiere=? ORDER BY last_used DESC LIMIT 1",
              (filiere_id, matiere))
    r = c.fetchone()
    conn.close()
    return r[0] if r else ""


def supprimer_cours(cours_id, clear_tc_group=False):
    """Supprime un cours. Si clear_tc_group, retire tout le tronc commun du créneau."""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT filiere_id, date_lundi, jour, creneau, matiere, groupe_tc FROM cours WHERE id = ?",
        (cours_id,),
    )
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    filiere_id, date_lundi, jour, creneau, matiere, groupe_tc = row

    if clear_tc_group and groupe_tc:
        c.execute(
            """DELETE FROM cours
               WHERE groupe_tc = ? AND date_lundi = ? AND jour = ? AND creneau = ?""",
            (groupe_tc, date_lundi, jour, creneau),
        )
    else:
        c.execute("DELETE FROM cours WHERE id = ?", (cours_id,))

    # Nettoyer les suggestions matière si plus utilisée cette semaine
    if matiere:
        c.execute(
            """DELETE FROM matieres_semaine
               WHERE filiere_id = ? AND date_lundi = ? AND matiere = ?
               AND NOT EXISTS (
                 SELECT 1 FROM cours
                 WHERE filiere_id = ? AND date_lundi = ? AND matiere = ?
               )""",
            (filiere_id, date_lundi, matiere, filiere_id, date_lundi, matiere),
        )
    conn.commit()
    conn.close()
    return True


def modifier_salle(salle_id, nom, capacite):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            "UPDATE salles SET nom = ?, capacite = ? WHERE id = ?",
            (nom, capacite, salle_id),
        )
        conn.commit()
        return c.rowcount > 0
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_grille_filiere(filiere_id, date_lundi):
    """Retourne la grille complète avec noms de salles pour une filière/semaine."""
    from config import JOURS, CRENEAUX
    grille = {}
    for jour in JOURS:
        for creneau, _, _ in CRENEAUX:
            cours = get_cours(filiere_id, date_lundi, jour, creneau)
            if cours:
                salle_nom = None
                if cours.salle_id:
                    salle = get_salle_by_id(cours.salle_id)
                    salle_nom = salle.nom if salle else None
                grille[f"{jour}|{creneau}"] = {
                    "id": cours.id,
                    "matiere": cours.matiere,
                    "enseignant": cours.enseignant,
                    "salle_id": cours.salle_id,
                    "salle_nom": salle_nom,
                    "groupe_tc": cours.groupe_tc,
                }
            else:
                grille[f"{jour}|{creneau}"] = None
    return grille


def get_filieres_avec_effectif(annee=None, etablissement=None, annee_univ=None):
    from config import ANNEE_COURANTE
    if annee_univ is None:
        annee_univ = ANNEE_COURANTE
    filieres = get_filieres(annee, etablissement)
    result = []
    for f in filieres:
        result.append({
            "id": f.id,
            "annee": f.annee,
            "nom": f.nom,
            "etablissement": f.etablissement,
            "effectif": get_effectif(annee_univ, f.id),
        })
    return result


def get_stats_semaine(date_lundi, filiere_id=None):
    conn = get_conn()
    c = conn.cursor()
    if filiere_id:
        c.execute("SELECT COUNT(*) FROM cours WHERE date_lundi=? AND filiere_id=? AND matiere != ''",
                  (date_lundi, filiere_id))
        total = c.fetchone()[0]
        c.execute("""SELECT COUNT(*) FROM cours
                     WHERE date_lundi=? AND filiere_id=? AND salle_id IS NOT NULL AND matiere != ''""",
                  (date_lundi, filiere_id))
        avec_salle = c.fetchone()[0]
        c.execute("""SELECT COUNT(DISTINCT groupe_tc) FROM cours
                     WHERE date_lundi=? AND filiere_id=? AND groupe_tc IS NOT NULL""",
                  (date_lundi, filiere_id))
        tc = c.fetchone()[0]
    else:
        c.execute("SELECT COUNT(*) FROM cours WHERE date_lundi=? AND matiere != ''", (date_lundi,))
        total = c.fetchone()[0]
        c.execute("""SELECT COUNT(*) FROM cours
                     WHERE date_lundi=? AND salle_id IS NOT NULL AND matiere != ''""", (date_lundi,))
        avec_salle = c.fetchone()[0]
        c.execute("""SELECT COUNT(DISTINCT groupe_tc) FROM cours
                     WHERE date_lundi=? AND groupe_tc IS NOT NULL""", (date_lundi,))
        tc = c.fetchone()[0]
    conn.close()
    return {"cours": total, "avec_salle": avec_salle, "tronc_commun": tc}


def copier_semaine(filiere_id, date_source, date_cible):
    """Copie les cours d'une semaine vers une autre pour une filière."""
    import time
    source = get_tous_cours_semaine(date_source)
    source = [c for c in source if c.filiere_id == filiere_id and c.matiere]
    if not source:
        return 0
    supprimer_cours_filiere_semaine(filiere_id, date_cible)
    tc_map = {}
    stamp = int(time.time())
    count = 0
    for c in source:
        groupe = None
        if c.groupe_tc:
            if c.groupe_tc not in tc_map:
                tc_map[c.groupe_tc] = f"TC_COPY_{stamp}_{len(tc_map)}"
            groupe = tc_map[c.groupe_tc]
        nouveau = Cours(
            id=None,
            filiere_id=filiere_id,
            date_lundi=date_cible,
            jour=c.jour,
            creneau=c.creneau,
            matiere=c.matiere,
            enseignant=c.enseignant,
            salle_id=None,
            groupe_tc=groupe,
        )
        sauvegarder_cours(nouveau)
        count += 1
    return count


def rechercher_conflits_enseignant(date_lundi, jour, creneau, enseignant, exclude_cours_id=None):
    """Détecte si un enseignant est déjà pris sur ce créneau."""
    if not enseignant:
        return []
    conn = get_conn()
    c = conn.cursor()
    query = """
        SELECT c.id, c.filiere_id, f.nom, f.annee, c.matiere
        FROM cours c
        JOIN filieres f ON f.id = c.filiere_id
        WHERE c.date_lundi=? AND c.jour=? AND c.creneau=?
          AND LOWER(c.enseignant)=LOWER(?) AND c.matiere != ''
    """
    params = [date_lundi, jour, creneau, enseignant]
    if exclude_cours_id:
        query += " AND c.id != ?"
        params.append(exclude_cours_id)
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [{"cours_id": r[0], "filiere_id": r[1], "filiere": f"{r[3]} {r[2]}", "matiere": r[4]} for r in rows]


def get_tous_enseignants():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT enseignant FROM enseignants_par_matiere ORDER BY enseignant")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_toutes_matieres():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT matiere FROM matieres_semaine ORDER BY matiere")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_etablissements():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, nom FROM etablissements ORDER BY nom")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "nom": r[1]} for r in rows]


def get_types_cours():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, nom FROM types_cours ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "nom": r[1]} for r in rows]


def get_filieres_tc_groupe(groupe_tc, date_lundi, jour, creneau):
    if not groupe_tc:
        return []
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT filiere_id FROM cours
                 WHERE groupe_tc=? AND date_lundi=? AND jour=? AND creneau=?""",
              (groupe_tc, date_lundi, jour, creneau))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


def sync_tronc_commun(date_lundi, jour, creneau, target_ids, matiere, enseignant, groupe_tc):
    """
    Applique un tronc commun : met à jour les filières cibles et retire
    l'ancien groupe pour les filières désélectionnées.
    """
    old_ids = set()
    for fid in target_ids:
        existant = get_cours(fid, date_lundi, jour, creneau)
        if existant and existant.groupe_tc:
            old_ids.update(get_filieres_tc_groupe(
                existant.groupe_tc, date_lundi, jour, creneau
            ))

    # Retirer les anciennes membres non sélectionnées
    for fid in old_ids:
        if fid in target_ids:
            continue
        cours = get_cours(fid, date_lundi, jour, creneau)
        if cours and cours.groupe_tc:
            cours.groupe_tc = None
            sauvegarder_cours(cours)

    ids = []
    for fid in target_ids:
        cours = get_cours(fid, date_lundi, jour, creneau)
        if cours:
            cours.matiere = matiere
            cours.enseignant = enseignant
            cours.groupe_tc = groupe_tc
            sauvegarder_cours(cours)
            ids.append(cours.id)
        else:
            nouveau = Cours(
                None, fid, date_lundi, jour, creneau,
                matiere, enseignant, None, groupe_tc,
            )
            ids.append(sauvegarder_cours(nouveau))
    return ids


def rechercher_conflits_semaine(date_lundi, filiere_id=None):
    """Liste les conflits enseignants sur toute la semaine."""
    from config import JOURS, CRENEAUX
    conflits = []
    seen = set()
    cours_list = get_tous_cours_semaine(date_lundi)
    if filiere_id:
        # Inclure les conflits qui touchent cette filière
        pass
    by_slot = {}
    for c in cours_list:
        if not (c.matiere or "").strip() or not (c.enseignant or "").strip():
            continue
        key = (c.jour, c.creneau, c.enseignant.strip().lower())
        by_slot.setdefault(key, []).append(c)

    for (jour, creneau, ens_key), items in by_slot.items():
        # Même groupe TC = pas un conflit
        groupes = {c.groupe_tc or f"alone_{c.id}" for c in items}
        if len(items) <= 1:
            continue
        if len(groupes) == 1 and next(iter(groupes)).startswith("TC"):
            continue
        # Conflit si plusieurs groupes distincts
        if len(groupes) > 1 or (len(items) > 1 and all(not c.groupe_tc for c in items)):
            entry_key = (jour, creneau, ens_key)
            if entry_key in seen:
                continue
            seen.add(entry_key)
            if filiere_id and not any(c.filiere_id == filiere_id for c in items):
                continue
            conflits.append({
                "jour": jour,
                "creneau": creneau,
                "enseignant": items[0].enseignant,
                "cours": [
                    {
                        "id": c.id,
                        "filiere_id": c.filiere_id,
                        "matiere": c.matiere,
                        "groupe_tc": c.groupe_tc,
                    }
                    for c in items
                ],
            })
    return conflits


def type_cours_id_from_name(nom):
    if not nom:
        return None
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM types_cours WHERE nom = ?", (nom,))
    r = c.fetchone()
    conn.close()
    return r[0] if r else None