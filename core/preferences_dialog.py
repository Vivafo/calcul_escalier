# core/preferences_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
from core import file_operations


class PreferencesDialog(tk.Toplevel):
    def __init__(self, parent, preferences: dict):
        super().__init__(parent)
        self.title("Préférences")
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)  # Fenêtre au-dessus du parent
        self.grab_set()  # Bloque l’interaction avec la fenêtre principale

        # Copie des préférences pour éviter d’écraser directement
        self.preferences = preferences.copy()

        # --- Unité par défaut ---
        ttk.Label(self, text="Unité par défaut :", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(15, 5), padx=10, sticky="w"
        )

        self.unit_var = tk.StringVar(value=self.preferences.get("unites_affichage", "pouces"))
        ttk.Radiobutton(self, text="Pouces", variable=self.unit_var, value="pouces").grid(
            row=1, column=0, padx=10, sticky="w"
        )
        ttk.Radiobutton(self, text="Centimètres", variable=self.unit_var, value="cm").grid(
            row=1, column=1, padx=10, sticky="w"
        )

        # --- Ligne de séparation ---
        ttk.Separator(self, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=15
        )

        # --- Boutons Sauvegarder / Annuler ---
        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Sauvegarder", command=self.save).pack(
            side="left", padx=5
        )
        ttk.Button(button_frame, text="Annuler", command=self.cancel).pack(
            side="left", padx=5
        )

        # --- Label statut ---
        self.status_label = ttk.Label(self, text="", foreground="gray")
        self.status_label.grid(row=4, column=0, columnspan=2, pady=(5, 10))

    def save(self):
        """Sauvegarde les préférences choisies et ferme la fenêtre"""
        self.preferences["unites_affichage"] = self.unit_var.get()
        file_operations.save_application_preferences(self.preferences)
        messagebox.showinfo("Préférences", "Préférences sauvegardées avec succès.", parent=self)
        self.destroy()

    def cancel(self):
        """Ferme la fenêtre sans rien sauvegarder"""
        self.status_label.config(text="Annulé, aucune modification enregistrée.")
        self.destroy()
