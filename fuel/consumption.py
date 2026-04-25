from utils.constants import GRAVITY

def estimate_endurance_fuel(engine_name, lap_time_s, num_laps=22):
    avg_consumption_per_lap_L = 0.25
    total = lap_time_s * num_laps / 75 * avg_consumption_per_lap_L
    return {
        "estimated_fuel_L": round(total, 2),
        "lap_time_s": lap_time_s,
        "num_laps": num_laps,
        "avg_per_lap_L": avg_consumption_per_lap_L,
        "note": "Based on 0.25L per 75s lap"
    }

def estimate_lap_time_from_fuel(fuel_L, num_laps=22, avg_consumption_L=0.25):
    return round(fuel_L / avg_consumption_L * 75 / num_laps, 1)

def check_fuel_tank_rule(volume_L):
    MAX_FUEL = 10
    return {
        "volume_L": volume_L,
        "max_allowed_L": MAX_FUEL,
        "compliant": volume_L <= MAX_FUEL,
        "rule": "FS T7.1"
    }

def calculate_fuel_weight_cog(fuel_L, tank_position_x_mm, tank_position_z_mm, vehicle_mass_kg):
    fuel_mass = fuel_L * 0.72
    cog_shift_x = (fuel_mass * tank_position_x_mm) / vehicle_mass_kg
    cog_shift_z = (fuel_mass * tank_position_z_mm) / vehicle_mass_kg
    return {
        "fuel_mass_kg": fuel_mass,
        "cog_shift_x_mm": round(cog_shift_x, 1),
        "cog_shift_z_mm": round(cog_shift_z, 1),
        "note": "Positive = rearward shift"
    }

def check_fuel_system(has_tank, has_pump, has_vent, fuel_capacity_L):
    checks = {
        "tank_exists": has_tank,
        "pump_exists": has_pump,
        "vent_exists": has_vent,
        "capacity_ok": fuel_capacity_L <= 10,
        "all_passed": has_tank and has_pump and has_vent and fuel_capacity_L <= 10
    }
    return checks