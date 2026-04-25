import math

def calculate_motion_ratio(rocker_arm_in, rocker_arm_out):
    mr = rocker_arm_in / rocker_arm_out
    return {
        "motion_ratio": round(mr, 3),
        "effect": "wheel travel is reduced" if mr < 1 else "wheel travel is amplified",
        "tip": "FS typical: 0.6-0.85"
    }

def calculate_wheel_rate(spring_rate_N_mm, motion_ratio):
    wr = spring_rate_N_mm * (motion_ratio ** 2)
    return {
        "spring_rate_N_mm": spring_rate_N_mm,
        "motion_ratio": motion_ratio,
        "wheel_rate_N_mm": round(wr, 2),
        "formula": "WR = SR × MR²"
    }

def calculate_natural_frequency(wheel_rate_N_mm, sprung_mass_kg):
    wn = math.sqrt((wheel_rate_N_mm * 1000) / sprung_mass_kg)
    fn = wn / (2 * math.pi)
    return {
        "natural_frequency_hz": round(fn, 2),
        "wheel_rate_N_mm": wheel_rate_N_mm,
        "sprung_mass_kg": sprung_mass_kg,
        "interpretation": "good" if 2.0 <= fn <= 3.5 else "check"
    }

def calculate_critical_damping(wheel_rate_N_mm, sprung_mass_kg):
    cc = 2 * math.sqrt(wheel_rate_N_mm * 1000 * sprung_mass_kg)
    return {
        "critical_damping_Ns_per_m": round(cc, 2),
        "wheel_rate_N_mm": wheel_rate_N_mm,
        "sprung_mass_kg": sprung_mass_kg
    }

def select_spring(target_wheel_rate, motion_ratio):
    required_spring_rate = target_wheel_rate / (motion_ratio ** 2)
    return {
        "required_spring_rate_N_mm": round(required_spring_rate, 1),
        "motion_ratio": motion_ratio,
        "target_wheel_rate": target_wheel_rate
    }

def check_ride_height_range(travel_min_mm, travel_max_mm, ride_height_mm):
    minRH = ride_height_mm - travel_min_mm
    maxRH = ride_height_mm + travel_max_mm
    return {
        "ride_height_mm": ride_height_mm,
        "min_with_travel_mm": round(minRH, 1),
        "max_with_travel_mm": round(maxRH, 1),
        "adequate": travel_min_mm >= 25
    }