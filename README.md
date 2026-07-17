# GestionCours

Application de gestion des emplois du temps universitaires (IST / UBS).

## Démarrage (interface web moderne)

```bash
pip install -r requirements.txt
python main.py
```

Ouvrez ensuite [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Ancienne interface bureau (Tkinter)

```bash
python main.py --desktop
```

## Fonctionnalités

- Emploi du temps hebdomadaire par filière / année / université
- Édition des cours (matière, enseignant, tronc commun)
- Allocation automatique des salles selon les effectifs
- Export PDF (filière ou toutes)
- Copie d'une semaine vers une autre
- Gestion des salles, effectifs et filières
- Recherche matière / enseignant
- Détection des conflits d'enseignants
- Raccourcis clavier (`←` `→` semaine, `T` aujourd'hui, `/` recherche)

## Structure

- `app.py` — API Flask + pages web
- `interface.py` — UI Tkinter (optionnelle)
- `database.py` — accès SQLite
- `allocation.py` — allocation des salles
- `export_pdf.py` — génération PDF
- `static/` / `templates/` — frontend moderne
