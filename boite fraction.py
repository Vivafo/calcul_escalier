import tkinter as tk
from tkinter import ttk
from fractions import Fraction

def set_theme_gris_fonce():
    root.configure(bg="#2C2F33")
    style.configure("TFrame", background="#2C2F33")
    style.configure("TLabel", background="#2C2F33", foreground="#F7F7F7", font=("Segoe UI", 10))
    style.configure("TRadiobutton", background="#2C2F33", foreground="#F7F7F7", font=("Segoe UI", 10, "bold"))
    style.configure("TCheckbutton", background="#2C2F33", foreground="#F7F7F7", font=("Segoe UI", 10))
    style.configure("TEntry", fieldbackground="#F7F7F7", background="#F7F7F7", foreground="#222222")
    style.configure("TCombobox", fieldbackground="#F7F7F7", background="#F7F7F7", foreground="#222222")
    label_resultat1.config(foreground="#00FFCC", font=("Segoe UI", 10, "bold"))
    label_resultat2.config(foreground="#F7F7F7")
    label_resultat3.config(foreground="#F7F7F7")

def set_theme_clair():
    root.configure(bg="#A8F5A2")
    style.configure("TFrame", background="#A8F5A2")
    style.configure("TLabel", background="#A8F5A2", foreground="#002060", font=("Segoe UI", 10))
    style.configure("TRadiobutton", background="#A8F5A2", foreground="#1A3E5C", font=("Segoe UI", 10, "bold"))
    style.configure("TCheckbutton", background="#A8F5A2", foreground="#1A3E5C", font=("Segoe UI", 10))
    style.configure("TEntry", fieldbackground="#E6F2E6", background="#E6F2E6", foreground="#222222")
    style.configure("TCombobox", fieldbackground="#E6F2E6", background="#E6F2E6", foreground="#222222")
    label_resultat1.config(foreground="#002060", font=("Segoe UI", 10, "bold"))
    label_resultat2.config(foreground="#002060")
    label_resultat3.config(foreground="#002060")

def update_numerator_options(*args):
    denom = current_denom.get()
    numerators = list(range(1, denom))
    combo_num['values'] = numerators
    if numerators:
        combo_num.set(numerators[0])
    else:
        combo_num.set('')
    calculer_pouces()

def calculer_pouces(*args):
    try:
        pouces = float(entry_pouces.get())
    except ValueError:
        pouces = 0
    try:
        num = int(combo_num.get())
    except ValueError:
        num = 0
    denom = current_denom.get()
    if denom == 0 or num == 0:
        if show_pieds_pouces.get():
            label_resultat1.config(text="Total (Pieds, Pouces, Fraction): —")
        else:
            label_resultat1.config(text="")
        if show_pouces.get():
            label_resultat2.config(text="Total (Pouces, Fraction): —")
        else:
            label_resultat2.config(text="")
        if show_cm.get():
            label_resultat3.config(text="Total (Centimètres): —")
        else:
            label_resultat3.config(text="")
        return
    total_pouces = pouces + num / denom
    pieds = int(total_pouces // 12)
    pouces_restants = int(total_pouces % 12)
    fraction_obj = Fraction(num, denom)
    num_simplified = fraction_obj.numerator
    denom_simplified = fraction_obj.denominator
    fraction_str = f"{num_simplified}/{denom_simplified}" if num_simplified else ""
    pieds_pouces_str = f"{pieds}' {pouces_restants}\" {fraction_str}".strip()
    pouces_str = f"{int(total_pouces)}\" {fraction_str}".strip() if num_simplified else f"{int(total_pouces)}\""
    total_cm = total_pouces * 2.54
    if show_pieds_pouces.get():
        label_resultat1.config(text=f"Total (Pieds, Pouces, Fraction): {pieds_pouces_str}")
    else:
        label_resultat1.config(text="")
    if show_pouces.get():
        label_resultat2.config(text=f"Total (Pouces, Fraction): {pouces_str}")
    else:
        label_resultat2.config(text="")
    if show_cm.get():
        label_resultat3.config(text=f"Total (Centimètres): {total_cm:.2f} cm")
    else:
        label_resultat3.config(text="")

root = tk.Tk()
root.title("Application de Mesures Professionnelle")
root.configure(bg="#A8F5A2")  # Vert doux moderne

style = ttk.Style()
style.theme_use('clam')
style.configure("TLabel", background="#A8F5A2", foreground="#002060", font=("Segoe UI", 10))
style.configure("TFrame", background="#A8F5A2")
style.configure("TRadiobutton", background="#A8F5A2", foreground="#1A3E5C", font=("Segoe UI", 10, "bold"))
style.configure("TCheckbutton", background="#A8F5A2", foreground="#1A3E5C", font=("Segoe UI", 10))
style.configure("TEntry", fieldbackground="#E6F2E6", background="#E6F2E6", foreground="#222222")
style.configure("TCombobox", fieldbackground="#E6F2E6", background="#E6F2E6", foreground="#222222")

main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill='both', expand=True)

# Titre
ttk.Label(main_frame, text="Convertisseur de Mesures", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=5, pady=(0,8))

# Ligne 1 : Pouces entiers
ttk.Label(main_frame, text="Pouces entiers:").grid(row=1, column=0, sticky="e", padx=2)
entry_pouces = ttk.Entry(main_frame, width=6)
entry_pouces.grid(row=1, column=1, padx=2)
entry_pouces.bind("<KeyRelease>", calculer_pouces)

# Ligne 2 : Dénominateur (radio boutons modernes)
ttk.Label(main_frame, text="Dénominateur:").grid(row=2, column=0, sticky="e", padx=2)
current_denom = tk.IntVar(value=8)
denoms = [2, 4, 8, 16]
for i, d in enumerate(denoms):
    ttk.Radiobutton(main_frame, text=f"/{d}", value=d, variable=current_denom, command=update_numerator_options).grid(row=2, column=1+i, sticky="w", padx=2)

# Ligne 3 : Numérateur
ttk.Label(main_frame, text="Numérateur:").grid(row=3, column=0, sticky="e", padx=2)
combo_num = ttk.Combobox(main_frame, width=5, state="readonly")
combo_num.grid(row=3, column=1, padx=2, sticky="w")
combo_num.bind("<<ComboboxSelected>>", calculer_pouces)

# Résultats
label_resultat1 = ttk.Label(main_frame, text="Total (Pieds, Pouces, Fraction): —", font=("Segoe UI", 10, "bold"))
label_resultat1.grid(row=4, column=0, columnspan=5, pady=(12,0), sticky="w")
label_resultat2 = ttk.Label(main_frame, text="Total (Pouces, Fraction): —", font=("Segoe UI", 10))
label_resultat2.grid(row=5, column=0, columnspan=5, sticky="w")
label_resultat3 = ttk.Label(main_frame, text="Total (Centimètres): —", font=("Segoe UI", 10))
label_resultat3.grid(row=6, column=0, columnspan=5, sticky="w")

# Ajout des cases à cocher pour choisir les informations à afficher
show_pieds_pouces = tk.BooleanVar(value=True)
show_pouces = tk.BooleanVar(value=True)
show_cm = tk.BooleanVar(value=True)

ttk.Label(main_frame, text="Afficher:").grid(row=7, column=0, sticky="e", pady=(10,0), padx=2)
ttk.Checkbutton(main_frame, text="Pieds, Pouces, Fraction", variable=show_pieds_pouces, command=calculer_pouces).grid(row=7, column=1, columnspan=2, sticky="w", pady=(10,0), padx=2)
ttk.Checkbutton(main_frame, text="Pouces, Fraction", variable=show_pouces, command=calculer_pouces).grid(row=8, column=1, columnspan=2, sticky="w", pady=(0,0), padx=2)
ttk.Checkbutton(main_frame, text="Centimètres", variable=show_cm, command=calculer_pouces).grid(row=9, column=1, columnspan=2, sticky="w", pady=(0,0), padx=2)

# Boutons pour changer le thème
btn_theme_dark = ttk.Button(main_frame, text="Mode gris foncé", command=set_theme_gris_fonce)
btn_theme_dark.grid(row=10, column=0, columnspan=2, pady=(15,0))
btn_theme_light = ttk.Button(main_frame, text="Mode clair", command=set_theme_clair)
btn_theme_light.grid(row=10, column=2, columnspan=2, pady=(15,0))

# Initialisation
update_numerator_options()

root.mainloop()
# This code is a complete tkinter application that allows users to convert measurements
# between feet, inches, and centimeters, with options for fractional inches.