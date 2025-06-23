# Fichier: CalculateurEscalier/main_app.py

import tkinter as tk
from tkinter import ttk, messagebox
import math
import subprocess
import json
import os

from core import constants, calculations
from utils import formatting, reporting, file_operations
from gui.dialogs import PreferencesDialog, LaserDialog

class ModernStairCalculator(tk.Tk):
    """
    Classe principale de l'interface du calculateur d'escalier.
    Gère la fenêtre principale, les entrées, les résultats et les interactions.
    """
    def __init__(self):
        super().__init__()
        
        # --- Configuration de la fenêtre principale ---
        self.title(f"Calculateur d'Escalier Pro v{constants.VERSION_PROGRAMME}")
        self.geometry("1200x850")
        self.minsize(900, 700)

        # --- Chargement et gestion des préférences ---
        constants.loaded_app_preferences = file_operations.load_application_preferences()
        self.app_preferences = constants.loaded_app_preferences

        self.latest_results = {} # Stocke les derniers résultats de calcul
        self.latest_coupe_results = {} # Stocke les résultats de l'outil de profondeur de coupe

        # REF-007: Ajout de la variable pour stocker les références des labels d'entrée pour le mode débogage
        self.input_labels_map = {} 
        # REF-008: Ajout d'un drapeau pour éviter les boucles de mise à jour entre marches/contremarches
        self._is_updating_ui = False

        # --- Définition des palettes de couleurs pour les thèmes ---
        self.themes = {
            "light": {
                "bg": "#F0F0F0", "fg": "#000000",
                "frame_bg": "#E0E0E0", "entry_bg": "#E0E0E0", "entry_fg": "#000000",
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
        self.switch_theme("light")
        self.update_debug_menu_label() # Appel initial pour le label du menu débogage
        # REF-007: Appel initial pour mettre à jour les labels d'entrée avec/sans codes de référence
        self._update_input_labels_for_debug() 
        self.recalculate_and_update_ui()

        # Définir les valeurs par défaut interactives
        self.hauteur_cm_souhaitee_var.set("7 1/2")
        self.giron_souhaite_var.set("9 1/4")

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

    def _create_menu(self):
        """Crée la barre de menu de l'application."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Préférences...", command=self.open_preferences_dialog)
        file_menu.add_command(label="Ouvrir un projet...", command=lambda: file_operations.charger_projet(self))
        file_menu.add_command(label="Sauvegarder le projet...", command=lambda: file_operations.sauvegarder_projet(self.latest_results, self))
        file_menu.add_separator()
        file_menu.add_command(label="Exporter le rapport (PDF)...", command=self.export_pdf_report)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit)
        
        # Menu Affichage (pour le thème)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Affichage", menu=view_menu)
        view_menu.add_command(label="Thème Clair", command=lambda: self.switch_theme("light"))
        view_menu.add_command(label="Thème Sombre", command=lambda: self.switch_theme("dark"))

        # Menu Outils
        tools_menu = tk.Menu(menubar, tearoff=0)
        self.tools_menu = tools_menu 
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="Assistance Laser (4 points)...", command=self.open_laser_dialog)
        tools_menu.add_command(label="Calculateur de Profondeur de Coupe...", command=self.open_profondeur_coupe_tool)
        tools_menu.add_separator()
        
        # Menu de débogage
        self.debug_menu_button = tk.Menu(tools_menu, tearoff=0)
        self.debug_menu_button.add_command(label="Activer / Désactiver (Ctrl+D)", command=self.toggle_debug_mode)
        tools_menu.add_cascade(label="Débogage", menu=self.debug_menu_button)
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
                    index = i
                    break

            if index != -1:
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
            print("Mode débogage ACTIVÉ. Les tracebacks complets des erreurs seront affichés.")
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
        self._create_interactive_frame(left_frame)
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
        """Crée le cadre pour les entrées utilisateur."""
        input_frame = ttk.LabelFrame(parent, text="1. Entrées de Base")
        input_frame.pack(fill="x", pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        entries_with_shortcuts = [
            ("Hauteur totale à monter :", "HT", self.hauteur_totale_var),
            ("Épaisseur plancher sup. :", "EPS", self.epaisseur_plancher_sup_var),
            ("Épaisseur plancher inf. :", "EPI", self.epaisseur_plancher_inf_var),
            ("Profondeur ouverture trémie :", "POT", self.profondeur_tremie_ouverture_var),
            ("Position départ trémie:", "PDT", self.position_tremie_var),
            ("Espace disponible (longueur) :", "ED", self.espace_disponible_var),
        ]

        for i, (text, shortcut, var) in enumerate(entries_with_shortcuts):
            # REF-007: Le texte du label est le texte original, le raccourci sera ajouté par _update_input_labels_for_debug
            label = ttk.Label(input_frame, text=text) 
            label.grid(row=i, column=0, sticky="w", padx=5, pady=8)
            
            # REF-007: Stocke la référence du label et son texte original pour mise à jour future
            self.input_labels_map[shortcut] = (label, text) 

            entry_frame = ttk.Frame(input_frame)
            entry_frame.grid(row=i, column=1, sticky="ew", padx=5, pady=8)
            
            entry = ttk.Entry(entry_frame, textvariable=var, width=15, font=('Segoe UI', 10))
            entry.pack(side="left", fill="x", expand=True)
            
            if shortcut == "HT":
                ttk.Button(entry_frame, text="Laser", command=self.open_laser_dialog, width=6).pack(side="left", padx=(5,0))

    def _create_interactive_frame(self, parent):
        """Crée le cadre pour l'ajustement interactif avec organisation personnalisée."""
        interactive_frame = ttk.LabelFrame(parent, text="2. Ajustement Interactif")
        interactive_frame.pack(fill="x", pady=10)
        for i in range(2):
            interactive_frame.columnconfigure(i, weight=1)
        for i in range(2):
            interactive_frame.rowconfigure(i, weight=1)

        # Gauche Haut : Nb Marches
        marches_frame = ttk.Frame(interactive_frame)
        marches_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        marches_frame.columnconfigure(1, weight=1)
        ttk.Label(marches_frame, text="Nb Marches (Manuel):", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky="w")
        marches_control_frame = ttk.Frame(marches_frame)
        marches_control_frame.grid(row=0, column=1, sticky="e")
        ttk.Button(marches_control_frame, text="-", command=self.decrement_marches, width=3).grid(row=0, column=0)
        ttk.Entry(marches_control_frame, textvariable=self.nombre_marches_manuel_var, width=5, justify='center').grid(row=0, column=1, padx=5)
        ttk.Button(marches_control_frame, text="+", command=self.increment_marches, width=3).grid(row=0, column=2)

        # Gauche Bas : Giron
        giron_frame = ttk.Frame(interactive_frame)
        giron_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        giron_frame.columnconfigure(1, weight=1)
        ttk.Label(giron_frame, text="Giron souhaité :", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky="w")
        giron_control_frame = ttk.Frame(giron_frame)
        giron_control_frame.grid(row=0, column=1, sticky="e")
        ttk.Button(giron_control_frame, text="-", command=self.decrement_giron, width=3).grid(row=0, column=0)
        ttk.Entry(giron_control_frame, textvariable=self.giron_souhaite_var, width=10, justify='center').grid(row=0, column=1, padx=5)
        ttk.Button(giron_control_frame, text="+", command=self.increment_giron, width=3).grid(row=0, column=2)

        # Droite Haut : Nb Contremarches
        cm_frame = ttk.Frame(interactive_frame)
        cm_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        cm_frame.columnconfigure(1, weight=1)
        ttk.Label(cm_frame, text="Nb Contremarches (CM):", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky="w")
        cm_control_frame = ttk.Frame(cm_frame)
        cm_control_frame.grid(row=0, column=1, sticky="e")
        ttk.Button(cm_control_frame, text="-", command=self.decrement_cm, width=3).grid(row=0, column=0)
        ttk.Entry(cm_control_frame, textvariable=self.nombre_cm_manuel_var, width=5, justify='center').grid(row=0, column=1, padx=5)
        ttk.Button(cm_control_frame, text="+", command=self.increment_cm, width=3).grid(row=0, column=2)

        # Droite Bas : Hauteur contremarche
        hcm_frame = ttk.Frame(interactive_frame)
        hcm_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        hcm_frame.columnconfigure(1, weight=1)
        ttk.Label(hcm_frame, text="Hauteur contremarche :", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky="w")
        hcm_control_frame = ttk.Frame(hcm_frame)
        hcm_control_frame.grid(row=0, column=1, sticky="e")
        ttk.Button(hcm_control_frame, text="-", command=self.decrement_hcm, width=3).grid(row=0, column=0)
        ttk.Entry(hcm_control_frame, textvariable=self.hauteur_cm_souhaitee_var, width=10, justify='center').grid(row=0, column=1, padx=5)
        ttk.Button(hcm_control_frame, text="+", command=self.increment_hcm, width=3).grid(row=0, column=2)

    def _create_results_frame(self, parent):
        """Crée le cadre pour l'affichage des résultats du calcul."""
        results_frame = ttk.LabelFrame(parent, text="3. Résultats et Conformité")
        results_frame.pack(fill="x", pady=10)
        results_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(2, weight=1)

        self.conformity_label = ttk.Label(results_frame, textvariable=self.conformity_status_var, style="Conformity.TLabel")
        self.conformity_label.grid(row=0, column=0, columnspan=3, pady=(5, 15), sticky="ew")

        results_labels_and_vars = [
            ("Hauteur réelle par CM :", self.hauteur_reelle_cm_res_var, self.hauteur_cm_message_var),
            ("Giron utilisé :", self.giron_souhaite_var, self.giron_message_var), # <-- res_var here is giron_souhaite_var
            ("Longueur totale escalier :", self.longueur_totale_res_var, self.longueur_disponible_message_var),
            ("Angle de l'escalier :", self.angle_res_var, self.angle_message_var),
            ("Long. limon (approximative) :", self.limon_res_var, None),
            ("Échappée calculée (min.) :", self.echappee_res_var, self.echappee_message_var),
            ("Formule de Blondel (2H+G) :", self.blondel_message_var, None),
            ("Long. min. escalier (par giron) :", self.longueur_min_escalier_var, None)
        ]

        for i, (text, res_var, msg_var) in enumerate(results_labels_and_vars, start=1):
            ttk.Label(results_frame, text=text).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            
            # REF-009: Assurez-vous que l'affichage du giron n'est pas traité comme un message d'indicateur avec des parenthèses
            # La variable giron_souhaite_var est une StringVar, son contenu est mis à jour par update_results_display
            # et ne devrait pas être affectée par le style d'indicateur des messages.
            # L'ajout du guillemet pour l'affichage est fait dans update_results_display.
            if res_var == self.giron_souhaite_var: # Cas spécifique pour le giron
                label = ttk.Label(results_frame, textvariable=res_var, font=('Segoe UI', 10, 'bold'))
                label.grid(row=i, column=1, sticky="w", padx=5)
                if msg_var: # Le message de conformité pour le giron est traité séparément
                    msg_label = ttk.Label(results_frame, textvariable=msg_var)
                    msg_label.grid(row=i, column=2, sticky="ew", padx=5)
                    msg_label.bind("<Configure>", lambda e, var=msg_var, widget=msg_label: self._update_indicator_style(var, widget))
                    self._update_indicator_style(msg_var, msg_label)
            elif res_var in [self.blondel_message_var, self.longueur_min_escalier_var]: # Cas pour Blondel et Longueur Min escalier
                label = ttk.Label(results_frame, textvariable=res_var, font=('Segoe UI', 10, 'bold'))
                label.grid(row=i, column=1, sticky="w", padx=5, columnspan=2) # Ces labels prennent 2 colonnes
                if msg_var: 
                    msg_label = ttk.Label(results_frame, textvariable=msg_var)
                    pass # Pas de msg_label séparé pour Blondel ou Longueur Min, le message est dans la variable elle-même
            else: # Cas général pour les autres résultats avec message de conformité
                ttk.Label(results_frame, textvariable=res_var, font=('Segoe UI', 10, 'bold')).grid(row=i, column=1, sticky="w", padx=5)
                if msg_var:
                    msg_label = ttk.Label(results_frame, textvariable=msg_var)
                    msg_label.grid(row=i, column=2, sticky="ew", padx=5)
                    msg_label.bind("<Configure>", lambda e, var=msg_var, widget=msg_label: self._update_indicator_style(var, widget))
                    self._update_indicator_style(msg_var, msg_label)


    def _update_indicator_style(self, var, widget):
        """Met à jour le style (couleur) d'un label d'indicateur en fonction de son contenu."""
        text = var.get()
        style_map = {
            "NON CONFORME": "Indicator.Red.TLabel", "TRÈS raide": "Indicator.Red.TLabel",
            "Confort Limité": "Indicator.Yellow.TLabel", "Pente raide": "Indicator.Yellow.TLabel",
            "Pente douce": "Indicator.Green.TLabel", "Pente standard": "Indicator.Green.TLabel",
            "OK": "Indicator.Green.TLabel"
        }
        style = "TLabel"
        display_text = ""
        for key, s in style_map.items():
            if key in text:
                style = s
                display_text = key
                break
        if "OK" in text: 
            style = "Indicator.Green.TLabel"
            display_text = "OK"

        widget.config(style=style, text=display_text)

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
        # L'ancienne trace de nombre_cm_manuel_var est retirée ici car elle est déplacée ci-dessous
        for var in [self.hauteur_totale_var, self.giron_souhaite_var, 
                    self.hauteur_cm_souhaitee_var, 
                    self.epaisseur_plancher_sup_var, self.epaisseur_plancher_inf_var,
                    self.profondeur_tremie_ouverture_var, self.position_tremie_var, 
                    self.espace_disponible_var]: 
            var.trace_add("write", lambda *args, var=var: self.recalculate_and_update_ui(changed_var=var))
        
        # REF-008: Traces spécifiques pour les variables de contremarches et de marches manuelles
        # Le lambda est important ici pour passer l'information sur la variable qui a déclenché l'événement
        self.nombre_cm_manuel_var.trace_add("write", lambda *args: self.recalculate_and_update_ui(changed_var=self.nombre_cm_manuel_var))
        self.nombre_marches_manuel_var.trace_add("write", lambda *args: self.recalculate_and_update_ui(changed_var=self.nombre_marches_manuel_var))

        self.canvas.bind("<Configure>", self.update_visual_preview)

    def decrement_cm(self):
        """Décrémente le nombre de contremarches et déclenche un recalcul."""
        try:
            current_val = int(self.nombre_cm_manuel_var.get())
            if current_val > 2: # Minimum 2 CM
                self.nombre_cm_manuel_var.set(str(current_val - 1))
        except ValueError:
            # Si l'entrée est vide ou non numérique, on tente de décrémenter à partir de la valeur ajustée
            adjusted_val = self.nombre_cm_ajuste_var.get()
            if adjusted_val > 2:
                self.nombre_cm_manuel_var.set(str(adjusted_val - 1))

    def increment_cm(self):
        """Incrémente le nombre de contremarches et déclenche un recalcul."""
        try:
            current_val = int(self.nombre_cm_manuel_var.get())
            if current_val < 50: # Limite arbitraire
                self.nombre_cm_manuel_var.set(str(current_val + 1))
        except ValueError:
            # Si l'entrée est vide ou non numérique, on tente d'incrémenter à partir de la valeur ajustée
            adjusted_val = self.nombre_cm_ajuste_var.get()
            if adjusted_val < 50:
                self.nombre_cm_manuel_var.set(str(adjusted_val + 1))

    # REF-008: Nouvelle fonction pour décrémenter le nombre de marches
    def decrement_marches(self):
        """Décrémente le nombre de marches manuel et déclenche un recalcul."""
        try:
            current_val = int(self.nombre_marches_manuel_var.get())
            if current_val > 1: # Minimum 1 marche (pour 2 CM)
                self.nombre_marches_manuel_var.set(str(current_val - 1))
        except ValueError:
            # Si l'entrée est vide ou non numérique, on tente de décrémenter à partir de la valeur calculée
            if self.latest_results and self.latest_results.get("nombre_girons", 0) > 1:
                self.nombre_marches_manuel_var.set(str(self.latest_results.get("nombre_girons") - 1))

    # REF-008: Nouvelle fonction pour incrémenter le nombre de marches
    def increment_marches(self):
        """Incrémente le nombre de marches manuel et déclenche un recalcul."""
        try:
            current_val = int(self.nombre_marches_manuel_var.get())
            if current_val < 49: # Limite arbitraire, 50 CM = 49 Marches
                self.nombre_marches_manuel_var.set(str(current_val + 1))
        except ValueError:
            # Si l'entrée est vide ou non numérique, on tente d'incrémenter à partir de la valeur calculée
            if self.latest_results and self.latest_results.get("nombre_girons", 0) < 49:
                self.nombre_marches_manuel_var.set(str(self.latest_results.get("nombre_girons") + 1))
    
    def decrement_hcm(self):
        """Décrémente la hauteur contremarche souhaitée de 1/8 pouce."""
        try:
            current_val = formatting.parser_fraction(self.hauteur_cm_souhaitee_var.get() or "7 1/2")
            new_val = max(5.0, current_val - 0.125)  # Minimum 5 pouces
            self.hauteur_cm_souhaitee_var.set(formatting.decimal_to_fraction_str(new_val, self.app_preferences))
        except ValueError:
            self.hauteur_cm_souhaitee_var.set("7 1/2")

    def increment_hcm(self):
        """Incrémente la hauteur contremarche souhaitée de 1/8 pouce."""
        try:
            current_val = formatting.parser_fraction(self.hauteur_cm_souhaitee_var.get() or "7 1/2")
            new_val = min(8.5, current_val + 0.125)  # Maximum 8 1/2 pouces
            self.hauteur_cm_souhaitee_var.set(formatting.decimal_to_fraction_str(new_val, self.app_preferences))
        except ValueError:
            self.hauteur_cm_souhaitee_var.set("7 1/2")

    def decrement_giron(self):
        """Décrémente le giron souhaité de 1/8 pouce."""
        try:
            current_val = formatting.parser_fraction(self.giron_souhaite_var.get() or "9 1/4")
            new_val = max(8.0, current_val - 0.125)  # Minimum 8 pouces
            self.giron_souhaite_var.set(formatting.decimal_to_fraction_str(new_val, self.app_preferences))
        except ValueError:
            self.giron_souhaite_var.set("9 1/4")

    def increment_giron(self):
        """Incrémente le giron souhaité de 1/8 pouce."""
        try:
            current_val = formatting.parser_fraction(self.giron_souhaite_var.get() or "9 1/4")
            new_val = min(12.0, current_val + 0.125)  # Maximum 12 pouces
            self.giron_souhaite_var.set(formatting.decimal_to_fraction_str(new_val, self.app_preferences))
        except ValueError:
            self.giron_souhaite_var.set("9 1/4")
    
    def recalculate_and_update_ui(self, *args, changed_var=None):
        """
        Recalcule les dimensions de l'escalier et met à jour l'interface.
        Gère la priorité entre la saisie manuelle de CM et de Marches.
        """
        # REF-008: Empêche la réentrée si déjà en cours de mise à jour (évite les boucles infinies)
        if self._is_updating_ui: 
            return

        self._is_updating_ui = True # REF-008: Active le drapeau de mise à jour
        self.clear_messages()
        if constants.DEBUG_MODE_ACTIVE: 
            # REF-008: Meilleure identification de la variable déclencheur pour le débogage
            trigger_name = "Init"
            if changed_var == self.nombre_cm_manuel_var:
                trigger_name = "Manuel CM"
            elif changed_var == self.nombre_marches_manuel_var:
                trigger_name = "Manuel Marches"
            elif changed_var:
                for attr_name in dir(self): # Recherche le nom de la variable déclencheur
                    if getattr(self, attr_name) is changed_var:
                        trigger_name = attr_name
                        break
            print(f"DEBUG: Recalcul déclenché par: {trigger_name}")

        try:
            # --- Détection du paramètre modifié pour logique bidirectionnelle ---
            # On détermine la priorité d'ajustement pour chaque couple
            # 1. Giron <-> Nb marches
            # 2. HCM <-> Nb contremarches
            #
            # On utilise le paramètre changed_var pour savoir ce que l'utilisateur a modifié
            # et on ajuste l'autre champ en conséquence

            # --- Récupération des valeurs brutes ---
            h_tot = formatting.parser_fraction(self.hauteur_totale_var.get().strip() or "0")
            giron_str = self.giron_souhaite_var.get().strip()
            h_cm_souhaitee_str = self.hauteur_cm_souhaitee_var.get().strip()
            nb_marches_manuel_str = self.nombre_marches_manuel_var.get().strip()
            nb_cm_manuel_str = self.nombre_cm_manuel_var.get().strip()

            # --- Logique bidirectionnelle pour giron <-> nb marches ---
            espace_dispo_str = self.espace_disponible_var.get().strip()
            if changed_var == self.giron_souhaite_var and h_tot > 0 and giron_str:
                # Si l'espace disponible est renseigné, on ajuste le nombre de marches
                if espace_dispo_str:
                    giron = formatting.parser_fraction(giron_str)
                    nb_marches = max(1, round((h_tot / giron)))
                    self.nombre_marches_manuel_var.set(str(nb_marches))
                    nb_cm_final = nb_marches + 1
                    nb_marches_final_calculated = nb_marches
                else:
                    # Si pas d'espace dispo, on ne touche pas au nombre de marches, on laisse la valeur actuelle
                    try:
                        nb_marches = int(nb_marches_manuel_str)
                    except Exception:
                        nb_marches = max(1, round(h_tot / formatting.parser_fraction(giron_str)))
                    nb_cm_final = nb_marches + 1
                    nb_marches_final_calculated = nb_marches
            elif changed_var == self.nombre_marches_manuel_var and h_tot > 0 and nb_marches_manuel_str.isdigit():
                # L'utilisateur a changé le nombre de marches, on ajuste le giron
                nb_marches = int(nb_marches_manuel_str)
                if nb_marches > 0:
                    giron = h_tot / nb_marches
                    self.giron_souhaite_var.set(formatting.decimal_to_fraction_str(giron, self.app_preferences))
                    nb_cm_final = nb_marches + 1
                    nb_marches_final_calculated = nb_marches
                else:
                    nb_cm_final = 2
                    nb_marches_final_calculated = 1
            # --- Logique bidirectionnelle pour HCM <-> nb contremarches ---
            elif changed_var == self.hauteur_cm_souhaitee_var and h_tot > 0 and h_cm_souhaitee_str:
                hcm = formatting.parser_fraction(h_cm_souhaitee_str)
                nb_cm = max(2, round(h_tot / hcm))
                self.nombre_cm_manuel_var.set(str(nb_cm))
                nb_cm_final = nb_cm
                nb_marches_final_calculated = max(1, nb_cm - 1)
            elif changed_var == self.nombre_cm_manuel_var and h_tot > 0 and nb_cm_manuel_str.isdigit():
                nb_cm = int(nb_cm_manuel_str)
                if nb_cm > 1:
                    hcm = h_tot / nb_cm
                    self.hauteur_cm_souhaitee_var.set(formatting.decimal_to_fraction_str(hcm, self.app_preferences))
                    nb_cm_final = nb_cm
                    nb_marches_final_calculated = max(1, nb_cm - 1)
                else:
                    nb_cm_final = 2
                    nb_marches_final_calculated = 1
        except Exception as e:
            nb_cm_final = 0
            nb_marches_final_calculated = 0
            if h_tot > 0 and h_cm_souhaitee_str:
                h_cm_souhaitee = formatting.parser_fraction(h_cm_souhaitee_str)
                if h_cm_souhaitee > 0:
                    nb_cm_final = round(h_tot / h_cm_souhaitee)
                    nb_marches_final_calculated = max(0, nb_cm_final - 1)
            elif h_tot > 0:
                nb_cm_final = math.ceil(h_tot / constants.HAUTEUR_CM_CONFORT_CIBLE)
                nb_marches_final_calculated = max(0, nb_cm_final - 1)
            if h_tot > 0:
                nb_cm_final = max(2, nb_cm_final)
                nb_marches_final_calculated = max(1, nb_marches_final_calculated)
            else:
                nb_cm_final = 0
                nb_marches_final_calculated = 0
            self.nombre_cm_manuel_var.set(str(nb_cm_final))
            self.nombre_marches_manuel_var.set(str(nb_marches_final_calculated))

        try:
            # --- Calculs principaux ---
            # Correction : la hauteur réelle par CM doit toujours être égale à la valeur saisie dans "Hauteur contremarche souhaitée"
            if changed_var == self.hauteur_cm_souhaitee_var and h_tot > 0 and h_cm_souhaitee_str:
                # L'utilisateur a modifié la hauteur contremarche souhaitée :
                h_reel_final = formatting.parser_fraction(h_cm_souhaitee_str)
            else:
                # Cas général : on recalcule normalement
                h_reel_final = h_tot / nb_cm_final if nb_cm_final else 0

            self.nombre_cm_ajuste_var.set(nb_cm_final) # Variable interne pour les calculs
            self.nombre_marches_final_display_var.set(str(nb_marches_final_calculated))
            
            giron = None
            if giron_str:
                giron = formatting.parser_fraction(giron_str)
            else:
                blondel_cible_moyenne = (constants.BLONDEL_MIN_POUCES + constants.BLONDEL_MAX_POUCES) / 2
                giron_deduit = blondel_cible_moyenne - (2 * h_reel_final)
                giron = max(constants.GIRON_MIN_REGLEMENTAIRE, min(giron_deduit, constants.GIRON_MAX_REGLEMENTAIRE))
                self.giron_souhaite_var.set(formatting.decimal_to_fraction_str(giron, self.app_preferences)) 
            
            if giron is None: raise ValueError("Giron indéterminé.")

            params = {
                "hauteur_totale_escalier": h_tot,
                "giron_souhaite": giron,
                "nombre_contremarches_ajuste": nb_cm_final,
                "epaisseur_marche": formatting.parser_fraction(self.app_preferences.get("default_tread_thickness", "1 1/16")),
                "epaisseur_plancher_sup": formatting.parser_fraction(self.epaisseur_plancher_sup_var.get() or "0"),
                "epaisseur_plancher_inf": formatting.parser_fraction(self.epaisseur_plancher_inf_var.get() or "0"),
                "profondeur_tremie_ouverture_entree": self.profondeur_tremie_ouverture_var.get(),
                "position_tremie_ouverture_entree": self.position_tremie_var.get(),
                "espace_disponible_entree": self.espace_disponible_var.get(),
            }
            
            self.latest_results = calculations.calculer_dimensions_escalier(loaded_app_preferences_dict=self.app_preferences, **params)
            
            self.latest_results["nombre_contremarches"] = nb_cm_final
            self.latest_results["hauteur_reelle_contremarche"] = h_reel_final
            self.latest_results["giron_utilise"] = giron 
            self.latest_results["nombre_girons"] = nb_marches_final_calculated 
            longueur_totale = self.latest_results["nombre_girons"] * giron
            self.latest_results["longueur_calculee_escalier"] = longueur_totale
            if longueur_totale > 0 and h_tot > 0:
                self.latest_results["angle_escalier"] = math.degrees(math.atan(h_tot / longueur_totale))
            else:
                self.latest_results["angle_escalier"] = 90.0 if h_tot > 0 else 0.0

            if longueur_totale > 0 and h_tot > 0:
                self.latest_results["longueur_limon_approximative"] = math.sqrt(h_tot**2 + longueur_totale**2)
            else:
                self.latest_results["longueur_limon_approximative"] = h_tot
            
            profondeur_tremie = formatting.parser_fraction(self.profondeur_tremie_ouverture_var.get() or "0")
            position_tremie = formatting.parser_fraction(self.position_tremie_var.get() or "0")
            
            if profondeur_tremie > 0:
                hauteur_sous_plafond = h_tot - params["epaisseur_plancher_sup"] 
                min_echappee = float('inf')
                for i in range(1, nb_cm_final + 1): 
                    x_point_on_stair = (i-1) * giron 
                    y_point_on_stair = (i-1) * h_reel_final 
                    
                    if x_point_on_stair >= position_tremie and x_point_on_stair < (position_tremie + profondeur_tremie):
                        echappee_actuelle = hauteur_sous_plafond - y_point_on_stair
                        min_echappee = min(min_echappee, echappee_actuelle)
                
                if min_echappee != float('inf'):
                    self.latest_results["min_echappee_calculee"] = min_echappee
                else:
                    self.latest_results["min_echappee_calculee"] = None
            else:
                self.latest_results["min_echappee_calculee"] = None

            self.update_results_display()
            self.update_warnings_display()
            self.update_visual_preview()
            self.update_reports()

        except (ValueError, ZeroDivisionError, tk.TclError) as e:
            self.conformity_status_var.set("ERREUR DE SAISIE")
            self.warnings_var.set(f"Format invalide ou données insuffisantes.\n({e})")
            self.conformity_label.config(foreground=self.themes[self.current_theme]["error"])
            self.clear_results_display()
            if constants.DEBUG_MODE_ACTIVE: raise
        except Exception as e:
            self.conformity_status_var.set("ERREUR INATTENDUE")
            self.warnings_var.set(f"Une erreur inattendue est survenue : {e}.")
            self.conformity_label.config(foreground=self.themes[self.current_theme]["error"])
            self.clear_results_display()
            if constants.DEBUG_MODE_ACTIVE: raise
        finally:
            self._is_updating_ui = False # REF-008: Désactive le drapeau une fois la mise à jour terminée

    def clear_messages(self):
        """Nettoie tous les messages d'avertissement et de conformité."""
        self.conformity_status_var.set("EN ATTENTE")
        self.conformity_label.config(foreground=self.themes[self.current_theme]["fg"])
        self.warnings_var.set("")
        self.hauteur_cm_message_var.set("")
        self.giron_message_var.set("")
        self.echappee_message_var.set("")
        self.blondel_message_var.set("")
        self.longueur_disponible_message_var.set("")
        self.angle_message_var.set("")

    def clear_results_display(self):
        """Efface les valeurs affichées dans les champs de résultats."""
        self.hauteur_reelle_cm_res_var.set("")
        self.longueur_totale_res_var.set("")
        self.angle_res_var.set("")
        self.limon_res_var.set(""); 
        self.echappee_res_var.set("")
        self.longueur_min_escalier_var.set("")
        if hasattr(self, 'report_text'): self.report_text.delete("1.0", tk.END)
        if hasattr(self, 'table_text'): self.table_text.delete("1.0", tk.END)

    def update_results_display(self):
        """Met à jour les StringVar des résultats avec les valeurs calculées."""
        res = self.latest_results
        prefs = self.app_preferences
        df = lambda val: formatting.decimal_to_fraction_str(val, prefs) if val is not None else "N/A"
        df_mm = lambda val: f"{df(val)} ({round(val * constants.POUCE_EN_MM)} mm)" if val is not None else "N/A"

        self.hauteur_reelle_cm_res_var.set(df_mm(res.get("hauteur_reelle_contremarche")))
        # REF-009: Ajout explicite du guillemet pour l'affichage du giron.
        self.giron_souhaite_var.set(df(res.get('giron_utilise'))) 
        self.longueur_totale_res_var.set(df_mm(res.get("longueur_calculee_escalier")))
        self.angle_res_var.set(f"{res.get('angle_escalier', 0):.2f}°")
        self.limon_res_var.set(df_mm(res.get("longueur_limon_approximative")))

        # REF-009: Ajout de l'échappée et de la longueur minimale de l'escal
        self.echappee_res_var.set(df_mm(res.get("min_echappee_calculee")))
        
        nb_girons = res.get("nombre_girons", 0)
        longueur_min_giron_req = nb_girons * constants.GIRON_MIN_REGLEMENTAIRE
        self.longueur_min_escalier_var.set(f"Req: {df_mm(longueur_min_giron_req)}")

    def update_warnings_display(self):
        """Met à jour les messages d'avertissement et le statut global."""
        if not self.latest_results:
            return
        res = self.latest_results
        warnings_list = []
        is_conform = True

        h_reel = res.get("hauteur_reelle_contremarche", 0)
        giron = res.get("giron_utilise", 0)
        echappee = res.get("min_echappee_calculee")
        angle = res.get("angle_escalier", 0)
        longueur_calculee = res.get("longueur_calculee_escalier", 0)
        espace_dispo_str = res.get("espace_disponible_entree", "")
        
        if not (constants.HAUTEUR_CM_MIN_REGLEMENTAIRE <= h_reel <= constants.HAUTEUR_CM_MAX_REGLEMENTAIRE):
            warnings_list.append(f"• H. CM non conforme.")
            self.hauteur_cm_message_var.set("NON CONFORME")
            is_conform = False
        else: self.hauteur_cm_message_var.set("OK")

        if not (constants.GIRON_MIN_REGLEMENTAIRE <= giron <= constants.GIRON_MAX_REGLEMENTAIRE):
            warnings_list.append(f"• Giron non conforme.")
            self.giron_message_var.set("NON CONFORME")
            is_conform = False
        elif giron < constants.GIRON_CONFORT_MIN_RES_STANDARD:
            warnings_list.append(f"• Giron conforme mais étroit.")
            self.giron_message_var.set("Confort Limité")
        else: self.giron_message_var.set("OK")

        blondel_val = (2 * h_reel) + giron
        if not (constants.BLONDEL_MIN_POUCES <= blondel_val <= constants.BLONDEL_MAX_POUCES):
            warnings_list.append(f"• Formule de Blondel (2H+G) non respectée.")
            self.blondel_message_var.set(f"NON CONFORME ({formatting.decimal_to_fraction_str(blondel_val, self.app_preferences)}\")") # Ajout valeur pour Blondel
            is_conform = False
        else: self.blondel_message_var.set(f"OK ({formatting.decimal_to_fraction_str(blondel_val, self.app_preferences)}\")")

        if echappee is not None:
            if echappee < constants.HAUTEUR_LIBRE_MIN_REGLEMENTAIRE:
                warnings_list.append(f"• Échappée insuffisante.")
                self.echappee_message_var.set("NON CONFORME")
                is_conform = False
            else: self.echappee_message_var.set("OK")
        else: self.echappee_message_var.set("N/A")

        if espace_dispo_str:
            try: 
                espace_dispo = formatting.parser_fraction(espace_dispo_str)
                if longueur_calculee > espace_dispo:
                    warnings_list.append("• L'escalier dépasse l'espace disponible.")
                    self.longueur_disponible_message_var.set("NON CONFORME")
                    is_conform = False
                else: self.longueur_disponible_message_var.set("OK")
            except ValueError:
                warnings_list.append("• Espace disponible : format invalide.")
                self.longueur_disponible_message_var.set("ERREUR")
                is_conform = False
        else: self.longueur_disponible_message_var.set("N/A")

        if angle > constants.ANGLE_CONFORT_RAIDE_MAIS_CONFORME_MAX:
             warnings_list.append("• Angle très raide, confort potentiellement limité.") 
             self.angle_message_var.set("TRÈS raide")
        elif angle > constants.ANGLE_STANDARD_MAX: # Changed from ANGLE_CONFORT_STANDARD_MAX to ANGLE_STANDARD_MAX if it exists
            warnings_list.append("• Angle raide, confort limité.")
            self.angle_message_var.set("Pente raide")
        else: self.angle_message_var.set("Pente standard")

        if not is_conform:
            self.conformity_status_var.set("✗ NON CONFORME")
            self.conformity_label.config(foreground=self.themes[self.current_theme]["error"])
            self.warnings_var.set("\n".join(warnings_list))
        elif warnings_list:
            self.conformity_status_var.set("CONFORME AVEC AVERTISSEMENTS")
            self.conformity_label.config(foreground=self.themes[self.current_theme]["warning"])
            self.warnings_var.set("\n".join(warnings_list))
        else:
            self.conformity_status_var.set("✓ CONFORME")
            self.conformity_label.config(foreground=self.themes[self.current_theme]["success"])
            self.warnings_var.set("Aucun avertissement.")

    def update_visual_preview(self, event=None):
        """Dessine un aperçu 2D de l'escalier sur le canvas."""
        self.canvas.delete("all")
        if not self.latest_results or self.latest_results.get("nombre_contremarches", 0) == 0:
            return

        colors = self.themes[self.current_theme]
        self.canvas.config(bg=colors["canvas_bg"])
        canvas_w, canvas_h, padding = self.canvas.winfo_width(), self.canvas.winfo_height(), 40

        h_tot = self.latest_results.get("hauteur_totale_escalier", 0)
        l_tot = self.latest_results.get("longueur_calculee_escalier", 0)
        if h_tot == 0 or l_tot == 0: return

        scale = min((canvas_w - 2 * padding) / l_tot, (canvas_h - 2 * padding) / h_tot) * 0.9
        ox, oy = padding, canvas_h - padding
        
        h_cm = self.latest_results.get("hauteur_reelle_contremarche", 0)
        giron = self.latest_results.get("giron_utilise", 0)
        nb_cm = self.latest_results.get("nombre_contremarches", 0)
        
        x, y = ox, oy
        for i in range(nb_cm):
            self.canvas.create_line(x, y, x, y - h_cm * scale, fill=colors["canvas_line"], width=2)
            y -= h_cm * scale
            if i < nb_cm - 1:
                self.canvas.create_line(x, y, x + giron * scale, y, fill=colors["canvas_line"], width=2)
                x += giron * scale

        # Ligne de pente corrigée suivant l'axe réel de l'escalier (nez de la première à la dernière marche)
        if nb_cm > 1:
            x1 = ox + giron * scale
            y1 = oy - h_cm * scale
            x2 = ox + (nb_cm - 1) * giron * scale
            y2 = oy - (nb_cm - 1) * h_cm * scale
            self.canvas.create_line(x1, y1, x2, y2, fill=colors["canvas_accent"], width=3, dash=(5, 2))

        prefs = self.app_preferences
        h_text = f"H={formatting.decimal_to_fraction_str(h_tot, prefs)}"
        l_text = f"L={formatting.decimal_to_fraction_str(l_tot, prefs)}"
        self.canvas.create_line(ox - 10, oy, ox - 10, oy - h_tot * scale, arrow=tk.BOTH, fill=colors["canvas_accent"])
        self.canvas.create_text(ox - 15, oy - (h_tot * scale) / 2, text=h_text, angle=90, fill=colors["fg"], anchor="s")
        self.canvas.create_line(ox, oy + 10, ox + l_tot * scale, oy + 10, arrow=tk.BOTH, fill=colors["canvas_accent"])
        self.canvas.create_text(ox + (l_tot * scale) / 2, oy + 15, text=l_text, fill=colors["fg"], anchor="n")

    def update_reports(self):
        """Génère et affiche les rapports dans les onglets dédiés."""
        if not self.latest_results: return
        report_text = reporting.generer_texte_trace(self.latest_results, self.app_preferences)
        table_text = reporting.generer_tableau_marches(self.latest_results, self.app_preferences)
        if hasattr(self, 'report_text'):
            self.report_text.delete("1.0", tk.END)
            self.report_text.insert(tk.END, report_text)
        if hasattr(self, 'table_text'):
            self.table_text.delete("1.0", tk.END)
            self.table_text.insert(tk.END, table_text)

    def switch_theme(self, theme_name):
        """Applique le thème de couleurs spécifié."""
        self.current_theme = theme_name
        colors = self.themes[theme_name]

        self.config(bg=colors["bg"])
        self.style.configure(".", background=colors["bg"], foreground=colors["fg"])
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
        self.style.configure("TButton", background=colors["button_bg"], foreground=colors["button_fg"])
        self.style.map("TButton", background=[('active', colors["accent"])])
        self.style.configure("TNotebook", background=colors["bg"])
        self.style.configure("TNotebook.Tab", background=colors["button_bg"], foreground=colors["fg"])
        self.style.map("TNotebook.Tab", background=[("selected", colors["accent"])], foreground=[("selected", colors["accent_fg"])])
        self.style.configure("TLabelFrame", background=colors["frame_bg"], bordercolor=colors["fg"])
        self.style.configure("TLabelFrame.Label", background=colors["frame_bg"], foreground=colors["fg"])
        
        for widget_name in ["report_text", "table_text"]:
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                widget.config(bg=colors["entry_bg"], fg=colors["fg"], insertbackground=colors["fg"])

        self.style.configure("Conformity.TLabel", foreground=colors["fg"])
        self.style.configure("Warning.TLabel", foreground=colors["warning"])
        self.style.configure("Error.TLabel", foreground=colors["error"])
        self.style.configure("Indicator.Green.TLabel", background=colors["success"], foreground=colors["accent_fg"])
        self.style.configure("Indicator.Yellow.TLabel", background=colors["warning"], foreground=colors["fg"])
        self.style.configure("Indicator.Red.TLabel", background=colors["error"], foreground=colors["accent_fg"])
        
        self.update_warnings_display()
        self.update_visual_preview()

    def open_preferences_dialog(self):
        """Ouvre le dialogue des préférences de l'application."""
        prefs_dialog = PreferencesDialog(self, self.app_preferences)
        self.wait_window(prefs_dialog)
        self.app_preferences = file_operations.load_application_preferences()
        self.recalculate_and_update_ui()

    def open_laser_dialog(self):
        """Ouvre le dialogue d'assistance laser."""
        laser_dialog = LaserDialog(self)
        self.wait_window(laser_dialog)

    def export_pdf_report(self):
        """Fonctionnalité future : exporte le rapport en PDF."""
        messagebox.showinfo("Fonctionnalité future", "L'exportation en PDF sera bientôt disponible !", parent=self)


if __name__ == "__main__":
    app = ModernStairCalculator()
    app.mainloop()