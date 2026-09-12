"""Dialogues de gestion (salles, filières, effectifs, cours)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
)

from config import ANNEE_COURANTE
from database import (
    ajouter_filiere,
    ajouter_salle,
    get_effectif,
    get_enseignants_pour_matiere,
    get_filieres,
    get_filieres_tc_groupe,
    get_matieres_semaine,
    get_salles,
    set_effectif,
    supprimer_filiere,
    supprimer_salle,
)


class SallesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des salles")
        self.resize(520, 420)
        layout = QVBoxLayout(self)

        form = QHBoxLayout()
        self.nom = QLineEdit()
        self.nom.setPlaceholderText("Nom (ex. Amphi A)")
        self.cap = QSpinBox()
        self.cap.setRange(1, 2000)
        self.cap.setValue(40)
        add_btn = QPushButton("Ajouter")
        add_btn.setObjectName("PrimaryButton")
        add_btn.clicked.connect(self._ajouter)
        form.addWidget(self.nom, 2)
        form.addWidget(self.cap, 1)
        form.addWidget(add_btn)
        layout.addLayout(form)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Nom", "Capacité", ""])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        close = QDialogButtonBox(QDialogButtonBox.Close)
        close.rejected.connect(self.reject)
        layout.addWidget(close)
        self.refresh()

    def refresh(self):
        salles = get_salles()
        self.table.setRowCount(0)
        for s in salles:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(s.nom))
            self.table.setItem(row, 1, QTableWidgetItem(str(s.capacite)))
            btn = QPushButton("Suppr.")
            btn.setObjectName("DangerButton")
            btn.clicked.connect(lambda _=False, sid=s.id: self._supprimer(sid))
            self.table.setCellWidget(row, 2, btn)

    def _ajouter(self):
        nom = self.nom.text().strip()
        cap = self.cap.value()
        if not nom:
            QMessageBox.warning(self, "Salles", "Nom requis.")
            return
        if not ajouter_salle(nom, cap):
            QMessageBox.warning(self, "Salles", "Salle déjà existante.")
            return
        self.nom.clear()
        self.refresh()

    def _supprimer(self, salle_id):
        if QMessageBox.question(self, "Salles", "Supprimer cette salle ?") != QMessageBox.Yes:
            return
        supprimer_salle(salle_id)
        self.refresh()


class FilieresDialog(QDialog):
    def __init__(self, annee: str, etablissement: str, parent=None):
        super().__init__(parent)
        self.annee = annee
        self.etablissement = etablissement
        self.setWindowTitle(f"Filières — {annee} / {etablissement}")
        self.resize(520, 420)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Ajout pour {annee} · {etablissement}"))

        form = QHBoxLayout()
        self.nom = QLineEdit()
        self.nom.setPlaceholderText("Nom de la filière")
        self.eff = QSpinBox()
        self.eff.setRange(0, 5000)
        self.eff.setValue(0)
        add_btn = QPushButton("Ajouter")
        add_btn.setObjectName("PrimaryButton")
        add_btn.clicked.connect(self._ajouter)
        form.addWidget(self.nom, 2)
        form.addWidget(self.eff, 1)
        form.addWidget(add_btn)
        layout.addLayout(form)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Filière", "Effectif", ""])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        close = QDialogButtonBox(QDialogButtonBox.Close)
        close.rejected.connect(self.reject)
        layout.addWidget(close)
        self.refresh()

    def refresh(self):
        rows = get_filieres(self.annee, self.etablissement)
        self.table.setRowCount(0)
        for f in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(f.nom))
            self.table.setItem(row, 1, QTableWidgetItem(str(get_effectif(ANNEE_COURANTE, f.id))))
            btn = QPushButton("Suppr.")
            btn.setObjectName("DangerButton")
            btn.clicked.connect(lambda _=False, fid=f.id: self._supprimer(fid))
            self.table.setCellWidget(row, 2, btn)

    def _ajouter(self):
        nom = self.nom.text().strip()
        if not nom:
            QMessageBox.warning(self, "Filières", "Nom requis.")
            return
        etab_id = 1 if self.etablissement == "IST" else 2
        fid = ajouter_filiere(self.annee, nom, etab_id)
        if not fid:
            QMessageBox.warning(self, "Filières", "Cette filière existe déjà.")
            return
        set_effectif(ANNEE_COURANTE, fid, self.eff.value())
        self.nom.clear()
        self.refresh()

    def _supprimer(self, filiere_id):
        if QMessageBox.question(self, "Filières", "Supprimer cette filière et ses cours ?") != QMessageBox.Yes:
            return
        supprimer_filiere(filiere_id)
        self.refresh()


class EffectifsDialog(QDialog):
    def __init__(self, etablissement: str | None = None, parent=None):
        super().__init__(parent)
        self.etablissement = etablissement
        self.setWindowTitle("Effectifs par filière")
        self.resize(520, 420)
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Filière", "Effectif", ""])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        close = QDialogButtonBox(QDialogButtonBox.Close)
        close.rejected.connect(self.reject)
        layout.addWidget(close)
        self.refresh()

    def refresh(self):
        rows = get_filieres(etablissement=self.etablissement)
        self.table.setRowCount(0)
        for f in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(f"{f.annee} — {f.nom}"))
            spin = QSpinBox()
            spin.setRange(0, 5000)
            spin.setValue(get_effectif(ANNEE_COURANTE, f.id))
            self.table.setCellWidget(row, 1, spin)
            btn = QPushButton("OK")
            btn.setObjectName("PrimaryButton")
            btn.clicked.connect(lambda _=False, fid=f.id, s=spin: self._save(fid, s))
            self.table.setCellWidget(row, 2, btn)

    def _save(self, filiere_id, spin: QSpinBox):
        set_effectif(ANNEE_COURANTE, filiere_id, spin.value())
        QMessageBox.information(self, "Effectifs", "Effectif mis à jour.")


class CoursDialog(QDialog):
    def __init__(
        self,
        filiere_id: int,
        date_lundi: str,
        jour: str,
        creneau: str,
        cours=None,
        parent=None,
    ):
        super().__init__(parent)
        self.filiere_id = filiere_id
        self.date_lundi = date_lundi
        self.jour = jour
        self.creneau = creneau
        self.cours = cours
        self.setWindowTitle(f"Cours — {jour} / {creneau}")
        self.resize(480, 520)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"{jour} · {creneau}"))

        form = QFormLayout()
        self.matiere = QComboBox()
        self.matiere.setEditable(True)
        self.matiere.addItems(get_matieres_semaine(filiere_id, date_lundi))
        self.enseignant = QComboBox()
        self.enseignant.setEditable(True)
        form.addRow("Matière", self.matiere)
        form.addRow("Enseignant", self.enseignant)
        layout.addLayout(form)

        self.tc = QCheckBox("Tronc commun")
        layout.addWidget(self.tc)

        self.tc_box = QWidget()
        tc_layout = QVBoxLayout(self.tc_box)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        self.tc_checks_layout = QVBoxLayout(inner)
        scroll.setWidget(inner)
        tc_layout.addWidget(scroll)
        layout.addWidget(self.tc_box)
        self.tc_box.setVisible(False)
        self.tc.toggled.connect(self.tc_box.setVisible)

        self.filiere_checks = {}
        current = None
        for f in get_filieres():
            # group loosely by annee
            cb = QCheckBox(f"{f.annee} — {f.nom}")
            if f.id == filiere_id:
                cb.setChecked(True)
                cb.setEnabled(False)
                current = f
            self.filiere_checks[f.id] = cb
            self.tc_checks_layout.addWidget(cb)

        if cours:
            self.matiere.setEditText(cours.matiere or "")
            self.enseignant.setEditText(cours.enseignant or "")
            if cours.groupe_tc:
                self.tc.setChecked(True)
                ids = get_filieres_tc_groupe(
                    cours.groupe_tc, date_lundi, jour, creneau
                )
                for fid, cb in self.filiere_checks.items():
                    if fid in ids:
                        cb.setChecked(True)

        self.matiere.currentTextChanged.connect(self._load_enseignants)
        self._load_enseignants(self.matiere.currentText())

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        clear_btn = QPushButton("Vider le créneau")
        clear_btn.setObjectName("DangerButton")
        clear_btn.clicked.connect(self._clear)
        buttons.addButton(clear_btn, QDialogButtonBox.ActionRole)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.result = None  # dict | "clear" | None

    def _load_enseignants(self, matiere: str):
        matiere = (matiere or "").strip()
        current = self.enseignant.currentText()
        self.enseignant.clear()
        if matiere:
            self.enseignant.addItems(get_enseignants_pour_matiere(matiere))
        if current:
            self.enseignant.setEditText(current)

    def _accept(self):
        matiere = self.matiere.currentText().strip()
        enseignant = self.enseignant.currentText().strip()
        if not matiere or not enseignant:
            QMessageBox.warning(self, "Cours", "Matière et enseignant requis.")
            return
        filieres_tc = []
        if self.tc.isChecked():
            filieres_tc = [fid for fid, cb in self.filiere_checks.items() if cb.isChecked()]
        self.result = {
            "matiere": matiere,
            "enseignant": enseignant,
            "filieres_tc": filieres_tc,
        }
        self.accept()

    def _clear(self):
        if QMessageBox.question(self, "Cours", "Vider ce créneau ?") != QMessageBox.Yes:
            return
        self.result = "clear"
        self.accept()
