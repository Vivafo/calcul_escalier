# Fichier: CalculateurEscalier/core/calculations.py
# (Seule la fonction calculer_dimensions_escalier est montrée, le reste du fichier est inchangé)

import math
from core import constants
from utils.formatting import parser_fraction, decimal_to_fraction_str

def calculer_dimensions_escalier(hauteur_totale_escalier, giron_souhaite, loaded_app_preferences_dict, **kwargs):
    """
    Calcule toutes les dimensions clés de l'escalier.
    NOTE: La logique de détermination du nombre de contremarches et de l'échappée
    est maintenant gérée dans main_app.py pour une meilleure interactivité.
    Cette fonction se concentre sur les calculs dérivés.
    """
    # Extraction des paramètres clés passés depuis main_app.py
    nombre_contremarches = kwargs.get("nombre_contremarches_ajuste", 1)
    if nombre_contremarches == 0: nombre_contremarches = 1 # Prévenir la division par zéro

    hauteur_reelle_contremarche = hauteur_totale_escalier / nombre_contremarches
    nombre_girons = max(0, nombre_contremarches - 1)
    
    # Calcul de la longueur et de l'angle
    longueur_calculee_escalier = nombre_girons * giron_souhaite
    angle_escalier = 0.0
    if longueur_calculee_escalier > 1e-6:
        angle_escalier = math.degrees(math.atan(hauteur_totale_escalier / longueur_calculee_escalier))
    elif hauteur_totale_escalier > 0:
        angle_escalier = 90.0

    # Longueur du limon
    longueur_limon_approximative = math.sqrt(hauteur_totale_escalier**2 + longueur_calculee_escalier**2)

    # --- MODIFIÉ : Ajout du calcul de Blondel ---
    blondel_value = (2 * hauteur_reelle_contremarche) + giron_souhaite

    # Préparation du dictionnaire de résultats
    results_dict = {
        "hauteur_totale_escalier": hauteur_totale_escalier,
        "nombre_contremarches": nombre_contremarches,
        "hauteur_reelle_contremarche": hauteur_reelle_contremarche,
        "nombre_girons": nombre_girons,
        "giron_utilise": giron_souhaite,
        "longueur_calculee_escalier": longueur_calculee_escalier,
        "angle_escalier": angle_escalier,
        "longueur_limon_approximative": longueur_limon_approximative,
        "blondel_value": blondel_value, # Clé ajoutée
        **kwargs 
    }
    return results_dict