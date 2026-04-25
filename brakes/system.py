from utils.constants import GRAVITY
import math

COMMON_CALIPERS = {
    "Wilwood_Dynalite": {"pistons": 4, "area_mm2": 1520, "weight_kg": 0.45},
    "AP_Racing_CP5555": {"pistons": 4, "area_mm2": 1780, "weight_kg": 0.52},
    "Brembo_P2_34": {"pistons": 2, "area_mm2": 908, "weight_kg": 0.30},
}

def calculate_brake_bias(front_weight_N, rear_weight_N, decel_g, cog_height_mm, wheelbase_mm):
    weight_transfer = decel_g * (front_weight_N + rear_weight_N) * cog_height_mm / wheelbase_mm
    dynamic_front = front_weight_N + weight_transfer
    dynamic_rear = rear_weight_N - weight_transfer
    ideal_bias = dynamic_front / (dynamic_front + dynamic_rear)
    return {
        "ideal_front_bias_pct": round(ideal_bias * 100, 1),
        "dynamic_front_N": round(dynamic_front, 0),
        "dynamic_rear_N": round(dynamic_rear, 0),
        "weight_transfer_N": round(weight_transfer, 0)
    }

def calculate_master_cylinder(pedal_ratio, pedal_force_N, desired_pressure_bar):
    mc_area = (pedal_force_N * pedal_ratio) / (desired_pressure_bar * 100000) * 1e6
    mc_diameter = 2 * math.sqrt(mc_area / math.pi)
    return {
        "mc_area_mm2": round(mc_area, 1),
        "mc_diameter_mm": round(mc_diameter, 1),
        "pedal_ratio": pedal_ratio,
        "desired_pressure_bar": desired_pressure_bar
    }

def calculate_brake_force(pressure_bar, caliper_piston_area_mm2, pad_friction, rotor_radius_mm, wheel_radius_mm):
    piston_force = pressure_bar * 1e5 * caliper_piston_area_mm2 / 1e6
    clamp_force = piston_force * 2
    brake_torque = clamp_force * pad_friction * (rotor_radius_mm / 1000)
    brake_force = brake_torque / (wheel_radius_mm / 1000)
    return {
        "brake_force_N": round(brake_force, 0),
        "brake_torque_Nm": round(brake_torque, 1),
        "clamp_force_N": round(clamp_force, 0)
    }

def check_pedal_travel(mc_bore_mm, caliper_bore_mm, pad_clearance_mm=0.15):
    return {
        "travel_mm_estimated": round(mc_bore_mm * 0.15 + caliper_bore_mm * 0.1, 1),
        "note": "Check against driver preference"
    }