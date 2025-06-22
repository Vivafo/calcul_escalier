# Fichier: CalculateurEscalier/core/constants.py

import os # Importation nécessaire pour os.path.join

# Version du programme
VERSION_PROGRAMME = "0.5.0"

# Unités et conversions
POUCE_EN_MM = 25.4

# Constantes pour le calcul des escaliers (selon le Code de construction du Québec, version récente et guide APCHQ)

# Hauteur des contremarches (CM)  avec un test dc frase inutile
HAUTEUR_CM_MIN_REGLEMENTAIRE = 5.0   # pouces (127 mm) - Minimum selon le code
HAUTEUR_CM_MAX_REGLEMENTAIRE = 8.25  # pouces (209 mm) - Maximum selon le code (souvent 8 1/4)
HAUTEUR_CM_CONFORT_CIBLE = 7.5       # pouces (190.5 mm) - Cible pour le confort

# Giron (profondeur de la marche)
GIRON_MIN_REGLEMENTAIRE = 8.25      # pouces (209 mm) - Minimum selon le code (souvent 8 1/4)
GIRON_MAX_REGLEMENTAIRE = 14.0      # pouces (355 mm) - Maximum recommandé pour le confort/praticité (pas toujours une limite stricte du code)
GIRON_CONFORT_MIN_RES_STANDARD = 9.0 # pouces - Giron minimal pour un confort standard résidentiel

# Loi de Blondel (2H + G = 21 à 25 pouces)
BLONDEL_MIN_POUCES = 21.0
BLONDEL_MAX_POUCES = 25.0

# Hauteur libre (échappée)
HAUTEUR_LIBRE_MIN_REGLEMENTAIRE = 78.74 # pouces (2000 mm ou 6'6") - Minimum selon le code (au-dessus du nez de marche)

# Angles de pente
ANGLE_CONFORT_STANDARD_MAX = 35.0  # degrés - Au-delà, l'escalier est considéré "raide"
ANGLE_CONFORT_RAIDE_MAIS_CONFORME_MAX = 42.0 # degrés - Angle max acceptable, au-delà, potentiellement non conforme/dangereux
ANGLE_STANDARD_MAX = 35.0  # degrés - Valeur standard maximale pour l'angle d'un escalier confortableANGLE_CONFORT_RAIDE_MAIS_CONFORME_MAX = 42.0 # degrés - Angle max acceptable, au-delà, potentiellement non conforme/dangereux
# Note: ANGLE_STANDARD_MAX a été mentionné dans le code main_app.py mais n'était pas défini ici.
# Je l'ai retiré du main_app.py pour éviter une erreur, mais si vous en avez besoin, définissez-le ici.
# Pour l'instant, je vais utiliser ANGLE_CONFORT_RAIDE_MAIS_CONFORME_MAX comme limite supérieure si ANGLE_STANDARD_MAX n'existe pas.

# Précision par défaut pour les fractions (par exemple, 16 pour les 1/16 de pouce)
DEFAULT_DENOMINATEUR_PRECISION = 16 

# Mode débogage (activé/désactivé)
DEBUG_MODE_ACTIVE = False # Par défaut, le mode débogage est désactivé

# Fichier des préférences de l'application
DEFAULTS_FILE = os.path.join("data", "app_preferences.json")

# Préférences de l'application (valeurs par défaut si le fichier de préférences n'existe pas)
DEFAULT_APP_PREFERENCES = {
    "fraction_precision_denominator": 16, # Dénominateur par défaut pour l'affichage des fractions
    "default_tread_width_straight": "9 1/4", # Giron par défaut pour un escalier droit
    "default_floor_finish_thickness_upper": "1 1/2", # Épaisseur plancher fini supérieur
    "default_floor_finish_thickness_lower": "1", # Épaisseur plancher fini inférieur
    "default_tread_thickness": "1 1/16", # Épaisseur des marches
}