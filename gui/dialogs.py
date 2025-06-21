import tkinter as tk
from tkinter import ttk, messagebox
from core import constants
from utils.formatting import parser_fraction
from utils.file_operations import save_application_preferences

# La classe pour le dialogue laser que nous pourrions utiliser plus tard
class LaserDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Assistance Laser")
        ttk.Label(self, text="Cette fonctionnalité sera bientôt disponible.").pack(padx=20, pady=20)
        self.transient(parent)
        self.grab_set()

# La nouvelle classe pour le dialogue des préférences
class PreferencesDialog(tk.Toplevel):
    def __init__(self, parent, app_prefs):
        super().__init__(parent)
        self.transient(parent)
        self.parent = parent
        self.app_preferences = app_prefs.copy()

        self.title("Préférences de l'Application")
        self.geometry("450x300")
        self.resizable(False, False)

        self.vars = {
            "default_tread_thickness": tk.StringVar(value=self.app_preferences.get("default_tread_thickness")),
            "default_riser_thickness": tk.StringVar(value=self.app_preferences.get("default_riser_thickness")),
            "default_tread_width_straight": tk.StringVar(value=self.app_preferences.get("default_tread_width_straight")),
            "display_fraction_precision": tk.StringVar(value=self.app_preferences.get("display_fraction_precision")),
        }

        self._create_widgets()
        
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.grab_set()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(expand=True, fill="both")

        fields_to_create = {
            "default_tread_thickness": "Épaisseur de marche par défaut:",
            "default_riser_thickness": "Épaisseur de contremarche par défaut:",
            "default_tread_width_straight": "Giron par défaut:",
        }

        row_index = 0
        for key, text in fields_to_create.items():
            ttk.Label(main_frame, text=text).grid(row=row_index, column=0, sticky="w", pady=5)
            entry = ttk.Entry(main_frame, textvariable=self.vars[key], width=15)
            entry.grid(row=row_index, column=1, sticky="e", pady=5, padx=5)
            row_index += 1
            
        ttk.Label(main_frame, text="Précision d'affichage (fractions):").grid(row=row_index, column=0, sticky="w", pady=5)
        precision_combobox = ttk.Combobox(
            main_frame,
            textvariable=self.vars["display_fraction_precision"],
            values=[str(d) for d in sorted(constants.ALLOWED_DENOMINATORS)],
            state="readonly",
            width=12
        )
        precision_combobox.grid(row=row_index, column=1, sticky="e", pady=5, padx=5)
        row_index += 1

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row_index, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(btn_frame, text="Sauvegarder et Fermer", command=self._save_and_close).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Annuler", command=self.destroy).pack(side="left")

    def _save_and_close(self):
        for key, var in self.vars.items():
            self.app_preferences[key] = var.get()
        
        save_application_preferences(self.app_preferences, parent=self)
        
        self.destroy()
        
        messagebox.showinfo(
            "Redémarrage Requis",
            "Les nouvelles préférences seront appliquées au prochain démarrage de l'application.",
            parent=self.parent
        )