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
    hauteur_reelle_contremarche = 0.0

    if changed_var_name == "nombre_cm_manuel_var" and nombre_cm_manuel is not None:
        # Priorité au nombre de contremarches saisi manuellement
        nombre_contremarches = nombre_cm_manuel
    elif changed_var_name == "nombre_marches_manuel_var" and nombre_marches_manuel is not None:
        # Priorité au nombre de marches saisi manuellement
        nombre_contremarches = nombre_marches_manuel + 1
    else:
        # Calcul initial basé sur la hauteur de CM souhaitée
        if hauteur_cm_souhaitee <= 0: # Fallback si HCM souhaitée est invalide ou 0
            hauteur_cm_souhaitee = constants.HAUTEUR_CM_CONFORT_CIBLE
        
        # Calculer le nombre de CM en arrondissant au plus proche entier
        nombre_contremarches = round(hauteur_totale_escalier / hauteur_cm_souhaitee)
        
        # Assurer un minimum de 2 contremarches pour un escalier
        if nombre_contremarches < 2:
            nombre_contremarches = 2

    # Calcul de la hauteur réelle de contremarche après détermination du nombre de CM
    if nombre_contremarches > 0:
        hauteur_reelle_contremarche = hauteur_totale_escalier / nombre_contremarches
    else:
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
    
    # Si le nombre de marches manuel a été forcé, cela a déjà déterminé le nombre de CM,
    # donc le nombre de girons est implicite.
    # Dans la logique actuelle, le giron est une entrée souhaitée, pas calculée à partir du nombre de marches.
    # On utilise donc le giron souhaité comme "giron_utilise".

    giron_utilise = giron_souhaite # Par défaut, on utilise le giron souhaité

    # --- 5. Vérification de conformité du Giron ---
    g_min = constants.GIRON_MIN_REGLEMENTAIRE
    g_max = constants.GIRON_MAX_REGLEMENTAIRE # Giron max est plus une recommandation
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
    if longueur_calculee_escalier > 0:
        angle_escalier = math.degrees(math.atan(hauteur_totale_escalier / longueur_calculee_escalier))
    
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
    
    if profondeur_tremie_ouverture > 0 and position_tremie_ouverture >= 0 and giron_utilise > 0 and hauteur_reelle_contremarche > 0:
        # Calculer la hauteur sous le plafond pour la première marche du haut
        # On assume que le haut de l'escalier (dernier giron) est au niveau du plancher supérieur.
        # La hauteur du plafond est la hauteur totale moins l'épaisseur du plancher supérieur.
        hauteur_sous_plafond = hauteur_totale_escalier - epaisseur_plancher_sup

        # Déterminer quelle contremarche est la plus critique sous la trémie
        # La marche critique est celle dont le nez de marche est le plus proche du début de la trémie,
        # mais aussi la plus haute.
        # Le nombre de contremarches *passées* avant la trémie
        # Le "- 1e-9" est pour gérer les flottants et s'assurer que si la position est exactement
        # sur un giron, on considère la marche *après* ce giron comme la critique pour l'échappée.
        marche_critique_idx = math.floor(position_tremie_ouverture / giron_utilise - 1e-9) + 1 # Index de la contremarche (1-based)

        # La hauteur de la contremarche critique (distance verticale du sol au nez de marche)
        hauteur_nez_marche_critique = hauteur_reelle_contremarche * marche_critique_idx

        # La hauteur de l'obstacle (le dessous du plancher supérieur)
        # L'échappée est la distance entre le nez de la marche critique et le dessous du plancher supérieur.
        # Le dessous du plancher supérieur est à (hauteur_totale_escalier - epaisseur_plancher_sup) du sol.
        # Donc, Echappée = (hauteur_totale_escalier - epaisseur_plancher_sup) - hauteur_nez_marche_critique
        # ATTENTION: Il faut s'assurer que l'on considère la "distance du sol" ou "hauteur relative"
        # Simplifié: Si le nez de marche critique est à X de hauteur, et le plafond est à Y de hauteur,
        # l'échappée est Y-X.
        # L'échappée est la hauteur entre le dessus du nez de marche et le dessous de l'obstacle.
        # L'obstacle est à (position_tremie_ouverture + profondeur_tremie_ouverture) du début de l'escalier,
        # MAIS sa hauteur est à Hauteur Totale.
        
        # Le calcul de l'échappée est délicat. Voici une approche standard :
        # L'échappée est la distance verticale entre un point sur la ligne de pente et un point verticalement au-dessus.
        # On cherche le point le plus bas du plafond au-dessus du nez de marche.
        
        # Le point le plus bas du plafond est à `position_tremie_ouverture` en X et `hauteur_totale_escalier` en Y
        # Le point le plus haut du plafond est à `position_tremie_ouverture + profondeur_tremie_ouverture` en X et `hauteur_totale_escalier` en Y
        
        # On doit vérifier pour chaque marche sous la trémie.
        # L'échappée est la distance verticale entre le nez de marche (x, y) et le point le plus bas du linteau de la trémie (x, Y_linteau).
        # Le linteau est à la hauteur totale (plancher haut).
        
        # La marche dont le nez se trouve le plus en avant sous la trémie donne la contremarche critique
        # pour l'échappée si la trémie est au début de l'escalier.
        # Si la trémie est loin dans l'escalier, la hauteur libre se calcule par rapport au point bas de la trémie.
        # On considère que le point le plus restrictif est le début de la trémie.
        
        # Pour simplifier et être robuste: on prend la hauteur du dessus de la marche la plus avancée sous l'ouverture
        # et on la soustrait de la hauteur du plancher supérieur (soit hauteur_totale_escalier).
        # La hauteur de la marche la plus avancée dans l'ouverture est:
        # hauteur_nez_marche = (floor(position_tremie_ouverture / giron_utilise) + 1) * hauteur_reelle_contremarche
        
        # Une autre interprétation, plus courante:
        # L'échappée est la distance verticale entre un point sur la ligne de pente et le point le plus bas de l'obstacle (le bas de la trémie).
        # Le bas de la trémie est à (Hauteur Totale - Épaisseur Plancher Supérieur) du sol.
        # Le point critique pour l'échappée est le nez de la marche qui est "sous" le début de la trémie.
        
        # Hauteur du dessous de la trémie par rapport au sol:
        h_dessous_tremie = hauteur_totale_escalier - epaisseur_plancher_sup

        # Giron de la contremarche située juste après le début de la trémie (si le début de la trémie n'est pas pile entre deux girons)
        # C'est la contremarche dont le nez est le plus proche de la position_tremie_ouverture, ou juste après.
        
        # Calcule l'indice (0-basé) de la marche la plus élevée qui est potentiellement sous la trémie
        # Si position_tremie_ouverture est 0, on considère la première marche (index 0)
        # Si position_tremie_ouverture est 10, giron 10, alors c'est la marche 1 (index 1)
        # C'est la (N+1)-ième contremarche qui est au-dessus du N-ième giron.
        
        # Exemple: position_tremie_ouverture = 20", giron = 10"
        # Premier giron à 10", deuxième giron à 20"
        # La marche la plus critique est celle dont le giron est à 20".
        
        # Nombre de girons avant le début de la trémie
        nb_girons_avant_tremie = math.ceil(position_tremie_ouverture / giron_utilise)
        
        # Si la trémie commence avant le premier giron (position_tremie_ouverture = 0 ou très petit)
        # Alors l'échappée est simplement la hauteur sous plafond.
        if nb_girons_avant_tremie == 0:
            min_echappee_calculee = h_dessous_tremie
        else:
            # Hauteur du nez de marche juste avant (ou au début de) la trémie
            hauteur_nez_marche_a_debut_tremie = nb_girons_avant_tremie * hauteur_reelle_contremarche
            
            # Distance horizontale depuis le début de l'escalier jusqu'au nez de cette marche
            distance_horiz_nez_marche = nb_girons_avant_tremie * giron_utilise

            # Calcul de l'échappée verticale au point de la trémie
            # La hauteur du point le plus bas du linteau au-dessus du niveau du sol est h_dessous_tremie.
            # L'échappée est la hauteur du linteau moins la hauteur de la "ligne de marche" à cet endroit.
            
            # On considère le point du bas de la trémie qui est le plus éloigné horizontalement du début de l'escalier.
            # Soit le point (X_tremie_fin, Y_tremie_bas) où Y_tremie_bas est h_dessous_tremie
            # et X_tremie_fin est position_tremie_ouverture + profondeur_tremie_ouverture.
            # On cherche le point sur le nez de marche le plus haut sous ce X_tremie_fin.
            
            # Revoir la formule de l'échappée selon APCHQ:
            # La hauteur libre minimale (échappée) est mesurée verticalement depuis le nez de chaque marche
            # jusqu'au point le plus bas de l'obstacle au-dessus.
            # Le point le plus bas de l'obstacle est le dessous du plancher supérieur.
            # On doit projeter le point du nez de marche sur la verticale qui passe par le début de la trémie.
            # C'est une vérification pour chaque marche sous l'ouverture.
            
            # Simplification: l'échappée critique se trouve souvent au nez de marche directement sous l'arête d'ouverture.
            # Donc, distance verticale entre le nez de marche (à X) et le plafond (à X).
            
            # Position horizontale de chaque nez de marche (pour les girons)
            girons_x_coords = [i * giron_utilise for i in range(1, nombre_girons + 1)] # Girons 1 à N
            
            min_echappee_calculee = float('inf') # Initialiser à l'infini
            
            for i in range(1, nombre_contremarches + 1): # Pour chaque contremarche (et son nez de marche associé)
                hauteur_nez_actuel = i * hauteur_reelle_contremarche
                
                # La coordonnée X du nez de marche est celle du giron précédent si on compte les girons depuis 1
                x_coord_nez_marche = (i-1) * giron_utilise
                
                # On ne vérifie l'échappée que pour les marches sous la trémie
                if x_coord_nez_marche >= position_tremie_ouverture and x_coord_nez_marche < (position_tremie_ouverture + profondeur_tremie_ouverture):
                    # La hauteur du plafond à ce point horizontal est la hauteur totale.
                    # L'échappée est Hauteur Totale (du sol au plafond) - Hauteur du nez de marche actuel.
                    echappee_pour_cette_marche = hauteur_totale_escalier - hauteur_nez_marche_actuel # Simplifié
                    
                    # Un calcul plus précis de l'échappée, comme le ferait un menuisier:
                    # L'échappée est la distance perpendiculaire entre la ligne des nez de marches et le point le plus bas de la trémie.
                    # Ou, plus simplement, la hauteur verticale entre le nez de marche et le point le plus bas de l'ouverture.
                    # Pour un escalier droit, l'échappée est la hauteur entre le "plan du giron" et le "plan du plafond".
                    
                    # Hauteur du point le plus bas de la trémie (verticalement au-dessus de la marche concernée)
                    # La hauteur libre est HLM. La profondeur trémie est L.
                    # Le nez de marche est à (Giron_prec, H_prec). Le point sous plafond est à (X_tremie, H_totale).
                    
                    # Méthode "Triangle Similaire" ou "Pente":
                    # Considérons que la trémie commence à X_start_tremie et se termine à X_end_tremie
                    # La hauteur du dessous du plancher est Y_plafond = HauteurTotale - EpaisseurPlancherSup
                    # La pente de l'escalier est p = hauteur_reelle_contremarche / giron_utilise
                    # La ligne des nez de marche commence à (0, hauteur_reelle_contremarche) et va jusqu'à (longueur_calculee_escalier, hauteur_totale_escalier)
                    
                    # La hauteur du nez de la `marche_idx`-ième marche est `marche_idx * hauteur_reelle_contremarche`.
                    # Sa position horizontale est `(marche_idx - 1) * giron_utilise`.
                    
                    # Le point le plus restrictif est le nez de la marche dont la projection verticale touche le début de la trémie.
                    # Ou, si le code est interprété comme "hauteur libre au-dessus de chaque nez de marche":
                    # Il faut trouver la marche (i) telle que (i-1)*giron < position_tremie ET i*giron > position_tremie
                    # Non, c'est plus simple: la hauteur libre est la distance verticale entre le nez de chaque marche
                    # et l'obstacle. L'obstacle est le dessous du plancher.
                    
                    # Position du nez de la marche qui est à l'extrémité de la trémie (du côté haut de l'escalier)
                    # C'est la marche la plus avancée dans la trémie, qui définit l'échappée.
                    # Le point le plus bas du linteau est à (position_tremie_ouverture, hauteur_totale_escalier - epaisseur_plancher_sup).
                    # Le nez de marche "sous" ce point serait le (N+1)ème nez de marche si N*giron < position_tremie.
                    
                    # Échappée = Hauteur du point le plus bas du linteau (Y) - Hauteur de la marche (Y_marche_proj) à la même position X.
                    # Y_marche_proj est une interpolation le long de la ligne de pente.
                    # Y_marche_proj = (X_point_sur_marche / longueur_calculee_escalier) * hauteur_totale_escalier
                    
                    # Le calcul d'échappée est crucial et souvent mal interprété.
                    # La hauteur libre est la hauteur perpendiculaire entre la ligne des nez de marche et le bord inférieur de la trémie.
                    # Pour simplifier dans l'application, on calcule la hauteur verticale au point critique.
                    
                    # Re-définition simple de l'échappée pour un escalier droit:
                    # Point le plus bas de la structure de l'étage supérieur = épaisseur du plancher supérieur (mesuré depuis le niveau du sol de l'étage supérieur).
                    # Donc, la hauteur du dessous de la trémie par rapport au plancher inférieur est :
                    # Hauteur Plancher Supérieur (depuis le sol du bas) - Epaisseur Plancher Supérieur.
                    # Soit H_obstacle = Hauteur_Totale_Escalier - Epaisseur_Plancher_Supérieur
                    
                    # La distance horizontale du début de l'escalier au point où l'échappée est la plus critique est généralement le début de la trémie.
                    # Calculons la hauteur de la ligne d'emmarchement (nez de marche) à cette position horizontale.
                    
                    if giron_utilise > 0 and hauteur_reelle_contremarche > 0:
                        pente_escalier = hauteur_reelle_contremarche / giron_utilise
                        
                        # Hauteur du point sur la ligne de nez de marche directement sous le début de la trémie
                        hauteur_nez_sous_tremie = pente_escalier * position_tremie_ouverture
                        
                        # L'échappée est la hauteur de la trémie (depuis le sol) moins la hauteur du nez de marche à ce même X.
                        current_echappee = h_dessous_tremie - hauteur_nez_sous_tremie
                        
                        # La trémie a une certaine profondeur. Il faut aussi vérifier si le bout de l'escalier ne touche pas la fin de la trémie.
                        # Mais le point le plus bas de l'obstacle est toujours celui au début de la trémie.
                        
                        # On considère l'échappée comme la hauteur verticale entre le nez de chaque marche
                        # et le point le plus bas de l'obstacle au-dessus.
                        # L'obstacle commence à (position_tremie_ouverture) et va jusqu'à (position_tremie_ouverture + profondeur_tremie_ouverture)
                        # La hauteur de l'obstacle est Hauteur_Totale - Epaisseur_Plancher_Sup.
                        
                        # On doit parcourir les marches qui se trouvent *sous* l'ouverture de la trémie.
                        # La première marche concernée est celle dont le giron est >= position_tremie_ouverture.
                        # La dernière marche concernée est celle dont le giron est < (position_tremie_ouverture + profondeur_tremie_ouverture).
                        
                        start_giron_idx = math.ceil(position_tremie_ouverture / giron_utilise)
                        end_giron_idx = math.floor((position_tremie_ouverture + profondeur_tremie_ouverture) / giron_utilise)
                        
                        for i in range(int(start_giron_idx), int(end_giron_idx) + 1):
                            if i < 0: continue # Ne pas vérifier les indices négatifs
                            if i >= nombre_girons: break # Ne pas dépasser le nombre de girons réels
                            
                            # X-coordonnée du nez de marche (fin du i-ème giron)
                            x_nez_marche = i * giron_utilise
                            # Y-coordonnée du nez de marche (hauteur du dessus du nez de marche)
                            y_nez_marche = (i + 1) * hauteur_reelle_contremarche
                            
                            # La hauteur du plafond à l'horizontale X_nez_marche
                            y_plafond_at_x = hauteur_totale_escalier # Pour un plafond plat à la hauteur totale
                            
                            # L'échappée est la hauteur du plafond moins la hauteur du nez de marche
                            current_echappee = y_plafond_at_x - y_nez_marche
                            
                            if current_echappee < min_echappee_calculee:
                                min_echappee_calculee = current_echappee
                    
                    if min_echappee_calculee == float('inf'): # Si aucune marche n'est sous la trémie, ou données invalides.
                        min_echappee_calculee = None # Indique qu'aucun calcul valide n'a été fait.
                        results["echappee_message"] = "Trémie ou espace insuffisant pour le calcul d'échappée."
                    else:
                        if min_echappee_calculee < echappee_min_reg:
                            results["echappee_message"] = "NON CONFORME"
                            warnings.append(f"Échappée calculée ({decimal_to_fraction_str(min_echappee_calculee, loaded_app_preferences_dict)}\") est inférieure à la norme ({decimal_to_fraction_str(echappee_min_reg, loaded_app_preferences_dict)}\").")
                            is_conform = False
                        else:
                            results["echappee_message"] = "OK"
    else:
        results["echappee_message"] = "Données trémie incomplètes"

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