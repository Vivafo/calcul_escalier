class StairCalculator:
    @staticmethod
    def adjust_from_height(height_total, giron_standard=9.25):
        """Calcule NM, NG, HCM à partir de la hauteur totale"""
        # Estimation initiale avec hauteur de contremarche idéale (7")
        nb_cm_ideal = round(height_total / 7.0)
        hcm = height_total / nb_cm_ideal
        nb_marches = nb_cm_ideal - 1
        return {
            "nombre_contremarches": nb_cm_ideal,
            "nombre_marches": nb_marches,
            "nombre_girons": nb_marches,
            "hauteur_cm": hcm,
            "giron": giron_standard,
            "longueur_totale": nb_marches * giron_standard
        }

    @staticmethod
    def adjust_from_marches(nb_marches, hauteur_totale=None, hcm=None, giron=9.25):
        """Ajuste les valeurs quand le nombre de marches change"""
        nb_cm = nb_marches + 1
        if hauteur_totale:
            new_hcm = hauteur_totale / nb_cm
        elif hcm:
            hauteur_totale = hcm * nb_cm
        else:
            hauteur_totale = 7 * nb_cm  # Valeur par défaut
            new_hcm = 7
        
        return {
            "nombre_contremarches": nb_cm,
            "nombre_marches": nb_marches,
            "nombre_girons": nb_marches,
            "hauteur_cm": new_hcm if hauteur_totale else hcm,
            "hauteur_totale": hauteur_totale,
            "giron": giron,
            "longueur_totale": nb_marches * giron
        }
