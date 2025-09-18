# core/laser_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox


class LaserDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Mesure Laser")
        self.geometry("350x160")
        self.resizable(False, False)
        self.transient(parent)  # Fenêtre au-dessus du parent
        self.grab_set()  # Bloque interaction avec la fenêtre principale

        self.result = None  # Stocke la valeur saisie

        # --- Label principal ---
        ttk.Label(
            self,
            text="Saisir une hauteur mesurée au laser :",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")

        # --- Champ de saisie ---
        self.value_var = tk.StringVar()
        entry = ttk.Entry(self, textvariable=self.value_var, width=20, justify="center")
        entry.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        entry.focus()  # Focus direct dans le champ

        # --- Boutons OK / Annuler ---
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)

        ttk.Button(button_frame, text="OK", command=self.save_value).pack(
            side="left", padx=5
        )
        ttk.Button(button_frame, text="Annuler", command=self.cancel).pack(
            side="left", padx=5
        )

    def save_value(self):
        """Valide et enregistre la valeur"""
        value = self.value_var.get().strip()
        if not value:
            messagebox.showerror("Erreur", "Veuillez entrer une valeur valide.", parent=self)
            return

        self.result = value  # Stocke la valeur saisie
        messagebox.showinfo("Laser", f"Valeur enregistrée : {value}", parent=self)
        self.destroy()

    def cancel(self):
        """Ferme sans rien sauvegarder"""
        self.result = None
        self.destroy()
