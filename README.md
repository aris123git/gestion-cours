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

## Tests

```bash
pip install -r requirements.txt
pytest -v
```

## Créer un `.exe` Windows

À faire **sur Windows**, dans le dossier du projet (branche avec `requirements.txt`, `templates/`, `static/`) :

```bat
build_exe.bat
```

Ou manuellement :

```bat
pip install -r requirements.txt pyinstaller
pyinstaller GestionCours.spec
```

Puis lancez `dist\GestionCours.exe` :
- le navigateur s’ouvre sur http://127.0.0.1:5000 (pas de terminal noir)
- une petite fenêtre « GestionCours est en cours » reste ouverte — fermez-la pour quitter

Si ça échoue : le fichier `gestioncours-error.log` à côté du `.exe`.

> Le `.exe` ne peut pas être généré depuis Linux/macOS. Windows Defender peut parfois bloquer un nouvel exécutable PyInstaller — autorisez-le si demandé.

## Fonctionnalités

- Emploi du temps hebdomadaire par filière / année / université
- Édition des cours (matière, enseignant, tronc commun)
- Allocation automatique des salles selon les effectifs
- Export PDF soigné (une filière) ou archive ZIP (toutes, filtrée par université)
- Design PDF aligné sur l'interface (vert campus, terracotta, polices Syne/Manrope)
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
