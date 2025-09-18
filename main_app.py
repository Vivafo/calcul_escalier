# Fichier: main_app.py

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import json
try:
    from core import reporting
except ImportError as e:
    print("ERREUR : Impossible d'importer reporting :", e)
    reporting = None

try:
    import core.file_operations as file_operations
except ImportError as e:
    print("ERREUR : Impossible d'importer core.file_operations :", e)
    file_operations = None

try:
    import core.formatting as formatting
except ImportError as e:
    print("ERREUR : Impossible d'importer core.formatting :", e)
    formatting = None

try:
    import core.calculations as calculations
except ImportError as e:
    print("ERREUR : Impossible d'importer core.calculations :", e)
    calculations = None

# Import direct des classes de dialogue
from core.preferences_dialog import PreferencesDialog

# Log pour vérifier le chemin d'accès
print("Chemin actuel :", os.path.dirname(os.path.abspath(__file__)))
print("Chemin PYTHONPATH :", sys.path)

# Ajouter dynamiquement le répertoire parent au PYTHONPATH
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importer le module constants en premier
try:
    import core.constants as constants
    print("Import de core.constants réussi.")
except ImportError as e:
    print("ERREUR : Impossible d'importer core.constants :", e)
    raise

# Vérification si le fichier constants.py existe
constants_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core", "constants.py")
if not os.path.exists(constants_path):
    print("ERREUR : Le fichier constants.py est introuvable :", constants_path)
else:
    print("Fichier constants.py trouvé :", constants_path)

# --- Vérification et création du dossier et fichier de préférences ---
DEFAULTS_FILE = constants.DEFAULTS_FILE
DEFAULT_APP_PREFERENCES = constants.DEFAULT_APP_PREFERENCES

os.makedirs(os.path.dirname(DEFAULTS_FILE), exist_ok=True)

if not os.path.exists(DEFAULTS_FILE):
    with open(DEFAULTS_FILE, 'w') as f:
        json.dump(DEFAULT_APP_PREFERENCES, f, indent=4)

class ModernStairCalculator(tk.Tk):
    """
    Classe principale de l'interface du calculateur d'escalier.
    Gère la fenêtre principale, les entrées, les résultats et les interactions.
    """

    def on_unit_change(self):
        """Callback exécuté quand on change l'unité (Pouces / Centimètres)."""
        new_unit = self.unites_var.get()
        previous_unit = getattr(self, "_current_input_unit", new_unit)
        print(f"⚙️ Unité sélectionnée : {new_unit}")

        if new_unit == previous_unit:
            self.app_preferences["unites_affichage"] = new_unit
            self._current_input_unit = new_unit
            return

        try:
            self._convert_inputs_between_units(previous_unit, new_unit)
        except Exception as exc:
            print(f"Erreur lors de la conversion des unités : {exc}")

        # Mettre à jour les préférences
        self.app_preferences["unites_affichage"] = new_unit
        self._current_input_unit = new_unit

        # Recalculer et rafraîchir l'UI
        try:
            self.recalculate_and_update_ui()
        except Exception as e:
            print(f"Erreur lors du recalcul après changement d'unité : {e}")

    def __init__(self):
        super().__init__()
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.title(f"Calculateur d'Escalier Pro v{constants.VERSION_PROGRAMME}")
        self.geometry("1200x850")
        self.minsize(900, 700)

        self._initialize_state()

        self._setup_style_definitions()
        self._create_menu()
        self._create_main_layout()
        self._bind_events()
        self.clear_messages()

    def _initialize_state(self):
        self._is_updating_ui = False
        self.latest_results = {}
        self.input_labels_map = {}

        self.themes = {
            "light": {
                "fg": "#1f2933",
                "success": "#1b8a3c",
                "warning": "#c27c1f",
                "error": "#c0392b",
                "canvas_line": "#274472",
            }
        }
        self.current_theme = "light"

        base_preferences = DEFAULT_APP_PREFERENCES.copy()
        if file_operations:
            try:
                loaded_prefs = file_operations.load_application_preferences()
                if isinstance(loaded_prefs, dict):
                    base_preferences.update(loaded_prefs)
            except Exception as exc:
                print("⚠️ Préférences par défaut utilisées (erreur de chargement) :", exc)
        self.app_preferences = base_preferences

        default_hcm = str(constants.HAUTEUR_CM_CONFORT_CIBLE)
        if formatting:
            try:
                default_hcm = formatting.decimal_to_fraction_str(
                    constants.HAUTEUR_CM_CONFORT_CIBLE, self.app_preferences
                )
            except Exception as exc:
                print("⚠️ Impossible de formater la hauteur CM par défaut :", exc)

        self.unites_var = tk.StringVar(
            value=self.app_preferences.get("unites_affichage", "pouces")
        )
        self.hauteur_totale_var = tk.StringVar()
        self.epaisseur_plancher_sup_var = tk.StringVar(
            value=self.app_preferences.get("default_floor_finish_thickness_upper", "0")
        )
        self.epaisseur_plancher_inf_var = tk.StringVar(
            value=self.app_preferences.get("default_floor_finish_thickness_lower", "0")
        )
        self.profondeur_tremie_ouverture_var = tk.StringVar()
        self.position_tremie_var = tk.StringVar()
        self.espace_disponible_var = tk.StringVar()
        self.nombre_marches_manuel_var = tk.StringVar(value="")
        self.nombre_cm_manuel_var = tk.StringVar(value="")
        self.giron_souhaite_var = tk.StringVar(
            value=self.app_preferences.get("default_tread_width_straight", "9 1/4")
        )
        self.hauteur_cm_souhaitee_var = tk.StringVar(value=default_hcm)

        self.tk_input_vars_dict = {
            "hauteur_totale_var": self.hauteur_totale_var,
            "hauteur_cm_souhaitee_var": self.hauteur_cm_souhaitee_var,
            "giron_souhaite_var": self.giron_souhaite_var,
            "epaisseur_plancher_sup_var": self.epaisseur_plancher_sup_var,
            "epaisseur_plancher_inf_var": self.epaisseur_plancher_inf_var,
            "profondeur_tremie_ouverture_var": self.profondeur_tremie_ouverture_var,
            "position_tremie_var": self.position_tremie_var,
            "espace_disponible_var": self.espace_disponible_var,
        }

        self._current_input_unit = self.unites_var.get()
        self._unit_sensitive_vars = [
            self.hauteur_totale_var,
            self.giron_souhaite_var,
            self.hauteur_cm_souhaitee_var,
            self.epaisseur_plancher_sup_var,
            self.epaisseur_plancher_inf_var,
            self.profondeur_tremie_ouverture_var,
            self.position_tremie_var,
            self.espace_disponible_var,
        ]

        self.conformity_status_var = tk.StringVar(value="EN ATTENTE")
        self.warnings_var = tk.StringVar(value="")
        self.hauteur_reelle_cm_res_var = tk.StringVar()
        self.giron_utilise_res_var = tk.StringVar()
        self.longueur_totale_res_var = tk.StringVar()
        self.angle_res_var = tk.StringVar()
        self.limon_res_var = tk.StringVar()
        self.echappee_res_var = tk.StringVar()
        self.longueur_min_escalier_var = tk.StringVar()

        self.hauteur_cm_message_var = tk.StringVar()
        self.giron_message_var = tk.StringVar()
        self.echappee_message_var = tk.StringVar()
        self.blondel_message_var = tk.StringVar()
        self.longueur_disponible_message_var = tk.StringVar()
        self.angle_message_var = tk.StringVar()
        self.hauteur_totale_ecart_message_var = tk.StringVar()

    def _convert_inputs_between_units(self, from_unit, to_unit):
        if not formatting or from_unit == to_unit:
            return

        factor = constants.POUCE_EN_CM
        was_updating = self._is_updating_ui
        self._is_updating_ui = True
        try:
            for var in self._unit_sensitive_vars:
                raw_value = var.get().strip()
                if not raw_value:
                    continue

                normalized_value = raw_value.replace(',', '.')
                try:
                    numeric_value = formatting.parser_fraction(normalized_value)
                except Exception:
                    continue

                if from_unit == "cm":
                    numeric_value /= factor

                if to_unit == "cm":
                    converted_value = numeric_value * factor
                    var.set(f"{converted_value:.2f}")
                else:
                    var.set(formatting.decimal_to_fraction_str(numeric_value, self.app_preferences))
        finally:
            self._is_updating_ui = was_updating

    def _setup_style_definitions(self):
        colors = self.themes[self.current_theme]
        self.style.configure("TLabelFrame", borderwidth=2, relief="groove", padding=10)
        self.style.configure("Conformity.TLabel", font=('Segoe UI', 12, 'bold'), foreground=colors["fg"])
        self.style.configure("Indicator.Green.TLabel", foreground=colors["success"], font=('Segoe UI', 9, 'bold'))
        self.style.configure("Indicator.Yellow.TLabel", foreground=colors["warning"], font=('Segoe UI', 9, 'bold'))
        self.style.configure("Indicator.Red.TLabel", foreground=colors["error"], font=('Segoe UI', 9, 'bold'))
        self.style.configure("InputControl.TFrame", padding=(4, 2))
        self.style.configure("DisplayValue.TLabel", font=('Segoe UI', 10, "bold"), foreground=colors["fg"], padding=(6, 2))

    def _create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Quitter", command=self.quit)

    def _create_main_layout(self):
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(expand=True, fill="both", padx=10, pady=10)
        left_frame = ttk.Frame(main_pane, padding=10)
        self._create_input_frame(left_frame)
        self._create_results_frame(left_frame)
        self._create_warnings_frame(left_frame)
        main_pane.add(left_frame, weight=1)
        right_notebook = ttk.Notebook(main_pane)
        self.notebook = right_notebook
        self._create_visual_tab(right_notebook)
        self._create_report_tab(right_notebook)
        self._create_table_tab(right_notebook)
        main_pane.add(right_notebook, weight=2)
        
    def _create_input_frame(self, parent):
        input_frame = ttk.LabelFrame(parent, text="1. Entrées et Ajustements de l'Escalier")
        input_frame.pack(fill="x", pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(3, weight=1)
        unit_frame = ttk.LabelFrame(input_frame, text="Unités")
        unit_frame.grid(row=0, column=4, rowspan=2, padx=5, pady=5, sticky="nsew")
        self.radio_pouces = ttk.Radiobutton(unit_frame, text="Pouces", variable=self.unites_var, value="pouces", command=self.on_unit_change)
        self.radio_cm = ttk.Radiobutton(unit_frame, text="Centimètres", variable=self.unites_var, value="cm", command=self.on_unit_change)
        self.radio_pouces.grid(row=0, column=0, padx=2, pady=2)
        self.radio_cm.grid(row=1, column=0, padx=2, pady=2)
        entries_main = [
            ("Hauteur totale :", "HT", self.hauteur_totale_var, False), ("Épaisseur plancher sup. :", "EPS", self.epaisseur_plancher_sup_var, False),
            ("Épaisseur plancher inf. :", "EPI", self.epaisseur_plancher_inf_var, False), ("Profondeur ouverture trémie :", "POT", self.profondeur_tremie_ouverture_var, True),
            ("Position départ trémie:", "PDT", self.position_tremie_var, True), ("Espace disponible (longueur) :", "ED", self.espace_disponible_var, True),
        ]
        row_idx = 0
        for text, shortcut, var, optional in entries_main:
            label = ttk.Label(input_frame, text=text)
            label.grid(row=row_idx, column=0, sticky="w", padx=5, pady=3)
            self.input_labels_map[shortcut] = (label, text)
            entry_frame = ttk.Frame(input_frame)
            entry_frame.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=3)
            entry = ttk.Entry(entry_frame, textvariable=var, width=12, font=('Segoe UI', 10))
            entry.pack(side="left", fill="x", expand=True)
            if shortcut == "HT":
                ttk.Button(entry_frame, text="Laser", command=self.open_laser_dialog, width=6).pack(side="left", padx=(5,0))
            row_idx += 1
        ttk.Separator(input_frame, orient='horizontal').grid(row=row_idx, column=0, columnspan=4, sticky='ew', pady=10)
        row_idx += 1
        ttk.Label(input_frame, text="Nb Marches (Girons) :", font=('Segoe UI', 10, 'bold')).grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
        marches_control_frame = ttk.Frame(input_frame, style="InputControl.TFrame")
        marches_control_frame.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=5)
        marches_control_frame.columnconfigure(1, weight=1)
        ttk.Button(marches_control_frame, text="-", command=self.decrement_marches, width=3).grid(row=0, column=0, padx=(0, 4))
        ttk.Entry(marches_control_frame, textvariable=self.nombre_marches_manuel_var, width=10, justify="center", font=('Segoe UI', 10)).grid(row=0, column=1, padx=4, sticky="ew")
        ttk.Button(marches_control_frame, text="+", command=self.increment_marches, width=3).grid(row=0, column=2, padx=(4, 0))
        ttk.Label(input_frame, text="Nb Contremarches (CM) :", font=('Segoe UI', 10, 'bold')).grid(row=row_idx, column=2, sticky="w", padx=5, pady=5)
        ttk.Label(
            input_frame,
            textvariable=self.nombre_cm_manuel_var,
            style="DisplayValue.TLabel",
            width=10,
            anchor="center",
            justify="center"
        ).grid(row=row_idx, column=3, sticky="ew", padx=5, pady=5)
        row_idx += 1
        ttk.Label(input_frame, text="Giron souhaité :", font=('Segoe UI', 10, 'bold')).grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
        giron_control_frame = ttk.Frame(input_frame, style="InputControl.TFrame")
        giron_control_frame.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=5)
        giron_control_frame.columnconfigure(1, weight=1)
        ttk.Button(giron_control_frame, text="-", command=self.decrement_giron, width=3).grid(row=0, column=0, padx=(0, 4))
        ttk.Entry(giron_control_frame, textvariable=self.giron_souhaite_var, width=10, justify="center", font=('Segoe UI', 10)).grid(row=0, column=1, padx=4, sticky="ew")
        ttk.Button(giron_control_frame, text="+", command=self.increment_giron, width=3).grid(row=0, column=2, padx=(4, 0))
        ttk.Label(input_frame, text="Hauteur contremarche :", font=('Segoe UI', 10, 'bold')).grid(row=row_idx, column=2, sticky="w", padx=5, pady=5)
        ttk.Label(
            input_frame,
            textvariable=self.hauteur_cm_souhaitee_var,
            style="DisplayValue.TLabel",
            width=10,
            anchor="center",
            justify="center"
        ).grid(row=row_idx, column=3, sticky="ew", padx=5, pady=5)
        row_idx += 1
        ttk.Button(input_frame, text="Appliquer Valeurs Idéales (confort)", command=self.apply_ideal_values).grid(row=row_idx, column=0, columnspan=4, pady=10)

    def _create_results_frame(self, parent):
        results_frame = ttk.LabelFrame(parent, text="2. Résultats et Conformité")
        results_frame.pack(fill="x", pady=10)
        results_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(2, weight=1)
        self.conformity_label = ttk.Label(results_frame, textvariable=self.conformity_status_var, style="Conformity.TLabel")
        self.conformity_label.grid(row=0, column=0, columnspan=3, pady=(5, 15), sticky="ew")
        results_labels_and_vars = [
            ("Hauteur réelle par CM :", self.hauteur_reelle_cm_res_var, self.hauteur_cm_message_var), ("Giron utilisé :", self.giron_utilise_res_var, self.giron_message_var),
            ("Longueur totale escalier :", self.longueur_totale_res_var, self.longueur_disponible_message_var), ("Angle de l'escalier :", self.angle_res_var, self.angle_message_var),
            ("Long. limon (approximative) :", self.limon_res_var, None), ("Échappée calculée (min.) :", self.echappee_res_var, self.echappee_message_var),
            ("Formule de Blondel (2H+G) :", self.blondel_message_var, None), ("Long. min. escalier (par giron) :", self.longueur_min_escalier_var, None),
            ("Écart Hauteur Totale :", self.hauteur_totale_ecart_message_var, None)
        ]
        for i, (text, res_var, msg_var) in enumerate(results_labels_and_vars, start=1):
            ttk.Label(results_frame, text=text).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            if res_var in [self.blondel_message_var, self.longueur_min_escalier_var, self.hauteur_totale_ecart_message_var]:
                label = ttk.Label(results_frame, textvariable=res_var, font=('Segoe UI', 10, 'bold'))
                label.grid(row=i, column=1, sticky="w", padx=5, columnspan=2)
            else:
                ttk.Label(results_frame, textvariable=res_var, font=('Segoe UI', 10, 'bold')).grid(row=i, column=1, sticky="w", padx=5)
                if msg_var:
                    msg_label = ttk.Label(results_frame, textvariable=msg_var)
                    msg_label.grid(row=i, column=2, sticky="ew", padx=5)
                    msg_label.bind("<Configure>", lambda e, v=msg_var, w=msg_label: self._update_indicator_style(v, w))
                    self._update_indicator_style(msg_var, msg_label)

    def _update_indicator_style(self, var, widget):
        text = var.get()
        style_map = { "NON CONFORME": "Indicator.Red.TLabel", "TRÈS RAIDE": "Indicator.Red.TLabel", "LIMITE": "Indicator.Yellow.TLabel", "Confort Limité": "Indicator.Yellow.TLabel", "OK": "Indicator.Green.TLabel", "OPTIMAL": "Indicator.Green.TLabel", "Nul": "TLabel" }
        display_map = { "NON CONFORME": "❌ NON CONFORME", "TRÈS RAIDE": "❌ TRÈS RAIDE", "LIMITE": "⚠️ LIMITE", "Confort Limité": "⚠️ CONFORT LIMITÉ", "OK": "✅ OK", "OPTIMAL": "✅ OPTIMAL", "Nul": "✅ Nul" }
        style, display_text = "TLabel", text
        for key, s in style_map.items():
            if key in text: style = s; display_text = display_map.get(key, text); break
        widget.config(style=style, text=display_text)

    def _create_warnings_frame(self, parent):
        warnings_frame = ttk.LabelFrame(parent, text="4. Résumé des Avertissements")
        warnings_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.warnings_label = ttk.Label(warnings_frame, textvariable=self.warnings_var, wraplength=380, justify=tk.LEFT)
        self.warnings_label.pack(padx=10, pady=10, fill="both", expand=True)

    def _create_visual_tab(self, notebook):
        visual_frame = ttk.Frame(notebook, padding=5)
        self.canvas = tk.Canvas(visual_frame) 
        self.canvas.pack(expand=True, fill="both")
        notebook.add(visual_frame, text="Aperçu 2D")

    def _create_report_tab(self, notebook):
        report_frame = ttk.Frame(notebook, padding=5)
        self.report_text = tk.Text(report_frame, wrap="word", font=("Courier New", 9)) 
        self.report_text.pack(expand=True, fill="both")
        notebook.add(report_frame, text="Plan de Traçage")
    
    def _create_table_tab(self, notebook):
        table_frame = ttk.Frame(notebook, padding=5)
        self.table_text = tk.Text(table_frame, wrap="none", font=("Courier New", 9)) 
        self.table_text.pack(expand=True, fill="both")
        notebook.add(table_frame, text="Tableau des Marches")

    def _bind_events(self):
        for var_name, var_obj in self.tk_input_vars_dict.items():
            var_obj.trace_add("write", lambda *args, vn=var_name: self.recalculate_and_update_ui(changed_var_name=vn))
        self.nombre_cm_manuel_var.trace_add("write", lambda *args, vn="nombre_cm_manuel_var": self.recalculate_and_update_ui(changed_var_name=vn))
        self.nombre_marches_manuel_var.trace_add("write", lambda *args, vn="nombre_marches_manuel_var": self.recalculate_and_update_ui(changed_var_name=vn))
        self.canvas.bind("<Configure>", self.update_visual_preview)
        self.hauteur_totale_var.trace_add("write", lambda *args: self._update_from_height())

    def _update_from_height(self):
        """Met à jour les valeurs quand la hauteur totale change"""
        if self._is_updating_ui:
            return
        try:
            height = formatting.parser_fraction(self.hauteur_totale_var.get())
            if height <= 0:
                return
                
            # Calcul du nombre de contremarches optimal
            hcm_ideal = constants.HAUTEUR_CM_CONFORT_CIBLE
            nb_cm = max(2, round(height / hcm_ideal))
            hcm_reel = height / nb_cm
            
            # Mise à jour des champs
            self._is_updating_ui = True
            self.nombre_cm_manuel_var.set(str(nb_cm))
            self.nombre_marches_manuel_var.set(str(nb_cm - 1))
            self.hauteur_cm_souhaitee_var.set(
                formatting.decimal_to_fraction_str(hcm_reel, self.app_preferences)
            )
            
            if constants.DEBUG_MODE_ACTIVE:
                print(f"DEBUG - Mise à jour depuis hauteur {height}: CM={nb_cm}, HCM={hcm_reel}")
        finally:
            self._is_updating_ui = False
            self.recalculate_and_update_ui()

    def _update_from_marches(self, new_nb_marches):
        """Met à jour les valeurs quand le nombre de marches change"""
        if self._is_updating_ui:
            return
        try:
            self._is_updating_ui = True
            nb_cm = new_nb_marches + 1
            self.nombre_cm_manuel_var.set(str(nb_cm))
            
            # Si on a une hauteur totale, on ajuste la hauteur de contremarse
            height = formatting.parser_fraction(self.hauteur_totale_var.get() or "0")
            if height > 0:
                hcm = height / nb_cm
                self.hauteur_cm_souhaitee_var.set(
                    formatting.decimal_to_fraction_str(hcm, self.app_preferences)
                )
            
            if constants.DEBUG_MODE_ACTIVE:
                print(f"DEBUG - Mise à jour depuis marches {new_nb_marches}: CM={nb_cm}")
        finally:
            self._is_updating_ui = False
            self.recalculate_and_update_ui()

    def _update_from_cm(self, new_nb_cm):
        """Met à jour les valeurs quand le nombre de contremarches change"""
        if self._is_updating_ui:
            return
        try:
            self._is_updating_ui = True
            self.nombre_marches_manuel_var.set(str(new_nb_cm - 1))
            
            # Si on a une hauteur totale, on ajuste la hauteur de contremarche
            height = formatting.parser_fraction(self.hauteur_totale_var.get() or "0")
            if height > 0:
                hcm = height / new_nb_cm
                self.hauteur_cm_souhaitee_var.set(
                    formatting.decimal_to_fraction_str(hcm, self.app_preferences)
                )
            
            if constants.DEBUG_MODE_ACTIVE:
                print(f"DEBUG - Mise à jour depuis CM {new_nb_cm}")
        finally:
            self._is_updating_ui = False
            self.recalculate_and_update_ui()

    def decrement_cm(self):
        """Décrémente le nombre de contremarches"""
        try:
            current_val = int(self.nombre_cm_manuel_var.get().strip() or "0")
            if current_val > 2:
                self._update_from_cm(current_val - 1)
        except ValueError:
            pass

    def increment_cm(self):
        """Incrémente le nombre de contremarches"""
        try:
            current_val = int(self.nombre_cm_manuel_var.get().strip() or "0")
            if current_val < 50:
                self._update_from_cm(current_val + 1)
        except ValueError:
            pass

    def decrement_marches(self):
        """Décrémente le nombre de marches"""
        try:
            current_val = int(self.nombre_marches_manuel_var.get().strip() or "0")
            if current_val > 1:
                self._update_from_marches(current_val - 1)
        except ValueError:
            pass

    def increment_marches(self):
        """Incrémente le nombre de marches"""
        try:
            current_val = int(self.nombre_marches_manuel_var.get().strip() or "0")
            if current_val < 49:
                self._update_from_marches(current_val + 1)
        except ValueError:
            pass

    def decrement_hcm(self):
        try:
            current_val = formatting.parser_fraction(self.hauteur_cm_souhaitee_var.get())
            new_val = max(constants.HAUTEUR_CM_MIN_REGLEMENTAIRE, current_val - 0.125)
            self.hauteur_cm_souhaitee_var.set(formatting.decimal_to_fraction_str(new_val, self.app_preferences))
        except (ValueError, Exception): pass

    def increment_hcm(self):
        try:
            current_val = formatting.parser_fraction(self.hauteur_cm_souhaitee_var.get())
            new_val = min(constants.HAUTEUR_CM_MAX_REGLEMENTAIRE, current_val + 0.125)
            self.hauteur_cm_souhaitee_var.set(formatting.decimal_to_fraction_str(new_val, self.app_preferences))
        except (ValueError, Exception): pass

    def decrement_giron(self):
        try:
            current_val = formatting.parser_fraction(self.giron_souhaite_var.get())
            new_val = max(constants.GIRON_MIN_REGLEMENTAIRE, current_val - 0.125)
            self.giron_souhaite_var.set(formatting.decimal_to_fraction_str(new_val, self.app_preferences))
        except (ValueError, Exception): pass

    def increment_giron(self):
        try:
            current_val = formatting.parser_fraction(self.giron_souhaite_var.get())
            new_val = min(constants.GIRON_MAX_REGLEMENTAIRE, current_val + 0.125)
            self.giron_souhaite_var.set(formatting.decimal_to_fraction_str(new_val, self.app_preferences))
        except (ValueError, Exception): pass

    def apply_ideal_values(self):
        default_tread = self.app_preferences.get("default_tread_width_straight", "9 1/4").replace('"', '')
        self.giron_souhaite_var.set(formatting.decimal_to_fraction_str(formatting.parser_fraction(default_tread), self.app_preferences))
        self.hauteur_cm_souhaitee_var.set(formatting.decimal_to_fraction_str(constants.HAUTEUR_CM_CONFORT_CIBLE, self.app_preferences))
        h_tot = formatting.parser_fraction(self.hauteur_totale_var.get() or "0")
        if h_tot > 0:
            nb_cm = max(2, round(h_tot / constants.HAUTEUR_CM_CONFORT_CIBLE))
            self.nombre_cm_manuel_var.set(str(nb_cm))
            self.nombre_marches_manuel_var.set(str(nb_cm - 1))
        messagebox.showinfo("Valeurs Idéales", "Les valeurs de confort ont été appliquées.", parent=self)

    def recalculate_and_update_ui(self, *args, changed_var_name=None):
        if self._is_updating_ui: return
        self._is_updating_ui = True
        self.clear_messages()
        
        try:
            # Vérification de l'initialisation des modules
            # Supprimé car inutile si le module est bien défini

            # 1. Récupération des valeurs
            input_values = {
                'hauteur_totale': self.hauteur_totale_var.get().strip(),
                'hauteur_cm': self.hauteur_cm_souhaitee_var.get().strip(),
                'nb_cm': self.nombre_cm_manuel_var.get().strip(),
                'nb_marches': self.nombre_marches_manuel_var.get().strip(),
                'giron': self.giron_souhaite_var.get().strip(),
                'ep_plancher_sup': self.epaisseur_plancher_sup_var.get().strip(),
                'ep_plancher_inf': self.epaisseur_plancher_inf_var.get().strip()
            }

            if constants.DEBUG_MODE_ACTIVE:
                print("\nDEBUG - Valeurs d'entrée:")
                for k, v in input_values.items():
                    print(f"  {k}: '{v}'")

            # 2. Validation des formats
            required_numeric_fields = {
                'giron': input_values['giron'],
                'ep_plancher_sup': input_values['ep_plancher_sup'],
                'ep_plancher_inf': input_values['ep_plancher_inf']
            }

            # Vérification des champs numériques obligatoires
            for field_name, value in required_numeric_fields.items():
                if not value:
                    raise ValueError(f"Le champ {field_name} est obligatoire")
                try:
                    _ = formatting.parser_fraction(value)
                except Exception as e:
                    raise ValueError(f"Format invalide pour {field_name}: {value} ({str(e)})")

            # 3. Vérification de la règle de saisie minimale
            valid_combinations = [
                input_values['hauteur_totale'] and input_values['hauteur_cm'],  # Cas 1
                input_values['nb_cm'] and input_values['hauteur_cm']           # Cas 2
                # Cas 3 supprimé car redondant avec le calcul automatique du nombre de contremarches
            ]

            if not any(valid_combinations):
                raise ValueError("Configuration invalide: fournir (hauteur totale ET hauteur CM) OU (nombre CM ET hauteur CM)")

            # 4. Conversion et calcul
            unite_calcul = "Pouces" if self.unites_var.get() == "pouces" else "Centimètres"
            
            if constants.DEBUG_MODE_ACTIVE:
                print(f"\nDEBUG - Lancement calcul avec unité: {unite_calcul}")

            calc_output = calculations.calculer_escalier_ajuste(
                hauteur_totale_escalier_str=input_values['hauteur_totale'],
                giron_souhaite_str=input_values['giron'],
                hauteur_cm_souhaitee_str=input_values['hauteur_cm'],
                nombre_marches_manuel_str=input_values['nb_marches'],
                nombre_cm_manuel_str=input_values['nb_cm'],
                epaisseur_plancher_sup_str=input_values['ep_plancher_sup'],
                epaisseur_plancher_inf_str=input_values['ep_plancher_inf'],
                profondeur_tremie_ouverture_str=self.profondeur_tremie_ouverture_var.get(),
                position_tremie_ouverture_str=self.position_tremie_var.get(),
                espace_disponible_str=self.espace_disponible_var.get(),
                loaded_app_preferences_dict=self.app_preferences,
                changed_var_name=changed_var_name,
                unite=unite_calcul
            )

            # 5. Traitement des résultats
            self.latest_results = calc_output.get("results", {})
            
            if constants.DEBUG_MODE_ACTIVE:
                print("\nDEBUG - Résultats reçus:", bool(self.latest_results))
                if self.latest_results:
                    print("  - nb_girons:", self.latest_results.get("nombre_girons"))
                    print("  - hauteur_cm:", self.latest_results.get("hauteur_reelle_contremarche"))
                    print("  - giron:", self.latest_results.get("giron_utilise"))

            if not self.latest_results:
                raise ValueError("Aucun résultat retourné par le calcul")

            # 6. Mise à jour de l'interface
            self._update_interface_from_results(self.latest_results)
            self.update_results_display()
            self.update_warnings_display(calc_output["warnings"], calc_output["is_conform"])
            self.update_visual_preview()
            self.update_reports()

        except ValueError as ve:
            self.conformity_status_var.set("DONNÉES INVALIDES")
            self.warnings_var.set(f"Erreur de validation: {str(ve)}")
            if constants.DEBUG_MODE_ACTIVE:
                print(f"\nDEBUG - Erreur de validation: {str(ve)}")
        except Exception as e:
            self.conformity_status_var.set("ERREUR DE CALCUL")
            self.warnings_var.set(f"Une erreur inattendue s'est produite: {str(e)}")
            if constants.DEBUG_MODE_ACTIVE:
                import traceback
                print("\nDEBUG - Erreur inattendue:")
                traceback.print_exc()
        finally:
            self._is_updating_ui = False

    def _update_interface_from_results(self, results):
        """Nouvelle méthode pour centraliser la mise à jour des champs depuis les résultats"""
        if not results:
            return

        # Mise à jour des valeurs calculées
        if self.unites_var.get() == 'pouces':
            if results.get("hauteur_reelle_contremarche") is not None:
                self.hauteur_cm_souhaitee_var.set(
                    formatting.decimal_to_fraction_str(
                        results["hauteur_reelle_contremarche"], 
                        self.app_preferences
                    )
                )
            if results.get("giron_utilise") is not None:
                self.giron_souhaite_var.set(
                    formatting.decimal_to_fraction_str(
                        results["giron_utilise"], 
                        self.app_preferences
                    )
                )
        else:
            if results.get("hauteur_reelle_contremarche") is not None:
                self.hauteur_cm_souhaitee_var.set(
                    f"{results['hauteur_reelle_contremarche'] * constants.POUCE_EN_CM:.2f}"
                )
            if results.get("giron_utilise") is not None:
                self.giron_souhaite_var.set(
                    f"{results['giron_utilise'] * constants.POUCE_EN_CM:.2f}"
                )

        # Mise à jour des nombres de marches/contremarches
        if results.get("nombre_contremarches") is not None:
            self.nombre_cm_manuel_var.set(str(results["nombre_contremarches"]))
        if results.get("nombre_girons") is not None:
            self.nombre_marches_manuel_var.set(str(results["nombre_girons"]))

    def update_results_display(self):
        res, prefs = self.latest_results, self.app_preferences
        df = lambda v: formatting.decimal_to_fraction_str(v, prefs) if v is not None else ""
        if self.unites_var.get() == 'cm':
            df_mm = lambda v: f"{v * constants.POUCE_EN_CM:.2f} cm" if v is not None else ""
        else:
            df_mm = lambda v: f"{df(v)} ({round(v * constants.POUCE_EN_MM)} mm)" if v else ""
        if not res: self.clear_results_display(); return
        self.hauteur_reelle_cm_res_var.set(df_mm(res.get("hauteur_reelle_contremarche")))
        self.giron_utilise_res_var.set(df_mm(res.get('giron_utilise')))
        self.longueur_totale_res_var.set(df_mm(res.get("longueur_calculee_escalier")))
        self.angle_res_var.set(f"{res.get('angle_escalier', 0):.2f}°")
        self.limon_res_var.set(df_mm(res.get("longueur_limon_approximative")))
        self.echappee_res_var.set(df_mm(res.get("min_echappee_calculee")))
        nb_girons = res.get("nombre_girons", 0)
        self.longueur_min_escalier_var.set(f"Req: {df_mm(nb_girons * constants.GIRON_MIN_REGLEMENTAIRE)}" if nb_girons else "")
        self.hauteur_cm_message_var.set(res.get("hauteur_cm_message", ""))
        self.giron_message_var.set(res.get("giron_message", ""))
        self.echappee_message_var.set(res.get("echappee_message", ""))
        self.blondel_message_var.set(f"{res.get('blondel_message', '')} ({df(res.get('blondel_value'))}\")")
        self.longueur_disponible_message_var.set(res.get("longueur_disponible_message", ""))
        self.angle_message_var.set(res.get("angle_message", ""))
        self.hauteur_totale_ecart_message_var.set(res.get("hauteur_totale_ecart_message", ""))

    def update_warnings_display(self, warnings, is_conform):
        self.warnings_var.set("\n".join(warnings) if warnings else "Aucun avertissement.")
        if not is_conform:
            self.conformity_status_var.set("✗ NON CONFORME")
            self.conformity_label.config(foreground=self.themes[self.current_theme]["error"])
        elif warnings:
            self.conformity_status_var.set("CONFORME AVEC AVERTISSEMENTS")
            self.conformity_label.config(foreground=self.themes[self.current_theme]["warning"])
        else:
            self.conformity_status_var.set("✓ CONFORME")
            self.conformity_label.config(foreground=self.themes[self.current_theme]["success"])

    def clear_messages(self):
        for var in [self.warnings_var, self.hauteur_cm_message_var, self.giron_message_var, self.echappee_message_var, self.blondel_message_var, self.longueur_disponible_message_var, self.angle_message_var, self.hauteur_totale_ecart_message_var]: var.set("")
        self.conformity_status_var.set("EN ATTENTE")
        self.conformity_label.config(foreground=self.themes[self.current_theme]["fg"])

    def clear_results_display(self):
        for var in [self.hauteur_reelle_cm_res_var, self.giron_utilise_res_var, self.longueur_totale_res_var, self.angle_res_var, self.limon_res_var, self.echappee_res_var, self.longueur_min_escalier_var]: var.set("")
        self.clear_messages()

    def update_visual_preview(self, event=None):
        self.canvas.delete("all")
        canvas_width, canvas_height = self.canvas.winfo_width(), self.canvas.winfo_height()
        nombre_girons = self.latest_results.get("nombre_girons")
        if nombre_girons is not None and nombre_girons > 0:
            res = self.latest_results
            giron, h_cm = res.get("giron_utilise", 0), res.get("hauteur_reelle_contremarche", 0)
            if giron <= 0 or h_cm <= 0: return
            total_w, total_h = res["nombre_girons"] * giron, res["nombre_contremarches"] * h_cm
            scale = min(canvas_width / total_w, canvas_height / total_h) * 0.8 if total_w > 0 and total_h > 0 else 1
            x, y = 50, canvas_height - 50
            for _ in range(res["nombre_girons"]):
                self.canvas.create_line(x, y, x + giron * scale, y, fill=self.themes[self.current_theme]["canvas_line"], width=2)
                x += giron * scale
                self.canvas.create_line(x, y, x, y - h_cm * scale, fill=self.themes[self.current_theme]["canvas_line"], width=2)
                y -= h_cm * scale
            self.canvas.create_text(canvas_width/2, 30, text=f"Escalier: {res['nombre_girons']} marches", fill=self.themes[self.current_theme]["canvas_line"], font=("Arial", 12, "bold"))

    def update_reports(self):
        if self.latest_results and self.latest_results.get("nombre_girons") is not None:
            plan = reporting.generer_texte_trace(self.latest_results, self.app_preferences)
            self.report_text.delete("1.0", tk.END); self.report_text.insert(tk.END, plan)
            params = reporting.generer_tableau_parametres(self.latest_results, self.app_preferences)
            marches = reporting.generer_tableau_marches(self.latest_results, self.app_preferences)
            self.table_text.delete("1.0", tk.END); self.table_text.insert(tk.END, f"{params}\n\n{marches}")
        else:
            msg = "Aucun résultat de calcul disponible."
            self.report_text.delete("1.0", tk.END); self.report_text.insert(tk.END, msg)
            self.table_text.delete("1.0", tk.END); self.table_text.insert(tk.END, msg)

    def open_preferences_dialog(self):
        PreferencesDialog(self, self.app_preferences)
        self.app_preferences = file_operations.load_application_preferences()
        self.recalculate_and_update_ui()
        
    def open_laser_dialog(self):
        # Import or define LaserDialog before using it
        try:
            from core.laser_dialog import LaserDialog
        except ImportError:
            messagebox.showerror("Erreur", "Le module LaserDialog est introuvable.", parent=self)
            return
        dlg = LaserDialog(self)
        self.wait_window(dlg)  # Attend la fermeture
        if dlg.result:
            self.hauteur_totale_var.set(dlg.result)
    def export_pdf_report(self): messagebox.showinfo("Export PDF", "La fonction d'exportation PDF est en développement.", parent=self)

if __name__ == "__main__":
    app = ModernStairCalculator()
    app.mainloop()
    # Si aucun résultat n'est affiché et que la conformité est "EN ATTENTE", cela signifie que les champs obligatoires ne sont pas tous remplis ou qu'une erreur de saisie empêche le calcul.
    # Pour diagnostiquer le problème, vérifiez que tous les champs obligatoires (hauteur totale, giron souhaité, hauteur contremarche souhaitée, épaisseur plancher sup/inf) sont bien renseignés et valides.
    # Règle de saisie minimale : il faut fournir soit la hauteur totale OU le nombre de contremarches ET la hauteur de contremarche,
    # OU le nombre de marches avec la hauteur de contremarche (hauteur totale = hauteur de contremarche * (nombre de marches + 1)).
    # Toutes les autres valeurs seront soit déduites automatiquement (valeurs par défaut) selon les informations fournies, soit modifiées par l'utilisateur en partie ou complètement.
    # Si le problème persiste, activez le mode débogage (Ctrl+D) pour afficher plus d'informations dans la console et faciliter la correction des entrées.
    # Toutes les autres valeurs seront soit déduites automatiquement (valeurs par défaut) selon les informations fournies, soit modifiées par l'utilisateur en partie ou complètement.
    # Si le problème persiste, activez le mode débogage (Ctrl+D) pour afficher plus d'informations dans la console et faciliter la correction des entrées.
