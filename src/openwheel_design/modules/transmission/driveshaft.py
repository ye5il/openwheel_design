import math

def calculate_driveshaft_torque(max_torque_Nm, safety_factor=2.5):
    return {
        "max_torque_Nm": max_torque_Nm,
        "required_capacity_Nm": round(max_torque_Nm * safety_factor, 1),
        "safety_factor": safety_factor
    }

def calculate_critical_speed(shaft_diameter_mm, length_mm, material="steel"):
    E = 207000 if material == "steel" else 70000
    rho = 7850 if material == "steel" else 2700
    I = math.pi * shaft_diameter_mm**4 / 64
    term = E * I / (rho * length_mm**4) * 1000
    n_crit = 30 * term**0.5 / math.pi
    return {
        "critical_rpm": round(n_crit, 0),
        "shaft_diameter_mm": shaft_diameter_mm,
        "length_mm": length_mm,
        "safe": n_crit > 8000
    }

def calculate_torsional_stiffness(shaft_diameter_mm, length_mm, material="steel"):
    G = 80000 if material == "steel" else 27000
    J = math.pi * shaft_diameter_mm**4 / 32
    K = G * J / length_mm
    return {
        "stiffness_Nm_per_rad": round(K / 1000, 2),
        "shaft_diameter_mm": shaft_diameter_mm
    }