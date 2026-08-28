"""Unit conversion helper — analytics endpoints always return weight_kg."""

KG_PER_LB = 0.453592


def kg_to_display(weight_kg: float, unit: str) -> float:
    if unit == "kg":
        return round(weight_kg, 2)
    return round(weight_kg / KG_PER_LB, 2)
