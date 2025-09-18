# core/file_operations.py
import json
import os
from core import constants

def load_application_preferences():
    """Charge les préférences depuis le fichier JSON, ou retourne les valeurs par défaut."""
    if os.path.exists(constants.DEFAULTS_FILE):
        try:
            with open(constants.DEFAULTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return constants.DEFAULT_APP_PREFERENCES.copy()
    else:
        return constants.DEFAULT_APP_PREFERENCES.copy()

def save_application_preferences(preferences: dict):
    """Sauvegarde les préférences dans le fichier JSON."""
    os.makedirs(os.path.dirname(constants.DEFAULTS_FILE), exist_ok=True)
    with open(constants.DEFAULTS_FILE, "w") as f:
        json.dump(preferences, f, indent=4)
