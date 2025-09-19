import math
from core import constants
from core.formatting import decimal_to_fraction_str



def generer_texte_trace(resultats_calcul, app_preferences):
    if not resultats_calcul or 'hauteur_reelle_contremarche' not in resultats_calcul:
        return "Aucun résultat de calcul disponible pour générer le tracé."

    try:
        h_reel = resultats_calcul['hauteur_reelle_contremarche'] or 0
        giron = resultats_calcul.get('giron_utilise', 0) or 0
        kwargs = resultats_calcul.get('kwargs', {})
        ep_marche = kwargs.get('epaisseur_marche', 0) or 0
        ep_plancher_sup = kwargs.get('epaisseur_plancher_sup', 0) or 0
        nombre_cm = resultats_calcul.get('nombre_contremarches', 0) or 0
        nombre_girons = resultats_calcul.get('nombre_girons')
        if nombre_girons in (None, 0) and nombre_cm:
            nombre_girons = max(nombre_cm - 1, 0)
        longueur_totale = resultats_calcul.get('longueur_calculee_escalier', 0) or 0
        blondel_value = resultats_calcul.get('blondel_value')

        def df(value):
            return decimal_to_fraction_str(value, app_preferences) if value not in (None, 0) else "N/A"

        def df_mm(value):
            return f"{value * constants.POUCE_EN_MM:.1f}" if value not in (None, 0) else "N/A"

        def mesure(label, valeur):
            if valeur in (None, 0):
                return f"  {label:<30}: N/A"
            return f"  {label:<30}: {df(valeur):>8}  (≈ {df_mm(valeur)} mm)"

        def info(label, valeur):
            return f"  {label:<30}: {valeur if valeur not in (None, 0) else 'N/A'}"

        h_cm_bas = max(h_reel - ep_marche, 0)
        largeur_document = 76
        ligne_entete = "=" * largeur_document
        ligne_section = "-" * largeur_document

        hypot_unitaire = math.sqrt((h_reel ** 2) + (giron ** 2)) if h_reel and giron else 0
        diagonale_lines = [
            "SECTION DIAGONALE — HYPOTÉNUSES",
            ligne_section,
        ]
        if hypot_unitaire:
            diagonale_lines.append(
                f"  Hypoténuse unitaire : {df(hypot_unitaire)}  (≈ {df_mm(hypot_unitaire)} mm)")
            diagonale_lines.append("  ---------------------------------------------------------------")
            diagonale_lines.append("  | CM # | Longueur cumulée (po) | Longueur cumulée (mm) |")
            diagonale_lines.append("  ---------------------------------------------------------------")
            cumul = hypot_unitaire
            total_cm = max(int(nombre_cm), 1)
            for idx in range(1, total_cm + 1):
                diagonale_lines.append(
                    f"  | CM {idx:>2} | {df(cumul):>21} | {df_mm(cumul):>21} |")
                cumul += hypot_unitaire
            diagonale_lines.append("  ---------------------------------------------------------------")
        else:
            diagonale_lines.append("  Hypoténuse non calculable (données insuffisantes)")
        diagonale_lines.append("")

        report_lines = [
            ligne_entete,
            "PLAN DE TRAÇAGE DU LIMON".center(largeur_document),
            ligne_entete,
            "",
            "PARAMÈTRES PRINCIPAUX",
            ligne_section,
            info("Nombre de contremarches", nombre_cm),
            info("Nombre de girons", nombre_girons),
            mesure("Hauteur réelle contremarche", h_reel),
            mesure("Giron utilisé", giron),
            mesure("Épaisseur de marche", ep_marche),
            mesure("Épaisseur plancher supérieur", ep_plancher_sup),
            mesure("Longueur développée", longueur_totale),
            mesure("Valeur Blondel (2H+G)", blondel_value),
            "",
        ] + diagonale_lines + [
            "POINTS DE CONTRÔLE",
            ligne_section,
            mesure("Contremarche départ (bas)", h_cm_bas),
            mesure("Contremarche arrivée (haut)", h_reel),
            info("Tolérance hauteur successive", f"± {df(constants.HAUTEUR_CM_TOLERANCE_SUCCESSIVE)}"),
            "",
            "TRAÇAGE SUR LIMON GAUCHE (vue face)",
            ligne_section,
            "  1. Positionner le limon avec la face mur accessible.",
            "  2. Aligner votre gabarit sur la marche d'arrivée (haut).",
            f"  3. Reporter la première contremarche: {df(h_reel)}.",
            f"  4. Alterner giron ({df(giron)}) et contremarche ({df(h_reel)}) pour chaque marche.",
            f"  5. Ajuster la dernière contremarche en bas: {df(h_cm_bas)} (retirer l'épaisseur de marche).",
            "",
            "TRAÇAGE SUR LIMON DROIT (vue face)",
            ligne_section,
            "  1. Démarrer le traçage par le bas du limon.",
            f"  2. Première contremarche (bas): {df(h_cm_bas)}.",
            f"  3. Alterner giron ({df(giron)}) et contremarche ({df(h_reel)}).",
            f"  4. Vérifier la dernière contremarche en haut: {df(h_reel)}.",
            "",
            "RAPPELS AVANT DÉCOUPE",
            ligne_section,
            "  - Vérifier les cotes réelles sur chantier avant découpe finale.",
            "  - Contrôler l'équerrage du limon sur deux marches successives.",
            "  - Identifier clairement les faces mur / extérieur sur la pièce.",
            "",
            "Révision générée automatiquement par le Calculateur Escalier.",
            ligne_entete
        ]

        return "\n".join(report_lines)

    except (KeyError, TypeError, ValueError) as e:
        return f"Erreur : Donnée manquante ou invalide pour générer le rapport. ({e})"

def generer_tableau_marches(resultats_calcul, app_preferences):
    hauteur_cm = resultats_calcul.get("hauteur_reelle_contremarche", 0)
    giron = resultats_calcul.get("giron_utilise", 0)
    nombre_contremarches = resultats_calcul.get("nombre_contremarches", 0)

    if hauteur_cm <= 0 or giron <= 0 or nombre_contremarches <= 0:
        return "Données insuffisantes pour générer le tableau d'hypoténuse cumulée."

    import math
    hypotenuse_unitaire = math.sqrt(hauteur_cm**2 + giron**2)

    def df(val):
        return decimal_to_fraction_str(val, app_preferences) if val is not None else "N/A"

    def df_mm(val):
        return round(val * constants.POUCE_EN_MM) if val is not None else "N/A"

    nombre_cm = max(int(nombre_contremarches), 0)

    tableau_lines = [
        "=== TABLEAU 1: HYPOTÉNUSE CUMULÉE ===",
        "",
        "Chaque valeur correspond à la somme cumulative de l'hypoténuse calculée pour chaque contremarche.",
        "La première ligne (Contremarche pied) correspond à la moitié de l'hypoténuse unitaire.",
        "",
        "| **Contremarche** | **Hypoténuse cumulée (pouces)** | **Hypoténuse cumulée (mm)** |",
        "|-----------------|----------------------------------|------------------------------|"
    ]

    marche_pied_cum = hypotenuse_unitaire / 2
    tableau_lines.append(f"| Contremarche 1 (pied) | {df(marche_pied_cum)} | {df_mm(marche_pied_cum)} |")

    for cm_index in range(2, nombre_cm + 1):
        hypotenuse_cumulee = marche_pied_cum + (cm_index - 1) * hypotenuse_unitaire
        label = f"Contremarche {cm_index}"
        if cm_index == nombre_cm:
            label += " (tête)"
        tableau_lines.append(f"| {label} | {df(hypotenuse_cumulee)} | {df_mm(hypotenuse_cumulee)} |")

    return "\n".join(tableau_lines)
def generer_tableau_parametres(resultats_calcul, app_preferences):
    hauteur_totale = resultats_calcul.get("hauteur_totale_escalier", 0)
    giron = resultats_calcul.get("giron_utilise", 0)
    hauteur_cm = resultats_calcul.get("hauteur_reelle_contremarche", 0)
    nombre_contremarches = resultats_calcul.get("nombre_contremarches", 0)
    nombre_girons = resultats_calcul.get("nombre_girons", 0)

    if hauteur_totale <= 0 or giron <= 0 or hauteur_cm <= 0:
        return "Données insuffisantes pour générer le tableau des paramètres de référence."

    import math
    hypotenuse_unitaire = math.sqrt(hauteur_cm**2 + giron**2)

    def df(val):
        return decimal_to_fraction_str(val, app_preferences) if val is not None else "N/A"

    def df_mm(val):
        return round(val * constants.POUCE_EN_MM) if val is not None else "N/A"

    stride = giron
    hcm = hauteur_cm
    nombre_girons_effectif = nombre_girons if nombre_girons else max(nombre_contremarches - 1, 0)
    longueur_totale = nombre_girons_effectif * stride
    tableau_lines = [
        "=== TABLEAU 2: PARAMÈTRES DE RÉFÉRENCE ===",
        "",
        f"Nombre de contremarches : {nombre_contremarches}",
        f"Hauteur réelle contremarche : {df(hcm)} (≈ {df_mm(hcm)} mm)",
        f"Giron utilisé : {df(stride)} (≈ {df_mm(stride)} mm)",
        f"Longueur totale escalier : {df(longueur_totale)}",
        f"Hypoténuse unitaire : {df(hypotenuse_unitaire)} (≈ {df_mm(hypotenuse_unitaire)} mm)",
    ]

    return "\n".join(tableau_lines)

