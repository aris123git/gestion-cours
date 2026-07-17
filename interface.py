import os
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from database import init_db, get_filieres, get_cours, sauvegarder_cours, ajouter_filiere, set_effectif, supprimer_filiere, supprimer_cours_filiere_semaine, get_matieres_semaine, get_enseignants_pour_matiere
from models import Cours
from dialogs import GestionSallesDialog, GestionEffectifsDialog
from export_pdf import export_all_filieres
from allocation import allouer_salles_par_jour, allouer_toute_la_semaine
from utils import get_lundi_week_courante, get_semaine_precedente, get_semaine_suivante
from config import JOURS, CRENEAUX, CRENEAUX_LABELS, ANNEE_COURANTE

class PlanningApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des cours - Université")
        self.root.geometry("1200x700")
        init_db()

        self.current_annee = tk.StringVar(value="L1")
        self.current_filiere_id = tk.IntVar()
        self.current_date_lundi = tk.StringVar(value=get_lundi_week_courante())
        self.current_etablissement = tk.StringVar(value="IST")
        self.current_type_cours = tk.StringVar(value="Jour")
        
        self.cache_matieres = {}
        self.cache_enseignants = {}

        self.setup_selector()
        self.setup_grid()
        self.setup_menu()
        self.load_filieres()

    def setup_selector(self):
        top_frame = ttk.Frame(self.root, padding=5)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Année :").pack(side=tk.LEFT, padx=5)
        self.cb_annee = ttk.Combobox(top_frame, textvariable=self.current_annee, values=["L1","L2","L3","Master","Doctorat"], state="readonly", width=10)
        self.cb_annee.pack(side=tk.LEFT, padx=5)
        self.cb_annee.bind("<<ComboboxSelected>>", lambda e: self.load_filieres())
        
        ttk.Label(top_frame, text="Université :").pack(side=tk.LEFT, padx=5)
        self.cb_etablissement = ttk.Combobox(top_frame, textvariable=self.current_etablissement, values=["IST", "UBS"], state="readonly", width=15)
        self.cb_etablissement.pack(side=tk.LEFT, padx=5)
        self.cb_etablissement.bind("<<ComboboxSelected>>", lambda e: self.load_filieres())

        ttk.Label(top_frame, text="Type :").pack(side=tk.LEFT, padx=5)
        self.cb_type_cours = ttk.Combobox(top_frame, textvariable=self.current_type_cours, values=["Jour", "Soir", "En ligne"], state="readonly", width=10)
        self.cb_type_cours.pack(side=tk.LEFT, padx=5)
        self.cb_type_cours.bind("<<ComboboxSelected>>", lambda e: self.charger_grille())
        
        ttk.Label(top_frame, text="Filière :").pack(side=tk.LEFT, padx=5)
        self.cb_filiere = ttk.Combobox(top_frame, state="readonly", width=25)
        self.cb_filiere.pack(side=tk.LEFT, padx=5)
        self.cb_filiere.bind("<<ComboboxSelected>>", self.on_filiere_changed)

        ttk.Label(top_frame, text="Semaine (lundi) :").pack(side=tk.LEFT, padx=5)
        self.entry_date = ttk.Entry(top_frame, textvariable=self.current_date_lundi, width=12)
        self.entry_date.pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="◀", command=self.semaine_precedente, width=2).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="▶", command=self.semaine_suivante, width=2).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Aujourd'hui", command=self.semaine_actuelle, width=10).pack(side=tk.LEFT, padx=5)

    def on_filiere_changed(self, event=None):
        selection = self.cb_filiere.get()
        if selection and " - " in selection:
            vrai_id = int(selection.split(" - ")[0])
            self.current_filiere_id.set(vrai_id)
        self.charger_grille()

    def load_filieres(self):
        annee = self.current_annee.get()
        etablissement = self.current_etablissement.get()
        filieres = get_filieres(annee, etablissement)
        if not filieres:
            self.cb_filiere['values'] = []
            self.cb_filiere.set('')
            self.current_filiere_id.set(0)
            return
        valeurs = [f"{f.id} - {f.nom}" for f in filieres]
        self.cb_filiere['values'] = valeurs
        self.cb_filiere.set(valeurs[0])
        self.current_filiere_id.set(filieres[0].id)
        self.charger_grille()

    def ajouter_filiere(self):
        dialog = Toplevel(self.root)
        dialog.title("Nouvelle filière")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text=f"Année : {self.current_annee.get()}").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(main_frame, text="Nom :").grid(row=1, column=0, sticky="w", pady=5)
        entry_nom = ttk.Entry(main_frame, width=30)
        entry_nom.grid(row=1, column=1, pady=5)
        ttk.Label(main_frame, text="Effectif :").grid(row=2, column=0, sticky="w", pady=5)
        entry_eff = ttk.Entry(main_frame, width=10)
        entry_eff.grid(row=2, column=1, sticky="w", pady=5)
        entry_eff.insert(0, "0")
        
        def valider():
            nom = entry_nom.get().strip()
            if not nom:
                messagebox.showerror("Erreur", "Nom requis")
                return
            try:
                eff = int(entry_eff.get())
            except:
                messagebox.showerror("Erreur", "Effectif invalide")
                return
            
            etab = self.current_etablissement.get()
            etablissement_id = 1 if etab == "IST" else 2
            
            fid = ajouter_filiere(self.current_annee.get(), nom, etablissement_id)
            if not fid:
                messagebox.showerror("Erreur", "Filière existe déjà")
                return
            set_effectif(ANNEE_COURANTE, fid, eff)
            messagebox.showinfo("Succès", f"Filière ajoutée")
            dialog.destroy()
            self.load_filieres()
        
        ttk.Button(main_frame, text="Ajouter", command=valider).grid(row=3, column=0, columnspan=2, pady=15)
        entry_nom.focus()

    def supprimer_filiere(self):
        selection = self.cb_filiere.get()
        if not selection or " - " not in selection:
            messagebox.showwarning("Attention", "Aucune filière sélectionnée.")
            return
        fid = int(selection.split(" - ")[0])
        if messagebox.askyesno("Confirmation", f"Supprimer {selection} ?"):
            supprimer_filiere(fid)
            self.load_filieres()

    def charger_grille(self):
        if not hasattr(self, 'entries') or not self.entries:
            return
        filiere_id = self.current_filiere_id.get()
        if not filiere_id:
            return
        date_lundi = self.current_date_lundi.get()
        for jour_idx, jour in enumerate(JOURS):
            for creneau_idx, (creneau, _, _) in enumerate(CRENEAUX):
                cours = get_cours(filiere_id, date_lundi, jour, creneau)
                entry_matiere = self.entries[creneau_idx][jour_idx][0]
                entry_enseignant = self.entries[creneau_idx][jour_idx][1]
                if cours:
                    entry_matiere.delete(0, tk.END)
                    entry_matiere.insert(0, cours.matiere)
                    entry_enseignant.delete(0, tk.END)
                    entry_enseignant.insert(0, cours.enseignant)
                else:
                    entry_matiere.delete(0, tk.END)
                    entry_enseignant.delete(0, tk.END)

    def auto_sauvegarder_champ(self, jour_idx, creneau_idx):
        filiere_id = self.current_filiere_id.get()
        if not filiere_id:
            return
        date_lundi = self.current_date_lundi.get()
        matiere = self.entries[creneau_idx][jour_idx][0].get().strip()
        enseignant = self.entries[creneau_idx][jour_idx][1].get().strip()
        if matiere and enseignant:
            jour = JOURS[jour_idx]
            creneau = CRENEAUX[creneau_idx][0]
            cours_existant = get_cours(filiere_id, date_lundi, jour, creneau)
            if cours_existant:
                cours_existant.matiere = matiere
                cours_existant.enseignant = enseignant
                sauvegarder_cours(cours_existant)
            else:
                nouveau = Cours(None, filiere_id, date_lundi, jour, creneau, matiere, enseignant, None, None)
                sauvegarder_cours(nouveau)
            allouer_salles_par_jour(date_lundi, jour)
            self.charger_grille()
            self.vider_cache()
    
    def vider_cache(self):
        self.cache_matieres.clear()
        self.cache_enseignants.clear()

    def setup_grid(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(main_frame)
        scroll_y = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scroll_x = ttk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = ttk.Frame(canvas)
        canvas.create_window((0,0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        ttk.Label(self.grid_frame, text="Jour / Créneau", font=('Arial',10,'bold'), relief="ridge").grid(row=0, column=0, sticky="nsew")
        for j, jour in enumerate(JOURS, start=1):
            ttk.Label(self.grid_frame, text=jour, font=('Arial',10,'bold'), relief="ridge").grid(row=0, column=j, sticky="nsew")

        self.entries = []
        for i, label in enumerate(CRENEAUX_LABELS):
            ttk.Label(self.grid_frame, text=label, relief="ridge").grid(row=i+1, column=0, sticky="nsew")
            row_entries = []
            for j in range(len(JOURS)):
                frame_cell = ttk.Frame(self.grid_frame, relief="ridge")
                frame_cell.grid(row=i+1, column=j+1, sticky="nsew", padx=1, pady=1)

                # MATIERE
                entry_matiere = ttk.Combobox(frame_cell, width=12)
                entry_matiere.pack(fill=tk.X, padx=2, pady=2)
                entry_matiere.bind('<FocusOut>', lambda e, j_idx=j, c_idx=i: self.auto_sauvegarder_champ(j_idx, c_idx))
                entry_matiere.bind('<Double-Button-1>', lambda e, j_idx=j, c_idx=i: self.modifier_cours(j_idx, c_idx))

                def on_matiere_focus(event, m=entry_matiere):
                    fid = self.current_filiere_id.get()
                    if not fid:
                        return
                    date_lundi = self.current_date_lundi.get()
                    key = f"{fid}|{date_lundi}"
                    if key in self.cache_matieres:
                        matieres = self.cache_matieres[key]
                    else:
                        matieres = get_matieres_semaine(fid, date_lundi)
                        self.cache_matieres[key] = matieres
                    m['values'] = matieres

                entry_matiere.bind('<FocusIn>', on_matiere_focus)

                # ENSEIGNANT
                entry_enseignant = ttk.Combobox(frame_cell, width=12)
                entry_enseignant.pack(fill=tk.X, padx=2, pady=2)
                entry_enseignant.bind('<FocusOut>', lambda e, j_idx=j, c_idx=i: self.auto_sauvegarder_champ(j_idx, c_idx))
                entry_enseignant.bind('<Double-Button-1>', lambda e, j_idx=j, c_idx=i: self.modifier_cours(j_idx, c_idx))

                def on_enseignant_focus(event, m=entry_matiere, e=entry_enseignant):
                    mat = m.get().strip()
                    if mat:
                        if mat in self.cache_enseignants:
                            profs = self.cache_enseignants[mat]
                        else:
                            profs = get_enseignants_pour_matiere(mat)
                            self.cache_enseignants[mat] = profs
                        e['values'] = profs
                    else:
                        e['values'] = []

                entry_enseignant.bind('<FocusIn>', on_enseignant_focus)

                # NAVIGATION ENTREE
                def on_enter_matiere(event, m=entry_matiere, e=entry_enseignant):
                    e.focus()
                    return "break"

                def on_enter_enseignant(event, j_idx=j, c_idx=i):
                    if j_idx + 1 < len(JOURS):
                        next_entry = self.entries[c_idx][j_idx + 1][0]
                    else:
                        if c_idx + 1 < len(CRENEAUX_LABELS):
                            next_entry = self.entries[c_idx + 1][0][0]
                        else:
                            next_entry = self.entries[0][0][0]
                    next_entry.focus()
                    return "break"

                entry_matiere.bind('<Return>', on_enter_matiere)
                entry_enseignant.bind('<Return>', on_enter_enseignant)

                row_entries.append((entry_matiere, entry_enseignant))
            self.entries.append(row_entries)

        for col in range(len(JOURS)+1):
            self.grid_frame.columnconfigure(col, weight=1)
        for row in range(len(CRENEAUX_LABELS)+1):
            self.grid_frame.rowconfigure(row, weight=1)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Sauvegarder", command=self.sauvegarder_tous).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Allouer les salles (semaine)", command=self.allouer_toute_semaine).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Exporter PDF", command=self.exporter_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Réinitialiser semaine", command=self.reinitialiser_semaine).pack(side=tk.LEFT, padx=5)

    def modifier_cours(self, jour_idx, creneau_idx):
        """Ouvre une boîte de dialogue uniquement pour le tronc commun"""
        fid = self.current_filiere_id.get()
        date_lundi = self.current_date_lundi.get()
        jour = JOURS[jour_idx]
        creneau = CRENEAUX[creneau_idx][0]
        
        cours_existant = get_cours(fid, date_lundi, jour, creneau)
        
        dialog = Toplevel(self.root)
        dialog.title("Tronc commun")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=f"{jour} - {CRENEAUX_LABELS[0 if creneau=='Matin' else 1]}", font=('Arial',10,'bold')).pack(pady=5)
        
        frame_filieres = ttk.LabelFrame(main_frame, text="Filières concernées par le tronc commun")
        frame_filieres.pack(fill=tk.BOTH, expand=True, pady=5)
        
        canvas = tk.Canvas(frame_filieres)
        scrollbar = ttk.Scrollbar(frame_filieres, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        filieres_vars = {}
        all_filieres = get_filieres()
        groupes = {}
        for f in all_filieres:
            if f.annee not in groupes:
                groupes[f.annee] = []
            groupes[f.annee].append(f)
        
        for annee in sorted(groupes.keys()):
            cadre_annee = ttk.LabelFrame(scrollable_frame, text=annee)
            cadre_annee.pack(fill="x", padx=5, pady=5)
            
            var_toutes = tk.BooleanVar()
            def select_all(annee=annee, var=var_toutes):
                for (a, fid), v in filieres_vars.items():
                    if a == annee:
                        v.set(var.get())
            
            cb_toutes = ttk.Checkbutton(cadre_annee, text="✓ Toutes les filières", variable=var_toutes, command=lambda a=annee, v=var_toutes: select_all(a, v))
            cb_toutes.pack(anchor="w", padx=10, pady=2)
            
            for f in groupes[annee]:
                var = tk.BooleanVar()
                cb = ttk.Checkbutton(cadre_annee, text=f.nom, variable=var)
                cb.pack(anchor="w", padx=20, pady=2)
                filieres_vars[(f.annee, f.id)] = var
        
        if cours_existant and cours_existant.groupe_tc:
            import sqlite3
            from config import DB_PATH
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT filiere_id FROM cours WHERE groupe_tc = ? AND date_lundi = ? AND jour = ? AND creneau = ?", 
                      (cours_existant.groupe_tc, date_lundi, jour, creneau))
            for row in c.fetchall():
                for (a, fid), var in filieres_vars.items():
                    if fid == row[0]:
                        var.set(True)
            conn.close()
        
        def valider_tc():
            filieres_tc = []
            for (a, fid), var in filieres_vars.items():
                if var.get():
                    filieres_tc.append(fid)
            
            if not filieres_tc:
                messagebox.showwarning("Attention", "Aucune filière sélectionnée.")
                return
            
            if fid not in filieres_tc:
                filieres_tc.append(fid)
            
            import time
            groupe_tc = f"TC_{int(time.time())}" if len(filieres_tc) > 1 else None
            
            for fid_tc in filieres_tc:
                cours = get_cours(fid_tc, date_lundi, jour, creneau)
                if cours:
                    cours.groupe_tc = groupe_tc
                    sauvegarder_cours(cours)
                else:
                    nouveau = Cours(None, fid_tc, date_lundi, jour, creneau, "", "", None, groupe_tc)
                    sauvegarder_cours(nouveau)
            
            self.charger_grille()
            messagebox.showinfo("Succès", f"Tronc commun appliqué à {len(filieres_tc)} filière(s)")
            dialog.destroy()
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Appliquer", command=valider_tc).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def reinitialiser_semaine(self):
        if messagebox.askyesno("Confirmation", "Supprimer tous les cours de cette semaine ?"):
            fid = self.current_filiere_id.get()
            date_lundi = self.current_date_lundi.get()
            supprimer_cours_filiere_semaine(fid, date_lundi)
            allouer_toute_la_semaine(date_lundi)
            self.charger_grille()

    def sauvegarder_tous(self):
        fid = self.current_filiere_id.get()
        date_lundi = self.current_date_lundi.get()
        for j_idx, jour in enumerate(JOURS):
            for c_idx, (creneau, _, _) in enumerate(CRENEAUX):
                mat = self.entries[c_idx][j_idx][0].get().strip()
                ens = self.entries[c_idx][j_idx][1].get().strip()
                if mat and ens:
                    cours = get_cours(fid, date_lundi, jour, creneau)
                    if cours:
                        cours.matiere = mat
                        cours.enseignant = ens
                        sauvegarder_cours(cours)
                    else:
                        nouveau = Cours(None, fid, date_lundi, jour, creneau, mat, ens, None, None)
                        sauvegarder_cours(nouveau)
        allouer_toute_la_semaine(date_lundi)
        self.charger_grille()
        self.vider_cache()
        messagebox.showinfo("Info", "Tous les cours ont été sauvegardés.")

    def allouer_toute_semaine(self):
        allouer_toute_la_semaine(self.current_date_lundi.get())
        self.charger_grille()
        messagebox.showinfo("Info", "Allocation des salles terminée.")

    def exporter_pdf(self):
        self.sauvegarder_tous()
        date_lundi = self.current_date_lundi.get()
        logo_path = os.path.join(os.path.dirname(__file__), "fichiers", "logoist.jpeg")
        if not os.path.exists(logo_path):
            print(f"Logo non trouvé : {logo_path}")
            logo_path = None
        else:
            print(f"✅ Logo trouvé : {logo_path}")
        resultats = export_all_filieres(date_lundi, ANNEE_COURANTE, logo_path)
        nb_ok = sum(1 for item in resultats if item[1])
        messagebox.showinfo("Export", f"Export terminé : {nb_ok} PDF générés")

    def semaine_precedente(self):
        self.current_date_lundi.set(get_semaine_precedente(self.current_date_lundi.get()))
        self.charger_grille()

    def semaine_suivante(self):
        self.current_date_lundi.set(get_semaine_suivante(self.current_date_lundi.get()))
        self.charger_grille()

    def semaine_actuelle(self):
        self.current_date_lundi.set(get_lundi_week_courante())
        self.charger_grille()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        menu_fichier = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=menu_fichier)
        menu_fichier.add_command(label="Exporter PDF", command=self.exporter_pdf)
        menu_fichier.add_separator()
        menu_fichier.add_command(label="Quitter", command=self.root.quit)

        menu_filieres = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Filières", menu=menu_filieres)
        menu_filieres.add_command(label="Nouvelle filière", command=self.ajouter_filiere)
        menu_filieres.add_command(label="Supprimer filière", command=self.supprimer_filiere)

        menu_config = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Configuration", menu=menu_config)
        menu_config.add_command(label="Gérer les salles", command=self.ouvrir_gestion_salles)
        menu_config.add_command(label="Effectifs par filière", command=self.ouvrir_effectifs)

    def ouvrir_gestion_salles(self):
        GestionSallesDialog(self.root)

    def ouvrir_effectifs(self):
        GestionEffectifsDialog(self.root)