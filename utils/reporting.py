from core import constants
from .formatting import decimal_to_fraction_str

def generer_texte_trace(resultats_calcul, app_preferences):
    if not resultats_calcul or 'hauteur_reelle_contremarche' not in resultats_calcul:
        return "Aucun résultat de calcul disponible pour générer le tracé."

    try:
        h_reel = resultats_calcul['hauteur_reelle_contremarche']
        giron = resultats_calcul.get('giron_utilise', 0)
        kwargs = resultats_calcul.get('kwargs', {})
        ep_marche = kwargs.get('epaisseur_marche', 0)
        ep_plancher_sup = kwargs.get('epaisseur_plancher_sup', 0)

        def df(value):
            return decimal_to_fraction_str(value, app_preferences)

        h_cm_bas = h_reel - ep_marche
        h_cm_haut = h_reel # Le limon arrive au niveau du plancher fini, donc on n'ajoute rien.
                           # L'ajustement se fait en coupant le bas du limon.
        
        report_lines = [
            "--- INSTRUCTIONS DE TRAÇAGE DU LIMON ---",
            f"Basé sur : H. Contremarche = {df(h_reel)}, Giron = {df(giron)}",
            f"Ép. Marche = {df(ep_marche)}",
            "-"*40,
            "ATTENTION : Toujours tracer sur la face 'côté mur' du limon.",
            "",
            "**Pour un LIMON GAUCHE (vue de face) :**",
            "1. Commencez le traçage par le HAUT de l'escalier.",
            "2. Tracez la PREMIÈRE CONTREMARCHE (en haut) avec une hauteur de :",
            f"   -> {df(h_reel)} (hauteur de base)",
            "3. Continuez en traçant alternativement le giron et la contremarche de base.",
            "4. Tracez la DERNIÈRE CONTREMARCHE (en bas) avec une hauteur de :",
            f"   -> {df(h_cm_bas)} (hauteur de base - épaisseur de la marche)",
            "",
            "**Pour un LIMON DROIT (vue de face) :**",
            "1. Commencez le traçage par le BAS de l'escalier.",
            "2. Tracez la PREMIÈRE CONTREMARCHE (en bas) avec une hauteur de :",
            f"   -> {df(h_cm_bas)} (hauteur de base - épaisseur de la marche)",
            "3. Continuez en traçant alternativement le giron et la contremarche de base.",
            "4. Tracez la DERNIÈRE CONTREMARCHE (en haut) avec une hauteur de :",
            f"   -> {df(h_reel)} (hauteur de base)",
            "",
            "--- FIN DES INSTRUCTIONS ---"
        ]
        
        return "\n".join(report_lines)

    except (KeyError, TypeError, ValueError) as e:
        return f"Erreur : Donnée manquante ou invalide pour générer le rapport. ({e})"

def generer_tableau_marches(resultats_calcul, app_preferences):
    # Extraction des valeurs calculées du programme
    hauteur_cm = resultats_calcul.get("hauteur_reelle_contremarche", 0)
    giron = resultats_calcul.get("giron_utilise", 0) 
    nombre_contremarches = resultats_calcul.get("nombre_contremarches", 0)
    nombre_girons = resultats_calcul.get("nombre_girons", 0)
    
    if hauteur_cm <= 0 or giron <= 0 or nombre_contremarches <= 0:
        return "Données insuffisantes pour générer le tableau d'hypoténuse cumulée."
    
    # Calcul de l'hypoténuse unitaire avec les vraies valeurs
    import math
    hypotenuse_unitaire = math.sqrt(hauteur_cm**2 + giron**2)
    
    # Fonctions de formatage
    def df(val):
        return decimal_to_fraction_str(val, app_preferences) if val is not None else "N/A"
    
    def df_mm(val):
        return round(val * 25.4) if val is not None else "N/A"
    
    # Construction du tableau
    tableau_lines = [
        "=== TABLEAU 1: HYPOTÉNUSE CUMULÉE ===",
        "",
        "Chaque valeur correspond à la somme cumulative de l'hypoténuse calculée pour chaque marche.",
        "La première ligne (Marche pied) correspond à la moitié de l'hypoténuse unitaire.",
        "",
        "| **Élément** | **Hypoténuse cumulée (pouces)** | **Hypoténuse cumulée (mm)** |",
        "|-------------|----------------------------------|------------------------------|"
    ]
    
    # Marche pied = moitié de l'hypoténuse unitaire
    marche_pied_cum = hypotenuse_unitaire / 2
    tableau_lines.append(f"| Marche pied | {df(marche_pied_cum)} | {df_mm(marche_pied_cum)} |")
    
    # Marches intermédiaires
    for i in range(2, nombre_girons + 1):
        element_nom = f"Marche {i}"
        hypotenuse_cumulee = marche_pied_cum + (i-1) * hypotenuse_unitaire
        tableau_lines.append(f"| {element_nom} | {df(hypotenuse_cumulee)} | {df_mm(hypotenuse_cumulee)} |")
    
    # Marche tête
    hypotenuse_cumulee_tete = marche_pied_cum + nombre_girons * hypotenuse_unitaire
    tableau_lines.append(f"| Marche tête | {df(hypotenuse_cumulee_tete)} | {df_mm(hypotenuse_cumulee_tete)} |")
    
    return "\n".join(tableau_lines)

def generer_tableau_parametres(resultats_calcul, app_preferences):
    # Extraction des vraies valeurs calculées
    hauteur_totale = resultats_calcul.get("hauteur_totale_escalier", 0)
    giron = resultats_calcul.get("giron_utilise", 0)
    hauteur_cm = resultats_calcul.get("hauteur_reelle_contremarche", 0)
    nombre_contremarches = resultats_calcul.get("nombre_contremarches", 0)
    
    if hauteur_totale <= 0 or giron <= 0 or hauteur_cm <= 0:
        return "Données insuffisantes pour générer le tableau des paramètres de référence."
    
    # Calcul de l'hypoténuse unitaire
    import math
    hypotenuse_unitaire = math.sqrt(hauteur_cm**2 + giron**2)
    
    # Fonctions de formatage
    def df(val):
        return decimal_to_fraction_str(val, app_preferences) if val is not None else "N/A"
    
    def df_mm(val):
        return round(val * 25.4) if val is not None else "N/A"
    
    # Construction du tableau
    tableau_lines = [
        "=== TABLEAU 2: PARAMÈTRES DE RÉFÉRENCE ===",
        "",
        "Ce tableau récapitule l'ensemble des valeurs essentielles utilisées dans le calcul de l'escalier.",
        "",
        "| **Paramètre** | **Valeur (pouces)** | **Valeur (mm)** |",
        "|---------------|---------------------|------------------|",
        f"| Hauteur totale | {df(hauteur_totale)} | {df_mm(hauteur_totale)} |",
        f"| Giron | {df(giron)} | {df_mm(giron)} |",
        f"| Hauteur par contremarche | {df(hauteur_cm)} | {df_mm(hauteur_cm)} |",
        f"| Hypoténuse unitaire | {df(hypotenuse_unitaire)} | {df_mm(hypotenuse_unitaire)} |",
        f"| Nombre de contremarches | {nombre_contremarches} | — |"
    ]
    
    return "\n".join(tableau_lines)
    
