import math

SPECIFIC_HEAT_IRON = 500
DISC_LIMITS = {"cast_iron": 700, "carbon_ceramic": 1000, "steel": 650}

def estimate_disc_temperature(kinetic_energy_J, disc_mass_kg, num_discs=2, initial_temp_C=20):
    heat_per_disc = kinetic_energy_J / num_discs
    delta_T = heat_per_disc / (disc_mass_kg * SPECIFIC_HEAT_IRON)
    final_temp = initial_temp_C + delta_T
    return {
        "final_temp_C": round(final_temp, 0),
        "delta_T": round(delta_T, 0),
        "warning": final_temp > 700
    }

def calculate_cooling_airflow(disc_temp_C, ambient_temp_C, disc_area_m2, convection_coeff=50):
    delta_T = disc_temp_C - ambient_temp_C
    q = convection_coeff * disc_area_m2 * delta_T
    return {
        "cooling_power_W": round(q, 1),
        "delta_T": delta_T,
        "note": "Natural convection estimate"
    }

def check_thermal_limit(temp_C, disc_material="cast_iron"):
    limit = DISC_LIMITS.get(disc_material, 700)
    return {
        "temp_C": temp_C,
        "limit_C": limit,
        "safe": temp_C < limit,
        "margin_C": limit - temp_C
    }

def calculate_brake_energy(vehicle_mass_kg, speed_kmh, target_speed_kmh=0):
    v1 = speed_kmh / 3.6
    v2 = target_speed_kmh / 3.6
    return {
        "kinetic_energy_J": round(0.5 * vehicle_mass_kg * (v1**2 - v2**2), 0),
        "from_speed_kmh": speed_kmh,
        "to_speed_kmh": target_speed_kmh
    }