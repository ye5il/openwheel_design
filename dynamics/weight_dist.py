def calculate_cog_height(masses_kg, heights_mm):
    total_mass = sum(masses_kg)
    weighted_h = sum(m * h for m, h in zip(masses_kg, heights_mm))
    return round(weighted_h / total_mass, 1)

def calculate_weight_distribution(masses_kg, x_positions_mm, wheelbase_mm):
    total = sum(masses_kg)
    front = sum(m for m, x in zip(masses_kg, x_positions_mm) if x < wheelbase_mm / 2)
    return {
        "front_pct": round(front / total * 100, 1),
        "rear_pct": round((total - front) / total * 100, 1)
    }

def estimate_polar_moment(masses_kg, distances_mm):
    Iz = sum(m * (r / 1000)**2 for m, r in zip(masses_kg, distances_mm))
    return {
        "Iz_kg_m2": round(Iz, 2),
        "interpretation": "agile" if Iz < 80 else "stable"
    }