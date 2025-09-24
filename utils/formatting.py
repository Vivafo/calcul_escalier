# Fichier: Calcul_escalierPy/utils/formatting.py

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

# Les dénominateurs impériaux autorisés pour l'affichage des fractions
ALLOWED_DENOMINATORS = {2, 4, 8, 16, 32, 64}


def decimal_to_fraction_str(decimal_val, app_preferences=None, denominator_limit=None):
    """
    Convertit une valeur décimale en représentation fractionnaire impériale.
    Restreint aux dénominateurs standards du système impérial: 2, 4, 8, 16, 32, 64.
    """
    if decimal_val is None:
        return "N/A"

    # Gérer les très petites valeurs proches de zéro pour qu'elles s'affichent comme "0"
    if -0.0001 < decimal_val < 0.0001:
        return "0"

    # Déterminer la limite du dénominateur
    if denominator_limit is None and app_preferences:
        denominator_limit = app_preferences.get("fraction_precision_denominator", 16) # Utilise 16 par défaut si non spécifié
    elif denominator_limit is None:
        denominator_limit = 16 # Fallback si pas de préférences ou limite passée

    # Filtrer les dénominateurs autorisés en fonction de la limite
    available_denominators = [d for d in sorted(list(ALLOWED_DENOMINATORS)) if d <= denominator_limit]
    if not available_denominators:
        available_denominators = [16] # Fallback si la limite est trop basse

    whole = int(math.floor(abs(decimal_val)))
    fraction_part_decimal = abs(decimal_val) - whole

    if fraction_part_decimal == 0:
        return str(int(decimal_val)) # Retourne juste l'entier si pas de partie fractionnaire

    # Trouver la meilleure approximation avec les dénominateurs impériaux
    best_numerator = 0
    best_denominator = 1
    min_diff = fraction_part_decimal # Initialiser avec la fraction elle-même

    for denominator in available_denominators:
        numerator = round(fraction_part_decimal * denominator)
        # S'assurer que le numérateur ne dépasse pas le dénominateur
        if numerator > denominator:
            numerator = denominator # Ex: 8/8 devient 1 entier
        
        current_diff = abs(fraction_part_decimal - (numerator / denominator))
        
        # Utilisez une petite tolérance pour les comparaisons de flottants
        if current_diff < min_diff - 1e-9: # Si la différence est significativement plus petite
            min_diff = current_diff
            best_numerator = numerator
            best_denominator = denominator
            if min_diff < 1e-9: # Si la différence est quasi nulle, on a trouvé la meilleure approximation
                break
        elif abs(current_diff - min_diff) < 1e-9: # Si la différence est égale, préférer un plus petit dénominateur
             if denominator < best_denominator:
                 best_numerator = numerator
                 best_denominator = denominator

    # Gérer les cas où le numérateur est 0 ou égal au dénominateur après arrondi/simplification
    if best_numerator == 0:
        fraction_str = ""
    else:
        # Simplifier la fraction
        gcd_val = math.gcd(best_numerator, best_denominator)
        simplified_num = best_numerator // gcd_val
        simplified_den = best_denominator // gcd_val
        
        if simplified_num == simplified_den: # Si 1/1, 2/2, etc., cela fait un entier
            whole += 1
            fraction_str = ""
        else:
            fraction_str = f"{simplified_num}/{simplified_den}"

    # Construire la chaîne finale
    if whole == 0:
        if fraction_str:
            return f"-{fraction_str}" if decimal_val < 0 else fraction_str
        else:
            return "0" # Si la valeur était initialement 0.x et arrondie à 0
    else:
        if fraction_str:
            return f"-{whole} {fraction_str}" if decimal_val < 0 else f"{whole} {fraction_str}"
        else:
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
        # Tente de convertir directement si c'est déjà un nombre
        try:
            return float(fraction_str)
        except (ValueError, TypeError):
            raise TypeError("L'entrée doit être une chaîne de caractères ou un nombre convertible en float.")
    
    # REF-011: Nettoyage de la chaîne: supprime les guillemets et les parenthèses.
    # Ceci est la correction clé pour éviter les erreurs de parsing.
    cleaned_str = fraction_str.strip().replace('"', '').replace('(', '').replace(')', '').strip()

    # Si la chaîne est vide après nettoyage, renvoyer 0.0 pour éviter des erreurs
    # ou soulever une erreur si une valeur vide n'est pas acceptée dans le contexte appelant
    if not cleaned_str:
        return 0.0

    total_value = 0.0
    
    # Gère les formats "X Y/Z"
    if ' ' in cleaned_str:
        parts = cleaned_str.split(' ', 1) # Splitte une seule fois pour préserver la fraction intacte
        try:
            whole_part = float(parts[0])
            fraction_part_str = parts[1]
            
            if '/' in fraction_part_str:
                frac_num, frac_den = map(float, fraction_part_str.split('/'))
                if frac_den == 0:
                    raise ValueError("Le dénominateur ne peut pas être zéro.")
                total_value = whole_part + (frac_num / frac_den) if whole_part >= 0 else whole_part - (frac_num / frac_den)
                return total_value
            # Si pas de '/', alors ce n'est pas un format X Y/Z valide avec fraction
            # On laisse passer pour tenter le parsing direct de float
        except ValueError:
            pass # Poursuivre la tentative de parsing comme une simple fraction ou un décimal
        
    # Gère les formats "Y/Z" ou les décimaux "X.Y" ou "X"
    if '/' in cleaned_str:
        try:
            numerator, denominator = map(float, cleaned_str.split('/'))
            if denominator == 0:
                raise ValueError("Le dénominateur ne peut pas être zéro.")
            return numerator / denominator
        except ValueError:
            pass # Poursuivre la tentative de parsing comme un décimal
            
    try:
        # Tente de convertir directement en décimal (pour "10", "9.5", etc.)
        return float(cleaned_str)
    except ValueError:
        raise ValueError(f"Format de valeur '{fraction_str}' (nettoyé: '{cleaned_str}') invalide. Attendu: '10', '9.5', '9 1/4' ou '1/2'.")
