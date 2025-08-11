# Fichier: utils/conversion.py

from core import constants
from utils import formatting

def convertir_variables_interface(app_instance, tk_vars_dict, unite_cible_str, prefs):
    """
    Convertit les valeurs des variables Tkinter d'une unité à une autre.
    'unite_cible_str' est soit 'pouces' soit 'cm'.
    """
    if app_instance._is_updating_ui:
        return
    app_instance._is_updating_ui = True

    try:
        # Détermine l'unité source en se basant sur la cible
        unite_source_str = 'cm' if unite_cible_str == 'pouces' else 'pouces'

        for key, var_obj in tk_vars_dict.items():
            valeur_str = var_obj.get()
            if not valeur_str:
                continue

            try:
                valeur_numerique = formatting.parser_fraction(valeur_str)
                
                if unite_source_str == 'pouces' and unite_cible_str == 'cm':
                    # Convertir des pouces en centimètres
                    new_val = valeur_numerique * constants.POUCE_EN_CM
                    var_obj.set(f"{new_val:.2f}")

                elif unite_source_str == 'cm' and unite_cible_str == 'pouces':
                    # Convertir des centimètres en pouces
                    new_val = valeur_numerique / constants.POUCE_EN_CM
                    var_obj.set(formatting.decimal_to_fraction_str(new_val, prefs))

            except (ValueError, TypeError):
                continue
    finally:
        app_instance._is_updating_ui = False
