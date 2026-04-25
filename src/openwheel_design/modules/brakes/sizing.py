import math

COMMON_ROTORS = {
    "200mm": {"diameter_mm": 200, "weight_kg": 1.5},
    "220mm": {"diameter_mm": 220, "weight_kg": 1.8},
    "250mm": {"diameter_mm": 250, "weight_kg": 2.2},
    "280mm": {"diameter_mm": 280, "weight_kg": 2.6},
}

CALIPER_SPECS = {
    "Wilwood_Dynalite": {"pistons": 4, "area_mm2": 1520},
    "AP_Racing_CP5555": {"pistons": 4, "area_mm2": 1780},
    "Brembo_P2_34": {"pistons": 2, "area_mm2": 908},
}

def size_rotor(vehicle_mass_kg, max_decel_g, max_speed_kmh, wheel_radius_mm=254):
    v = max_speed_kmh / 3.6
    KE = 0.5 * vehicle_mass_kg * v**2
    required_area = KE / (max_decel_g * wheel_radius_mm * 200)
    return {
        "recommended_area_mm2": round(required_area, 0),
        "kinetic_energy_J": round(KE, 0),
        "tip": "200-280mm typical for FS"
    }

def select_caliper(required_clamp_force_N):
    results = []
    for name, spec in CALIPER_SPECS.items():
        max_force = spec["area_mm2"] * 100
        results.append({
            "name": name,
            "max_force_N": max_force,
            "adequate": max_force >= required_clamp_force_N,
            "pistons": spec["pistons"]
        })
    results.sort(key=lambda x: x["adequate"], reverse=True)
    return results[0] if results else None

def calculate_pad_area(required_brake_force_N, max_pad_pressure_MPa=10):
    area = required_brake_force_N / max_pad_pressure_MPa
    return {
        "pad_area_mm2": round(area, 0),
        "required_force_N": required_brake_force_N,
        "max_pressure_MPa": max_pad_pressure_MPa
    }

def list_rotors():
    return COMMON_ROTORS

def list_calipers():
    return list(CALIPER_SPECS.keys())