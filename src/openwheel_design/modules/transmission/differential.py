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
    I = math.pi * shaft_diameter_mm**4 / 64
    p_crit = math.pi**2 * E * I / (unsupported_length_mm**4 * 1000)
    return {
        "critical_rpm": round(p_crit**0.5 / (2 * math.pi) * 60, 0),
        "shaft_diameter_mm": shaft_diameter_mm
    }

def check_torque_capacity(input_torque_Nm, shaft_diameter_mm=25,
                          material_shear_strength_MPa=350,
                          safety_factor=2.0):
    """Check if shaft can handle the input torque with safety margin.
    Uses maximum shear stress theory for solid circular shaft:
    tau_max = 16*T / (pi * d^3)
    """
    import math
    d = shaft_diameter_mm
    required_torque = input_torque_Nm * safety_factor
    # Max shear stress from applied torque (convert Nm to N*mm)
    tau_applied = 16 * (required_torque * 1000) / (math.pi * d**3)
    adequate = tau_applied <= material_shear_strength_MPa
    return {
        "adequate": adequate,
        "input_torque_Nm": input_torque_Nm,
        "required_torque_Nm": round(required_torque, 1),
        "applied_shear_stress_MPa": round(tau_applied, 1),
        "material_shear_strength_MPa": material_shear_strength_MPa,
        "safety_factor": safety_factor,
        "utilization_pct": round(tau_applied / material_shear_strength_MPa * 100, 1)
    }