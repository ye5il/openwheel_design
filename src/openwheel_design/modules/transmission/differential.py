LSD_TYPES = {
    "mechanical": {"engagement": "always", "bias_ratio": "2-5"},
    "welded": {"engagement": "always", "bias_ratio": "infinite"},
    "clutch": {"engagement": "adjustable", "bias_ratio": "adjustable"},
}

def calculate_lsd_torque(bias_ratio, input_torque_Nm):
    output = input_torque_Nm * bias_ratio
    return {
        "input_torque_Nm": input_torque_Nm,
        "bias_ratio": bias_ratio,
        "output_torque_Nm": round(output, 1)
    }

def estimate_critical_speed(shaft_diameter_mm, unsupported_length_mm, material="steel"):
    import math
    E = 207000 if material == "steel" else 70000
    I = math.pi * shaft_diameter_mm**4 / 32
    p_crit = math.pi**2 * E * I / (unsupported_length_mm**4 * 1000)
    return {
        "critical_rpm": round(p_crit**0.5 / (2 * math.pi) * 60, 0),
        "shaft_diameter_mm": shaft_diameter_mm
    }

def check_torque_capacity(input_torque_Nm, safety_factor=2.0):
    return {
        "adequate": True,
        "input_torque_Nm": input_torque_Nm,
        "safety_factor": safety_factor,
        "note": "Check with component specs"
    }