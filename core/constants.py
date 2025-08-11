# Fichier: core/constants.py

# --- Constantes de Version et de Configuration ---
VERSION_PROGRAMME = "2.1"
DEBUG_MODE_ACTIVE = False

# --- Constantes de Conversion d'Unités ---
POUCE_EN_CM = 2.54
POUCE_EN_MM = 25.4

# --- Constantes Spécifiques aux Calculs ---
# CORRECTION : Ajout de la constante manquante pour la fonction laser.
# Tolérance en pouces pour la validation des mesures laser (ex: 1/8 de pouce).
TOLERANCE_MESURE_LASER = 0.125 

# --- Constantes Réglementaires et de Confort (en POUCES) ---
# Hauteur de contremarche (riser height)
HAUTEUR_CM_MIN_REGLEMENTAIRE = 5.0
HAUTEUR_CM_MAX_REGLEMENTAIRE = 7.75
HAUTEUR_CM_CONFORT_CIBLE = 7.5

# Giron (tread width)
GIRON_MIN_REGLEMENTAIRE = 9.25
GIRON_MAX_REGLEMENTAIRE = 13.0
GIRON_CONFORT_CIBLE = 10.0

# Formule de Blondel (2H + G)
BLONDEL_MIN = 24.0
BLONDEL_MAX = 25.0
BLONDEL_CIBLE_IDEAL = 24.5

# Échappée (headroom)
ECHAPPEE_MIN_REGLEMENTAIRE = 80.0

# Angle de l'escalier
ANGLE_CONFORT_MIN = 30.0
ANGLE_CONFORT_MAX = 37.0

# --- Préférences par Défaut de l'Application ---
DEFAULTS_FILE = "data/app_preferences.json"
DEFAULT_APP_PREFERENCES = {
    "unites_affichage": "pouces",
    "precision_fraction": 16,
    "default_floor_finish_thickness_upper": "1 1/2",
    "default_floor_finish_thickness_lower": "1",
    "default_tread_width_straight": "9 1/4",
    "default_tread_width_pie": "10"
}
