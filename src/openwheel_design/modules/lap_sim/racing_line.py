import math

def calculate_corner_entry_speed(mu, turn_radius_m, downforce_N=0, mass_kg=200):
    total_grip = mu * mass_kg * 9.81 + downforce_N
    v = math.sqrt(total_grip * turn_radius_m / mass_kg)
    return round(v * 3.6, 1)

def calculate_racing_line_parameters(track_points):
    if len(track_points) < 2:
        return None
    
    speeds = [p.get("speed", 0) for p in track_points]
    accelerations = []
    for i in range(1, len(track_points)):
        dv = speeds[i] - speeds[i-1]
        dt = track_points[i].get("dt", 1)
        accel = dv / dt if dt > 0 else 0
        accelerations.append(accel)
    
    return {
        "min_speed": min(speeds),
        "max_speed": max(speeds),
        "avg_accel": round(sum(accelerations) / len(accelerations), 2),
        "max_decel": round(min(accelerations), 2) if accelerations else 0
    }

def optimize_corner_line(turn_radius_m, entry_speed_kmh, exit_speed_kmh):
    v_in = entry_speed_kmh / 3.6
    v_out = exit_speed_kmh / 3.6
    radius = turn_radius_m
    delta_v = v_in - v_out
    
    braking_distance = abs(delta_v**2) / (2 * 0.8 * 9.81)
    return {
        "turn_radius_m": radius,
        "braking_distance_m": round(braking_distance, 2),
        "entry_speed_kmh": entry_speed_kmh,
        "exit_speed_kmh": exit_speed_kmh
    }

def calculate_theoretical_best_theoretical_lap(track_m, mass_kg, max_power_kW):
    base = track_m / 30
    adj = max_power_kW / mass_kg * 0.1
    return round(base - adj, 2)

class RacingLineOptimizer:
    def __init__(self, track_data):
        self.track = track_data
    
    def calculate_optimal_racing_line(self):
        return {"optimized": True, "racing_line": "apex"}
    
    def identify_slow_sectors(self):
        return {"slow_sectors": []}
    
    def suggest_Improvements(self):
        return {"suggestions": []}