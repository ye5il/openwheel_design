from ..utils.constants import GRAVITY
import math

COMMON_CALIPERS = {
    "Wilwood_Dynalite": {"pistons": 4, "area_mm2": 1520, "weight_kg": 0.45},
    "AP_Racing_CP5555": {"pistons": 4, "area_mm2": 1780, "weight_kg": 0.52},
    "Brembo_P2_34": {"pistons": 2, "area_mm2": 908, "weight_kg": 0.30},
}

def calculate_brake_bias(front_weight_N, rear_weight_N, decel_g, cog_height_mm, wheelbase_mm):
    import warnings
    weight_transfer = decel_g * (front_weight_N + rear_weight_N) * cog_height_mm / wheelbase_mm
    dynamic_front = front_weight_N + weight_transfer
    dynamic_rear = rear_weight_N - weight_transfer

    warning_msg = None
    if dynamic_rear < 0:
        warning_msg = (
            "Dynamic rear axle load is negative ({:.0f} N). "
            "Weight transfer ({:.0f} N) exceeds static rear load ({:.0f} N). "
            "The rear axle would lift; reduce deceleration or lower CoG.".format(
                dynamic_rear, weight_transfer, rear_weight_N
            )
        )
        warnings.warn(warning_msg, stacklevel=2)

    ideal_bias = dynamic_front / (dynamic_front + dynamic_rear) if (dynamic_front + dynamic_rear) != 0 else 1.0
    result = {
        "ideal_front_bias_pct": round(ideal_bias * 100, 1),
        "dynamic_front_N": round(dynamic_front, 0),
        "dynamic_rear_N": round(dynamic_rear, 0),
        "weight_transfer_N": round(weight_transfer, 0)
    }
    if warning_msg:
        result["warning"] = warning_msg
    return result

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

def check_pedal_travel(mc_bore_mm, mc_stroke_mm=25.0, caliper_bore_mm=32.0,
                       n_pistons=4, n_calipers=4, pad_clearance_mm=0.15,
                       pedal_ratio=5.0):
    """Calculate pedal travel from master cylinder and caliper geometry.

    Each caliper needs (n_pistons * piston_area * pad_clearance) of fluid volume
    to push pads against the disc.  The master cylinder displaces
    (MC_bore_area * MC_stroke) of fluid.  Pedal travel at the foot is
    MC_stroke * pedal_ratio.  If total caliper demand exceeds MC displacement
    the system cannot develop full clamp force.

    Args:
        mc_bore_mm: Master cylinder bore diameter (mm).
        mc_stroke_mm: Master cylinder piston stroke (mm).
        caliper_bore_mm: Single caliper piston bore diameter (mm).
        n_pistons: Number of pistons per caliper.
        n_calipers: Total number of calipers (typically 4).
        pad_clearance_mm: Pad-to-rotor gap each piston must close (mm).
        pedal_ratio: Mechanical advantage of the pedal lever.

    Returns:
        dict with travel, volume, and compliance info.
    """
    mc_area = math.pi * (mc_bore_mm / 2) ** 2          # mm^2
    mc_volume = mc_area * mc_stroke_mm                  # mm^3

    piston_area = math.pi * (caliper_bore_mm / 2) ** 2 # mm^2
    volume_per_caliper = n_pistons * piston_area * pad_clearance_mm  # mm^3
    total_caliper_volume = volume_per_caliper * n_calipers           # mm^3

    # Stroke the MC must actually travel to supply caliper volume
    mc_stroke_needed = total_caliper_volume / mc_area   # mm
    pedal_travel = mc_stroke_needed * pedal_ratio       # mm at the foot

    volume_ok = mc_volume >= total_caliper_volume

    return {
        "pedal_travel_mm": round(pedal_travel, 1),
        "mc_stroke_needed_mm": round(mc_stroke_needed, 2),
        "mc_volume_mm3": round(mc_volume, 1),
        "total_caliper_volume_mm3": round(total_caliper_volume, 1),
        "volume_sufficient": volume_ok,
        "note": ("MC provides enough fluid volume"
                 if volume_ok
                 else "MC volume insufficient; increase bore or stroke")
    }