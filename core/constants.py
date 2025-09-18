# Fichier: core/constants.py

# --- Constantes de Version et de Configuration ---
VERSION_PROGRAMME = "1.0.0"
DEBUG_MODE_ACTIVE = False

# --- Constantes de Conversion d'Unités ---
POUCE_EN_CM = 2.54
POUCE_EN_MM = 25.4
TOLERANCE_MESURE_LASER = 0.125  # Tolérance de mesure en pouces (1/8")

# --- Constantes Réglementaires et de Confort (en POUCES) ---
HAUTEUR_CM_MIN_REGLEMENTAIRE = 5.75
HAUTEUR_CM_MAX_REGLEMENTAIRE = 7.875
HAUTEUR_CM_TOLERANCE_SUCCESSIVE = 5 / 25.4  # 5 mm ≈ 3/16"
HAUTEUR_CM_CONFORT_CIBLE = 7.0

HAUTEUR_LIBRE_MIN_REGLEMENTAIRE = 80.0

GIRON_MIN_REGLEMENTAIRE = 9.0
GIRON_MAX_REGLEMENTAIRE = 14.0
GIRON_CONFORT_MIN_RES_STANDARD = 9.25
GIRON_CONFORT_CIBLE = 9.25

BLONDEL_MIN = 24.0
BLONDEL_MAX = 25.0
BLONDEL_IDEAL = 24.5
BLONDEL_MIN_POUCES = BLONDEL_MIN
BLONDEL_MAX_POUCES = BLONDEL_MAX

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

ANGLE_CONFORT_STANDARD_MAX = 37.0
ANGLE_CONFORT_RAIDE_MAIS_CONFORME_MAX = 42.0


