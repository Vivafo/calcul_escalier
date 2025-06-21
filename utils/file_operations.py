# Fichier: CalculateurEscalier/utils/file_operations.py

import json
import os
from core import constants

def load_application_preferences():
    """
    Charge les préférences de l'application depuis un fichier JSON.
    Retourne les préférences chargées ou les préférences par défaut si le fichier n'existe pas.
    """
    preferences = {}
    if os.path.exists(constants.DEFAULTS_FILE):
        try:
            with open(constants.DEFAULTS_FILE, 'r', encoding='utf-8') as f:
                preferences = json.load(f)
        except json.JSONDecodeError:
            print(f"Erreur: Le fichier de préférences '{constants.DEFAULTS_FILE}' est corrompu. Utilisation des préférences par défaut.")
        except Exception as e:
            print(f"Erreur inattendue lors du chargement des préférences: {e}. Utilisation des préférences par défaut.")
    
    # S'assurer que toutes les clés par défaut sont présentes
    # REF-014: Utilisation de DEFAULT_APP_PREFERENCES au lieu de FALLBACK_PREFERENCES
    merged_preferences = constants.DEFAULT_APP_PREFERENCES.copy() 
    merged_preferences.update(preferences)
    return merged_preferences

def save_application_preferences(preferences):
    """
    Sauvegarde les préférences de l'application dans un fichier JSON.
    Crée le dossier 'data' si nécessaire.
    """
    data_dir = os.path.dirname(constants.DEFAULTS_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    try:
        with open(constants.DEFAULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(preferences, f, indent=4)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des préférences: {e}")

def charger_projet(app):
    """Charge les données du projet dans l'application."""
    # Fonctionnalité future : Implémenter le chargement d'un projet
    messagebox.showinfo("Charger Projet", "La fonction de chargement de projet est en développement !", parent=app)

def sauvegarder_projet(data, app):
    """Sauvegarde les données du projet."""
    # Fonctionnalité future : Implémenter la sauvegarde d'un projet
    messagebox.showinfo("Sauvegarder Projet", "La fonction de sauvegarde de projet est en développement !", parent=app)