# GestionCours

Application locale de gestion des emplois du temps universitaires (IST / UBS).

## Démarrage (bureau natif PySide6 — recommandé)

Comme **Gestion_app** : fenêtre Windows native, **sans navigateur**.

```bash
pip install -r requirements.txt
python main.py
```

## Autres interfaces

```bash
python main.py --web     # Flask + navigateur local
python main.py --tk      # ancienne UI Tkinter
```

## Tests

```bash
pip install -r requirements.txt
pytest -v
```

## Créer un `.exe` Windows

```bat
build_exe.bat
```

Résultat : `dist\GestionCours.exe` — **fenêtre bureau** (PySide6), pas de navigateur.

> À builder sur Windows. Windows Defender peut demander une autorisation au premier lancement.

## Fonctionnalités

- Emploi du temps hebdomadaire par filière / année / université
- Édition des cours (matière, enseignant, tronc commun)
- Allocation automatique des salles selon les effectifs
- Export PDF (type Jour/Soir/En ligne, filières TC, notes BOA)
- Copie d'une semaine, conflits enseignants
- Gestion salles / effectifs / filières

## Structure

- `desktop/` — UI PySide6 (bureau)
- `app.py` / `static/` / `templates/` — UI web optionnelle
- `interface.py` — UI Tkinter optionnelle
- `database.py` — SQLite
- `allocation.py` — allocation des salles
- `export_pdf.py` — PDF
