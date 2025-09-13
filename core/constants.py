# Fichier: core/constants.py

# --- Constantes de Version et de Configuration ---
VERSION_PROGRAMME = "1.0.0"
DEBUG_MODE_ACTIVE = False

# --- Constantes de Conversion d'Unités ---
POUCE_EN_CM = 2.54
POUCE_EN_MM = 25.4
TOLERANCE_MESURE_LASER = 0.125  # Tolérance de mesure en pouces (1/8")

# --- Constantes Réglementaires et de Confort (en POUCES) ---
HAUTEUR_CM_MIN_REGLEMENTAIRE = 5.0
HAUTEUR_CM_MAX_REGLEMENTAIRE = 7.75
HAUTEUR_CM_CONFORT_CIBLE = 7.0

GIRON_MIN_REGLEMENTAIRE = 9.0
GIRON_MAX_REGLEMENTAIRE = 14.0
GIRON_CONFORT_CIBLE = 9.25

BLONDEL_MIN = 24.0
BLONDEL_MAX = 25.0
BLONDEL_IDEAL = 24.5

# --- Préférences par Défaut de l'Application ---
import os
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(APP_DIR, "data")
DEFAULTS_FILE = os.path.join(DATA_DIR, "preferences.json")
DEFAULT_APP_PREFERENCES = {
    "unites_affichage": "pouces",
    "default_tread_width_straight": "9 1/4",
    "default_floor_finish_thickness_upper": "1 1/2",
    "default_floor_finish_thickness_lower": "1",
    "show_debug_info": False
}
    "default_floor_finish_thickness_lower": "1",
    "show_debug_info": False
}
import os
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(APP_DIR, "data")
DEFAULTS_FILE = os.path.join(DATA_DIR, "preferences.json")
DEFAULT_APP_PREFERENCES = {
    "unites_affichage": "pouces",
    "default_tread_width_straight": "9 1/4",
    "default_floor_finish_thickness_upper": "1 1/2",
    "default_floor_finish_thickness_lower": "1",
    "show_debug_info": False
}
