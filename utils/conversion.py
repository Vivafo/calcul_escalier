"""
Module de conversion d'unités pour le Calculateur d'Escalier VIP.
Permet de convertir dynamiquement toutes les variables d'interface Tkinter
lors du changement d'unité (Pouces <-> Centimètres).
"""

POUCE_EN_CM = 2.54


def convertir_variables_interface(tk_input_vars_dict, unite_source, unite_cible):
    """
    Convertit toutes les variables d'entrée de l'interface Tkinter d'une unité à l'autre.
    tk_input_vars_dict : dict {nom_champ: tk.StringVar}
    unite_source : "Pouces" ou "Centimètres"
    unite_cible : "Pouces" ou "Centimètres"
    """
    if unite_source == unite_cible:
        return
    for var in tk_input_vars_dict.values():
        try:
            val = var.get().replace(",", ".")
            if not val.strip():
                continue
            v = eval(val) if "/" not in val else eval(val.replace("/", "/1.0/"))
            if unite_source == "Pouces" and unite_cible == "Centimètres":
                v = v * POUCE_EN_CM
            elif unite_source == "Centimètres" and unite_cible == "Pouces":
                v = v / POUCE_EN_CM
            var.set(str(round(v, 3)))
        except Exception:
            continue
