import tkinter as tk
from tkinter import ttk, messagebox
import math
from core import constants
from gui.dialogs import PreferencesDialog
from utils.formatting import decimal_to_fraction_str, parser_fraction
from utils.reporting import generer_texte_trace
from utils.file_operations import load_application_preferences

class MainWindow:
    def __init__(self, master, app_prefs):
        self.master = master
        self.app_preferences = app_prefs
        self.latest_results = {}

        self.master.title("Calculateur d'Escalier Interactif")
        self.master.geometry("850x700")

        # --- Création du menu ---
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Préférences...", command=self.open_preferences_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.master.quit)

        self._setup_style()
        self._setup_tk_variables()
        self._create_main_layout()
        self._bind_events()

    def open_preferences_dialog(self):
        prefs_dialog = PreferencesDialog(self.master, self.app_preferences)
        self.master.wait_window(prefs_dialog)
        # Recharger les préférences pour qu'elles soient disponibles pour les prochains calculs
        self.app_preferences = load_application_preferences()

    def _setup_style(self):
        style = ttk.Style()
        style.configure("TLabelFrame", borderwidth=2, relief="groove", padding=10)
        style.configure("TButton", padding=5)
        style.configure("Warning.TLabel", foreground="orange", font=('TkDefaultFont', 9, 'italic'))
        style.configure("Error.TLabel", foreground="red", font=('TkDefaultFont', 10, 'bold'))

    def _setup_tk_variables(self):
        # Variables pour les entrées
        self.hauteur_totale_var = tk.StringVar()
        self.giron_souhaite_var = tk.StringVar(value=self.app_preferences.get("default_tread_width_straight", "9 1/4"))
        self.epaisseur_plancher_inf_var = tk.StringVar(value="0")
        self.espace_disponible_var = tk.StringVar()
        self.longueur_marche_var = tk.StringVar(value="36")
        self.profondeur_limon_var = tk.StringVar(value="9 1/4")
        self.nombre_cm_var = tk.IntVar()
        
        # Variables pour la trémie
        self.longueur_tremie_var = tk.StringVar()
        self.position_tremie_var = tk.StringVar()
        self.epaisseur_plancher_sup_var = tk.StringVar(value=self.app_preferences.get("default_floor_finish_thickness_upper", "1 1/2"))

        # Variables pour les résultats et messages
        self.hauteur_reelle_cm_res_var = tk.StringVar()
        self.longueur_totale_res_var = tk.StringVar()
        self.angle_res_var = tk.StringVar()
        self.limon_res_var = tk.StringVar()
        self.echappee_res_var = tk.StringVar()
        self.hauteur_cm_message_var = tk.StringVar()
        self.giron_message_var = tk.StringVar()
        self.longueur_message_var = tk.StringVar()
        self.echappee_message_var = tk.StringVar()

    def _create_main_layout(self):
        notebook = ttk.Notebook(self.master)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        calcul_tab = ttk.Frame(notebook, padding="10")
        report_tab = ttk.Frame(notebook, padding="10")
        notebook.add(calcul_tab, text="Calculateur Principal")
        notebook.add(report_tab, text="Rapports")

        # --- Onglet Calculateur ---
        input_frame = ttk.LabelFrame(calcul_tab, text="1. Entrées de Base")
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        interactive_frame = ttk.LabelFrame(calcul_tab, text="2. Ajustement Interactif")
        interactive_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        results_frame = ttk.LabelFrame(calcul_tab, text="3. Résultats et Conformité")
        results_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self._populate_input_frame(input_frame)
        self._populate_interactive_frame(interactive_frame)
        self._populate_results_frame(results_frame)

        # --- Onglet Rapports ---
        self.report_text_area = tk.Text(report_tab, wrap="word", height=20, width=80, font=("Courier New", 9))
        self.report_text_area.pack(expand=True, fill="both", pady=5)
        
        report_actions_frame = ttk.Frame(report_tab)
        report_actions_frame.pack(fill="x", pady=5)
        ttk.Button(report_actions_frame, text="Générer le plan de traçage", command=self.generate_and_display_report).pack()

    def _populate_input_frame(self, parent):
        entries = [
            ("Hauteur totale à monter:", self.hauteur_totale_var),
            ("Giron souhaité:", self.giron_souhaite_var),
            ("Espace disponible (longueur):", self.espace_disponible_var),
            ("Longueur de la marche (Largeur):", self.longueur_marche_var),
            ("Profondeur du limon:", self.profondeur_limon_var),
        ]
        for i, (text, var) in enumerate(entries):
            ttk.Label(parent, text=text).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            ttk.Entry(parent, textvariable=var, width=15).grid(row=i, column=1, sticky="w", padx=5, pady=3)
        
        ttk.Separator(parent, orient='horizontal').grid(row=len(entries), column=0, columnspan=2, sticky='ew', pady=10)
        
        tremie_entries = [
            ("Hauteur du 2e étage (Ép. plancher sup.):", self.epaisseur_plancher_sup_var),
            ("Épaisseur plancher inférieur:", self.epaisseur_plancher_inf_var), # <-- NOUVEAU
            ("Largeur de l'ouverture (Trémie):", self.longueur_tremie_var),
            ("Position de la trémie:", self.position_tremie_var),
        ]
        for i, (text, var) in enumerate(tremie_entries, start=len(entries)+1):
            ttk.Label(parent, text=text).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            ttk.Entry(parent, textvariable=var, width=15).grid(row=i, column=1, sticky="w", padx=5, pady=3)

    def _populate_interactive_frame(self, parent):
        ttk.Label(parent, text="Nombre de contremarches:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        btn_frame = ttk.Frame(parent)
        ttk.Button(btn_frame, text="-", command=self.decrement_cm, width=3).pack(side="left")
        ttk.Label(btn_frame, textvariable=self.nombre_cm_var, font=('TkDefaultFont', 12, 'bold')).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="+", command=self.increment_cm, width=3).pack(side="left")
        btn_frame.grid(row=0, column=1, padx=5)

    def _populate_results_frame(self, parent):
        results_labels = [
            ("Hauteur réelle par CM:", self.hauteur_reelle_cm_res_var, self.hauteur_cm_message_var),
            ("Longueur totale de l'escalier:", self.longueur_totale_res_var, self.longueur_message_var),
            ("Angle de l'escalier:", self.angle_res_var, None),
            ("Longueur du limon:", self.limon_res_var, None),
        ]
        for i, (text, res_var, msg_var) in enumerate(results_labels):
            ttk.Label(parent, text=text).grid(row=i, column=0, sticky="w", pady=4)
            ttk.Label(parent, textvariable=res_var, font=('TkDefaultFont', 10, 'bold')).grid(row=i, column=1, sticky="w")
            if msg_var:
                ttk.Label(parent, textvariable=msg_var, style="Error.TLabel").grid(row=i, column=2, sticky="w", padx=10)
        
        ttk.Label(parent, textvariable=self.giron_message_var, style="Warning.TLabel").grid(row=len(results_labels), column=0, columnspan=3, sticky="w", pady=5)
        
        ttk.Separator(parent, orient='horizontal').grid(row=len(results_labels)+1, column=0, columnspan=3, sticky='ew', pady=10)
        
        ttk.Label(parent, text="Échappée calculée:").grid(row=len(results_labels)+2, column=0, sticky="w", pady=4)
        ttk.Label(parent, textvariable=self.echappee_res_var, font=('TkDefaultFont', 10, 'bold')).grid(row=len(results_labels)+2, column=1, sticky="w")
        ttk.Label(parent, textvariable=self.echappee_message_var, style="Error.TLabel").grid(row=len(results_labels)+2, column=2, sticky="w", padx=10)

    def _bind_events(self):
        """Lie les événements aux fonctions."""
        # La variable de hauteur a un traitement spécial
        self.hauteur_totale_var.trace_add("write", self.on_hauteur_change)
        
        # Toutes les autres variables déclenchent une mise à jour directe
        for var in [self.hauteur_totale_var, self.giron_souhaite_var, self.espace_disponible_var,
                    self.longueur_marche_var, self.profondeur_limon_var, self.longueur_tremie_var,
                    self.position_tremie_var, self.epaisseur_plancher_sup_var,
                    self.epaisseur_plancher_inf_var]: # <-- AJOUTER ICI
            var.trace_add("write", self.recalculate_and_update_ui)

    def on_hauteur_change(self, *args):
        try:
            h_tot = parser_fraction(self.hauteur_totale_var.get())
            nb_cm = math.ceil(h_tot / constants.HAUTEUR_CM_CONFORT_CIBLE) if h_tot > 0 else 0
            self.nombre_cm_var.set(nb_cm if nb_cm > 1 else 2) # S'assurer d'au moins 2 contremarches
        except (ValueError, ZeroDivisionError, tk.TclError):
            self.nombre_cm_var.set(0)

    def decrement_cm(self):
        if self.nombre_cm_var.get() > 2:
            self.nombre_cm_var.set(self.nombre_cm_var.get() - 1)
            self.recalculate_and_update_ui()

    def increment_cm(self):
        self.nombre_cm_var.set(self.nombre_cm_var.get() + 1)
        self.recalculate_and_update_ui()

    def recalculate_and_update_ui(self, *args):
        self.clear_results()
        try:
            h_tot = parser_fraction(self.hauteur_totale_var.get())
            giron = parser_fraction(self.giron_souhaite_var.get())
            nb_cm = self.nombre_cm_var.get()

            if nb_cm < 2: return

            self.latest_results['hauteur_totale'] = h_tot
            self.latest_results['giron_utilise'] = giron
            self.latest_results['nombre_contremarches'] = nb_cm
            self.latest_results['kwargs'] = {
                'epaisseur_marche': parser_fraction(self.app_preferences.get('default_tread_thickness')),
                'epaisseur_plancher_sup': parser_fraction(self.epaisseur_plancher_sup_var.get())
            }

            h_reel = h_tot / nb_cm
            self.latest_results['hauteur_reelle_contremarche'] = h_reel
            longueur_totale = (nb_cm - 1) * giron
            angle = math.degrees(math.atan(h_tot / longueur_totale)) if longueur_totale > 0 else 90
            longueur_limon = math.sqrt(h_tot**2 + longueur_totale**2)

            self.hauteur_reelle_cm_res_var.set(decimal_to_fraction_str(h_reel, self.app_preferences))
            self.longueur_totale_res_var.set(decimal_to_fraction_str(longueur_totale, self.app_preferences))
            self.angle_res_var.set(f"{angle:.2f}°")
            self.limon_res_var.set(decimal_to_fraction_str(longueur_limon, self.app_preferences))
            
            self.hauteur_cm_message_var.set("NON CONFORME" if not (constants.HAUTEUR_CM_MIN_REGLEMENTAIRE <= h_reel <= constants.HAUTEUR_CM_MAX_REGLEMENTAIRE) else "")
            
            if not (constants.GIRON_MIN_REGLEMENTAIRE <= giron <= constants.GIRON_MAX_REGLEMENTAIRE):
                self.giron_message_var.set("Giron NON CONFORME")
            elif giron < constants.GIRON_CONFORT_MIN:
                self.giron_message_var.set(f"Conforme mais < {constants.GIRON_CONFORT_MIN}\"")
            else:
                self.giron_message_var.set("")
            
            espace_dispo = parser_fraction(self.espace_disponible_var.get())
            longueur_marche = parser_fraction(self.longueur_marche_var.get())
            if espace_dispo > 0:
                self.longueur_message_var.set("DÉPASSE ESPACE DISPO" if (longueur_totale + longueur_marche) > espace_dispo else "")
            
            long_tremie = parser_fraction(self.longueur_tremie_var.get())
            pos_tremie = parser_fraction(self.position_tremie_var.get())
            ep_plancher = parser_fraction(self.epaisseur_plancher_sup_var.get())

            if long_tremie > 0 and giron > 0:
                hauteur_plafond = h_tot - ep_plancher
                marche_critique_index = math.floor(pos_tremie / giron)
                hauteur_dessus_marche_critique = (marche_critique_index + 1) * h_reel
                echappee_calculee = hauteur_plafond - hauteur_dessus_marche_critique
                
                self.echappee_res_var.set(decimal_to_fraction_str(echappee_calculee, self.app_preferences))
                if echappee_calculee < constants.HAUTEUR_LIBRE_MIN_REGLEMENTAIRE:
                    self.echappee_message_var.set("NON CONFORME")
                elif echappee_calculee < constants.HAUTEUR_LIBRE_CONFORT_MIN:
                    self.echappee_message_var.set(f"Conforme mais < {decimal_to_fraction_str(constants.HAUTEUR_LIBRE_CONFORT_MIN, self.app_preferences)}\"")
                else:
                    self.echappee_message_var.set("")
        except (ValueError, ZeroDivisionError, tk.TclError):
            pass

    def clear_results(self):
        for var in [self.hauteur_reelle_cm_res_var, self.longueur_totale_res_var, self.angle_res_var,
                    self.limon_res_var, self.echappee_res_var, self.hauteur_cm_message_var,
                    self.giron_message_var, self.longueur_message_var, self.echappee_message_var]:
            var.set("")
        self.latest_results = {}

    def generate_and_display_report(self):
        if not self.latest_results:
            messagebox.showwarning("Aucun Calcul", "Veuillez d'abord effectuer un calcul valide.", parent=self.master)
            return
        
        report_text = generer_texte_trace(self.latest_results, self.app_preferences)
        self.report_text_area.delete("1.0", tk.END)
        self.report_text_area.insert(tk.END, report_text)
        notebook = self.master.winfo_children()[0]
        notebook.select(1)