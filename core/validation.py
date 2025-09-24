# Fichier: Calcul_escalierPy/core/validation.py
# Contenu actuel (vérifié et validé)

from tkinter import messagebox # Dépendance à Tkinter pour les messages
from utils.formatting import parser_fraction

def validate_generic_fraction_format(value_str, field_name="Ce champ", can_be_empty=False, parent_window=None):
    """
    Valide le format de fraction générique.
    'parent_window' est la fenêtre parente pour le messagebox.
    """
    if not value_str.strip():
        if can_be_empty:
            return True
        messagebox.showerror("Erreur Format", f"{field_name} ne peut être vide.", parent=parent_window)
        return False
    try:
        parser_fraction(value_str) # Utilise la fonction de utils.formatting
        return True
    except ValueError as e:
        messagebox.showerror(f"Erreur Format ({field_name})", str(e), parent=parent_window)
        return False

# Fonctions de validation spécifiques
# Elles devraient maintenant toutes accepter 'parent_window' pour le passer à validate_generic_fraction_format

def validate_hauteur_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Hauteur totale directe", parent_window=parent_window)

def validate_hg_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Valeur HG (laser)", parent_window=parent_window)

def validate_hd_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Valeur HD (laser)", parent_window=parent_window)

def validate_bg_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Valeur BG (laser)", parent_window=parent_window)

def validate_bd_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Valeur BD (laser)", parent_window=parent_window)

def validate_laser_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Hauteur du laser au sol", parent_window=parent_window)

def validate_giron_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Giron souhaité", can_be_empty=False, parent_window=parent_window)

def validate_longueur_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Espace disponible", can_be_empty=True, parent_window=parent_window)

def validate_epaisseur_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Épaisseur marche", can_be_empty=False, parent_window=parent_window)

def validate_nez_marche_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Largeur nez de marche", can_be_empty=False, parent_window=parent_window)

def validate_epaisseur_contremarche_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Épaisseur contremarche", can_be_empty=False, parent_window=parent_window)

def validate_epaisseur_plancher_format(value_str, field_name="Épaisseur plancher", parent_window=None):
    return validate_generic_fraction_format(value_str, field_name, can_be_empty=False, parent_window=parent_window)

def validate_longueur_tremie_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Longueur trémie", can_be_empty=True, parent_window=parent_window)

def validate_position_tremie_format(value_str, parent_window=None):
    return validate_generic_fraction_format(value_str, "Position trémie", can_be_empty=True, parent_window=parent_window)
