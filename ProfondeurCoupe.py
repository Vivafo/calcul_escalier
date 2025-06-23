# Fichier: ProfondeurCoupe.py
# Programme indépendant avec GUI Tkinter pour calculer le décalage de lame H90 et H45.

import tkinter as tk
from tkinter import ttk, messagebox
import math
import json # Utilisé pour la sortie structurée des données

# Constante de conversion
POUCE_EN_MM = 25.4

# --- Fonctions de Calcul (adaptées pour des entrées en mm) ---
def calculer_H90_mm(rayon_lame_mm, epaisseur_bois_mm, profondeur_depassement_P_mm):
    if profondeur_depassement_P_mm < epaisseur_bois_mm:
        return {
            "H_val": None,
            "message": f"ERREUR_H90: P ({profondeur_depassement_P_mm:.2f}mm) < h ({epaisseur_bois_mm:.2f}mm)."
        }
    try:
        d_dessous = rayon_lame_mm - profondeur_depassement_P_mm
        d_dessus = rayon_lame_mm - profondeur_depassement_P_mm + epaisseur_bois_mm

        if rayon_lame_mm**2 < d_dessous**2:
            return {
                "H_val": None,
                "message": f"ERREUR_H90: r² < d_dessous² (r={rayon_lame_mm:.2f}, d_inf={d_dessous:.2f}). Vérifiez P."
            }
        # Gestion des cas où le terme sous la racine est très proche de zéro ou négatif
        terme_sqrt_dessous = rayon_lame_mm**2 - d_dessous**2
        proj_dessous = math.sqrt(max(0, terme_sqrt_dessous))


        terme_sqrt_dessus = rayon_lame_mm**2 - d_dessus**2
        if terme_sqrt_dessus < -1e-9 and not abs(terme_sqrt_dessus) < 1e-9 : # si négatif et pas quasi nul
             return { "H_val": None, "message": f"ERREUR_H90: r² < d_dessus² (r={rayon_lame_mm:.2f}, d_sup={d_dessus:.2f})." }
        proj_dessus = math.sqrt(max(0, terme_sqrt_dessus))
        
        H90_val = proj_dessous - proj_dessus
        return {"H_val": H90_val, "message": "Calcul H90 réussi."}
    except Exception as e:
        return {"H_val": None, "message": f"ERREUR_H90_INATTENDUE: {e}"}

def calculer_H45_mm(rayon_lame_mm, epaisseur_bois_mm, profondeur_depassement_P_mm):
    cos_45 = math.cos(math.radians(45))
    limite_sup_P_mm = (2 * rayon_lame_mm * cos_45) - epaisseur_bois_mm

    if not (-1e-9 <= profondeur_depassement_P_mm <= limite_sup_P_mm + 1e-9): # Tolérance pour comparaison flottants
        return {
            "H_val": None,
            "message": f"ERREUR_H45: P ({profondeur_depassement_P_mm:.2f}mm) hors intervalle [0, {limite_sup_P_mm:.2f}mm]."
        }
    try:
        zc = (rayon_lame_mm * cos_45) - profondeur_depassement_P_mm
        d_prime_dessous = abs(zc) / cos_45
        d_prime_dessus = abs(epaisseur_bois_mm - zc) / cos_45
        
        terme_sqrt_dessous = rayon_lame_mm**2 - d_prime_dessous**2
        if terme_sqrt_dessous < -1e-9:
            return {
                "H_val": None,
                "message": f"ERREUR_H45: r² < d'_dessous² (r={rayon_lame_mm:.2f}, d'_inf={d_prime_dessous:.2f})."
            }
        proj_dessous_45 = math.sqrt(max(0, terme_sqrt_dessous))

        terme_sqrt_dessus = rayon_lame_mm**2 - d_prime_dessus**2
        if terme_sqrt_dessus < -1e-9:
            return {
                "H_val": None,
                "message": f"ERREUR_H45: r² < d'_dessus² (r={rayon_lame_mm:.2f}, d'_sup={d_prime_dessus:.2f})."
            }
        proj_dessus_45 = math.sqrt(max(0, terme_sqrt_dessus))
        
        H45_val = proj_dessous_45 - proj_dessus_45
        return {"H_val": H45_val, "message": "Calcul H45 réussi."}
    except Exception as e:
        return {"H_val": None, "message": f"ERREUR_H45_INATTENDUE: {e}"}

# --- Utilitaire de parsing (identique à celui de votre projet) ---
# Pour que ce programme soit vraiment indépendant et puisse utiliser parser_fraction,
# il faudrait soit que ce fichier soit dans la structure de CalculateurEscalier
# pour que l'import fonctionne, soit copier/adapter parser_fraction ici.
# Option 1: Si ProfondeurCoupe.py est dans le dossier racine de CalculateurEscalier:
try:
    from utils.formatting import parser_fraction, ALLOWED_DENOMINATORS # Tente d'importer depuis le projet parent
    from core.validation import validate_generic_fraction_format
except ImportError:
    # Fallback si l'import échoue (ProfondeurCoupe.py est VRAIMENT isolé)
    ALLOWED_DENOMINATORS = {2, 4, 8, 16, 32, 64}
    def parser_fraction(input_str): # Version simplifiée si isolé
        if not isinstance(input_str, str):
            try: return float(input_str)
            except (ValueError, TypeError): raise ValueError("L'entrée doit être une chaîne ou un nombre.")
        original_input = input_str
        input_str = input_str.replace(',', '.').replace('-', ' ').strip()
        if not input_str: raise ValueError("L'entrée ne peut être vide.")
        parts = input_str.split()
        total_value = 0.0
        try:
            if len(parts) == 1:
                part1 = parts[0]
                if '/' in part1:
                    num_str, den_str = part1.split('/'); num, den = float(num_str), int(den_str)
                    if den == 0: raise ZeroDivisionError("Dénominateur zéro."); 
                    if den not in ALLOWED_DENOMINATORS: raise ValueError(f"Dénominateur {den} non permis.")
                    total_value = num / den
                else: total_value = float(part1)
            elif len(parts) == 2:
                integer_part_str, fraction_part_str = parts[0], parts[1]
                total_value = float(integer_part_str)
                if '/' in fraction_part_str:
                    num_str, den_str = fraction_part_str.split('/'); num, den = float(num_str), int(den_str)
                    if den == 0: raise ZeroDivisionError("Dénominateur zéro.")
                    if den not in ALLOWED_DENOMINATORS: raise ValueError(f"Dénominateur {den} non permis.")
                    total_value += (num / den) if total_value >= 0 else -(num / den)
                else: raise ValueError("Format fraction invalide.")
            else: raise ValueError("Format invalide (trop de parties).")
            return total_value
        except ValueError as e: raise ValueError(f"Format invalide pour '{original_input}': {e}")
        except ZeroDivisionError as e: raise ValueError(f"Format invalide pour '{original_input}': {e}")
        except Exception as e: raise ValueError(f"Erreur parsing '{original_input}': {e}")

    def validate_generic_fraction_format(value_str, field_name="Ce champ", can_be_empty=False, parent_window=None):
        # Fallback validation si isolé
        if not value_str.strip():
            if can_be_empty: return True
            if parent_window: messagebox.showerror("Erreur Format", f"{field_name} ne peut être vide.", parent=parent_window)
            return False
        try:
            parser_fraction(value_str)
            return True
        except ValueError as e:
            if parent_window: messagebox.showerror(f"Erreur Format ({field_name})", str(e), parent=parent_window)
            return False

class ProfondeurCoupeApp:
    def __init__(self, master):
        self.master = master
        master.title("Profondeur de Coupe Scie Circulaire")
        master.geometry("650x600") # Ajustez au besoin

        self.unite_saisie = tk.StringVar(value="pouces") # pouces | mm

        # Valeurs par défaut (peuvent être chargées depuis un fichier ou passées)
        self.default_marque = "Marque Scie XYZ"
        self.default_modele = "Modèle ABC-123"
        self.default_diam_lame = "6 1/2" # Pouces
        self.default_largeur_lame = "1/8" # Pouces
        self.default_prof_coupe = "2 1/8" # Pouces
        self.default_angle_D = "48"
        self.default_angle_G = "-3"
        self.default_epaisseur_bois_H = "3/4" # Pouces
        self.default_prof_depassement_P_H = "1/4" # Pouces

        self._create_widgets()
        self._setup_layout()
        self.update_labels_unites() # Met à jour les "(pouces)" ou "(mm)" initiaux

    def _create_widgets(self):
        self.main_frame = ttk.Frame(self.master, padding="10")

        # --- Section Informations Scie ---
        info_scie_frame = ttk.LabelFrame(self.main_frame, text="Informations de la Scie", padding="10")
        
        self.marque_var = tk.StringVar(value=self.default_marque)
        self.modele_var = tk.StringVar(value=self.default_modele)
        self.diam_lame_var = tk.StringVar(value=self.default_diam_lame)
        self.largeur_lame_var = tk.StringVar(value=self.default_largeur_lame)
        self.prof_coupe_var = tk.StringVar(value=self.default_prof_coupe)
        self.angle_D_var = tk.StringVar(value=self.default_angle_D)
        self.angle_G_var = tk.StringVar(value=self.default_angle_G)

        ttk.Label(info_scie_frame, text="Marque (*):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.marque_entry = ttk.Entry(info_scie_frame, textvariable=self.marque_var, width=25)
        self.marque_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)

        ttk.Label(info_scie_frame, text="Modèle:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(info_scie_frame, textvariable=self.modele_var, width=25).grid(row=0, column=3, sticky=tk.EW, padx=5, pady=2)

        self.lbl_diam_lame = ttk.Label(info_scie_frame, text="Grandeur Lame (*):")
        self.lbl_diam_lame.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.diam_lame_entry = ttk.Entry(info_scie_frame, textvariable=self.diam_lame_var, width=10)
        self.diam_lame_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        self.lbl_largeur_lame = ttk.Label(info_scie_frame, text="Largeur Lame:")
        self.lbl_largeur_lame.grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(info_scie_frame, textvariable=self.largeur_lame_var, width=10).grid(row=1, column=3, sticky=tk.EW, padx=5, pady=2)

        self.lbl_prof_coupe = ttk.Label(info_scie_frame, text="Prof. Coupe Max:")
        self.lbl_prof_coupe.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(info_scie_frame, textvariable=self.prof_coupe_var, width=10).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(info_scie_frame, text="Angle Max Droit (°):").grid(row=2, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(info_scie_frame, textvariable=self.angle_D_var, width=10).grid(row=2, column=3, sticky=tk.EW, padx=5, pady=2)

        ttk.Label(info_scie_frame, text="Angle Max Gauche (°):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(info_scie_frame, textvariable=self.angle_G_var, width=10).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)
        
        info_scie_frame.columnconfigure(1, weight=1)
        info_scie_frame.columnconfigure(3, weight=1)

        # --- Section Unités ---
        unite_frame = ttk.LabelFrame(self.main_frame, text="Unité de Saisie pour Dimensions", padding="10")
        ttk.Radiobutton(unite_frame, text="Pouces (fraction)", variable=self.unite_saisie, value="pouces", command=self.update_labels_unites).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(unite_frame, text="Millimètres (décimal)", variable=self.unite_saisie, value="mm", command=self.update_labels_unites).pack(side=tk.LEFT, padx=10)

        # --- Section Paramètres pour Calcul H ---
        params_H_frame = ttk.LabelFrame(self.main_frame, text="Paramètres pour Calcul Décalage (H)", padding="10")
        
        self.epaisseur_bois_H_var = tk.StringVar(value=self.default_epaisseur_bois_H)
        self.prof_depassement_P_H_var = tk.StringVar(value=self.default_prof_depassement_P_H)

        self.lbl_epaisseur_bois_H = ttk.Label(params_H_frame, text="Épaisseur Bois (h) (*):")
        self.lbl_epaisseur_bois_H.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.epaisseur_bois_H_entry = ttk.Entry(params_H_frame, textvariable=self.epaisseur_bois_H_var, width=10)
        self.epaisseur_bois_H_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)

        self.lbl_prof_depassement_P_H = ttk.Label(params_H_frame, text="Prof. Dépassement (P) (*):")
        self.lbl_prof_depassement_P_H.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.prof_depassement_P_H_entry = ttk.Entry(params_H_frame, textvariable=self.prof_depassement_P_H_var, width=10)
        self.prof_depassement_P_H_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        params_H_frame.columnconfigure(1, weight=1)

        # --- Boutons Actions ---
        action_frame = ttk.Frame(self.main_frame, padding="10")
        ttk.Button(action_frame, text="Calculer H90 / H45", command=self._on_calculate).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Transmettre Résultats & Quitter", command=self._on_transmit_and_quit).pack(side=tk.LEFT, padx=10)

        # --- Section Résultats ---
        results_frame = ttk.LabelFrame(self.main_frame, text="Résultats des Calculs (en mm)", padding="10")
        self.h90_result_var = tk.StringVar(value="H90: -- mm")
        self.h90_interpret_var = tk.StringVar(value="")
        self.h45_result_var = tk.StringVar(value="H45: -- mm")
        self.h45_interpret_var = tk.StringVar(value="")

        ttk.Label(results_frame, textvariable=self.h90_result_var, font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=2)
        ttk.Label(results_frame, textvariable=self.h90_interpret_var).pack(anchor=tk.W, pady=2)
        ttk.Label(results_frame, textvariable=self.h45_result_var, font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=(5,2))
        ttk.Label(results_frame, textvariable=self.h45_interpret_var).pack(anchor=tk.W, pady=2)

        # Packing des frames principaux
        self.main_frame.pack(expand=True, fill=tk.BOTH)
        info_scie_frame.pack(fill=tk.X, padx=5, pady=5)
        unite_frame.pack(fill=tk.X, padx=5, pady=5)
        params_H_frame.pack(fill=tk.X, padx=5, pady=5)
        action_frame.pack(fill=tk.X, padx=5, pady=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def _setup_layout(self): # Pourrait être fusionné dans _create_widgets
        pass

    def update_labels_unites(self):
        unit_suffix = "(pouces)" if self.unite_saisie.get() == "pouces" else "(mm)"
        self.lbl_diam_lame.config(text=f"Grandeur Lame (*): {unit_suffix}")
        self.lbl_largeur_lame.config(text=f"Largeur Lame: {unit_suffix}")
        self.lbl_prof_coupe.config(text=f"Prof. Coupe Max: {unit_suffix}")
        self.lbl_epaisseur_bois_H.config(text=f"Épaisseur Bois (h) (*): {unit_suffix}")
        self.lbl_prof_depassement_P_H.config(text=f"Prof. Dépassement (P) (*): {unit_suffix}")

    def _validate_inputs(self, values_dict):
        """Valide les entrées nécessaires et les formats."""
        required_text_fields = {"marque": values_dict["marque"]}
        for field, value in required_text_fields.items():
            if not value.strip():
                messagebox.showerror("Entrée Requise", f"Le champ '{field}' est obligatoire.", parent=self.master)
                return False
        
        # Champs numériques ou fractionnaires (ceux utilisés pour le calcul H)
        fields_to_validate = {
            "Grandeur Lame": values_dict["diam_lame"],
            "Épaisseur Bois (h)": values_dict["epaisseur_bois_H"],
            "Prof. Dépassement (P)": values_dict["prof_depassement_P_H"]
        }
        # Validation des autres champs numériques (angles, etc.) peut être ajoutée ici si besoin
        # avec validate_generic_numeric_format ou similaire.

        for name, value_str in fields_to_validate.items():
            if not validate_generic_fraction_format(value_str, name, parent_window=self.master):
                # Focus sur le champ en erreur si possible (nécessiterait de passer les widgets)
                return False
        return True

    def _get_value_mm(self, value_str):
        """Parse la valeur et la convertit en mm si l'unité de saisie est 'pouces'."""
        val = parser_fraction(value_str) # parser_fraction est sensé gérer les exceptions
        if self.unite_saisie.get() == "pouces":
            return val * POUCE_EN_MM
        return val # Déjà en mm

    def _on_calculate(self):
        current_values = {
            "marque": self.marque_var.get(),
            "diam_lame": self.diam_lame_var.get(),
            "epaisseur_bois_H": self.epaisseur_bois_H_var.get(),
            "prof_depassement_P_H": self.prof_depassement_P_H_var.get()
        }
        if not self._validate_inputs(current_values):
            # Affiche un message d'erreur clair dans les résultats
            self.h90_result_var.set("H90: -- mm")
            self.h90_interpret_var.set("Entrée(s) invalide(s)")
            self.h45_result_var.set("H45: -- mm")
            self.h45_interpret_var.set("")
            return

        try:
            diam_lame_mm = self._get_value_mm(self.diam_lame_var.get())
            rayon_lame_mm = diam_lame_mm / 2.0
            epaisseur_bois_H_mm = self._get_value_mm(self.epaisseur_bois_H_var.get())
            prof_depassement_P_H_mm = self._get_value_mm(self.prof_depassement_P_H_var.get())
        except ValueError as e: # Erreur de parser_fraction
            self.h90_result_var.set("H90: Erreur")
            self.h90_interpret_var.set(f"Erreur de valeur : {e}")
            self.h45_result_var.set("H45: Erreur")
            self.h45_interpret_var.set("")
            return
        except Exception as e:
            self.h90_result_var.set("H90: Erreur")
            self.h90_interpret_var.set(f"Erreur inattendue : {e}")
            self.h45_result_var.set("H45: Erreur")
            self.h45_interpret_var.set("")
            return

        # Calcul H90
        res_h90 = calculer_H90_mm(rayon_lame_mm, epaisseur_bois_H_mm, prof_depassement_P_H_mm)
        if res_h90["H_val"] is not None:
            self.h90_result_var.set(f"H90: {res_h90['H_val']:.2f} mm")
            if res_h90['H_val'] > 1e-6: self.h90_interpret_var.set("Dessous APRÈS dessus.")
            elif res_h90['H_val'] < -1e-6: self.h90_interpret_var.set("Dessous AVANT dessus.")
            else: self.h90_interpret_var.set("Contacts simultanés horizontalement.")
        else:
            self.h90_result_var.set("H90: Erreur")
            self.h90_interpret_var.set(res_h90['message'])

        # Calcul H45
        res_h45 = calculer_H45_mm(rayon_lame_mm, epaisseur_bois_H_mm, prof_depassement_P_H_mm)
        if res_h45["H_val"] is not None:
            self.h45_result_var.set(f"H45: {res_h45['H_val']:.2f} mm")
            if res_h45['H_val'] > 1e-6: self.h45_interpret_var.set("Dessous APRÈS dessus.")
            elif res_h45['H_val'] < -1e-6: self.h45_interpret_var.set("Dessous AVANT dessus.")
            else: self.h45_interpret_var.set("Contacts simultanés horizontalement.")
        else:
            self.h45_result_var.set("H45: Erreur")
            self.h45_interpret_var.set(res_h45['message'])

    def _on_transmit_and_quit(self):
        # Valider les entrées avant de transmettre
        current_values_for_validation = {
            "marque": self.marque_var.get(),
            "diam_lame": self.diam_lame_var.get(),
            "epaisseur_bois_H": self.epaisseur_bois_H_var.get(),
            "prof_depassement_P_H": self.prof_depassement_P_H_var.get()
        }
        if not self._validate_inputs(current_values_for_validation):
            messagebox.showwarning("Validation Échouée", 
                                 "Veuillez corriger les erreurs avant de transmettre.", parent=self.master)
            return
            
        # Ré-exécute les calculs pour s'assurer que les résultats sont à jour avec les champs
        self._on_calculate() # Ceci met à jour les self.hXX_result_var et self.hXX_interpret_var

        # Collecter toutes les données à transmettre, en s'assurant que les dimensions sont en mm
        data_to_transmit = {
            "info_scie": {},
            "params_calcul_H_mm": {},
            "resultats_H_mm": {}
        }
        try:
            # Informations générales sur la scie (converties en mm si applicable et si désiré)
            # Pour l'instant, on les garde telles quelles sauf si une conversion spécifique est demandée.
            data_to_transmit["info_scie"]["marque"] = self.marque_var.get()
            data_to_transmit["info_scie"]["modele"] = self.modele_var.get()
            # Les dimensions générales de la scie sont aussi converties en mm pour la transmission
            data_to_transmit["info_scie"]["diametre_lame_mm"] = self._get_value_mm(self.diam_lame_var.get())
            data_to_transmit["info_scie"]["largeur_lame_mm"] = self._get_value_mm(self.largeur_lame_var.get()) if self.largeur_lame_var.get().strip() else None
            data_to_transmit["info_scie"]["profondeur_coupe_max_mm"] = self._get_value_mm(self.prof_coupe_var.get()) if self.prof_coupe_var.get().strip() else None
            data_to_transmit["info_scie"]["angle_max_droit_deg"] = float(self.angle_D_var.get()) if self.angle_D_var.get().strip() else None
            data_to_transmit["info_scie"]["angle_max_gauche_deg"] = float(self.angle_G_var.get()) if self.angle_G_var.get().strip() else None

            # Paramètres utilisés pour le calcul H, convertis en mm
            diam_lame_calc_mm = self._get_value_mm(self.diam_lame_var.get()) # Diamètre lame pour calcul
            data_to_transmit["params_calcul_H_mm"]["diametre_lame_utilisé_mm"] = diam_lame_calc_mm
            data_to_transmit["params_calcul_H_mm"]["rayon_lame_utilisé_mm"] = diam_lame_calc_mm / 2.0
            data_to_transmit["params_calcul_H_mm"]["epaisseur_bois_h_mm"] = self._get_value_mm(self.epaisseur_bois_H_var.get())
            data_to_transmit["params_calcul_H_mm"]["profondeur_depassement_P_mm"] = self._get_value_mm(self.prof_depassement_P_H_var.get())
            data_to_transmit["params_calcul_H_mm"]["unite_saisie_initiale"] = self.unite_saisie.get()

            # Résultats H90/H45 (extraits des StringVar, qui sont déjà formatées)
            # On veut les valeurs numériques brutes si possible, pas les chaînes formatées avec "H90: ..."
            # Donc on re-calcule ou on stocke les valeurs numériques lors du calcul.
            # Pour la simplicité de la transmission, on peut prendre les chaînes, ou extraire.
            # Refaisons le calcul pour avoir les valeurs numériques brutes des H.
            r_mm = data_to_transmit["params_calcul_H_mm"]["rayon_lame_utilisé_mm"]
            h_mm = data_to_transmit["params_calcul_H_mm"]["epaisseur_bois_h_mm"]
            P_mm = data_to_transmit["params_calcul_H_mm"]["profondeur_depassement_P_mm"]
            
            res_h90_final = calculer_H90_mm(r_mm, h_mm, P_mm)
            res_h45_final = calculer_H45_mm(r_mm, h_mm, P_mm)

            data_to_transmit["resultats_H_mm"]["H90_mm"] = res_h90_final["H_val"]
            data_to_transmit["resultats_H_mm"]["H90_message"] = res_h90_final["message"]
            data_to_transmit["resultats_H_mm"]["H45_mm"] = res_h45_final["H_val"]
            data_to_transmit["resultats_H_mm"]["H45_message"] = res_h45_final["message"]

        except ValueError as e: # Erreur de parser_fraction ou float()
            messagebox.showerror("Erreur de Valeur", f"Valeur numérique invalide lors de la collecte des données: {e}", parent=self.master)
            return
        except Exception as e: # Autre erreur
             messagebox.showerror("Erreur Inattendue", f"Erreur lors de la préparation des données: {e}", parent=self.master)
             return

        # Sortie des données en JSON sur la console (pour que le programme parent puisse les lire)
        try:
            json_output = json.dumps(data_to_transmit, ensure_ascii=False, indent=2)
            print("---DEBUT_JSON_PROFONDEUR_COUPE---")
            print(json_output)
            print("---FIN_JSON_PROFONDEUR_COUPE---")
        except Exception as e:
            # Si JSON fail, fallback à un print simple d'erreur pour le parent
            print("ERREUR_JSON_SERIALIZATION")
            print(str(e))

        self.master.quit() # Ou self.master.destroy() si c'est la fenêtre principale

if __name__ == "__main__":
    # Si ProfondeurCoupe.py est exécuté directement
    # Pour les imports relatifs (utils.formatting), ce script doit être
    # exécutable depuis le répertoire racine du projet CalculateurEscalier,
    # ou le PYTHONPATH doit être configuré.
    # Exemple: python ProfondeurCoupe.py (si dans le même dossier que main_app.py)
    # ou python tools/ProfondeurCoupe.py (si vous le mettez dans un dossier tools)
    
    # Ajout temporaire du chemin parent pour permettre les imports relatifs s'il est dans un sous-dossier
    # import os, sys
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # parent_dir = os.path.dirname(current_dir) 
    # if parent_dir not in sys.path:
    #    sys.path.insert(0, parent_dir)
    # # Maintenant, les imports comme `from utils.formatting import parser_fraction` devraient mieux fonctionner
    # # s'il est dans un sous-dossier de CalculateurEscalier et que CalculateurEscalier est le dossier parent.

    print("Démarrage du programme…")
    root = tk.Tk()
    app = ProfondeurCoupeApp(root)
    root.mainloop()