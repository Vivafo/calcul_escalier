import tkinter as tk
from tkinter import ttk, messagebox
from core import constants
from utils.formatting import parser_fraction
from utils.file_operations import save_application_preferences

# La classe pour le dialogue laser que nous pourrions utiliser plus tard
class LaserDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent # Sauvegarde la référence au parent
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

        # Assurez-vous que les clés existent dans app_prefs avant de les utiliser pour la valeur par défaut
        # Utilisez .get() avec une valeur par défaut pour éviter les KeyError
        self.vars = {
            "default_tread_thickness": tk.StringVar(value=self.app_preferences.get("default_tread_thickness", "1 1/16")),
            "default_riser_thickness": tk.StringVar(value=self.app_preferences.get("default_riser_thickness", "3/4")),
            "default_tread_width_straight": tk.StringVar(value=self.app_preferences.get("default_tread_width_straight", "9 1/4")),
            "display_fraction_precision": tk.StringVar(value=self.app_preferences.get("fraction_precision_denominator", "16")), # Correction de la clé ici aussi
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
            # Utilise constants.ALLOWED_DENOMINATORS si elle existe, sinon une liste par défaut
            values=[str(d) for d in sorted(getattr(constants, 'ALLOWED_DENOMINATORS', [2, 4, 8, 16, 32, 64]))],
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
        # Valider les entrées avant de sauvegarder
        errors = []
        for key in ["default_tread_thickness", "default_riser_thickness", "default_tread_width_straight"]:
            try:
                parser_fraction(self.vars[key].get())
            except ValueError:
                errors.append(f"Format invalide pour '{key.replace('_', ' ').title()}'.")
        
        try:
            precision = int(self.vars["display_fraction_precision"].get())
            if precision not in getattr(constants, 'ALLOWED_DENOMINATORS', [2, 4, 8, 16, 32, 64]):
                errors.append("Précision de fraction non valide.")
        except ValueError:
            errors.append("Précision de fraction non numérique.")

        if errors:
            messagebox.showerror("Erreur de validation", "\n".join(errors), parent=self)
            return

        for key, var in self.vars.items():
            if key == "display_fraction_precision":
                self.app_preferences["fraction_precision_denominator"] = int(var.get())
            else:
                self.app_preferences[key] = var.get()
        
        save_application_preferences(self.app_preferences) # Plus besoin de passer 'parent=self' ici
        
        self.destroy()
        
        messagebox.showinfo(
            "Redémarrage Requis",
            "Les nouvelles préférences seront appliquées au prochain démarrage de l'application.",
            parent=self.parent
        )
