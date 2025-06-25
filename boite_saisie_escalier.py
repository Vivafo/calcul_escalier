import tkinter as tk
from tkinter import ttk
import math

class ChampAvecFleches(ttk.Frame):
    """Widget personnalisé avec Entry et boutons +/- pour contrôler des valeurs numériques."""
    
    def __init__(self, parent, var, step=1, largeur=8, unite="", minval=None, maxval=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.var = var
        self.step = step
        self.minval = minval
        self.maxval = maxval
        
        # Bouton de décrémentation avec largeur réduite et sans padding
        ttk.Button(self, text="−", width=2, command=self.decrementer).pack(side="left")
        
        # Champ de saisie avec largeur réduite
        self.entry = ttk.Entry(self, textvariable=self.var, width=largeur, justify="center")
        self.entry.pack(side="left", padx=1)
        
        # Bouton d'incrémentation avec largeur réduite et sans padding
        ttk.Button(self, text="+", width=2, command=self.incrementer).pack(side="left")

    def incrementer(self):
        """Incrémente la valeur selon le pas défini."""
        try:
            val = float(self.var.get().replace(',', '.'))
        except ValueError:
            val = 0
        val += self.step
        if self.maxval is not None:
            val = min(val, self.maxval)
        self.var.set(str(val))

    def decrementer(self):
        """Décrémente la valeur selon le pas défini."""
        try:
            val = float(self.var.get().replace(',', '.'))
        except ValueError:
            val = 0
        val -= self.step
        if self.minval is not None:
            val = max(val, self.minval)
        self.var.set(str(val))

class SaisieEscalierComplete(ttk.Frame):
    """Interface complète de saisie d'escalier avec sections A, B et C selon les spécifications."""
    
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        
        # Variables de saisie (utilisant les mêmes noms que votre projet)
        self.hauteur_totale_var = tk.StringVar(value="108")
        self.longueur_escalier_var = tk.StringVar(value="")
        self.nombre_marche_var = tk.StringVar(value="15")
        self.giron_var = tk.StringVar(value="9.25")
        self.nombre_contremarche_var = tk.StringVar(value="16")
        self.hauteur_contremarche_var = tk.StringVar(value="7.5")
        self.longueur_ouverture_var = tk.StringVar(value="60")
        self.hauteur_plafond_var = tk.StringVar(value="96")
        
        # Variables de résultats
        self.longueur_min_var = tk.StringVar()
        self.nombre_contremarche_res_var = tk.StringVar()
        self.hauteur_cm_res_var = tk.StringVar()
        
        # Liaisons pour recalcul automatique
        self._bind_variables()
        
        # Construction de l'interface
        self._construire_interface()
        
        # Calcul initial
        self.recalculer()

    def _bind_variables(self):
        """Lie les variables aux événements de recalcul."""
        variables = [
            self.hauteur_totale_var, self.longueur_escalier_var, self.nombre_marche_var,
            self.giron_var, self.nombre_contremarche_var, self.hauteur_contremarche_var,
            self.longueur_ouverture_var, self.hauteur_plafond_var
        ]
        
        for var in variables:
            var.trace_add("write", lambda *args: self.recalculer())

    def _construire_interface(self):
        """Construit l'interface utilisateur selon les spécifications exactes."""
        
        # Configuration de la grille principale
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        
        # SECTION A - Hauteur Total et Longueur Escalier
        frame_a = ttk.LabelFrame(self, text="A - Dimensions de Base", padding=10)
        frame_a.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        frame_a.columnconfigure(1, weight=1)
        frame_a.columnconfigure(3, weight=1)
        
        # Hauteur Total
        ttk.Label(frame_a, text="Hauteur Total", anchor="w").grid(row=0, column=0, sticky="w", padx=3, pady=3)
        ChampAvecFleches(frame_a, self.hauteur_totale_var, step=1, largeur=8).grid(row=0, column=1, sticky="w", padx=3, pady=3)
        
        # Longueur Escalier  
        ttk.Label(frame_a, text="Longueur Escalier", anchor="w").grid(row=0, column=2, sticky="w", padx=3, pady=3)
        ChampAvecFleches(frame_a, self.longueur_escalier_var, step=1, largeur=8).grid(row=0, column=3, sticky="w", padx=3, pady=3)
        
        # SECTION B - Nombre de Marches et Contremarches (AVEC ALIGNEMENT CORRIGÉ)
        frame_b = ttk.LabelFrame(self, text="B - Marches et Contremarches", padding=10)
        frame_b.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        frame_b.columnconfigure(1, weight=1)
        frame_b.columnconfigure(3, weight=1)
        
        # Première ligne : Nombre de marches et Nombre contremarches
        ttk.Label(frame_b, text="Nombre de Marches", anchor="w").grid(row=0, column=0, sticky="w", padx=3, pady=3)
        ChampAvecFleches(frame_b, self.nombre_marche_var, step=1, largeur=8, minval=1).grid(row=0, column=1, sticky="w", padx=3, pady=3)
        
        ttk.Label(frame_b, text="Nombre Contremarche", anchor="w").grid(row=0, column=2, sticky="w", padx=3, pady=3)
        ChampAvecFleches(frame_b, self.nombre_contremarche_var, step=1, largeur=8, minval=1).grid(row=0, column=3, sticky="w", padx=3, pady=3)
        
        # Deuxième ligne : Giron et Hauteur contremarche
        ttk.Label(frame_b, text="Giron", anchor="w").grid(row=1, column=0, sticky="w", padx=3, pady=3)
        ChampAvecFleches(frame_b, self.giron_var, step=0.125, largeur=8).grid(row=1, column=1, sticky="w", padx=3, pady=3)
        
        ttk.Label(frame_b, text="Hauteur Contremarche", anchor="w").grid(row=1, column=2, sticky="w", padx=3, pady=3)
        ChampAvecFleches(frame_b, self.hauteur_contremarche_var, step=0.125, largeur=8).grid(row=1, column=3, sticky="w", padx=3, pady=3)
        
        # SECTION C - Trémis
        frame_c = ttk.LabelFrame(self, text="C - Trémis", padding=10)
        frame_c.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        frame_c.columnconfigure(1, weight=1)
        frame_c.columnconfigure(3, weight=1)
        
        # Première ligne : Longueur d'ouverture
        ttk.Label(frame_c, text="Longueur d'Ouverture", anchor="w").grid(row=0, column=0, sticky="w", padx=3, pady=3)
        ChampAvecFleches(frame_c, self.longueur_ouverture_var, step=1, largeur=8).grid(row=0, column=1, sticky="w", padx=3, pady=3)
        
        # Deuxième ligne : Hauteur du plafond
        ttk.Label(frame_c, text="Hauteur du Plafond", anchor="w").grid(row=1, column=0, sticky="w", padx=3, pady=3)
        ChampAvecFleches(frame_c, self.hauteur_plafond_var, step=1, largeur=8).grid(row=1, column=1, sticky="w", padx=3, pady=3)
        
        # SECTION RÉSULTATS
        frame_resultats = ttk.LabelFrame(self, text="Résultats", padding=10)
        frame_resultats.grid(row=0, column=2, rowspan=3, sticky="nsew", padx=5, pady=5)
        frame_resultats.columnconfigure(1, weight=1)
        
        ttk.Label(frame_resultats, text="Longueur Escalier Minimum", anchor="w").grid(row=0, column=0, sticky="w", padx=3, pady=3)
        ChampAvecFleches(frame_resultats, self.longueur_min_var, step=1, largeur=8).grid(row=0, column=1, sticky="w", padx=3, pady=3)
        
        ttk.Label(frame_resultats, text="Nombre Contremarche", anchor="w").grid(row=1, column=0, sticky="w", padx=3, pady=3)
        ChampAvecFleches(frame_resultats, self.nombre_contremarche_res_var, step=1, largeur=8).grid(row=1, column=1, sticky="w", padx=3, pady=3)
        
        ttk.Label(frame_resultats, text="Hauteur CM", anchor="w").grid(row=2, column=0, sticky="w", padx=3, pady=3)
        ChampAvecFleches(frame_resultats, self.hauteur_cm_res_var, step=0.125, largeur=8).grid(row=2, column=1, sticky="w", padx=3, pady=3)
        
        # BOUTONS
        frame_boutons = ttk.Frame(self)
        frame_boutons.grid(row=3, column=0, columnspan=3, pady=15)
        
        ttk.Button(frame_boutons, text="Laser", command=self.action_laser).pack(side="left", padx=10)
        ttk.Button(frame_boutons, text="Appliquer Valeurs Idéales", command=self.appliquer_valeurs_ideales).pack(side="left", padx=10)

    def recalculer(self):
        """Recalcule les valeurs basées sur les entrées."""
        try:
            # Récupération des valeurs
            hauteur_totale = float(self.hauteur_totale_var.get() or "0")
            nombre_marches = int(float(self.nombre_marche_var.get() or "0"))
            giron = float(self.giron_var.get() or "0")
            
            if hauteur_totale > 0 and nombre_marches > 0:
                # Calculs basiques (adaptez selon votre logique métier)
                nombre_contremarches = nombre_marches + 1
                hauteur_cm = hauteur_totale / nombre_contremarches
                longueur_min = nombre_marches * giron
                
                # Mise à jour des résultats
                self.nombre_contremarche_res_var.set(str(nombre_contremarches))
                self.hauteur_cm_res_var.set(f"{hauteur_cm:.3f}")
                self.longueur_min_var.set(f"{longueur_min:.1f}")
            else:
                # Réinitialisation si valeurs invalides
                self.nombre_contremarche_res_var.set("")
                self.hauteur_cm_res_var.set("")
                self.longueur_min_var.set("")
                
        except (ValueError, ZeroDivisionError):
            # Gestion des erreurs de calcul
            pass

    def action_laser(self):
        """Action du bouton Laser."""
        print("Action Laser - À implémenter selon vos besoins")
        
    def appliquer_valeurs_ideales(self):
        """Applique des valeurs idéales prédéfinies."""
        self.giron_var.set("9.25")
        self.hauteur_contremarche_var.set("7.5")
        self.nombre_marche_var.set("15")
        print("Valeurs idéales appliquées")

    def get_donnees(self):
        """Retourne toutes les données saisies sous forme de dictionnaire."""
        return {
            "hauteur_totale": self.hauteur_totale_var.get(),
            "longueur_escalier": self.longueur_escalier_var.get(),
            "nombre_marche": self.nombre_marche_var.get(),
            "giron": self.giron_var.get(),
            "nombre_contremarche": self.nombre_contremarche_var.get(),
            "hauteur_contremarche": self.hauteur_contremarche_var.get(),
            "longueur_ouverture": self.longueur_ouverture_var.get(),
            "hauteur_plafond": self.hauteur_plafond_var.get(),
            "longueur_min": self.longueur_min_var.get(),
            "nombre_contremarche_res": self.nombre_contremarche_res_var.get(),
            "hauteur_cm_res": self.hauteur_cm_res_var.get()
        }

# Application de test
class ApplicationTest(tk.Tk):
    """Application de test pour l'interface de saisie."""
    
    def __init__(self):
        super().__init__()
        self.title("Interface de Saisie Escalier - Boutons Alignés")
        self.geometry("850x450")  # Réduit légèrement pour s'adapter aux boutons plus petits
        
        # Interface de saisie
        self.saisie = SaisieEscalierComplete(self)
        self.saisie.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Bouton de test pour récupérer les données
        ttk.Button(self, text="Afficher Données", 
                   command=self.afficher_donnees).pack(pady=10)

    def afficher_donnees(self):
        """Affiche toutes les données saisies."""
        donnees = self.saisie.get_donnees()
        print("\n=== DONNÉES SAISIES ===")
        for cle, valeur in donnees.items():
            print(f"{cle}: {valeur}")
        print("========================\n")

# Point d'entrée pour les tests
if __name__ == "__main__":
    app = ApplicationTest()
    app.mainloop()
