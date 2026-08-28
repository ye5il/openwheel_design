import math

def calculate_gear_ratios(engine_max_rpm, wheel_radius_mm, max_speed_kmh, num_gears=6):
    v_max = max_speed_kmh / 3.6
    omega_wheel = v_max / (wheel_radius_mm / 1000)
    top_gear_ratio = engine_max_rpm / (omega_wheel * 60 / (2 * math.pi))
    
    ratio_spread = 3.8
    ratios = []
    for i in range(num_gears):
        r = top_gear_ratio * (ratio_spread ** ((num_gears - 1 - i) / (num_gears - 1)))
        ratios.append(round(r, 2))
    return ratios

def calculate_speed_at_rpm(gear_ratio, final_drive, wheel_radius_mm, rpm):
    omega_engine = rpm * 2 * math.pi / 60
    omega_wheel = omega_engine / (gear_ratio * final_drive)
    v = omega_wheel * (wheel_radius_mm / 1000)
    return round(v * 3.6, 1)

def calculate_rpm_at_speed(speed_kmh, gear_ratio, final_drive, wheel_radius_mm):
    v = speed_kmh / 3.6
    omega_wheel = v / (wheel_radius_mm / 1000)
    omega_engine = omega_wheel * gear_ratio * final_drive
    rpm = omega_engine * 60 / (2 * math.pi)
    return round(rpm, 0)

def calculate_rpm_drop(ratio_1, ratio_2, peak_torque_rpm):
    ratio_drop = (ratio_2 / ratio_1 - 1) * 100
    return {
        "drop_percent": round(ratio_drop, 1),
        "in_torque_band": ratio_drop < 10,
        "recommendation": "shift earlier" if ratio_drop > 15 else "good"
    }

def optimize_gear_ratios(max_rpm, num_gears=6, first_ratio=3.5,
                          top_ratio=0.9, final_drive=3.0,
                          tire_radius_mm=260):
    if num_gears < 2:
        return {"error": "Need at least 2 gears"}

    ratios = []
    for i in range(num_gears):
        r = first_ratio * (top_ratio / first_ratio) ** (i / (num_gears - 1))
        ratios.append(round(r, 3))

    tire_radius_m = tire_radius_mm / 1000.0
    speeds = []
    for r in ratios:
        omega_wheel = (max_rpm * 2 * math.pi / 60) / (r * final_drive)
        v_kmh = omega_wheel * tire_radius_m * 3.6
        speeds.append(round(v_kmh, 1))

    return {
        "num_gears": num_gears,
        "ratios": ratios,
        "final_drive": final_drive,
        "max_speed_per_gear_kmh": speeds,
        "progression": "geometric"
    }

def check_rpm_in_torque_band(rpm, peak_torque_rpm, bandwidth=2000):
    return {
        "in_band": peak_torque_rpm - bandwidth <= rpm <= peak_torque_rpm + bandwidth,
        "rpm": rpm,
        "peak_torque_rpm": peak_torque_rpm
    }