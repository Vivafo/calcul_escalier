# core/formatting.py
from fractions import Fraction

def parser_fraction(value: str) -> float:
    """
    Convertit une chaîne de type '7 1/4' ou '2.5' en float (pouces).
    """
    value = value.strip()
    if " " in value:  # ex: "7 1/4"
        whole, frac = value.split()
        return float(whole) + float(Fraction(frac))
    elif "/" in value:  # ex: "1/2"
        return float(Fraction(value))
    else:
        return float(value)

def decimal_to_fraction_str(value: float, preferences=None) -> str:
    """
    Convertit un float en fraction lisible (ex: 7.25 → '7 1/4').
    Limite volontairement les dénominateurs à 16 pour rester sur des fractions usuelles.
    """
    if value is None:
        return ""

    precision = 16
    frac = Fraction(round(value * precision), precision)
    is_negative = frac < 0
    frac = abs(frac)

    whole, remainder = divmod(frac.numerator, frac.denominator)
    if whole and remainder:
        result = f"{whole} {remainder}/{frac.denominator}"
    elif whole:
        result = str(whole)
    else:
        result = f"{remainder}/{frac.denominator}"

    return f"-{result}" if is_negative and result else result
