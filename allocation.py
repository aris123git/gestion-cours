from collections import defaultdict
from config import DB_PATH, ANNEE_COURANTE, JOURS
from database import get_salles, get_effectif, get_tous_cours_par_jour
import sqlite3

def allouer_salles_par_jour(date_lundi, jour):
    """
    Alloue les salles pour un jour donné.
    Règle : les plus grands effectifs choisissent les plus grandes salles en premier.
    """
    salles = get_salles()
    if not salles:
        return {}
    
    # Trier les salles par capacité DÉCROISSANTE (les plus grandes d'abord)
    salles.sort(key=lambda s: s.capacite, reverse=True)
    
    # Récupérer tous les cours de ce jour
    cours_jour = get_tous_cours_par_jour(date_lundi, jour)
    if not cours_jour:
        return {}
    
    # Grouper par créneau (matin/après-midi)
    par_creneau = defaultdict(list)
    for cours in cours_jour:
        par_creneau[cours.creneau].append(cours)
    
    allocation = {}
    
    for creneau, cours_list in par_creneau.items():
        # Grouper par groupe TC (tronc commun)
        groupes = defaultdict(list)
        for c in cours_list:
            key = c.groupe_tc if c.groupe_tc else f"alone_{c.id}"
            groupes[key].append(c)
        
        # Calculer l'effectif total pour chaque groupe
        jobs = []
        for key, cours_groupe in groupes.items():
            effectif_total = 0
            for c in cours_groupe:
                effectif_total += get_effectif(ANNEE_COURANTE, c.filiere_id)
            jobs.append((effectif_total, cours_groupe))
        
        # Trier par effectif DÉCROISSANT (priorité aux plus gros)
        jobs.sort(key=lambda x: x[0], reverse=True)
        
        # Allouer les salles
        salles_occupees = set()
        for effectif, cours_groupe in jobs:
            salle_choisie = None
            for salle in salles:
                if salle.id not in salles_occupees and salle.capacite >= effectif:
                    salle_choisie = salle
                    break
            if salle_choisie:
                salles_occupees.add(salle_choisie.id)
                for c in cours_groupe:
                    allocation[c.id] = salle_choisie.id
            else:
                # Aucune salle trouvée (capacité insuffisante)
                for c in cours_groupe:
                    allocation[c.id] = None
    
    # Mettre à jour la base de données
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for cours_id, salle_id in allocation.items():
        cur.execute("UPDATE cours SET salle_id = ? WHERE id = ?", (salle_id, cours_id))
    conn.commit()
    conn.close()
    
    return allocation

def allouer_toute_la_semaine(date_lundi):
    """Alloue les salles pour tous les jours de la semaine"""
    for jour in JOURS:
        allouer_salles_par_jour(date_lundi, jour)