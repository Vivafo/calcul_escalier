# Fichier: main_app.py

import tkinter as tk
from tkinter import ttk, messagebox
import math
import subprocess
import json
import os

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
        # Charger les préférences AVANT toute utilisation
        self.app_preferences = file_operations.load_application_preferences()

        self.latest_results = {} # Stocke les derniers résultats de calcul
        self.latest_coupe_results = {} # Stocke les résultats de l'outil de profondeur de coupe

        # REF-007: Ajout de la variable pour stocker les références des labels d'entrée pour le mode débogage
        self.input_labels_map = {} 
        # REF-008: Ajout d'un drapeau pour éviter les boucles de mise à jour entre marches/contremarches
        self._is_updating_ui = False

        # Ajout de la variable d'unités d'affichage
        self.unites_var = tk.StringVar(value=self.app_preferences.get("unites_affichage", "pouces"))

        # Import du module conversion (pour éviter les imports circulaires)
        from utils import conversion
        self.conversion = conversion
    def on_unit_change(self):
        unite_source = "Pouces" if self.unites_var.get() == "pouces" else "Centimètres"
        unite_cible = "Centimètres" if unite_source == "Pouces" else "Pouces"
        self.conversion.convertir_variables_interface(self.tk_input_vars_dict, unite_source, unite_cible)
        self.recalculate_and_update_ui()

        # --- Définition des palettes de couleurs pour les thèmes ---
        self.themes = {
            "light": {
                "bg": "#F0F0F0", "fg": "#000000",
                "frame_bg": "#FFFFFF", "entry_bg": "#FFFFFF", "entry_fg": "#000000",
                "button_bg": "#E1E1E1", "button_fg": "#000000",
                "accent": "#0078D7", "accent_fg": "#FFFFFF",
                "success": "#107C10", "warning": "#D83B01", "error": "#D13438",
                "canvas_bg": "#EAEAEA", "canvas_line": "#333333", "canvas_accent": "#005A9E"
            },
            "dark": {
                "bg": "#2D2D2D", "fg": "#FFFFFF",
                "frame_bg": "#3C3C3C", "entry_bg": "#2D2D2D", "entry_fg": "#FFFFFF",
                "button_bg": "#505050", "button_fg": "#FFFFFF",
                "accent": "#2E9AFE", "accent_fg": "#FFFFFF",
                "success": "#39D457", "warning": "#FF8C00", "error": "#FF4C4C",
                "canvas_bg": "#252525", "canvas_line": "#CCCCCC", "canvas_accent": "#2E9AFE"
            }
        }
        self.current_theme = "light"

        # IMPORTANT: L'ordre des appels est crucial ici
        self._setup_style_definitions()
        self._setup_tk_variables()
        self._create_menu()
        self._create_main_layout() # <-- Cette fonction crée les labels d'entrée

        self._bind_events()
       
        self.update_debug_menu_label() # Appel initial pour le label du menu débogage
        # REF-007: Appel initial pour mettre à jour les labels d'entrée avec/sans codes de référence
        self._update_input_labels_for_debug() 
        self.recalculate_and_update_ui()

        # Définir les valeurs par défaut interactives
        # Ces valeurs sont initialisées dans _setup_tk_variables
        # self.hauteur_cm_souhaitee_var.set("7 1/2")
        # self.giron_souhaite_var.set("9 1/4")
    
    def _finalize_startup(self):
        if constants.DEBUG_MODE_ACTIVE:
            print("DEBUG: Initialisation tardive de l'interface...")
            print("  - HT:", self.hauteur_totale_var.get())
            print("  - Giron:", self.giron_souhaite_var.get())
            print("  - HCM:", self.hauteur_cm_souhaitee_var.get())

        self.recalculate_and_update_ui()

        if self.latest_results:
            self.update_results_display()
            self.update_visual_preview()
            self.update_reports()
        
    def _setup_style_definitions(self):
        """Configure les définitions de styles visuels de l'application."""
        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        # Styles personnalisés
        self.style.configure("TLabelFrame", borderwidth=2, relief="groove", padding=10)
        self.style.configure("TButton", padding=5)
        
        # Styles pour les messages de conformité/avertissement
        self.style.configure("Conformity.TLabel", font=('Segoe UI', 14, 'bold'), foreground=self.themes[self.current_theme]["fg"])
        self.style.configure("Warning.TLabel", foreground=self.themes[self.current_theme]["warning"], font=('TkDefaultFont', 9, 'italic'))
        self.style.configure("Error.TLabel", foreground=self.themes[self.current_theme]["error"], font=('TkDefaultFont', 10, 'bold'))
        # Styles pour les indicateurs (Vert/Jaune/Rouge)
        self.style.configure("Indicator.Green.TLabel", background=self.themes[self.current_theme]["success"], foreground=self.themes[self.current_theme]["accent_fg"], font=('Segoe UI', 9, 'bold'))
        self.style.configure("Indicator.Yellow.TLabel", background=self.themes[self.current_theme]["warning"], foreground=self.themes[self.current_theme]["fg"], font=('Segoe UI', 9, 'bold'))
        self.style.configure("Indicator.Red.TLabel", background=self.themes[self.current_theme]["error"], foreground=self.themes[self.current_theme]["accent_fg"], font=('Segoe UI', 9, 'bold'))
        self.style.configure("Small.TLabel", font=('Segoe UI', 8)) 

    def _setup_tk_variables(self):
        """Initialise les variables Tkinter utilisées pour l'interface."""
        # Variables pour les entrées utilisateur
        self.hauteur_totale_var = tk.StringVar(value="108")
        
        # REF-010 & REF-011: Formater la valeur par défaut du giron et de la HCM en fraction dès l'initialisation
        # La valeur lue des préférences peut contenir des guillemets, il faut les enlever pour le parser.
        default_tread_width_straight = self.app_preferences.get("default_tread_width_straight", "9 1/4").replace('"', '')
        
        default_giron_str = formatting.decimal_to_fraction_str(
            formatting.parser_fraction(default_tread_width_straight), # Utilisez la valeur nettoyée
            self.app_preferences
        )
        self.giron_souhaite_var = tk.StringVar(value=default_giron_str)

        default_hcm_str = formatting.decimal_to_fraction_str(
            constants.HAUTEUR_CM_CONFORT_CIBLE,
            self.app_preferences
        )
        self.hauteur_cm_souhaitee_var = tk.StringVar(value=default_hcm_str)

        self.epaisseur_plancher_sup_var = tk.StringVar(value=self.app_preferences.get("default_floor_finish_thickness_upper", "1 1/2"))
        self.profondeur_tremie_ouverture_var = tk.StringVar(value="")
        self.position_tremie_var = tk.StringVar(value="")
        self.epaisseur_plancher_inf_var = tk.StringVar(value=self.app_preferences.get("default_floor_finish_thickness_lower", "1"))
        self.espace_disponible_var = tk.StringVar(value="")
        self.nombre_cm_manuel_var = tk.StringVar(value="")
        self.nombre_cm_ajuste_var = tk.IntVar(value=0) # Variable interne pour le nombre de CM ajusté
        
        # REF-008: Nouvelle variable pour l'entrée manuelle du nombre de marches
        self.nombre_marches_manuel_var = tk.StringVar(value="")
        # REF-008: Variable pour l'affichage final du nombre de marches (girons) dans l'UI
        self.nombre_marches_final_display_var = tk.StringVar(value="") 

        # Variables pour les résultats affichés
        self.conformity_status_var = tk.StringVar(value="EN ATTENTE")
        self.hauteur_reelle_cm_res_var = tk.StringVar()
        self.giron_utilise_res_var = tk.StringVar()  # <-- Ajouté pour l'affichage du giron utilisé
        self.longueur_totale_res_var = tk.StringVar()
        self.angle_res_var = tk.StringVar()
        self.limon_res_var = tk.StringVar()
        self.echappee_res_var = tk.StringVar()
        self.longueur_min_escalier_var = tk.StringVar()

        # Variable pour les messages d'avertissement et de conformité
        self.warnings_var = tk.StringVar()
        self.hauteur_cm_message_var = tk.StringVar()
        self.giron_message_var = tk.StringVar()
        self.echappee_message_var = tk.StringVar()
        self.blondel_message_var = tk.StringVar()
        self.longueur_disponible_message_var = tk.StringVar()
        self.angle_message_var = tk.StringVar()
        # Nouvelle variable pour le message d'écart de hauteur totale
        self.hauteur_totale_ecart_message_var = tk.StringVar() 

        # Dictionnaire pour conversion dynamique pouces/cm
        self.tk_input_vars_dict = {
            "hauteur_totale_escalier": self.hauteur_totale_var,
            "giron_souhaite": self.giron_souhaite_var,
            "hauteur_cm_souhaitee": self.hauteur_cm_souhaitee_var,
            "epaisseur_plancher_sup": self.epaisseur_plancher_sup_var,
            "epaisseur_plancher_inf": self.epaisseur_plancher_inf_var,
            "longueur_tremie": self.profondeur_tremie_ouverture_var,
            "position_tremie": self.position_tremie_var,
            "espace_disponible": self.espace_disponible_var
        }

    def _create_menu(self):
        """Crée la barre de menu de l'application."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        # Utilisation de lambda pour s'assurer que self est correctement lié au moment de l'appel
        file_menu.add_command(label="Préférences...", command=lambda: self.open_preferences_dialog())
        file_menu.add_command(label="Ouvrir un projet...", command=lambda: file_operations.charger_projet(self))
        file_menu.add_command(label="Sauvegarder le projet...", command=lambda: file_operations.sauvegarder_projet(self.latest_results, self))
        file_menu.add_separator()
        file_menu.add_command(label="Exporter le rapport (PDF)...", command=lambda: self.export_pdf_report())
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit)
        
        # Menu Affichage (pour le thème)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Affichage", menu=view_menu)
     
     

        
        # Menu Outils
        tools_menu = tk.Menu(menubar, tearoff=0)
        self.tools_menu = tools_menu 
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="Assistance Laser (4 points)...", command=lambda: self.open_laser_dialog())
        tools_menu.add_command(label="Calculateur de Profondeur de Coupe...", command=lambda: self.open_profondeur_coupe_tool())
        tools_menu.add_separator()
        
        # Menu de débogage
        self.debug_menu_button = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Débogage", menu=self.debug_menu_button)
        # La commande toggle_debug_mode doit aussi être une lambda pour la cohérence
        self.debug_menu_button.add_command(label="Activer / Désactiver (Ctrl+D)", command=lambda: self.toggle_debug_mode())
        
        self.debug_menu_index = tools_menu.index(tk.END) # Sauvegarde l'index de ce menu pour pouvoir le modifier plus tard
        self.bind_all("<Control-d>", lambda event: self.toggle_debug_mode())
        
    def open_profondeur_coupe_tool(self):
        """
        Lance le script ProfondeurCoupe.py comme un processus séparé,
        capture sa sortie JSON, et affiche les résultats.
        """
        script_path = "ProfondeurCoupe.py"
        if not os.path.exists(script_path):
            messagebox.showerror("Erreur Fichier", f"Le fichier '{script_path}' est introuvable.", parent=self)
            return

        try:
            result = subprocess.run(
                ['python', script_path], 
                capture_output=True, 
                text=True, 
                check=True,
                encoding='utf-8'
            )
            
            output = result.stdout
            
            start_marker = "---DEBUT_JSON_PROFONDEUR_COUPE---"
            end_marker = "---FIN_JSON_PROFONDEUR_COUPE---"
            
            if start_marker in output and end_marker in output:
                json_part_start = output.find(start_marker) + len(start_marker)
                json_part_end = output.find(end_marker)
                json_string = output[json_part_start:json_part_end].strip()
                
                self.latest_coupe_results = json.loads(json_string)
                
                res = self.latest_coupe_results.get("resultats_H_mm", {})
                h90 = res.get('H90_mm')
                h45 = res.get('H45_mm')
                
                h90_str = f"{h90:.2f} mm" if h90 is not None else "Erreur de calcul"
                h45_str = f"{h45:.2f} mm" if h45 is not None else "Erreur de calcul"

                messagebox.showinfo(
                    "Résultats Profondeur de Coupe",
                    f"Les calculs de décalage ont été reçus avec succès:\n\n"
                    f"  • Décalage H90: {h90_str}\n"
                    f"  • Décalage H45: {h45_str}\n\n"
                    "Ces données sont maintenant disponibles pour de futurs calculs.",
                    parent=self
                )
            else:
                messagebox.showwarning("Erreur de Communication", 
                                       "Impossible de trouver les données JSON dans la sortie du script.", parent=self)

        except FileNotFoundError:
            messagebox.showerror("Erreur Python", "L'interpréteur 'python' n'a pas été trouvé. Assurez-vous que Python est dans votre PATH.", parent=self)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erreur d'Exécution", f"L'outil de profondeur de coupe a rencontré une erreur:\n\n{e.stderr}", parent=self)
        except json.JSONDecodeError:
            messagebox.showerror("Erreur de Données", "Impossible de lire les résultats retournés par l'outil (format JSON invalide).", parent=self)
        except Exception as e:
            messagebox.showerror("Erreur Inattendue", f"Une erreur inattendue est survenue en lançant l'outil:\n{e}", parent=self)

    # REF-007: Nouvelle fonction pour gérer l'affichage des codes de référence dans les labels d'entrée
    def _update_input_labels_for_debug(self):
        """Met à jour les labels des champs d'entrée pour afficher ou masquer les codes de référence en mode débogage."""
        for shortcut, (label_widget, original_text) in self.input_labels_map.items():
            if constants.DEBUG_MODE_ACTIVE:
                label_widget.config(text=f"{original_text} ({shortcut})")
            else:
                label_widget.config(text=original_text)

    # REF-002 (Corrigé par REF-005): Modification de la fonction pour mettre à jour le label du menu débogage
    def update_debug_menu_label(self): 
        try:
            index = -1
            for i in range(self.tools_menu.index(tk.END) + 1):
                try:
                    label = self.tools_menu.entrycget(i, "label")
                except Exception:
                    continue
                if label and "Débogage" in label:
                    # Check for exact match first to prevent partial matches
                    if "Débogage" in label: # This is a simple contains check, could be more robust
                        index = i
                        break

            if index != -1:
                # Ensure the correct entry is being updated, especially after new items
                actual_label_text = self.tools_menu.entrycget(index, "label")
                if "Débogage" in actual_label_text: # Double check we're modifying the right one
                    if constants.DEBUG_MODE_ACTIVE:
                        new_label = "Débogage: Actif (Vert)"
                    else:
                        new_label = "Débogage: Inactif (Rouge)"
                    self.tools_menu.entryconfig(index, label=new_label)
        except Exception as e:
            if constants.DEBUG_MODE_ACTIVE:
                print(f"DEBUG: Erreur lors de la mise à jour du label de débogage: {e}")
            pass 

    # REF-001: Ajout de la fonction pour activer/désactiver le mode débogage
    def toggle_debug_mode(self):
        """Bascule le mode débogage et met à jour l'interface."""
        constants.DEBUG_MODE_ACTIVE = not constants.DEBUG_MODE_ACTIVE
        if constants.DEBUG_MODE_ACTIVE:
            print("Mode débogage ACTIVÉ. Les tracebacks complètes des erreurs seront affichées.")
        else:
            print("Mode débogage DÉSACTIVÉ.")
        self.update_debug_menu_label() # Met à jour le label du menu
        # REF-007: Appel pour mettre à jour les labels d'entrée
        self._update_input_labels_for_debug() 
        self.recalculate_and_update_ui()


    def _create_main_layout(self):
        """Crée l'agencement principal de l'interface utilisateur."""
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(expand=True, fill="both", padx=10, pady=10)

        left_frame = ttk.Frame(main_pane, padding=10)
        self._create_input_frame(left_frame)
        # self._create_interactive_frame(left_frame) # Supprimé car fusionné
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
        """
        Crée le cadre pour les entrées utilisateur et les contrôles interactifs fusionnés.
        C'est ici que les boîtes 1 et 2 sont fusionnées visuellement et fonctionnellement.
        """
        input_frame = ttk.LabelFrame(parent, text="1. Entrées et Ajustements de l'Escalier")
        input_frame.pack(fill="x", pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(3, weight=1)
        # Ajout du sélecteur d'unités
        unit_frame = ttk.LabelFrame(input_frame, text="Unités")
        unit_frame.grid(row=0, column=4, rowspan=2, padx=5, pady=5, sticky="nsew")
        self.radio_pouces = ttk.Radiobutton(unit_frame, text="Pouces", variable=self.unites_var, value="pouces", command=self.on_unit_change)
        self.radio_cm = ttk.Radiobutton(unit_frame, text="Centimètres", variable=self.unites_var, value="cm", command=self.on_unit_change)
        self.radio_pouces.grid(row=0, column=0, padx=2, pady=2)
        self.radio_cm.grid(row=1, column=0, padx=2, pady=2)
        
        # Grid pour les entrées principales (ancienne Boîte 1)
        # Hauteur Totale, Epaisseur plancher, Trémie, Espace Disponible
        entries_main = [
            ("Hauteur totale :", "HT", self.hauteur_totale_var, False),
            ("Épaisseur plancher sup. :", "EPS", self.epaisseur_plancher_sup_var, False),
            ("Épaisseur plancher inf. :", "EPI", self.epaisseur_plancher_inf_var, False),
            ("Profondeur ouverture trémie :", "POT", self.profondeur_tremie_ouverture_var, True), # Optional
            ("Position départ trémie:", "PDT", self.position_tremie_var, True), # Optional
            ("Espace disponible (longueur) :", "ED", self.espace_disponible_var, True), # Optional
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
                ttk.Button(entry_frame, text="Laser", command=lambda: self.open_laser_dialog(), width=6).pack(side="left", padx=(5,0))
            row_idx += 1

        ttk.Separator(input_frame, orient='horizontal').grid(row=row_idx, column=0, columnspan=4, sticky='ew', pady=10)
        row_idx += 1

        # Grid pour les ajustements interactifs (ancienne Boîte 2)
        # Nb Marches, Nb Contremarches, Giron souhaité, Hauteur Contremarche
        
        # Nb Marches
        ttk.Label(input_frame, text="Nb Marches (Girons) :", font=('Segoe UI', 10, 'bold')).grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
        marches_control_frame = ttk.Frame(input_frame)
        marches_control_frame.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(marches_control_frame, text="-", command=lambda: self.decrement_marches(), width=3).pack(side="left")
        ttk.Entry(marches_control_frame, textvariable=self.nombre_marches_manuel_var, width=5, justify='center', font=('Segoe UI', 10)).pack(side="left", padx=5)
        ttk.Button(marches_control_frame, text="+", command=lambda: self.increment_marches(), width=3).pack(side="left")
        
        # Nb Contremarches
        ttk.Label(input_frame, text="Nb Contremarches (CM) :", font=('Segoe UI', 10, 'bold')).grid(row=row_idx, column=2, sticky="w", padx=5, pady=5)
        cm_control_frame = ttk.Frame(input_frame)
        cm_control_frame.grid(row=row_idx, column=3, sticky="ew", padx=5, pady=5)
        ttk.Button(cm_control_frame, text="-", command=lambda: self.decrement_cm(), width=3).pack(side="left")
        ttk.Entry(cm_control_frame, textvariable=self.nombre_cm_manuel_var, width=5, justify='center', font=('Segoe UI', 10)).pack(side="left", padx=5)
        ttk.Button(cm_control_frame, text="+", command=lambda: self.increment_cm(), width=3).pack(side="left")
        row_idx += 1

        # Giron Souhaité
        ttk.Label(input_frame, text="Giron souhaité :", font=('Segoe UI', 10, 'bold')).grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
        giron_control_frame = ttk.Frame(input_frame)
        giron_control_frame.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(giron_control_frame, text="-", command=lambda: self.decrement_giron(), width=3).pack(side="left")
        ttk.Entry(giron_control_frame, textvariable=self.giron_souhaite_var, width=10, justify='center', font=('Segoe UI', 10)).pack(side="left", padx=5)
        ttk.Button(giron_control_frame, text="+", command=lambda: self.increment_giron(), width=3).pack(side="left")

        # Hauteur Contremarche
        ttk.Label(input_frame, text="Hauteur contremarche :", font=('Segoe UI', 10, 'bold')).grid(row=row_idx, column=2, sticky="w", padx=5, pady=5)
        hcm_control_frame = ttk.Frame(input_frame)
        hcm_control_frame.grid(row=row_idx, column=3, sticky="ew", padx=5, pady=5)
        ttk.Button(hcm_control_frame, text="-", command=lambda: self.decrement_hcm(), width=3).pack(side="left")
        ttk.Entry(hcm_control_frame, textvariable=self.hauteur_cm_souhaitee_var, width=10, justify='center', font=('Segoe UI', 10)).pack(side="left", padx=5)
        ttk.Button(hcm_control_frame, text="+", command=lambda: self.increment_hcm(), width=3).pack(side="left")
        row_idx += 1

        # Bouton "Appliquer Valeurs Idéales"
        apply_ideal_button = ttk.Button(input_frame, text="Appliquer Valeurs Idéales (confort)", command=lambda: self.apply_ideal_values())
        apply_ideal_button.grid(row=row_idx, column=0, columnspan=4, pady=10)
        row_idx += 1

    def _create_interactive_frame(self, parent): # Cette fonction n'est plus nécessaire après la fusion
        pass

    def _create_results_frame(self, parent):
        """Crée le cadre pour l'affichage des résultats du calcul."""
        results_frame = ttk.LabelFrame(parent, text="2. Résultats et Conformité") # Titre changé à 2
        results_frame.pack(fill="x", pady=10)
        results_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(2, weight=1)

        self.conformity_label = ttk.Label(results_frame, textvariable=self.conformity_status_var, style="Conformity.TLabel")
        self.conformity_label.grid(row=0, column=0, columnspan=3, pady=(5, 15), sticky="ew")

        results_labels_and_vars = [
            ("Hauteur réelle par CM :", self.hauteur_reelle_cm_res_var, self.hauteur_cm_message_var),
            ("Giron utilisé :", self.giron_utilise_res_var, self.giron_message_var),  # <-- Utilise la nouvelle variable
            ("Longueur totale escalier :", self.longueur_totale_res_var, self.longueur_disponible_message_var),
            ("Angle de l'escalier :", self.angle_res_var, self.angle_message_var),
            ("Long. limon (approximative) :", self.limon_res_var, None),
            ("Échappée calculée (min.) :", self.echappee_res_var, self.echappee_message_var),
            ("Formule de Blondel (2H+G) :", self.blondel_message_var, None),
            ("Long. min. escalier (par giron) :", self.longueur_min_escalier_var, None),
            ("Écart Hauteur Totale :", self.hauteur_totale_ecart_message_var, None) # Nouveau champ pour l'écart
        ]

        for i, (text, res_var, msg_var) in enumerate(results_labels_and_vars, start=1):
            ttk.Label(results_frame, text=text).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            
            # REF-009: Assurez-vous que l'affichage du giron n'est pas traité comme un message d'indicateur avec des parenthèses
            # La variable giron_souhaite_var est une StringVar, son contenu est mis à jour par update_results_display
            # et ne devrait pas être affectée par le style d'indicateur des messages.
            # L'ajout du guillemet pour l'affichage est fait dans update_results_display.
            if res_var == self.giron_utilise_res_var: # Cas spécifique pour le giron
                label = ttk.Label(results_frame, textvariable=res_var, font=('Segoe UI', 10, 'bold'))
                label.grid(row=i, column=1, sticky="w", padx=5)
                if msg_var: # Le message de conformité pour le giron est traité séparément
                    msg_label = ttk.Label(results_frame, textvariable=msg_var)
                    msg_label.grid(row=i, column=2, sticky="ew", padx=5)
                    # Correction: Passer la bonne StringVar (msg_var) et le bon widget (msg_label)
                    msg_label.bind("<Configure>", lambda e, current_msg_var=msg_var, widget=msg_label: self._update_indicator_style(current_msg_var, widget))
                    self._update_indicator_style(msg_var, msg_label) 

            elif res_var in [self.blondel_message_var, self.longueur_min_escalier_var, self.hauteur_totale_ecart_message_var]: # Cas pour Blondel, Longueur Min escalier et Écart Hauteur Totale
                label = ttk.Label(results_frame, textvariable=res_var, font=('Segoe UI', 10, 'bold'))
                label.grid(row=i, column=1, sticky="w", padx=5, columnspan=2) # Ces labels prennent 2 colonnes
                # Pas de msg_label séparé pour ces variables, le message est dans la variable elle-même
            else: # Cas général pour les autres résultats avec message de conformité
                ttk.Label(results_frame, textvariable=res_var, font=('Segoe UI', 10, 'bold')).grid(row=i, column=1, sticky="w", padx=5)
                if msg_var:
                    msg_label = ttk.Label(results_frame, textvariable=msg_var)
                    msg_label.grid(row=i, column=2, sticky="ew", padx=5)
                    # Correction: Passer la bonne StringVar (msg_var) et le bon widget (msg_label)
                    msg_label.bind("<Configure>", lambda e, current_msg_var=msg_var, widget=msg_label: self._update_indicator_style(current_msg_var, widget))
                    self._update_indicator_style(msg_var, msg_label)


    def _update_indicator_style(self, var, widget):
        """Version améliorée avec plus d'indicateurs.
        'var' est la StringVar du message (ex: self.hauteur_cm_message_var).
        'widget' est le widget Label qui affiche ce message.
        """
        text = var.get() # On obtient le texte actuel de la StringVar
        style_map = {
            "NON CONFORME": ("Indicator.Red.TLabel", "❌ NON CONFORME"),
            "TRÈS RAIDE": ("Indicator.Red.TLabel", "❌ TRÈS RAIDE"),
            "LIMITE": ("Indicator.Yellow.TLabel", "⚠️ LIMITE"),
            "Confort Limité": ("Indicator.Yellow.TLabel", "⚠️ CONFORT LIMITÉ"),
            "OK": ("Indicator.Green.TLabel", "✅ OK"),
            "OPTIMAL": ("Indicator.Green.TLabel", "✅ OPTIMAL"),
            "Nul": ("TLabel", "✅ Nul") # Pour l'écart de hauteur totale, "Nul" est positif.
        }
        
        style = "TLabel" # Style par défaut
        display_text = text # Texte affiché par défaut si aucun match

        for key, (s, display) in style_map.items():
            if key in text: # Vérifie si la clé est présente dans le texte actuel de la StringVar
                style = s
                display_text = display # Utilise le texte d'affichage prédéfini pour l'indicateur
                break
        
        widget.config(style=style, text=display_text) # Applique le style et le texte au widget Label


    def _create_warnings_frame(self, parent):
        """Crée le cadre pour afficher tous les avertissements consolidés."""
        warnings_frame = ttk.LabelFrame(parent, text="4. Résumé des Avertissements")
        warnings_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        self.warnings_label = ttk.Label(warnings_frame, textvariable=self.warnings_var, wraplength=380, justify=tk.LEFT)
        self.warnings_label.pack(padx=10, pady=10, fill="both", expand=True)

    def _create_visual_tab(self, notebook):
        """Crée l'onglet d'aperçu visuel 2D."""
        visual_frame = ttk.Frame(notebook, padding=5)
        self.canvas = tk.Canvas(visual_frame) 
        self.canvas.pack(expand=True, fill="both")
        notebook.add(visual_frame, text="Aperçu 2D")

    def _create_report_tab(self, notebook):
        """Crée l'onglet pour le plan de traçage."""
        report_frame = ttk.Frame(notebook, padding=5)
        self.report_text = tk.Text(report_frame, wrap="word", font=("Courier New", 9)) 
        self.report_text.pack(expand=True, fill="both")
        notebook.add(report_frame, text="Plan de Traçage")
    
    def _create_table_tab(self, notebook):
        """Crée l'onglet pour le tableau des marches."""
        table_frame = ttk.Frame(notebook, padding=5)
        self.table_text = tk.Text(table_frame, wrap="none", font=("Courier New", 9)) 
        self.table_text.pack(expand=True, fill="both")
        notebook.add(table_frame, text="Tableau des Marches")

    def _bind_events(self):
        """Lie les événements des entrées au recalcul."""
        # Toutes les variables déclenchent un recalcul avec le nom de la variable modifiée
        for var_name, var_obj in {
            "hauteur_totale_var": self.hauteur_totale_var,
            "giron_souhaite_var": self.giron_souhaite_var,
            "hauteur_cm_souhaitee_var": self.hauteur_cm_souhaitee_var,
            "epaisseur_plancher_sup_var": self.epaisseur_plancher_sup_var,
            "epaisseur_plancher_inf_var": self.epaisseur_plancher_inf_var,
            "profondeur_tremie_ouverture_var": self.profondeur_tremie_ouverture_var,
            "position_tremie_var": self.position_tremie_var,
            "espace_disponible_var": self.espace_disponible_var,
            "nombre_cm_manuel_var": self.nombre_cm_manuel_var,
            "nombre_marches_manuel_var": self.nombre_marches_manuel_var
        }.items():
            var_obj.trace_add("write", lambda *args, vn=var_name: self.recalculate_and_update_ui(changed_var_name=vn))
        
        self.canvas.bind("<Configure>", self.update_visual_preview)

    def decrement_cm(self):
        """Décrémente le nombre de contremarches et déclenche un recalcul."""
        try:
            current_val_str = self.nombre_cm_manuel_var.get()
            if current_val_str.strip():
                current_val = int(current_val_str)
            else:
                # Utilise la hauteur totale actuelle pour calculer un fallback raisonnable
                h_tot_val = formatting.parser_fraction(self.hauteur_totale_var.get() or "0")
                if h_tot_val > 0:
                    current_val = round(h_tot_val / constants.HAUTEUR_CM_CONFORT_CIBLE)
                else:
                    current_val = 2 # Minimum logique si hauteur totale est 0 ou non valide
                current_val = self.latest_results.get("nombre_contremarches", current_val) if self.latest_results else current_val # Fallback avec latest_results si dispo

            if current_val > 2: # Minimum 2 CM
                self.nombre_cm_manuel_var.set(str(current_val - 1))
            else:
                messagebox.showwarning("Minimum atteint", "Le nombre de contremarches ne peut pas être inférieur à 2.", parent=self)
        except ValueError:
            h_tot_val = formatting.parser_fraction(self.hauteur_totale_var.get() or "0")
            if h_tot_val > 0:
                fallback_val = round(h_tot_val / constants.HAUTEUR_CM_CONFORT_CIBLE)
            else:
                fallback_val = 2
            self.nombre_cm_manuel_var.set(str(max(2, (self.latest_results.get("nombre_contremarches", fallback_val) - 1) if self.latest_results else fallback_val - 1 )))
        except Exception as e:
            if constants.DEBUG_MODE_ACTIVE: print(f"Erreur dans decrement_cm: {e}")
            pass

    def increment_cm(self):
        """Incrémente le nombre de contremarches et déclenche un recalcul."""
        try:
            current_val_str = self.nombre_cm_manuel_var.get()
            if current_val_str.strip():
                current_val = int(current_val_str)
            else:
                h_tot_val = formatting.parser_fraction(self.hauteur_totale_var.get() or "0")
                if h_tot_val > 0:
                    current_val = round(h_tot_val / constants.HAUTEUR_CM_CONFORT_CIBLE)
                else:
                    current_val = 2 # Sera ajusté à 2 min
                current_val = self.latest_results.get("nombre_contremarches", current_val) if self.latest_results else current_val # Fallback avec latest_results si dispo

            if current_val < 50: # Limite arbitraire
                self.nombre_cm_manuel_var.set(str(current_val + 1))
            else:
                messagebox.showwarning("Maximum atteint", "Le nombre de contremarches ne devrait pas dépasser 50.", parent=self)
        except ValueError:
            h_tot_val = formatting.parser_fraction(self.hauteur_totale_var.get() or "0")
            if h_tot_val > 0:
                fallback_val = round(h_tot_val / constants.HAUTEUR_CM_CONFORT_CIBLE)
            else:
                fallback_val = 2
            self.nombre_cm_manuel_var.set(str(min(50, (self.latest_results.get("nombre_contremarches", fallback_val) + 1) if self.latest_results else fallback_val + 1 )))
        except Exception as e:
            if constants.DEBUG_MODE_ACTIVE: print(f"Erreur dans increment_cm: {e}")
            pass

    def decrement_marches(self):
        """Décrémente le nombre de marches manuel et déclenche un recalcul."""
        try:
            current_val_str = self.nombre_marches_manuel_var.get()
            if current_val_str.strip():
                current_val = int(current_val_str)
            else:
                h_tot_val = formatting.parser_fraction(self.hauteur_totale_var.get() or "0")
                if h_tot_val > 0:
                    current_val = (round(h_tot_val / constants.HAUTEUR_CM_CONFORT_CIBLE) - 1)
                else:
                    current_val = 1 # Minimum logique avant d'être ajusté à 1
                current_val = self.latest_results.get("nombre_girons", current_val) if self.latest_results else current_val # Fallback avec latest_results si dispo


            if current_val > 1: # Minimum 1 marche
                self.nombre_marches_manuel_var.set(str(current_val - 1))
            else:
                messagebox.showwarning("Minimum atteint", "Le nombre de marches ne peut pas être inférieur à 1.", parent=self)
        except ValueError:
            h_tot_val = formatting.parser_fraction(self.hauteur_totale_var.get() or "0")
            if h_tot_val > 0:
                fallback_val = (round(h_tot_val / constants.HAUTEUR_CM_CONFORT_CIBLE) - 1)
            else:
                fallback_val = 1
            self.nombre_marches_manuel_var.set(str(max(1, (self.latest_results.get("nombre_girons", fallback_val) - 1) if self.latest_results else fallback_val - 1 )))
        except Exception as e:
            if constants.DEBUG_MODE_ACTIVE: print(f"Erreur dans decrement_marches: {e}")
            pass

    def increment_marches(self):
        """Incrémente le nombre de marches manuel et déclenche un recalcul."""
        try:
            current_val_str = self.nombre_marches_manuel_var.get()
            if current_val_str.strip():
                current_val = int(current_val_str)
            else:
                h_tot_val = formatting.parser_fraction(self.hauteur_totale_var.get() or "0")
                if h_tot_val > 0:
                    current_val = (round(h_tot_val / constants.HAUTEUR_CM_CONFORT_CIBLE) - 1)
                else:
                    current_val = 1 # Sera ajusté
                current_val = self.latest_results.get("nombre_girons", current_val) if self.latest_results else current_val # Fallback avec latest_results si dispo

            if current_val < 49: # Limite arbitraire (50 CM = 49 Marches)
                self.nombre_marches_manuel_var.set(str(current_val + 1))
            else:
                messagebox.showwarning("Maximum atteint", "Le nombre de marches ne devrait pas dépasser 49.", parent=self)
        except ValueError:
            h_tot_val = formatting.parser_fraction(self.hauteur_totale_var.get() or "0")
            if h_tot_val > 0:
                fallback_val = (round(h_tot_val / constants.HAUTEUR_CM_CONFORT_CIBLE) - 1)
            else:
                fallback_val = 1
            self.nombre_marches_manuel_var.set(str(min(49, (self.latest_results.get("nombre_girons", fallback_val) + 1) if self.latest_results else fallback_val + 1 )))
        except Exception as e:
            if constants.DEBUG_MODE_ACTIVE: print(f"Erreur dans increment_marches: {e}")
            pass
    
def decrement_hcm(self):
    """Décrémente la hauteur contremarche souhaitée de 1/8 pouce (ou ≈ 0.3175 cm)."""
    try:
        unite = self.unites_var.get()
        valeur_par_defaut = constants.HAUTEUR_CM_CONFORT_CIBLE
        texte = self.hauteur_cm_souhaitee_var.get()

        if not texte:
            texte = str(valeur_par_defaut * constants.POUCE_EN_CM) if unite == "cm" else str(valeur_par_defaut)

        current_val = formatting.parser_fraction(texte)

        if unite == "cm":
            new_val = max(constants.HAUTEUR_CM_MIN_REGLEMENTAIRE * constants.POUCE_EN_CM, current_val - 0.3175)
            self.hauteur_cm_souhaitee_var.set(f"{new_val:.2f}")
        else:
            new_val = max(constants.HAUTEUR_CM_MIN_REGLEMENTAIRE, current_val - 0.125)
            self.hauteur_cm_souhaitee_var.set(formatting.decimal_to_fraction_str(new_val, self.app_preferences))
    except ValueError:
        fallback = valeur_par_defaut - (0.3175 if unite == "cm" else 0.125)
        if unite == "cm":
            self.hauteur_cm_souhaitee_var.set(f"{fallback * constants.POUCE_EN_CM:.2f}")
        else:
            self.hauteur_cm_souhaitee_var.set(formatting.decimal_to_fraction_str(fallback, self.app_preferences))
    except Exception as e:
        if constants.DEBUG_MODE_ACTIVE:
            print(f"Erreur dans decrement_hcm: {e}")


def increment_hcm(self):
    """Incrémente la hauteur contremarche souhaitée de 1/8 pouce (ou ≈ 0.3175 cm)."""
    try:
        unite = self.unites_var.get()
        valeur_par_defaut = constants.HAUTEUR_CM_CONFORT_CIBLE
        texte = self.hauteur_cm_souhaitee_var.get()

        if not texte:
            texte = str(valeur_par_defaut * constants.POUCE_EN_CM) if unite == "cm" else str(valeur_par_defaut)

        current_val = formatting.parser_fraction(texte)

        if unite == "cm":
            new_val = min(constants.HAUTEUR_CM_MAX_REGLEMENTAIRE * constants.POUCE_EN_CM, current_val + 0.3175)
            self.hauteur_cm_souhaitee_var.set(f"{new_val:.2f}")
        else:
            new_val = min(constants.HAUTEUR_CM_MAX_REGLEMENTAIRE, current_val + 0.125)
            self.hauteur_cm_souhaitee_var.set(formatting.decimal_to_fraction_str(new_val, self.app_preferences))
    except ValueError:
        fallback = valeur_par_defaut + (0.3175 if unite == "cm" else 0.125)
        if unite == "cm":
            self.hauteur_cm_souhaitee_var.set(f"{fallback * constants.POUCE_EN_CM:.2f}")
        else:
            self.hauteur_cm_souhaitee_var.set(formatting.decimal_to_fraction_str(fallback, self.app_preferences))
    except Exception as e:
        if constants.DEBUG_MODE_ACTIVE:
            print(f"Erreur dans increment_hcm: {e}")

    def apply_ideal_values(self):
        """Applique des valeurs idéales prédéfinies pour le confort."""
        # REF-010: Utiliser les valeurs par défaut des préférences pour le giron
        default_tread_width_straight = self.app_preferences.get("default_tread_width_straight", "9 1/4").replace('"', '')
        self.giron_souhaite_var.set(formatting.decimal_to_fraction_str(
            formatting.parser_fraction(default_tread_width_straight), self.app_preferences))
        
        # REF-011: Utiliser la constante HAUTEUR_CM_CONFORT_CIBLE pour la hauteur de contremarche
        self.hauteur_cm_souhaitee_var.set(formatting.decimal_to_fraction_str(
            constants.HAUTEUR_CM_CONFORT_CIBLE, self.app_preferences))

        # Recalculer le nombre de CM en fonction de la hauteur totale et de la HCM de confort
        h_tot_val = formatting.parser_fraction(self.hauteur_totale_var.get() or "0")
        if h_tot_val > 0:
            nombre_cm_ideal = round(h_tot_val / constants.HAUTEUR_CM_CONFORT_CIBLE)
            if nombre_cm_ideal < 2: # S'assurer d'au moins 2 contremarches
                nombre_cm_ideal = 2
            self.nombre_cm_manuel_var.set(str(nombre_cm_ideal))
            # Mettre à jour le nombre de marches en conséquence
            self.nombre_marches_manuel_var.set(str(nombre_cm_ideal - 1))
        
        messagebox.showinfo("Valeurs Idéales", "Les valeurs de giron et de hauteur de contremarche de confort ont été appliquées.", parent=self)


# CONTENU DE LA METHODE : recalculate_and_update_ui

def recalculate_and_update_ui(self, *args, changed_var_name=None):
    """
    Recalcule les dimensions de l'escalier et met à jour l'interface.
    Gère la priorité entre la saisie manuelle de CM et de Marches.
    """
    if self._is_updating_ui:
        return
    self._is_updating_ui = True
    self.clear_messages()

    try:
        # Déterminer l'unité courante pour le calcul
        unite = "Pouces" if self.unites_var.get() == "pouces" else "Centimètres"

        # Appel de la fonction principale
        calc_output = calculations.calculer_escalier_ajuste(
            hauteur_totale_escalier_str=self.hauteur_totale_var.get(),
            giron_souhaite_str=self.giron_souhaite_var.get(),
            hauteur_cm_souhaitee_str=self.hauteur_cm_souhaitee_var.get(),
            nombre_marches_manuel_str=self.nombre_marches_manuel_var.get(),
            nombre_cm_manuel_str=self.nombre_cm_manuel_var.get(),
            epaisseur_plancher_sup_str=self.epaisseur_plancher_sup_var.get(),
            epaisseur_plancher_inf_str=self.epaisseur_plancher_inf_var.get(),
            profondeur_tremie_ouverture_str=self.profondeur_tremie_ouverture_var.get(),
            position_tremie_ouverture_str=self.position_tremie_var.get(),
            espace_disponible_str=self.espace_disponible_var.get(),
            loaded_app_preferences_dict=self.app_preferences,
            changed_var_name=changed_var_name,
            unite=unite
        )

        self.latest_results = calc_output["results"]
        global_warnings = calc_output["warnings"]
        global_is_conform = calc_output["is_conform"]

        # Mise à jour des champs en fonction des résultats calculés
        if self.latest_results.get("hauteur_reelle_contremarche") is not None:
            self.hauteur_cm_souhaitee_var.set(
                formatting.decimal_to_fraction_str(
                    self.latest_results["hauteur_reelle_contremarche"],
                    self.app_preferences
                )
            )
        if self.latest_results.get("giron_utilise") is not None:
            self.giron_souhaite_var.set(
                formatting.decimal_to_fraction_str(
                    self.latest_results["giron_utilise"],
                    self.app_preferences
                )
            )
        if self.latest_results.get("nombre_contremarches") is not None:
            self.nombre_cm_manuel_var.set(str(self.latest_results["nombre_contremarches"]))
        if self.latest_results.get("nombre_girons") is not None:
            self.nombre_marches_manuel_var.set(str(self.latest_results["nombre_girons"]))

        self.update_results_display()
        self.update_warnings_display(global_warnings, global_is_conform)
        self.update_visual_preview()
        self.update_reports()

    except Exception as e:
        self.conformity_status_var.set("ERREUR DE SAISIE")
        self.warnings_var.set(f"Format invalide ou données insuffisantes.\n({e})")
        self.conformity_label.config(foreground=self.themes[self.current_theme]["error"])
        self.clear_results_display()

        if constants.DEBUG_MODE_ACTIVE:
            import traceback
            traceback.print_exc()
    finally:
        self._is_updating_ui = False


    def update_results_display(self):
        """Met à jour les StringVar des résultats avec les valeurs calculées."""
        res = self.latest_results
        prefs = self.app_preferences
        df = lambda val: formatting.decimal_to_fraction_str(val, prefs) if val is not None else ""
        df_mm = lambda val: f"{df(val)} ({round(val * constants.POUCE_EN_MM)} mm)" if val is not None and val != "" else ""
        
        # Correction : n'affiche rien si latest_results est vide ou incomplet
        if not res or not res.get("hauteur_totale_escalier") or not res.get("giron_utilise"):
            self.hauteur_reelle_cm_res_var.set("")
            self.giron_utilise_res_var.set("")  # <-- Effacer la variable résultat du giron
            self.longueur_totale_res_var.set("")
            self.angle_res_var.set("")
            self.limon_res_var.set("")
            self.echappee_res_var.set("")
            self.longueur_min_escalier_var.set("")
            self.blondel_message_var.set("")
            self.hauteur_totale_ecart_message_var.set("") # Effacer l'écart si les résultats sont incomplets
            return
            
        self.hauteur_reelle_cm_res_var.set(df_mm(res.get("hauteur_reelle_contremarche")))
        self.giron_utilise_res_var.set(df_mm(res.get('giron_utilise'))) # Afficher aussi en mm
        self.longueur_totale_res_var.set(df_mm(res.get("longueur_calculee_escalier")))
        self.angle_res_var.set(f"{res.get('angle_escalier', 0):.2f}°" if res.get('angle_escalier') is not None else "")
        self.limon_res_var.set(df_mm(res.get("longueur_limon_approximative")))
        self.echappee_res_var.set(df_mm(res.get("min_echappee_calculee")))
        
        # Le calcul de longueur_min_escalier_var doit être fait à partir de nombre_girons
        nb_girons = res.get("nombre_girons", 0)
        longueur_min_giron_req = nb_girons * constants.GIRON_MIN_REGLEMENTAIRE
        self.longueur_min_escalier_var.set(f"Req: {df_mm(longueur_min_giron_req)}" if nb_girons else "")

        # Mise à jour des messages individuels (pris des résultats de calculs)
        self.hauteur_cm_message_var.set(res.get("hauteur_cm_message", ""))
        self.giron_message_var.set(res.get("giron_message", ""))
        self.echappee_message_var.set(res.get("echappee_message", ""))
        self.blondel_message_var.set(f"{res.get('blondel_message', '')} ({df(res.get('blondel_value'))}\")")
        self.longueur_disponible_message_var.set(res.get("longueur_disponible_message", ""))
        self.angle_message_var.set(res.get("angle_message", ""))
        self.hauteur_totale_ecart_message_var.set(res.get("hauteur_totale_ecart_message", "")) # Mise à jour du nouvel écart


    def update_warnings_display(self, global_warnings, global_is_conform):
        """Met à jour le résumé des avertissements et le statut global de conformité."""
        self.warnings_var.set("\n".join(global_warnings) if global_warnings else "Aucun avertissement.")

        if not global_is_conform:
            self.conformity_status_var.set("✗ NON CONFORME")
            self.conformity_label.config(foreground=self.themes[self.current_theme]["error"])
        elif global_warnings:
            self.conformity_status_var.set("CONFORME AVEC AVERTISSEMENTS")
            self.conformity_label.config(foreground=self.themes[self.current_theme]["warning"])
        else:
            self.conformity_status_var.set("✓ CONFORME")
            self.conformity_label.config(foreground=self.themes[self.current_theme]["success"])


    def clear_messages(self):
        """Nettoyage tous les messages d'avertissement et de conformité."""
        self.conformity_status_var.set("EN ATTENTE")
        self.conformity_label.config(foreground=self.themes[self.current_theme]["fg"])
        self.warnings_var.set("")
        self.hauteur_cm_message_var.set("")
        self.giron_message_var.set("")
        self.echappee_message_var.set("")
        self.blondel_message_var.set("")
        self.longueur_disponible_message_var.set("")
        self.angle_message_var.set("")
        self.hauteur_totale_ecart_message_var.set("") # Nettoyage du nouvel indicateur

    def clear_results_display(self):
        """Efface les résultats affichés dans l’interface."""
        self.hauteur_reelle_cm_res_var.set("")
        self.giron_utilise_res_var.set("")  # <-- Effacer la variable résultat du giron
        self.longueur_totale_res_var.set("")
        self.angle_res_var.set("")
        self.limon_res_var.set("")
        self.echappee_res_var.set("")
        self.longueur_min_escalier_var.set("")
        self.blondel_message_var.set("")
        self.hauteur_cm_message_var.set("")
        self.giron_message_var.set("")
        self.echappee_message_var.set("")
        self.longueur_disponible_message_var.set("")
        self.angle_message_var.set("")
        self.conformity_status_var.set("EN ATTENTE")
        self.warnings_var.set("")
        self.hauteur_totale_ecart_message_var.set("") # Effacer le nouvel indicateur

    def update_visual_preview(self, event=None):
        """
        Met à jour l'aperçu visuel 2D de l'escalier sur le canvas.
        'event' est passé par l'événement <Configure> de Tkinter, mais peut être None si appelé manuellement.
        """
        # Effacer le canvas avant de redessiner
        self.canvas.delete("all")
        
        # Récupérer les dimensions du canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Si des résultats de calcul sont disponibles, dessiner l'escalier
        if self.latest_results:
            # Exemple : dessiner des lignes pour représenter l'escalier
            nombre_girons = self.latest_results.get("nombre_girons", 0)
            if nombre_girons > 0:
                # Calculer des proportions pour dessiner
                giron = self.latest_results.get("giron_utilise", 0)
                hauteur_cm = self.latest_results.get("hauteur_reelle_contremarche", 0)
                
                if giron > 0 and hauteur_cm > 0:
                    # Ajuster l'échelle pour que l'escalier s'adapte au canvas
                    scale_x = canvas_width / (nombre_girons * giron) if giron > 0 else 1
                    scale_y = canvas_height / (nombre_girons * hauteur_cm) if hauteur_cm > 0 else 1
                    scale = min(scale_x, scale_y) * 0.8  # Réduire un peu pour laisser de la marge
                    
                    x = 50  # Point de départ en x (marge)
                    y = canvas_height - 50  # Point de départ en y (bas du canvas)
                    
                    # Dessiner chaque marche
                    for i in range(nombre_girons):
                        # Dessiner le giron (ligne horizontale)
                        self.canvas.create_line(x, y, x + giron * scale, y, 
                                              fill=self.themes[self.current_theme]["canvas_line"], width=2)
                        x += giron * scale
                        # Dessiner la contremarche (ligne verticale)
                        self.canvas.create_line(x, y, x, y - hauteur_cm * scale, 
                                              fill=self.themes[self.current_theme]["canvas_line"], width=2)
                        y -= hauteur_cm * scale
                    
                    # Ajouter un titre
                    self.canvas.create_text(canvas_width/2, 30, 
                                          text=f"Escalier: {nombre_girons} marches", 
                                          fill=self.themes[self.current_theme]["canvas_line"], 
                                          font=("Arial", 12, "bold"))

    def open_preferences_dialog(self):
        """Ouvre la boîte de dialogue des préférences."""
        prefs_dialog = PreferencesDialog(self, self.app_preferences) # Passer self.app_preferences
        self.wait_window(prefs_dialog)
        # Recharger les préférences après la fermeture de la boîte de dialogue si elles ont été modifiées
        self.app_preferences = file_operations.load_application_preferences()
        # Forcer un recalcul pour appliquer les nouvelles préférences immédiatement
        self.recalculate_and_update_ui()
        
    def open_laser_dialog(self):
        """Ouvre la boîte de dialogue d'assistance laser."""
        laser_dialog = LaserDialog(self)
        self.wait_window(laser_dialog)

    def export_pdf_report(self):
        """Exporte le rapport de calcul en PDF."""
        # Ceci est une fonctionnalité future, le PDF nécessite des bibliothèques tierces
        messagebox.showinfo("Export PDF", "La fonction d'exportation PDF est en développement. Veuillez utiliser l'onglet 'Plan de Traçage' et 'Tableau des Marches' pour l'instant.", parent=self)

    def update_reports(self):
        """Met à jour les onglets de rapport (plan de traçage et tableaux)."""
        if self.latest_results:
            plan_tracage_text = reporting.generer_texte_trace(self.latest_results, self.app_preferences)
            self.report_text.delete("1.0", tk.END)
            self.report_text.insert(tk.END, plan_tracage_text)

            tableau_marches_text = reporting.generer_tableau_marches(self.latest_results, self.app_preferences)
            self.table_text.delete("1.0", tk.END)
            self.table_text.insert(tk.END, tableau_marches_text)
            
            tableau_params_text = reporting.generer_tableau_parametres(self.latest_results, self.app_preferences)
            # Ajouter le tableau des paramètres avant le tableau des marches pour une meilleure organisation
            full_table_content = f"{tableau_params_text}\n\n{tableau_marches_text}"
            self.table_text.delete("1.0", tk.END)
            self.table_text.insert(tk.END, full_table_content)

        else:
            self.report_text.delete("1.0", tk.END)
            self.report_text.insert(tk.END, "Aucun résultat de calcul disponible.")
            self.table_text.delete("1.0", tk.END)
            self.table_text.insert(tk.END, "Aucun résultat de calcul disponible.")


# --- DÉBUT DU BLOC DE DÉMARRAGE DE L'APPLICATION ---
# C'est ce bloc qui permet à l'application Tkinter de se lancer
    if __name__ == "__main__":
        import core.constants as constants
        constants.DEBUG_MODE_ACTIVE = True  # Active temporairement le débogage

        app = ModernStairCalculator()
        app.mainloop()  
# --- FIN DU BLOC DE DÉMARRAGE DE L'APPLICATION ---