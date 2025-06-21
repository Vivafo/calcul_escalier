# Fichier: CalculateurEscalier/utils/formatting.py

import math
# Assurez-vous que constants est importé ou que les valeurs sont définies localement si formatting.py est autonome
try:
    from core import constants
except ImportError:
    # Fallback pour le développement ou les tests si core n'est pas accessible
    class ConstantsFallback:
        DEFAULT_DENOMINATEUR_PRECISION = 16 
        DEFAULT_FORMAT_DECIMAL_PLACES = 2
    constants = ConstantsFallback()

def decimal_to_fraction_str(decimal_val, app_preferences=None, denominator_limit=None):
    """
    Convertit une valeur décimale en une chaîne de caractères représentant une fraction en pouces.
    Ex: 9.25 -> "9 1/4"
    Ajuste la précision du dénominateur en fonction des préférences de l'application.
    Ne retourne PAS le guillemet à la fin.
    """
    if decimal_val is None:
        return "N/A"

    # Gérer les cas de valeurs très proches de zéro mais négatives, affichées comme "0"
    if -0.0001 < decimal_val < 0.0001:
        return "0"

    if denominator_limit is None and app_preferences:
        denominator_limit = app_preferences.get("fraction_precision_denominator", constants.DEFAULT_DENOMINATEUR_PRECISION)
    elif denominator_limit is None:
        denominator_limit = constants.DEFAULT_DENOMINATEUR_PRECISION

    # Limiter le dénominateur aux puissances de 2
    possible_denominators = [2, 4, 8, 16, 32, 64]
    current_denominator_limit = 1
    for d in possible_denominators:
        if d <= denominator_limit:
            current_denominator_limit = d
        else:
            break

    whole = int(math.floor(abs(decimal_val)))
    fraction = abs(decimal_val) - whole

    if fraction == 0:
        return str(int(decimal_val)) # Retourne juste l'entier sans fraction ni guillemet

    # Trouver la meilleure approximation de la fraction
    best_numerator = 0
    best_denominator = 1
    min_diff = fraction

    for denominator in range(1, current_denominator_limit + 1):
        numerator = round(fraction * denominator)
        current_diff = abs(fraction - (numerator / denominator))
        # Si la différence est très petite, considérer comme exact
        if current_diff < min_diff - 1e-9: # Utiliser une tolérance pour la comparaison
            min_diff = current_diff
            best_numerator = numerator
            best_denominator = denominator
            if min_diff < 0.0001: # Assez proche pour arrêter
                break
    
    # Gérer les cas où le numérateur pourrait être le dénominateur (ex: 4/4 devient 1)
    if best_numerator == best_denominator:
        whole += 1
        fraction_str = "" # Pas de partie fractionnaire
    elif best_numerator == 0:
        fraction_str = ""
    else:
        # Simplifier la fraction
        gcd_val = math.gcd(best_numerator, best_denominator)
        best_numerator //= gcd_val
        best_denominator //= gcd_val
        fraction_str = f"{best_numerator}/{best_denominator}"

    if whole == 0:
        if fraction_str:
            return f"-{fraction_str}" if decimal_val < 0 else fraction_str
        else: # Cas où c'est 0.0 et pas de fraction (ou 0/X)
            return "0"
    else:
        if fraction_str:
            # MODIFIÉ: Ne retourne PAS le guillemet ici.
            return f"-{whole} {fraction_str}" if decimal_val < 0 else f"{whole} {fraction_str}"
        else: # Cas où c'est un entier (ex: 5.0)
            return str(int(decimal_val)) # Retourne juste l'entier


def parser_fraction(fraction_str):
    """
    Convertit une chaîne de caractères représentant une valeur en pouces (entier, décimal, ou fraction)
    en une valeur décimale.
    Ex: "10" -> 10.0
    Ex: "9.5" -> 9.5
    Ex: "9 1/2" -> 9.5
    Ex: "1/4" -> 0.25
    Gère aussi les guillemets et les parenthèses si présents.
    """
    if not isinstance(fraction_str, str):
        raise TypeError("L'entrée doit être une chaîne de caractères.")
    
    # REF-011: Nettoyage de la chaîne: supprime les guillemets et les parenthèses.
    # Ceci est la correction clé pour éviter les erreurs de parsing.
    cleaned_str = fraction_str.strip().replace('"', '').replace('(', '').replace(')', '').strip()

    # Si la chaîne est vide après nettoyage
    if not cleaned_str:
        return 0.0 # Ou soulever une erreur, selon le comportement souhaité pour les entrées vides

    if ' ' in cleaned_str:
        # Gère les formats "X Y/Z"
        parts = cleaned_str.split(' ', 1) # Splitte une seule fois pour préserver la fraction
        try:
            whole = float(parts[0])
            fraction_part = parts[1]
            if '/' in fraction_part:
                frac_num, frac_den = map(float, fraction_part.split('/'))
                if frac_den == 0:
                    raise ValueError("Le dénominateur ne peut pas être zéro.")
                return whole + (frac_num / frac_den) if whole >= 0 else whole - (frac_num / frac_den)
            else:
                pass 
        except ValueError:
            pass 

    if '/' in cleaned_str:
        # Gère les formats "Y/Z"
        try:
            numerator, denominator = map(float, cleaned_str.split('/'))
            if denominator == 0:
                raise ValueError("Le dénominateur ne peut pas être zéro.")
            return numerator / denominator
        except ValueError:
            pass 
        
    try:
        # Tente de convertir directement en décimal
        return float(cleaned_str)
    except ValueError:
        raise ValueError(f"Format de valeur '{fraction_str}' invalide.")