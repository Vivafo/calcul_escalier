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
    # Cette fonction peut être développée plus tard
    return "Le tableau des marches n'est pas encore implémenté."