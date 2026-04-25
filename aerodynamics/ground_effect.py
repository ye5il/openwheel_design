import math

def estimate_ground_effect_factor(ride_height_mm, reference_height_mm=150):
    if ride_height_mm < 10:
        return 3.0
    factor = (reference_height_mm / ride_height_mm) ** 0.5
    return round(min(factor, 3.0), 3)

def calculate_diffuser_downforce(diffuser_angle_deg, area_m2, speed_kmh):
    v = speed_kmh / 3.6
    eff = min(1.0, diffuser_angle_deg / 15)
    base = 0.5 * 1.225 * v**2 * area_m2 * 1.5
    df = base * eff
    return {
        "downforce_N": round(df, 0),
        "diffuser_angle_deg": diffuser_angle_deg,
        "efficiency": eff
    }

def check_ride_height_aero(ride_height_mm):
    return {
        "ride_height_mm": ride_height_mm,
        "ground_effect_strong": ride_height_mm < 30,
        "bottoming_risk": ride_height_mm < 20,
        "recommendation": "25-35mm optimal for FS"
    }