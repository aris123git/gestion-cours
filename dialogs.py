import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import get_filieres, get_salles, ajouter_salle, supprimer_salle, get_effectif, set_effectif, get_enseignants_pour_matiere, get_matieres_semaine, get_dernier_enseignant_filiere_matiere, sauvegarder_cours
from models import Cours
from config import ANNEE_COURANTE, JOURS, CRENEAUX, CRENEAUX_LABELS

class CoursDialog(tk.Toplevel):
    def __init__(self, parent, filiere_id, date_lundi, jour, creneau_idx, cours_existant=None):
        super().__init__(parent)
        self.title("Cours" if not cours_existant else "Modifier cours")
        self.filiere_id = filiere_id
        self.date_lundi = date_lundi
        self.jour = jour
        self.creneau = CRENEAUX[creneau_idx][0]
        self.cours_existant = cours_existant
        self.result = None
        self.setup_ui()
        if cours_existant:
            self.entry_matiere.insert(0, cours_existant.matiere)
            self.entry_enseignant.insert(0, cours_existant.enseignant)
        self.bind_autocomplete()
        self.grab_set()
        self.wait_window()

    def setup_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main, text=f"{self.jour} - {CRENEAUX_LABELS[0 if self.creneau=='Matin' else 1]}").grid(row=0, column=0, columnspan=2, pady=5)
        
        ttk.Label(main, text="Matière :").grid(row=1, column=0, sticky="e", pady=2)
        self.entry_matiere = ttk.Combobox(main, width=40)
        self.entry_matiere.grid(row=1, column=1, sticky="w", pady=2)
        
        ttk.Label(main, text="Enseignant :").grid(row=2, column=0, sticky="e", pady=2)
        self.entry_enseignant = ttk.Combobox(main, width=40)
        self.entry_enseignant.grid(row=2, column=1, sticky="w", pady=2)
        
        # ========== TRONC COMMUN ==========
        self.var_tc = tk.BooleanVar()
        self.cb_tc = ttk.Checkbutton(main, text="Tronc commun", variable=self.var_tc, command=self.on_tc_toggle)
        self.cb_tc.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
        
        # Cadre pour la liste des filières
        self.frame_filieres = ttk.LabelFrame(main, text="Sélectionner les filières concernées")
        self.frame_filieres.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=5)
        
        # Canvas pour scrollbar
        canvas = tk.Canvas(self.frame_filieres, height=150)
        scrollbar = ttk.Scrollbar(self.frame_filieres, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0,0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Dictionnaire pour stocker les cases
        self.filieres_vars = {}  # { (annee, id_filiere): (var, nom) }
        self.charger_liste_filieres()
        
        # Désactiver la liste au départ
        self.frame_filieres.grid_remove()
        
        # Boutons
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Valider", command=self.valider).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self.destroy).pack(side=tk.LEFT, padx=5)
        
        main.columnconfigure(1, weight=1)
    
    def charger_liste_filieres(self):
        """Charge les filières regroupées par année avec case 'Toutes'"""
        from database import get_filieres
        filieres = get_filieres()
        
        # Regrouper par année
        groupes = {}
        for f in filieres:
            if f.annee not in groupes:
                groupes[f.annee] = []
            groupes[f.annee].append(f)
        
        # Créer un cadre par année
        for annee in sorted(groupes.keys()):
            cadre_annee = ttk.LabelFrame(self.scrollable_frame, text=annee)
            cadre_annee.pack(fill="x", padx=5, pady=5)
            
            # Variable pour "Toutes"
            var_toutes = tk.BooleanVar()
            
            # Fonction pour sélectionner/désélectionner toutes les filières de l'année
            def select_all(annee=annee, var=var_toutes):
                for (a, fid), (v, _) in self.filieres_vars.items():
                    if a == annee:
                        v.set(var.get())
            
            cb_toutes = ttk.Checkbutton(cadre_annee, text="✓ Toutes les filières", variable=var_toutes, command=select_all)
            cb_toutes.pack(anchor="w", padx=10, pady=2)
            
            # Cases par filière
            for f in groupes[annee]:
                var_filiere = tk.BooleanVar()
                cb = ttk.Checkbutton(cadre_annee, text=f.nom, variable=var_filiere)
                cb.pack(anchor="w", padx=20, pady=2)
                self.filieres_vars[(annee, f.id)] = (var_filiere, f.nom)
    
    def on_tc_toggle(self):
        if self.var_tc.get():
            self.frame_filieres.grid()
        else:
            self.frame_filieres.grid_remove()
    
    def bind_autocomplete(self):
        matieres = get_matieres_semaine(self.filiere_id, self.date_lundi)
        self.entry_matiere['values'] = matieres
        self.entry_matiere.bind('<<ComboboxSelected>>', lambda e: self.pre_remplir_enseignant())
        self.entry_matiere.bind('<FocusOut>', lambda e: self.pre_remplir_enseignant())
    
    def pre_remplir_enseignant(self):
        matiere = self.entry_matiere.get().strip()
        if matiere:
            enseignant = get_dernier_enseignant_filiere_matiere(self.filiere_id, matiere)
            if enseignant:
                self.entry_enseignant.delete(0, tk.END)
                self.entry_enseignant.insert(0, enseignant)
            self.entry_enseignant['values'] = get_enseignants_pour_matiere(matiere)
    
    def valider(self):
        matiere = self.entry_matiere.get().strip()
        enseignant = self.entry_enseignant.get().strip()
        if not matiere or not enseignant:
            messagebox.showerror("Erreur", "Matière et enseignant sont requis.")
            return
        
        # Récupérer les filières sélectionnées pour le tronc commun
        if self.var_tc.get():
            filieres_tc = []
            for (annee, fid), (var, nom) in self.filieres_vars.items():
                if var.get():
                    filieres_tc.append(fid)
            if not filieres_tc:
                messagebox.showerror("Erreur", "Sélectionnez au moins une filière pour le tronc commun.")
                return
            # Ajouter la filière courante si elle n'est pas déjà dans la liste
            if self.filiere_id not in filieres_tc:
                filieres_tc.append(self.filiere_id)
        else:
            filieres_tc = [self.filiere_id]
        
        # Générer un identifiant unique pour ce groupe TC
        import time
        groupe_tc = f"TC_{int(time.time())}" if self.var_tc.get() else None
        
        # Créer un cours pour chaque filière
        for fid in filieres_tc:
            cours = Cours(
                id=self.cours_existant.id if self.cours_existant and fid == self.filiere_id else None,
                filiere_id=fid,
                date_lundi=self.date_lundi,
                jour=self.jour,
                creneau=self.creneau,
                matiere=matiere,
                enseignant=enseignant,
                salle_id=None,
                groupe_tc=groupe_tc
            )
            sauvegarder_cours(cours)
        
        messagebox.showinfo("Succès", f"Cours ajouté/modifié pour {len(filieres_tc)} filière(s)")
        self.destroy()

# ========== GESTION SALLES ==========
class GestionSallesDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gestion des salles")
        self.geometry("500x400")
        self.setup_ui()
        self.rafraichir()

    def setup_ui(self):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Button(frame, text="Ajouter salle", command=self.ajouter_salle).pack(pady=5)
        self.tree = ttk.Treeview(frame, columns=("nom", "capacite"), show="headings")
        self.tree.heading("nom", text="Nom")
        self.tree.heading("capacite", text="Capacité")
        self.tree.pack(fill=tk.BOTH, expand=True)
        ttk.Button(frame, text="Supprimer sélection", command=self.supprimer_salle).pack(pady=5)

    def rafraichir(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in get_salles():
            self.tree.insert("", tk.END, values=(s.nom, s.capacite), tags=(s.id,))

    def ajouter_salle(self):
        nom = simpledialog.askstring("Ajouter", "Nom de la salle:")
        if not nom: return
        cap = simpledialog.askinteger("Ajouter", "Capacité:")
        if cap is None: return
        ajouter_salle(nom, cap)
        self.rafraichir()

    def supprimer_salle(self):
        sel = self.tree.selection()
        if not sel: return
        salle_id = self.tree.item(sel[0], "tags")[0]
        if messagebox.askyesno("Confirm", "Supprimer cette salle ?"):
            supprimer_salle(salle_id)
            self.rafraichir()

# ========== GESTION EFFECTIFS ==========
class GestionEffectifsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Effectifs par filière")
        self.geometry("500x400")
        self.setup_ui()
        self.rafraichir()

    def setup_ui(self):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(frame, columns=("filiere", "effectif"), show="headings")
        self.tree.heading("filiere", text="Filière")
        self.tree.heading("effectif", text="Effectif")
        self.tree.pack(fill=tk.BOTH, expand=True)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Modifier effectif", command=self.modifier_effectif).pack(side=tk.LEFT, padx=5)

    def rafraichir(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for f in get_filieres():
            eff = get_effectif(ANNEE_COURANTE, f.id)
            self.tree.insert("", tk.END, values=(f"{f.annee} {f.nom}", eff), tags=(f.id,))

    def modifier_effectif(self):
        sel = self.tree.selection()
        if not sel: return
        filiere_id = self.tree.item(sel[0], "tags")[0]
        ancien = self.tree.item(sel[0], "values")[1]
        nouveau = simpledialog.askinteger("Effectif", "Nouvel effectif:", initialvalue=ancien)
        if nouveau is not None:
            set_effectif(ANNEE_COURANTE, filiere_id, nouveau)
            self.rafraichir()