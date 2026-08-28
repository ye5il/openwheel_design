import math

TRACK_TEMPLATES = {
    "dynamic_skidpad": {"length_m": 45.72, "radius_m": 15.25, "figure8": False},
    "acceleration": {"length_m": 75, "radius_m": 0, "figure8": False},
    "autocross": {"length_m": 1000, "radius_m": 30, "figure8": True},
    "endurance_fs": {"length_m": 1000, "radius_m": 40, "figure8": False},
}

def estimate_energy_consumption(speed_profile, mass_kg, drag_CD=1.5, area_m2=1.2, dt_seconds=1.0):
    total_energy_kWh = 0
    for speed in speed_profile:
        power_kW = calculate_power_at_speed(speed, mass_kg, drag_CD, area_m2)
        total_energy_kWh += power_kW * (dt_seconds / 3600)
    return round(total_energy_kWh, 4)

def calculate_power_at_speed(speed_kmh, mass_kg, drag_CD=1.5, area_m2=1.2):
    v = speed_kmh / 3.6
    rho = 1.225
    drag = 0.5 * rho * v**2 * drag_CD * area_m2
    roll = mass_kg * 9.81 * 0.015
    aero_power = drag * v
    roll_power = roll * v
    return round((aero_power + roll_power) / 1000, 2)

def simulate_lap(track_name, vehicle_params):
    raise NotImplementedError(
        "simulate_lap is a placeholder and does not produce valid results. "
        "It will be replaced by the quasi-steady-state (QSS) lap simulation engine."
    )

def calculate_range(kWh_available, track_length_km, num_laps, power_per_lap_kWh):
    total = track_length_km * num_laps
    return round(kWh_available / (power_per_lap_kWh / total), 1)

def compare_aero_configs(config_a, config_b, vehicle_params):
    power_a = calculate_power_at_speed(80, vehicle_params["mass_kg"], config_a, vehicle_params["frontal_area_m2"])
    power_b = calculate_power_at_speed(80, vehicle_params["mass_kg"], config_b, vehicle_params["frontal_area_m2"])
    return {
        "config_a_power_kW": power_a,
        "config_b_power_kW": power_b,
        "savings_kW": round(power_a - power_b, 2),
        "faster_config": "A" if power_a < power_b else "B"
    }

def calculate_theoretical_best_lap(track_length_m, max_power_kW, mass_kg):
    power_ratio = max_power_kW / mass_kg * 100
    base_time = track_length_m / 35
    adjustment = (0.5 - power_ratio) * 2
    return round(base_time - adjustment, 2)

def optimize_gear_shift_points(track_radius_profile, engine_rpm_profile):
    shifts = []
    for i in range(len(track_radius_profile) - 1):
        if engine_rpm_profile[i] >= 12000 and engine_rpm_profile[i+1] < 12000:
            shifts.append(i)
    return shifts
