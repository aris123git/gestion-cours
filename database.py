import sqlite3
from config import DB_PATH
from models import Salle, Filiere, Cours, Effectif

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # === TABLES EXISTANTES ===
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
    
    # === NOUVELLES TABLES ===
    c.execute('''CREATE TABLE IF NOT EXISTS etablissements (
                    id INTEGER PRIMARY KEY,
                    nom TEXT UNIQUE NOT NULL
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS types_cours (
                    id INTEGER PRIMARY KEY,
                    nom TEXT UNIQUE NOT NULL
                )''')
    
    # Ajout des valeurs par défaut
    c.execute("INSERT OR IGNORE INTO etablissements (id, nom) VALUES (1, 'IST')")
    c.execute("INSERT OR IGNORE INTO etablissements (id, nom) VALUES (2, 'UBS')")
    c.execute("INSERT OR IGNORE INTO types_cours (id, nom) VALUES (1, 'Jour')")
    c.execute("INSERT OR IGNORE INTO types_cours (id, nom) VALUES (2, 'Soir')")
    c.execute("INSERT OR IGNORE INTO types_cours (id, nom) VALUES (3, 'En ligne')")
    
    # Ajout des colonnes si elles n'existent pas
    try:
        c.execute("ALTER TABLE filieres ADD COLUMN etablissement_id INTEGER")
    except sqlite3.OperationalError:
        pass
    
    try:
        c.execute("ALTER TABLE salles ADD COLUMN etablissement_id INTEGER")
    except sqlite3.OperationalError:
        pass
    
    try:
        c.execute("ALTER TABLE cours ADD COLUMN type_cours_id INTEGER")
    except sqlite3.OperationalError:
        pass
    
    # Mettre à jour les anciennes filières (etablissement_id = NULL → IST)
    c.execute("UPDATE filieres SET etablissement_id = 1 WHERE etablissement_id IS NULL")
    
    conn.commit()
    conn.close()
    print("Base de données initialisée avec succès")

# ========== FILIERES ==========
def ajouter_filiere(annee, nom, etablissement_id=1):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    query = """
        SELECT f.id, f.annee, f.nom 
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
    return [Filiere(id=r[0], annee=r[1], nom=r[2]) for r in rows]

def get_filiere_by_id(id_):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, annee, nom FROM filieres WHERE id = ?", (id_,))
    r = c.fetchone()
    conn.close()
    if r:
        return Filiere(id=r[0], annee=r[1], nom=r[2])
    return None

def supprimer_filiere(filiere_id):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, nom, capacite FROM salles ORDER BY capacite, nom")
    rows = c.fetchall()
    conn.close()
    return [Salle(id=r[0], nom=r[1], capacite=r[2]) for r in rows]

def supprimer_salle(id_):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM salles WHERE id = ?", (id_,))
    conn.commit()
    conn.close()

def get_salle_by_id(salle_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, nom, capacite FROM salles WHERE id = ?", (salle_id,))
    r = c.fetchone()
    conn.close()
    if r:
        return Salle(id=r[0], nom=r[1], capacite=r[2])
    return None

# ========== EFFECTIFS ==========
def set_effectif(annee_univ, filiere_id, effectif):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO effectifs (annee_universitaire, filiere_id, effectif) VALUES (?, ?, ?)",
              (annee_univ, filiere_id, effectif))
    conn.commit()
    conn.close()

def get_effectif(annee_univ, filiere_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT effectif FROM effectifs WHERE annee_universitaire = ? AND filiere_id = ?", (annee_univ, filiere_id))
    r = c.fetchone()
    conn.close()
    return r[0] if r else 0

# ========== COURS ==========
def supprimer_cours_filiere_semaine(filiere_id, date_lundi):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM cours WHERE filiere_id = ? AND date_lundi = ?", (filiere_id, date_lundi))
    c.execute("DELETE FROM matieres_semaine WHERE filiere_id = ? AND date_lundi = ?", (filiere_id, date_lundi))
    conn.commit()
    conn.close()

def sauvegarder_cours(cours: Cours):
    conn = sqlite3.connect(DB_PATH)
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
    
    c.execute("INSERT OR REPLACE INTO matiere_enseignant (filiere_id, matiere, enseignant, last_used) VALUES (?,?,?, CURRENT_TIMESTAMP)",
              (cours.filiere_id, cours.matiere, cours.enseignant))
    c.execute("INSERT OR IGNORE INTO matieres_semaine (filiere_id, date_lundi, matiere) VALUES (?,?,?)",
              (cours.filiere_id, cours.date_lundi, cours.matiere))
    c.execute("INSERT OR IGNORE INTO enseignants_par_matiere (matiere, enseignant) VALUES (?,?)",
              (cours.matiere, cours.enseignant))
    
    conn.commit()
    conn.close()
    return cours.id

def get_cours(filiere_id, date_lundi, jour, creneau):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT matiere FROM matieres_semaine WHERE filiere_id=? AND date_lundi=? ORDER BY rowid",
              (filiere_id, date_lundi))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_enseignants_pour_matiere(matiere):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT enseignant FROM enseignants_par_matiere WHERE matiere = ? ORDER BY enseignant", (matiere,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_dernier_enseignant_filiere_matiere(filiere_id, matiere):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT enseignant FROM matiere_enseignant WHERE filiere_id=? AND matiere=? ORDER BY last_used DESC LIMIT 1",
              (filiere_id, matiere))
    r = c.fetchone()
    conn.close()
    return r[0] if r else ""