# Fichier: main_app.py

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import math
import subprocess
import json

# CORRECTION: Ajoute le répertoire du projet au chemin de recherche de Python
# pour s'assurer que les modules (core, utils, gui) sont toujours trouvés.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import constants, calculations
from utils import formatting, reporting, file_operations
from gui.dialogs import PreferencesDialog, LaserDialog

# --- Vérification et création du dossier et fichier de préférences ---
from core.constants import DEFAULTS_FILE, DEFAULT_APP_PREFERENCES

# Vérifier si le dossier data existe, sinon le créer
os.makedirs(os.path.dirname(DEFAULTS_FILE), exist_ok=True)

# Vérifier si le fichier de préférences existe, sinon le créer avec les valeurs par défaut
if not os.path.exists(DEFAULTS_FILE):
    with open(DEFAULTS_FILE, 'w') as f:
        json.dump(DEFAULT_APP_PREFERENCES, f, indent=4)

class ModernStairCalculator(tk.Tk):
    """
    Classe principale de l'interface du calculateur d'escalier.
    Gère la fenêtre principale, les entrées, les résultats et les interactions.
    """
    def __init__(self):
        super().__init__()
        self.style = ttk.Style(self)
        self.style.theme_use("clam")  # ou "default", "alt", etc.
        
        self.after(200, self._finalize_startup)

        # --- Configuration de la fenêtre principale ---
        self.title(f"Calculateur d'Escalier Pro v{constants.VERSION_PROGRAMME}")
        self.geometry("1200x850")
        self.minsize(900, 700)

        # --- Chargement et gestion des préférences ---
        self.app_preferences = file_operations.load_application_preferences()

        self.latest_results = {} 
        self.latest_coupe_results = {} 

        self.input_labels_map = {} 
        self._is_updating_ui = False

        self.unites_var = tk.StringVar(value=self.app_preferences.get("unites_affichage", "pouces"))

        from utils import conversion
        self.conversion = conversion
    
        self.themes = {
            "light": { "bg": "#F0F0F0", "fg": "#000000", "frame_bg": "#FFFFFF", "entry_bg": "#FFFFFF", "entry_fg": "#000000", "button_bg": "#E1E1E1", "button_fg": "#000000", "accent": "#0078D7", "accent_fg": "#FFFFFF", "success": "#107C10", "warning": "#D83B01", "error": "#D13438", "canvas_bg": "#EAEAEA", "canvas_line": "#333333", "canvas_accent": "#005A9E" },
            "dark": { "bg": "#2D2D2D", "fg": "#FFFFFF", "frame_bg": "#3C3C3C", "entry_bg": "#2D2D2D", "entry_fg": "#FFFFFF", "button_bg": "#505050", "button_fg": "#FFFFFF", "accent": "#2E9AFE", "accent_fg": "#FFFFFF", "success": "#39D457", "warning": "#FF8C00", "error": "#FF4C4C", "canvas_bg": "#252525", "canvas_line": "#CCCCCC", "canvas_accent": "#2E9AFE" }
        }
        self.current_theme = "light"

        self._setup_style_definitions()
        self._setup_tk_variables()
        self._create_menu()
        self._create_main_layout()
        self._bind_events()
        self.update_debug_menu_label()
        self._update_input_labels_for_debug() 
        self.recalculate_and_update_ui()

    def on_unit_change(self):
        self.conversion.convertir_variables_interface(self, self.tk_input_vars_dict, self.unites_var.get(), self.app_preferences)
        self.recalculate_and_update_ui()

    def _finalize_startup(self):
        if constants.DEBUG_MODE_ACTIVE:
            print("DEBUG: Initialisation tardive de l'interface...")
        self.recalculate_and_update_ui()
        if self.latest_results:
            self.update_results_display()
            self.update_visual_preview()
            self.update_reports()
        
    def _setup_style_definitions(self):
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure("TLabelFrame", borderwidth=2, relief="groove", padding=10)
        self.style.configure("TButton", padding=5)
        self.style.configure("Conformity.TLabel", font=('Segoe UI', 14, 'bold'), foreground=self.themes[self.current_theme]["fg"])
        self.style.configure("Warning.TLabel", foreground=self.themes[self.current_theme]["warning"], font=('TkDefaultFont', 9, 'italic'))
        self.style.configure("Error.TLabel", foreground=self.themes[self.current_theme]["error"], font=('TkDefaultFont', 10, 'bold'))
        self.style.configure("Indicator.Green.TLabel", background=self.themes[self.current_theme]["success"], foreground=self.themes[self.current_theme]["accent_fg"], font=('Segoe UI', 9, 'bold'))
        self.style.configure("Indicator.Yellow.TLabel", background=self.themes[self.current_theme]["warning"], foreground=self.themes[self.current_theme]["fg"], font=('Segoe UI', 9, 'bold'))
        self.style.configure("Indicator.Red.TLabel", background=self.themes[self.current_theme]["error"], foreground=self.themes[self.current_theme]["accent_fg"], font=('Segoe UI', 9, 'bold'))
        self.style.configure("Small.TLabel", font=('Segoe UI', 8)) 

    def _setup_tk_variables(self):
        self.hauteur_totale_var = tk.StringVar(value="108")
        default_tread_width_straight = self.app_preferences.get("default_tread_width_straight", "9 1/4").replace('"', '')
        default_giron_str = formatting.decimal_to_fraction_str(formatting.parser_fraction(default_tread_width_straight), self.app_preferences)
        self.giron_souhaite_var = tk.StringVar(value=default_giron_str)
        default_hcm_str = formatting.decimal_to_fraction_str(constants.HAUTEUR_CM_CONFORT_CIBLE, self.app_preferences)
        self.hauteur_cm_souhaitee_var = tk.StringVar(value=default_hcm_str)
        self.epaisseur_plancher_sup_var = tk.StringVar(value=self.app_preferences.get("default_floor_finish_thickness_upper", "1 1/2"))
        self.profondeur_tremie_ouverture_var = tk.StringVar(value="")
        self.position_tremie_var = tk.StringVar(value="")
        self.epaisseur_plancher_inf_var = tk.StringVar(value=self.app_preferences.get("default_floor_finish_thickness_lower", "1"))
        self.espace_disponible_var = tk.StringVar(value="")
        self.nombre_cm_manuel_var = tk.StringVar(value="")
        self.nombre_cm_ajuste_var = tk.IntVar(value=0)
        self.nombre_marches_manuel_var = tk.StringVar(value="")
        self.nombre_marches_final_display_var = tk.StringVar(value="") 
        self.conformity_status_var = tk.StringVar(value="EN ATTENTE")
        self.hauteur_reelle_cm_res_var = tk.StringVar()
        self.giron_utilise_res_var = tk.StringVar()
        self.longueur_totale_res_var = tk.StringVar()
        self.angle_res_var = tk.StringVar()
        self.limon_res_var = tk.StringVar()
        self.echappee_res_var = tk.StringVar()
        self.longueur_min_escalier_var = tk.StringVar()
        self.warnings_var = tk.StringVar()
        self.hauteur_cm_message_var = tk.StringVar()
        self.giron_message_var = tk.StringVar()
        self.echappee_message_var = tk.StringVar()
        self.blondel_message_var = tk.StringVar()
        self.longueur_disponible_message_var = tk.StringVar()
        self.angle_message_var = tk.StringVar()
        self.hauteur_totale_ecart_message_var = tk.StringVar() 
        self.tk_input_vars_dict = {
            "hauteur_totale_escalier": self.hauteur_totale_var, "giron_souhaite": self.giron_souhaite_var,
            "hauteur_cm_souhaitee": self.hauteur_cm_souhaitee_var, "epaisseur_plancher_sup": self.epaisseur_plancher_sup_var,
            "epaisseur_plancher_inf": self.epaisseur_plancher_inf_var, "longueur_tremie": self.profondeur_tremie_ouverture_var,
            "position_tremie": self.position_tremie_var, "espace_disponible": self.espace_disponible_var
        }

    def _create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Préférences...", command=self.open_preferences_dialog)
        file_menu.add_command(label="Ouvrir un projet...", command=lambda: file_operations.charger_projet(self))
        file_menu.add_command(label="Sauvegarder le projet...", command=lambda: file_operations.sauvegarder_projet(self.latest_results, self))
        file_menu.add_separator()
        file_menu.add_command(label="Exporter le rapport (PDF)...", command=self.export_pdf_report)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Affichage", menu=view_menu)
        tools_menu = tk.Menu(menubar, tearoff=0)
        self.tools_menu = tools_menu 
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="Assistance Laser (4 points)...", command=self.open_laser_dialog)
        tools_menu.add_command(label="Calculateur de Profondeur de Coupe...", command=self.open_profondeur_coupe_tool)
        tools_menu.add_separator()
        self.debug_menu_button = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Débogage", menu=self.debug_menu_button)
        self.debug_menu_button.add_command(label="Activer / Désactiver (Ctrl+D)", command=self.toggle_debug_mode)
        self.debug_menu_index = tools_menu.index(tk.END)
        self.bind_all("<Control-d>", lambda event: self.toggle_debug_mode())
        
    def open_profondeur_coupe_tool(self):
        script_path = "ProfondeurCoupe.py"
        if not os.path.exists(script_path):
            messagebox.showerror("Erreur Fichier", f"Le fichier '{script_path}' est introuvable.", parent=self)
            return
        try:
            result = subprocess.run(['python', script_path], capture_output=True, text=True, check=True, encoding='utf-8')
            output = result.stdout
            start_marker, end_marker = "---DEBUT_JSON_PROFONDEUR_COUPE---", "---FIN_JSON_PROFONDEUR_COUPE---"
            if start_marker in output and end_marker in output:
                json_part_start = output.find(start_marker) + len(start_marker)
                json_part_end = output.find(end_marker)
                json_string = output[json_part_start:json_part_end].strip()
                self.latest_coupe_results = json.loads(json_string)
                res = self.latest_coupe_results.get("resultats_H_mm", {})
                h90, h45 = res.get('H90_mm'), res.get('H45_mm')
                h90_str = f"{h90:.2f} mm" if h90 is not None else "Erreur de calcul"
                h45_str = f"{h45:.2f} mm" if h45 is not None else "Erreur de calcul"
                messagebox.showinfo("Résultats Profondeur de Coupe", f"Les calculs de décalage ont été reçus avec succès:\n\n  • Décalage H90: {h90_str}\n  • Décalage H45: {h45_str}\n\nCes données sont maintenant disponibles pour de futurs calculs.", parent=self)
            else:
                messagebox.showwarning("Erreur de Communication", "Impossible de trouver les données JSON dans la sortie du script.", parent=self)
        except FileNotFoundError: messagebox.showerror("Erreur Python", "L'interpréteur 'python' n'a pas été trouvé. Assurez-vous que Python est dans votre PATH.", parent=self)
        except subprocess.CalledProcessError as e: messagebox.showerror("Erreur d'Exécution", f"L'outil de profondeur de coupe a rencontré une erreur:\n\n{e.stderr}", parent=self)
        except json.JSONDecodeError: messagebox.showerror("Erreur de Données", "Impossible de lire les résultats retournés par l'outil (format JSON invalide).", parent=self)
        except Exception as e: messagebox.showerror("Erreur Inattendue", f"Une erreur inattendue est survenue en lançant l'outil:\n{e}", parent=self)

    def _update_input_labels_for_debug(self):
        for shortcut, (label_widget, original_text) in self.input_labels_map.items():
            label_widget.config(text=f"{original_text} ({shortcut})" if constants.DEBUG_MODE_ACTIVE else original_text)

    def update_debug_menu_label(self): 
        try:
            index = -1
            for i in range(self.tools_menu.index(tk.END) + 1):
                try: label = self.tools_menu.entrycget(i, "label")
                except Exception: continue
                if label and "Débogage" in label:
                    if "Débogage" in label: index = i; break
            if index != -1:
                actual_label_text = self.tools_menu.entrycget(index, "label")
                if "Débogage" in actual_label_text:
                    new_label = "Débogage: Actif (Vert)" if constants.DEBUG_MODE_ACTIVE else "Débogage: Inactif (Rouge)"
                    self.tools_menu.entryconfig(index, label=new_label)
        except Exception as e:
            if constants.DEBUG_MODE_ACTIVE: print(f"DEBUG: Erreur lors de la mise à jour du label de débogage: {e}")

    def toggle_debug_mode(self):
        constants.DEBUG_MODE_ACTIVE = not constants.DEBUG_MODE_ACTIVE
        print(f"Mode débogage {'ACTIVÉ' if constants.DEBUG_MODE_ACTIVE else 'DÉSACTIVÉ'}.")
        self.update_debug_menu_label()
        self._update_input_labels_for_debug() 
        self.recalculate_and_update_ui()

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
        marches_control_frame = ttk.Frame(input_frame)
        marches_control_frame.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(marches_control_frame, text="-", command=self.decrement_marches, width=3).pack(side="left")
        ttk.Entry(marches_control_frame, textvariable=self.nombre_marches_manuel_var, width=5, justify='center', font=('Segoe UI', 10)).pack(side="left", padx=5)
        ttk.Button(marches_control_frame, text="+", command=self.increment_marches, width=3).pack(side="left")
        ttk.Label(input_frame, text="Nb Contremarches (CM) :", font=('Segoe UI', 10, 'bold')).grid(row=row_idx, column=2, sticky="w", padx=5, pady=5)
        cm_control_frame = ttk.Frame(input_frame)
        cm_control_frame.grid(row=row_idx, column=3, sticky="ew", padx=5, pady=5)
        ttk.Button(cm_control_frame, text="-", command=self.decrement_cm, width=3).pack(side="left")
        ttk.Entry(cm_control_frame, textvariable=self.nombre_cm_manuel_var, width=5, justify='center', font=('Segoe UI', 10)).pack(side="left", padx=5)
        ttk.Button(cm_control_frame, text="+", command=self.increment_cm, width=3).pack(side="left")
        row_idx += 1
        ttk.Label(input_frame, text="Giron souhaité :", font=('Segoe UI', 10, 'bold')).grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
        giron_control_frame = ttk.Frame(input_frame)
        giron_control_frame.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(giron_control_frame, text="-", command=self.decrement_giron, width=3).pack(side="left")
        ttk.Entry(giron_control_frame, textvariable=self.giron_souhaite_var, width=10, justify='center', font=('Segoe UI', 10)).pack(side="left", padx=5)
        ttk.Button(giron_control_frame, text="+", command=self.increment_giron, width=3).pack(side="left")
        ttk.Label(input_frame, text="Hauteur contremarche :", font=('Segoe UI', 10, 'bold')).grid(row=row_idx, column=2, sticky="w", padx=5, pady=5)
        hcm_control_frame = ttk.Frame(input_frame)
        hcm_control_frame.grid(row=row_idx, column=3, sticky="ew", padx=5, pady=5)
        ttk.Button(hcm_control_frame, text="-", command=self.decrement_hcm, width=3).pack(side="left")
        ttk.Entry(hcm_control_frame, textvariable=self.hauteur_cm_souhaitee_var, width=10, justify='center', font=('Segoe UI', 10)).pack(side="left", padx=5)
        ttk.Button(hcm_control_frame, text="+", command=self.increment_hcm, width=3).pack(side="left")
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

    def decrement_cm(self):
        try:
            current_val_str = self.nombre_cm_manuel_var.get()
            current_val = int(current_val_str) if current_val_str.strip() else self.latest_results.get("nombre_contremarches", 2)
            if current_val > 2: self.nombre_cm_manuel_var.set(str(current_val - 1))
        except (ValueError, Exception): pass

    def increment_cm(self):
        try:
            current_val_str = self.nombre_cm_manuel_var.get()
            current_val = int(current_val_str) if current_val_str.strip() else self.latest_results.get("nombre_contremarches", 1)
            if current_val < 50: self.nombre_cm_manuel_var.set(str(current_val + 1))
        except (ValueError, Exception): pass

    def decrement_marches(self):
        try:
            current_val_str = self.nombre_marches_manuel_var.get()
            current_val = int(current_val_str) if current_val_str.strip() else self.latest_results.get("nombre_girons", 1)
            if current_val > 1: self.nombre_marches_manuel_var.set(str(current_val - 1))
        except (ValueError, Exception): pass

    def increment_marches(self):
        try:
            current_val_str = self.nombre_marches_manuel_var.get()
            current_val = int(current_val_str) if current_val_str.strip() else self.latest_results.get("nombre_girons", 0)
            if current_val < 49: self.nombre_marches_manuel_var.set(str(current_val + 1))
        except (ValueError, Exception): pass
    
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
            # CORRECTION: S'assurer que l'unité est envoyée avec une majuscule
            unite_calcul = "Pouces" if self.unites_var.get() == "pouces" else "Centimètres"

            calc_output = calculations.calculer_escalier_ajuste(
                hauteur_totale_escalier_str=self.hauteur_totale_var.get(), giron_souhaite_str=self.giron_souhaite_var.get(),
                hauteur_cm_souhaitee_str=self.hauteur_cm_souhaitee_var.get(), nombre_marches_manuel_str=self.nombre_marches_manuel_var.get(),
                nombre_cm_manuel_str=self.nombre_cm_manuel_var.get(), epaisseur_plancher_sup_str=self.epaisseur_plancher_sup_var.get(),
                epaisseur_plancher_inf_str=self.epaisseur_plancher_inf_var.get(), profondeur_tremie_ouverture_str=self.profondeur_tremie_ouverture_var.get(),
                position_tremie_ouverture_str=self.position_tremie_var.get(), espace_disponible_str=self.espace_disponible_var.get(),
                loaded_app_preferences_dict=self.app_preferences, changed_var_name=changed_var_name,
                unite=unite_calcul
            )
            self.latest_results = calc_output["results"]
            
            if self.latest_results:
                hcm_reelle_pouces = self.latest_results.get("hauteur_reelle_contremarche")
                giron_utilise_pouces = self.latest_results.get("giron_utilise")
                
                if self.unites_var.get() == 'pouces':
                    if hcm_reelle_pouces is not None: self.hauteur_cm_souhaitee_var.set(formatting.decimal_to_fraction_str(hcm_reelle_pouces, self.app_preferences))
                    if giron_utilise_pouces is not None: self.giron_souhaite_var.set(formatting.decimal_to_fraction_str(giron_utilise_pouces, self.app_preferences))
                else: # Mode 'cm'
                    if hcm_reelle_pouces is not None: self.hauteur_cm_souhaitee_var.set(f"{hcm_reelle_pouces * constants.POUCE_EN_CM:.2f}")
                    if giron_utilise_pouces is not None: self.giron_souhaite_var.set(f"{giron_utilise_pouces * constants.POUCE_EN_CM:.2f}")

                if self.latest_results.get("nombre_contremarches") is not None: self.nombre_cm_manuel_var.set(str(self.latest_results["nombre_contremarches"]))
                if self.latest_results.get("nombre_girons") is not None: self.nombre_marches_manuel_var.set(str(self.latest_results["nombre_girons"]))

            self.update_results_display()
            self.update_warnings_display(calc_output["warnings"], calc_output["is_conform"])
            self.update_visual_preview()
            self.update_reports()
        except Exception as e:
            self.conformity_status_var.set("ERREUR DE SAISIE")
            self.warnings_var.set(f"Format invalide ou données insuffisantes.\n({e})")
            if constants.DEBUG_MODE_ACTIVE: import traceback; traceback.print_exc()
        finally:
            self._is_updating_ui = False

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
        
    def open_laser_dialog(self): LaserDialog(self)
    def export_pdf_report(self): messagebox.showinfo("Export PDF", "La fonction d'exportation PDF est en développement.", parent=self)

if __name__ == "__main__":
    app = ModernStairCalculator()
    app.mainloop()
