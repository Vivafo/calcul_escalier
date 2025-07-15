# Fichier: CalculateurEscalier/core/calculations.py

import math
from core import constants # Pour accéder aux constantes réglementaires et aux préférences chargées
from utils.formatting import parser_fraction, decimal_to_fraction_str
from core.validation import ( # Importation des fonctions de validation
    validate_hauteur_format, validate_giron_format, validate_epaisseur_plancher_format,
    validate_longueur_tremie_format, validate_position_tremie_format
)

def calculer_escalier_ajuste(
    hauteur_totale_escalier_str,
    giron_souhaite_str,
    hauteur_cm_souhaitee_str,
    nombre_marches_manuel_str,
    nombre_cm_manuel_str,
    epaisseur_plancher_sup_str,
    epaisseur_plancher_inf_str,
    profondeur_tremie_ouverture_str,
    position_tremie_ouverture_str,
    espace_disponible_str,
    loaded_app_preferences_dict,
    changed_var_name=None # Nom de la variable qui a déclenché le calcul
):
    """
    Calcule les dimensions optimales d'un escalier en fonction des entrées utilisateur
    et des normes. Gère la priorité entre le nombre de marches/contremarches
    et les dimensions souhaitées.

    Retourne un dictionnaire avec les résultats de calcul, les messages d'avertissement
    et un statut de conformité global.
    """
    results = {
        "hauteur_totale_escalier": None,
        "hauteur_reelle_contremarche": None,
        "giron_utilise": None,
        "nombre_contremarches": None,
        "nombre_girons": None,
        "longueur_calculee_escalier": None,
        "angle_escalier": None,
        "longueur_limon_approximative": None,
        "min_echappee_calculee": None,
        "blondel_value": None,
        # Messages pour l'affichage détaillé de la conformité
        "hauteur_cm_message": "",
        "giron_message": "",
        "blondel_message": "",
        "echappee_message": "",
        "longueur_disponible_message": "",
        "angle_message": "",
        "hauteur_totale_ecart_message": "",
        "kwargs": {} # Pour stocker les épaisseurs pour le reporting
    }
    warnings = []
    is_conform = True

    # --- 1. Parsing et Validation des entrées brutes ---
    # Convertir toutes les entrées en pouces décimaux
    try:
        hauteur_totale_escalier = parser_fraction(hauteur_totale_escalier_str)
        giron_souhaite = parser_fraction(giron_souhaite_str)
        hauteur_cm_souhaitee = parser_fraction(hauteur_cm_souhaitee_str)
        epaisseur_plancher_sup = parser_fraction(epaisseur_plancher_sup_str)
        epaisseur_plancher_inf = parser_fraction(epaisseur_plancher_inf_str)
        
        # Les champs optionnels peuvent être vides
        profondeur_tremie_ouverture = parser_fraction(profondeur_tremie_ouverture_str) if profondeur_tremie_ouverture_str.strip() else 0.0
        position_tremie_ouverture = parser_fraction(position_tremie_ouverture_str) if position_tremie_ouverture_str.strip() else 0.0
        espace_disponible = parser_fraction(espace_disponible_str) if espace_disponible_str.strip() else 0.0

        nombre_marches_manuel = int(nombre_marches_manuel_str) if nombre_marches_manuel_str.strip() else None
        nombre_cm_manuel = int(nombre_cm_manuel_str) if nombre_cm_manuel_str.strip() else None
        
        # Récupérer l'épaisseur de marche par défaut des préférences
        epaisseur_marche = parser_fraction(loaded_app_preferences_dict.get("default_tread_thickness", "1 1/16"))
        
        results["kwargs"]["epaisseur_marche"] = epaisseur_marche
        results["kwargs"]["epaisseur_plancher_sup"] = epaisseur_plancher_sup

    except ValueError as e:
        warnings.append(f"Erreur de format pour une entrée: {e}. Veuillez utiliser des nombres ou des fractions valides (ex: '10', '9 1/4', '3/4').")
        is_conform = False
        return {"results": results, "warnings": warnings, "is_conform": is_conform}

    # Vérifications minimales pour éviter les divisions par zéro ou calculs absurdes
    if hauteur_totale_escalier <= 0:
        warnings.append("La hauteur totale de l'escalier doit être supérieure à zéro.")
        is_conform = False
        return {"results": results, "warnings": warnings, "is_conform": is_conform}
    
    if giron_souhaite <= 0:
        warnings.append("Le giron souhaité doit être supérieur à zéro.")
        is_conform = False
        return {"results": results, "warnings": warnings, "is_conform": is_conform}

    # --- 2. Détermination du nombre de contremarches et hauteur réelle ---
    nombre_contremarches = 0
    hauteur_reelle_contremarche = 0.0 # Initialisation

    # Priorité 1: Nombre de CM ou de marches manuel
    if nombre_cm_manuel is not None:
        nombre_contremarches = nombre_cm_manuel
    elif nombre_marches_manuel is not None:
        nombre_contremarches = nombre_marches_manuel + 1
    else:
        # Priorité 2: Calcul du nombre de CM optimal basé sur la hauteur de CM souhaitée
        if hauteur_cm_souhaitee <= 0: # Fallback si HCM souhaitée est invalide ou 0.
            hauteur_cm_souhaitee = constants.HAUTEUR_CM_CONFORT_CIBLE
            
        # Calculer le nombre de CM en arrondissant au plus proche entier
        nombre_contremarches = round(hauteur_totale_escalier / hauteur_cm_souhaitee)
            
    # Assurer un minimum de 2 contremarches pour un escalier, quel que soit le mode de détermination
    if nombre_contremarches < 2:
        nombre_contremarches = 2

    # Calcul universel de la hauteur réelle de contremarche après détermination de nombre_contremarches
    if nombre_contremarches > 0:
        hauteur_reelle_contremarche = hauteur_totale_escalier / nombre_contremarches
    else:
        # Ce cas ne devrait pas arriver souvent avec le min de 2 CM, mais c'est une sécurité
        warnings.append("Impossible de déterminer un nombre valide de contremarches.")
        is_conform = False
        return {"results": results, "warnings": warnings, "is_conform": is_conform}


    # --- 3. Vérification de conformité de la Hauteur de Contremarche ---
    h_min = constants.HAUTEUR_CM_MIN_REGLEMENTAIRE
    h_max = constants.HAUTEUR_CM_MAX_REGLEMENTAIRE
    h_confort_cible = constants.HAUTEUR_CM_CONFORT_CIBLE

    if not (h_min <= hauteur_reelle_contremarche <= h_max):
        results["hauteur_cm_message"] = "NON CONFORME"
        warnings.append(f"Hauteur réelle CM ({decimal_to_fraction_str(hauteur_reelle_contremarche, loaded_app_preferences_dict)}\") est hors normes ({decimal_to_fraction_str(h_min, loaded_app_preferences_dict)}\" à {decimal_to_fraction_str(h_max, loaded_app_preferences_dict)}\").")
        is_conform = False
    elif abs(hauteur_reelle_contremarche - h_confort_cible) > 0.5: # Si plus de 1/2 pouce d'écart avec le confort cible
        results["hauteur_cm_message"] = "Confort Limité"
        warnings.append(f"Hauteur réelle CM ({decimal_to_fraction_str(hauteur_reelle_contremarche, loaded_app_preferences_dict)}\") a un confort limité (cible: {decimal_to_fraction_str(h_confort_cible, loaded_app_preferences_dict)}\").")
    else:
        results["hauteur_cm_message"] = "OPTIMAL" # Ou "OK"

    # --- 4. Calcul du nombre de girons et ajustements si nécessaire ---
    nombre_girons = nombre_contremarches - 1
    
    # On utilise le giron souhaité comme "giron_utilise"
    giron_utilise = giron_souhaite 

    # --- 5. Vérification de conformité du Giron ---
    g_min = constants.GIRON_MIN_REGLEMENTAIRE
    g_max = constants.GIRON_MAX_REGLEMENTAIRE 
    g_confort_min = constants.GIRON_CONFORT_MIN_RES_STANDARD

    if not (g_min <= giron_utilise <= g_max):
        results["giron_message"] = "NON CONFORME"
        warnings.append(f"Giron utilisé ({decimal_to_fraction_str(giron_utilise, loaded_app_preferences_dict)}\") est hors normes ({decimal_to_fraction_str(g_min, loaded_app_preferences_dict)}\" à {decimal_to_fraction_str(g_max, loaded_app_preferences_dict)}\").")
        is_conform = False
    elif giron_utilise < g_confort_min:
        results["giron_message"] = "Confort Limité"
        warnings.append(f"Giron utilisé ({decimal_to_fraction_str(giron_utilise, loaded_app_preferences_dict)}\") a un confort limité (recommandé: >{decimal_to_fraction_str(g_confort_min, loaded_app_preferences_dict)}\").")
    else:
        results["giron_message"] = "OK"

    # --- 6. Calculs secondaires (longueur, angle, limon) ---
    longueur_calculee_escalier = nombre_girons * giron_utilise
    
    angle_escalier = 0.0
    # Correction de l'angle : s'assurer que longueur_calculee_escalier n'est pas zéro pour éviter ZeroDivisionError
    # et que la hauteur n'est pas zéro non plus pour éviter un angle de 0 sans raison.
    if longueur_calculee_escalier > 0 and hauteur_totale_escalier > 0:
        angle_escalier = math.degrees(math.atan(hauteur_totale_escalier / longueur_calculee_escalier))
    elif hauteur_totale_escalier > 0 and longueur_calculee_escalier == 0:
        angle_escalier = 90.0 # Escalier vertical (cas limite ou erreur)
    
    longueur_limon_approximative = math.sqrt(hauteur_totale_escalier**2 + longueur_calculee_escalier**2)

    # --- 7. Vérification Loi de Blondel ---
    blondel_value = (2 * hauteur_reelle_contremarche) + giron_utilise
    b_min = constants.BLONDEL_MIN_POUCES
    b_max = constants.BLONDEL_MAX_POUCES

    if not (b_min <= blondel_value <= b_max):
        results["blondel_message"] = "NON CONFORME"
        warnings.append(f"Loi de Blondel ({decimal_to_fraction_str(blondel_value, loaded_app_preferences_dict)}\") est hors normes ({decimal_to_fraction_str(b_min, loaded_app_preferences_dict)}\" à {decimal_to_fraction_str(b_max, loaded_app_preferences_dict)}\").")
        is_conform = False
    else:
        results["blondel_message"] = "OK"

    # --- 8. Vérification Échappée (Hauteur Libre) ---
    min_echappee_calculee = None
    echappee_min_reg = constants.HAUTEUR_LIBRE_MIN_REGLEMENTAIRE
    
    # Vérifier si les données de trémie sont renseignées pour tenter le calcul
    if profondeur_tremie_ouverture > 0 and position_tremie_ouverture >= 0 and giron_utilise > 0 and hauteur_reelle_contremarche > 0:
        
        # Calcul de la hauteur du dessous de la trémie par rapport au niveau du sol de l'étage inférieur
        # C'est la hauteur totale moins l'épaisseur du plancher supérieur (au niveau du 2e étage)
        h_dessous_tremie = hauteur_totale_escalier - epaisseur_plancher_sup

        # La pente de l'escalier (Hauteur / Giron)
        pente_escalier = hauteur_reelle_contremarche / giron_utilise

        # Pour calculer l'échappée, on doit considérer la hauteur verticale entre la ligne
        # de nez de marche et le dessous de l'obstacle (la trémie) au-dessus.
        # Le point le plus critique est généralement au début de la trémie.

        # Hauteur de la ligne de nez de marche au début de la trémie (position_tremie_ouverture)
        # y = pente * x
        hauteur_nez_a_debut_tremie = pente_escalier * position_tremie_ouverture
        
        # Calcul de l'échappée verticale à la position_tremie_ouverture
        current_echappee = h_dessous_tremie - hauteur_nez_a_debut_tremie
        
        # Il faut aussi considérer la situation où la trémie couvre plusieurs marches.
        # La hauteur libre minimale est la plus petite distance verticale entre le nez de marche
        # et le dessous de l'obstacle.
        
        min_echappee_calculee = float('inf') # Initialiser avec une valeur très grande
        
        # Itérer sur les girons qui se trouvent sous la trémie pour trouver l'échappée minimale
        # La trémie va de position_tremie_ouverture à (position_tremie_ouverture + profondeur_tremie_ouverture)
        
        # Déterminer les indices des girons (marches) qui se trouvent sous l'ouverture de la trémie
        # Un giron est à X_i = i * giron_utilise. Le nez de marche est à (i*giron, (i+1)*HCM).
        # On doit vérifier pour chaque marche dont le nez est sous l'ouverture de la trémie.
        
        # L'approche la plus simple et réglementaire est de mesurer à partir du nez de chaque marche.
        # On va vérifier les marches dont le nez est APRÈS le début de la trémie
        # et AVANT la fin de la trémie.
        
        # On itère de la première contremarche (i=1) à la dernière (nombre_contremarches)
        for i in range(1, nombre_contremarches + 1):
            # Coordonnée horizontale (X) du nez de la marche 'i' (qui correspond à la fin du (i-1)ième giron)
            x_nez_marche = (i - 1) * giron_utilise
            # Coordonnée verticale (Y) du nez de la marche 'i' (hauteur de la contremarche 'i')
            y_nez_marche = i * hauteur_reelle_contremarche

            # Vérifier si ce nez de marche se trouve sous l'ouverture de la trémie
            # Un nez de marche est "sous" la trémie si son X est entre le début et la fin de l'ouverture
            if x_nez_marche >= position_tremie_ouverture and x_nez_marche <= (position_tremie_ouverture + profondeur_tremie_ouverture):
                
                # La hauteur du point le plus bas de l'obstacle au-dessus de ce nez de marche.
                # Ce point est à la hauteur totale de l'escalier (plafond) moins l'épaisseur du plancher supérieur.
                # MAIS seulement si la position horizontale est dans l'ouverture.
                
                # Le code de construction dit que l'échappée se mesure verticalement au-dessus du nez de marche.
                # Si le nez de marche est à `x_nez_marche` de l'origine de l'escalier,
                # et que le plafond est à `hauteur_totale_escalier`
                # et que la trémie commence à `position_tremie_ouverture`
                # et qu'elle a une profondeur de `profondeur_tremie_ouverture`.
                
                # L'échappée est la hauteur verticale de la surface de marche à l'objet le plus bas au-dessus.
                # L'objet le plus bas est le bas de la structure de l'étage supérieur.
                # Le bas de la structure est à `hauteur_totale_escalier - epaisseur_plancher_sup`.
                
                # Echappée verticale au nez de cette marche
                current_echappee_val = (hauteur_totale_escalier - epaisseur_plancher_sup) - y_nez_marche
                
                # Si cette valeur est plus petite que la min_echappee_calculee actuelle, la mettre à jour
                min_echappee_calculee = min(min_echappee_calculee, current_echappee_val)

        # Après avoir vérifié toutes les marches sous la trémie, vérifier la conformité.
        if min_echappee_calculee == float('inf'): # Aucune marche n'était sous la trémie ou calcul non pertinent
            results["echappee_message"] = "Trémie hors zone ou données manquantes."
            min_echappee_calculee = 0.0 # Pour afficher un 0 si non calculé, mais le message l'explique
        elif min_echappee_calculee < echappee_min_reg:
            results["echappee_message"] = "NON CONFORME"
            warnings.append(f"Échappée calculée ({decimal_to_fraction_str(min_echappee_calculee, loaded_app_preferences_dict)}\") est inférieure à la norme ({decimal_to_fraction_str(echappee_min_reg, loaded_app_preferences_dict)}\").")
            is_conform = False
        else:
            results["echappee_message"] = "OK"
    else:
        results["echappee_message"] = "Données trémie incomplètes" # Ou non pertinentes si profondeur = 0

    # --- 9. Vérification Longueur Disponible ---
    if espace_disponible > 0:
        if longueur_calculee_escalier > espace_disponible:
            results["longueur_disponible_message"] = "DÉPASSE ESPACE DISPO"
            warnings.append(f"Longueur de l'escalier ({decimal_to_fraction_str(longueur_calculee_escalier, loaded_app_preferences_dict)}\") dépasse l'espace disponible ({decimal_to_fraction_str(espace_disponible, loaded_app_preferences_dict)}\").")
            is_conform = False
        else:
            results["longueur_disponible_message"] = "OK"
    else:
        results["longueur_disponible_message"] = "Espace non renseigné"
        warnings.append("L'espace disponible n'est pas renseigné, la longueur de l'escalier n'est pas vérifiée.")

    # --- 10. Vérification Angle ---
    angle_standard_max = constants.ANGLE_CONFORT_STANDARD_MAX
    angle_raide_max = constants.ANGLE_CONFORT_RAIDE_MAIS_CONFORME_MAX

    if angle_escalier > angle_raide_max:
        results["angle_message"] = "TRÈS RAIDE"
        warnings.append(f"L'angle de l'escalier ({angle_escalier:.2f}°) est très raide (recommandé <{angle_raide_max}°).")
        is_conform = False
    elif angle_escalier > angle_standard_max:
        results["angle_message"] = "Confort Limité"
        warnings.append(f"L'angle de l'escalier ({angle_escalier:.2f}°) a un confort limité (recommandé <{angle_standard_max}°).")
    else:
        results["angle_message"] = "OPTIMAL"

    # --- 11. Calcul de l'écart de hauteur totale (si le nombre de CM a été ajusté) ---
    hauteur_totale_recalculee_par_cm = hauteur_reelle_contremarche * nombre_contremarches
    ecart_hauteur = hauteur_totale_escalier - hauteur_totale_recalculee_par_cm
    
    if abs(ecart_hauteur) > (1/64): # Si l'écart est supérieur à 1/64 de pouce (petite tolérance pour flottants)
        results["hauteur_totale_ecart_message"] = f"Écart: {decimal_to_fraction_str(ecart_hauteur, loaded_app_preferences_dict)}\""
        warnings.append(f"La hauteur totale saisie ({decimal_to_fraction_str(hauteur_totale_escalier, loaded_app_preferences_dict)}\") diffère de la hauteur réelle de {decimal_to_fraction_str(ecart_hauteur, loaded_app_preferences_dict)}\" (Hauteur CM * Nb CM).")
        # Cet écart n'est pas nécessairement une non-conformité majeure, mais un avertissement.
    else:
        results["hauteur_totale_ecart_message"] = "Nul"

    # --- Remplir le dictionnaire de résultats final ---
    results["hauteur_totale_escalier"] = hauteur_totale_escalier
    results["hauteur_reelle_contremarche"] = hauteur_reelle_contremarche
    results["giron_utilise"] = giron_utilise
    results["nombre_contremarches"] = nombre_contremarches
    results["nombre_girons"] = nombre_girons
    results["longueur_calculee_escalier"] = longueur_calculee_escalier
    results["angle_escalier"] = angle_escalier
    results["longueur_limon_approximative"] = longueur_limon_approximative
    results["min_echappee_calculee"] = min_echappee_calculee
    results["blondel_value"] = blondel_value

    return {"results": results, "warnings": warnings, "is_conform": is_conform}

from core.constants import POUCE_EN_CM, TOLERANCE_MESURE_LASER
from utils.formatting import parser_fraction


def calculer_hauteur_totale_par_laser(hls_str, hg_str, hd_str, bg_str, bd_str, preferences):
    """
    Calcule la hauteur totale d'escalier à partir de 4 mesures laser + hauteur laser au sol.
    Retourne un dictionnaire avec la hauteur en pouces, en mètres, et des observations.
    """
    try:
        hls = parser_fraction(hls_str)
        hg = parser_fraction(hg_str)
        hd = parser_fraction(hd_str)
        bg = parser_fraction(bg_str)
        bd = parser_fraction(bd_str)

        haut = (hg + hd) / 2
        bas = (bg + bd) / 2

        hauteur_totale_pouces = haut - bas + hls
        hauteur_metres = hauteur_totale_pouces * POUCE_EN_CM / 100

        observations = []
        if abs(hg - hd) > TOLERANCE_MESURE_LASER:
            observations.append("Différence significative entre HG et HD. Vérifiez le niveau supérieur.")
        if abs(bg - bd) > TOLERANCE_MESURE_LASER:
            observations.append("Différence significative entre BG et BD. Vérifiez le niveau inférieur.")

        return {
            "hauteur_totale_calculee_pouces": hauteur_totale_pouces,
            "hauteur_totale_calculee_metres": hauteur_metres,
            "observations": observations
        }

    except Exception as e:
        return {
            "erreur": f"Erreur dans le calcul laser : {str(e)}",
            "hauteur_totale_calculee_pouces": 0.0,
            "hauteur_totale_calculee_metres": 0.0,
            "observations": []
        }