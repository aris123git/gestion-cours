"""Fenêtre principale PySide6 — Planning + navigation latérale."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QApplication,
)

import os

from config import (
    ANNEE_COURANTE,
    CRENEAUX,
    CRENEAUX_LABELS,
    JOURS,
    RESOURCE_DIR,
)
from database import (
    get_cours,
    get_etablissements,
    get_filieres,
    get_filieres_avec_effectif,
    get_grille_filiere,
    get_salle_by_id,
    get_stats_semaine,
    init_db,
    sauvegarder_cours,
    supprimer_cours,
    supprimer_cours_filiere_semaine,
    sync_tronc_commun,
    rechercher_conflits_enseignant,
    rechercher_conflits_semaine,
    copier_semaine,
)
from models import Cours
from allocation import allouer_toute_la_semaine
from export_pdf import export_une_filiere, export_all_filieres_zip
from utils import get_lundi_week_courante, get_semaine_precedente, get_semaine_suivante, format_date_fr

from desktop.dialogs import CoursDialog, EffectifsDialog, FilieresDialog, SallesDialog
from desktop.theme import build_stylesheet


def _to_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


class SlotCell(QFrame):
    def __init__(self, jour: str, creneau: str, on_edit, parent=None):
        super().__init__(parent)
        self.jour = jour
        self.creneau = creneau
        self.on_edit = on_edit
        self.setObjectName("SlotCell")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(88)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        self.matiere = QLabel("Ajouter…")
        self.matiere.setObjectName("SlotEmpty")
        self.enseignant = QLabel("")
        self.enseignant.setObjectName("SlotEnseignant")
        self.meta = QLabel("")
        self.meta.setObjectName("SlotMeta")
        layout.addWidget(self.matiere)
        layout.addWidget(self.enseignant)
        layout.addWidget(self.meta)
        layout.addStretch(1)

    def mouseDoubleClickEvent(self, event):
        self.on_edit(self.jour, self.creneau)
        super().mouseDoubleClickEvent(event)

    def set_cours(self, cours: dict | None):
        if not cours or not (cours.get("matiere") or "").strip():
            self.setProperty("filled", "false")
            self.setProperty("tc", "false")
            self.matiere.setObjectName("SlotEmpty")
            self.matiere.setText("Ajouter…")
            self.enseignant.setText("")
            self.meta.setText("")
        else:
            self.setProperty("filled", "true")
            self.setProperty("tc", "true" if cours.get("groupe_tc") else "false")
            self.matiere.setObjectName("SlotMatiere")
            self.matiere.setText(cours["matiere"])
            self.enseignant.setText(cours.get("enseignant") or "")
            bits = []
            if cours.get("salle_nom"):
                bits.append(f"Salle {cours['salle_nom']}")
            if cours.get("groupe_tc"):
                bits.append("Tronc commun")
            self.meta.setText(" · ".join(bits))
        self.style().unpolish(self)
        self.style().polish(self)
        self.matiere.style().unpolish(self.matiere)
        self.matiere.style().polish(self.matiere)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        init_db()
        self.setObjectName("MainWindow")
        self.setWindowTitle("GestionCours — Emplois du temps")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 820)

        self.date_lundi = get_lundi_week_courante()
        self.filiere_id = None
        self.cells: dict[tuple[str, str], SlotCell] = {}
        self.type_cours = "Jour"

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(14, 18, 14, 18)
        side.setSpacing(6)

        logo_path = os.path.join(RESOURCE_DIR, "fichiers", "logoist.jpeg")
        if os.path.exists(logo_path):
            logo = QLabel()
            pix = QPixmap(logo_path).scaled(42, 42, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pix)
            side.addWidget(logo)

        title = QLabel("GestionCours")
        title.setObjectName("SidebarTitle")
        side.addWidget(title)
        sub = QLabel("Planning universitaire")
        sub.setObjectName("SidebarSubtitle")
        side.addWidget(sub)

        self.nav_group_btns = []
        for text, slot in (
            ("Planning", self._noop),
            ("Salles", self.open_salles),
            ("Filières", self.open_filieres),
            ("Effectifs", self.open_effectifs),
        ):
            btn = QPushButton(text)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.clicked.connect(slot)
            side.addWidget(btn)
            self.nav_group_btns.append(btn)
        self.nav_group_btns[0].setChecked(True)

        side.addStretch(1)
        quit_btn = QPushButton("Quitter")
        quit_btn.setObjectName("DangerButton")
        quit_btn.clicked.connect(QApplication.instance().quit)
        side.addWidget(quit_btn)
        root.addWidget(sidebar)

        # Content
        content_wrap = QVBoxLayout()
        content_wrap.setContentsMargins(18, 16, 18, 16)
        content_wrap.setSpacing(12)
        content = QWidget()
        content.setLayout(content_wrap)
        root.addWidget(content, 1)

        header = QHBoxLayout()
        htext = QVBoxLayout()
        page_title = QLabel("Emploi du temps")
        page_title.setObjectName("PageTitle")
        hint = QLabel("Double-cliquez une case pour éditer · allocation auto des salles")
        hint.setObjectName("PageHint")
        htext.addWidget(page_title)
        htext.addWidget(hint)
        header.addLayout(htext, 1)
        content_wrap.addLayout(header)

        # Filters
        filters = QHBoxLayout()
        self.cb_annee = QComboBox()
        self.cb_annee.addItems(["L1", "L2", "L3", "Master", "Doctorat"])
        self.cb_etab = QComboBox()
        for e in get_etablissements():
            self.cb_etab.addItem(e["nom"], e["id"])
        self.cb_type = QComboBox()
        self.cb_type.addItems(["Jour", "Soir", "En ligne"])
        self.cb_filiere = QComboBox()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self._set_date_widget(self.date_lundi)

        for label, widget in (
            ("Année", self.cb_annee),
            ("Université", self.cb_etab),
            ("Type", self.cb_type),
            ("Filière", self.cb_filiere),
            ("Semaine", self.date_edit),
        ):
            box = QVBoxLayout()
            lab = QLabel(label)
            lab.setObjectName("PageHint")
            box.addWidget(lab)
            box.addWidget(widget)
            filters.addLayout(box)

        prev = QPushButton("◀")
        nxt = QPushButton("▶")
        today = QPushButton("Aujourd'hui")
        prev.clicked.connect(lambda: self.shift_week(-1))
        nxt.clicked.connect(lambda: self.shift_week(1))
        today.clicked.connect(self.goto_today)
        filters.addWidget(prev)
        filters.addWidget(nxt)
        filters.addWidget(today)
        filters.addStretch(1)
        content_wrap.addLayout(filters)

        # Stats
        stats_row = QHBoxLayout()
        self.stat_cours = self._stat_card("Cours")
        self.stat_salles = self._stat_card("Salles allouées")
        self.stat_tc = self._stat_card("Tronc commun")
        self.stat_week = self._stat_card("Semaine du", highlight=True)
        for card in (self.stat_cours, self.stat_salles, self.stat_tc, self.stat_week):
            stats_row.addWidget(card)
        content_wrap.addLayout(stats_row)

        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_alloc = QPushButton("Allouer les salles")
        self.btn_alloc.setObjectName("PrimaryButton")
        self.btn_conflits = QPushButton("Vérifier conflits")
        self.btn_pdf = QPushButton("PDF filière")
        self.btn_zip = QPushButton("Exporter ZIP")
        self.btn_copy = QPushButton("Copier semaine…")
        self.btn_reset = QPushButton("Réinitialiser")
        self.btn_reset.setObjectName("DangerButton")
        for b in (self.btn_alloc, self.btn_conflits, self.btn_pdf, self.btn_zip, self.btn_copy, self.btn_reset):
            toolbar.addWidget(b)
        toolbar.addStretch(1)
        content_wrap.addLayout(toolbar)

        self.btn_alloc.clicked.connect(self.allouer)
        self.btn_conflits.clicked.connect(self.verifier_conflits)
        self.btn_pdf.clicked.connect(self.export_one)
        self.btn_zip.clicked.connect(self.export_zip)
        self.btn_copy.clicked.connect(self.copy_week)
        self.btn_reset.clicked.connect(self.reset_week)

        # Schedule grid in scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        grid_host = QWidget()
        self.grid = QGridLayout(grid_host)
        self.grid.setSpacing(8)
        self.grid.setContentsMargins(4, 4, 4, 4)
        scroll.setWidget(grid_host)
        content_wrap.addWidget(scroll, 1)

        self.grid.addWidget(QLabel(""), 0, 0)
        for j, jour in enumerate(JOURS, start=1):
            lab = QLabel(jour)
            lab.setObjectName("DayHeader")
            self.grid.addWidget(lab, 0, j)
        for i, (creneau, _, _) in enumerate(CRENEAUX, start=1):
            lab = QLabel(CRENEAUX_LABELS[i - 1])
            lab.setObjectName("CreneauLabel")
            self.grid.addWidget(lab, i, 0)
            for j, jour in enumerate(JOURS, start=1):
                cell = SlotCell(jour, creneau, self.edit_slot)
                self.cells[(jour, creneau)] = cell
                self.grid.addWidget(cell, i, j)

        self.cb_annee.currentTextChanged.connect(lambda _: self.reload_filieres())
        self.cb_etab.currentTextChanged.connect(lambda _: self.reload_filieres())
        self.cb_type.currentTextChanged.connect(self._on_type)
        self.cb_filiere.currentIndexChanged.connect(self._on_filiere)
        self.date_edit.dateChanged.connect(self._on_date)

        self.reload_filieres()

    def _noop(self):
        self.nav_group_btns[0].setChecked(True)

    def _stat_card(self, title: str, highlight: bool = False) -> QFrame:
        card = QFrame()
        card.setObjectName("StatHighlight" if highlight else "StatCard")
        lay = QVBoxLayout(card)
        val = QLabel("0")
        val.setObjectName("StatValue")
        lab = QLabel(title)
        lab.setObjectName("StatTitle")
        lay.addWidget(val)
        lay.addWidget(lab)
        card._value = val  # type: ignore[attr-defined]
        return card

    def _set_date_widget(self, iso: str):
        d = datetime.fromisoformat(iso).date()
        self.date_edit.blockSignals(True)
        self.date_edit.setDate(QDate(d.year, d.month, d.day))
        self.date_edit.blockSignals(False)

    def _on_type(self, text: str):
        self.type_cours = text

    def _on_filiere(self, _idx: int):
        self.filiere_id = self.cb_filiere.currentData()
        self.refresh_grille()

    def _on_date(self, qdate: QDate):
        d = date(qdate.year(), qdate.month(), qdate.day())
        self.date_lundi = _to_monday(d).isoformat()
        self._set_date_widget(self.date_lundi)
        self.refresh_grille()

    def shift_week(self, direction: int):
        if direction < 0:
            self.date_lundi = get_semaine_precedente(self.date_lundi)
        else:
            self.date_lundi = get_semaine_suivante(self.date_lundi)
        self._set_date_widget(self.date_lundi)
        self.refresh_grille()

    def goto_today(self):
        self.date_lundi = get_lundi_week_courante()
        self._set_date_widget(self.date_lundi)
        self.refresh_grille()

    def reload_filieres(self):
        annee = self.cb_annee.currentText()
        etab = self.cb_etab.currentText()
        rows = get_filieres_avec_effectif(annee, etab)
        current = self.filiere_id
        self.cb_filiere.blockSignals(True)
        self.cb_filiere.clear()
        for r in rows:
            self.cb_filiere.addItem(f"{r['nom']} ({r['effectif']})", r["id"])
        self.cb_filiere.blockSignals(False)
        if not rows:
            self.filiere_id = None
            self.refresh_grille()
            return
        idx = 0
        for i, r in enumerate(rows):
            if r["id"] == current:
                idx = i
                break
        self.cb_filiere.setCurrentIndex(idx)
        self.filiere_id = self.cb_filiere.currentData()
        self.refresh_grille()

    def refresh_grille(self):
        if not self.filiere_id:
            for cell in self.cells.values():
                cell.set_cours(None)
            self.stat_cours._value.setText("0")
            self.stat_salles._value.setText("0")
            self.stat_tc._value.setText("0")
            self.stat_week._value.setText(format_date_fr(self.date_lundi))
            return

        grille = get_grille_filiere(self.filiere_id, self.date_lundi)
        stats = get_stats_semaine(self.date_lundi, self.filiere_id)
        for (jour, creneau), cell in self.cells.items():
            cell.set_cours(grille.get(f"{jour}|{creneau}"))
        self.stat_cours._value.setText(str(stats["cours"]))
        self.stat_salles._value.setText(str(stats["avec_salle"]))
        self.stat_tc._value.setText(str(stats["tronc_commun"]))
        self.stat_week._value.setText(format_date_fr(self.date_lundi))

    def edit_slot(self, jour: str, creneau: str):
        if not self.filiere_id:
            QMessageBox.warning(self, "Planning", "Sélectionnez une filière.")
            return
        cours = get_cours(self.filiere_id, self.date_lundi, jour, creneau)
        dlg = CoursDialog(self.filiere_id, self.date_lundi, jour, creneau, cours, self)
        if dlg.exec() != dlg.Accepted or dlg.result is None:
            return

        if dlg.result == "clear":
            if cours:
                supprimer_cours(cours.id, clear_tc_group=bool(cours.groupe_tc))
            allouer_toute_la_semaine(self.date_lundi)
            self.refresh_grille()
            return

        data = dlg.result
        matiere = data["matiere"]
        enseignant = data["enseignant"]
        filieres_tc = data["filieres_tc"] or [self.filiere_id]

        conflits = rechercher_conflits_enseignant(
            self.date_lundi, jour, creneau, enseignant,
            exclude_cours_id=cours.id if cours else None,
        )
        ignore = set(filieres_tc) | {self.filiere_id}
        conflits = [c for c in conflits if c["filiere_id"] not in ignore]
        if conflits:
            detail = "\n".join(f"- {c['filiere']} ({c['matiere']})" for c in conflits[:6])
            if QMessageBox.question(
                self,
                "Conflit enseignant",
                f"{enseignant} est déjà pris :\n{detail}\n\nForcer quand même ?",
            ) != QMessageBox.Yes:
                return

        targets = list(dict.fromkeys([self.filiere_id, *filieres_tc]))
        import time as _time
        groupe = f"TC_{int(_time.time())}" if len(targets) > 1 else None
        if len(targets) > 1:
            sync_tronc_commun(
                self.date_lundi, jour, creneau, targets, matiere, enseignant, groupe
            )
        else:
            if cours and cours.groupe_tc:
                sync_tronc_commun(
                    self.date_lundi, jour, creneau, [self.filiere_id], matiere, enseignant, None
                )
            else:
                if cours:
                    cours.matiere = matiere
                    cours.enseignant = enseignant
                    cours.groupe_tc = None
                    sauvegarder_cours(cours)
                else:
                    sauvegarder_cours(
                        Cours(None, self.filiere_id, self.date_lundi, jour, creneau, matiere, enseignant, None, None)
                    )

        allouer_toute_la_semaine(self.date_lundi)
        self.refresh_grille()

    def open_salles(self):
        for b in self.nav_group_btns:
            b.setChecked(False)
        self.nav_group_btns[1].setChecked(True)
        SallesDialog(self).exec()
        self.nav_group_btns[0].setChecked(True)
        self.refresh_grille()

    def open_filieres(self):
        for b in self.nav_group_btns:
            b.setChecked(False)
        self.nav_group_btns[2].setChecked(True)
        FilieresDialog(self.cb_annee.currentText(), self.cb_etab.currentText(), self).exec()
        self.nav_group_btns[0].setChecked(True)
        self.reload_filieres()

    def open_effectifs(self):
        for b in self.nav_group_btns:
            b.setChecked(False)
        self.nav_group_btns[3].setChecked(True)
        EffectifsDialog(self.cb_etab.currentText(), self).exec()
        self.nav_group_btns[0].setChecked(True)
        self.reload_filieres()

    def allouer(self):
        rapport = allouer_toute_la_semaine(self.date_lundi)
        self.refresh_grille()
        failed = len(rapport.get("failed") or [])
        msg = f"{rapport.get('assigned', 0)} salle(s) allouée(s)"
        if failed:
            QMessageBox.warning(self, "Allocation", f"{msg}\n{failed} échec(s).")
        else:
            QMessageBox.information(self, "Allocation", msg)

    def verifier_conflits(self):
        conflits = rechercher_conflits_semaine(self.date_lundi, self.filiere_id)
        if not conflits:
            QMessageBox.information(self, "Conflits", "Aucun conflit enseignant cette semaine.")
            return
        lines = [
            f"{c['jour']} {c['creneau']} — {c['enseignant']} ({len(c['cours'])} cours)"
            for c in conflits[:12]
        ]
        QMessageBox.warning(self, "Conflits", f"{len(conflits)} conflit(s) :\n\n" + "\n".join(lines))

    def export_one(self):
        if not self.filiere_id:
            QMessageBox.warning(self, "Export", "Sélectionnez une filière.")
            return
        path = export_une_filiere(
            self.filiere_id, self.date_lundi, type_cours=self.cb_type.currentText()
        )
        if not path:
            QMessageBox.critical(self, "Export", "Échec de l'export.")
            return
        QMessageBox.information(self, "Export", f"PDF généré :\n{path}")

    def export_zip(self):
        zip_path, resultats = export_all_filieres_zip(
            self.date_lundi,
            etablissement=self.cb_etab.currentText(),
            type_cours=self.cb_type.currentText(),
        )
        if not zip_path:
            QMessageBox.warning(self, "Export", "Aucun PDF à exporter.")
            return
        QMessageBox.information(
            self,
            "Export",
            f"{sum(1 for r in resultats if r[1])} PDF dans :\n{zip_path}",
        )

    def copy_week(self):
        if not self.filiere_id:
            return
        # Copie depuis la semaine précédente
        source = get_semaine_precedente(self.date_lundi)
        if QMessageBox.question(
            self,
            "Copier semaine",
            f"Copier les cours de la semaine du {format_date_fr(source)} vers la semaine affichée ?",
        ) != QMessageBox.Yes:
            return
        n = copier_semaine(self.filiere_id, source, self.date_lundi)
        allouer_toute_la_semaine(self.date_lundi)
        self.refresh_grille()
        QMessageBox.information(self, "Copie", f"{n} cours copiés.")

    def reset_week(self):
        if not self.filiere_id:
            return
        if QMessageBox.question(
            self, "Réinitialiser", "Supprimer tous les cours de cette semaine pour la filière ?"
        ) != QMessageBox.Yes:
            return
        supprimer_cours_filiere_semaine(self.filiere_id, self.date_lundi)
        allouer_toute_la_semaine(self.date_lundi)
        self.refresh_grille()


def run_desktop_qt():
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(build_stylesheet())
    win = MainWindow()
    win.show()
    return app.exec()
