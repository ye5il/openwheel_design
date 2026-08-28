import math

RHO_SEA_LEVEL = 1.225

def calculate_downforce(CL, area_m2, speed_kmh, air_density=RHO_SEA_LEVEL):
    v = speed_kmh / 3.6
    return round(0.5 * air_density * v**2 * area_m2 * CL, 0)

def calculate_drag(CD, area_m2, speed_kmh, air_density=RHO_SEA_LEVEL):
    v = speed_kmh / 3.6
    return round(0.5 * air_density * v**2 * area_m2 * CD, 0)

def calculate_lift_to_drag(CL, CD):
    return round(CL / CD, 3) if CD > 0 else 0

def calculate_aero_balance(front_df_N, rear_df_N):
    total = front_df_N + rear_df_N
    front_pct = front_df_N / total * 100 if total > 0 else 0
    return {
        "front_pct": round(front_pct, 1),
        "rear_pct": round(100 - front_pct, 1),
        "balanced": 38 <= front_pct <= 48
    }

def calculate_aero_at_speeds(CL, CD, area_m2, speeds=None):
    if speeds is None:
        speeds = [30, 50, 70, 90, 110]
    results = []
    for v in speeds:
        df = calculate_downforce(CL, area_m2, v)
        dr = calculate_drag(CD, area_m2, v)
        results.append({"speed_kmh": v, "downforce_N": df, "drag_N": dr})
    return results

def estimate_cornering_speed(mechanical_grip_N, aero_df_N, corner_radius_m, vehicle_mass_kg):
    total_grip = mechanical_grip_N + aero_df_N
    v = math.sqrt(total_grip * corner_radius_m / vehicle_mass_kg)
    return round(v * 3.6, 1)

def estimate_power_loss_from_drag(drag_N, speed_kmh):
    v = speed_kmh / 3.6
    return round(drag_N * v / 1000, 2)