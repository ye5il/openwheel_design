def calculate_understeer_gradient(front_cs, rear_cs, front_weight_N, rear_weight_N):
    import math
    a1 = front_weight_N / front_cs
    a2 = rear_weight_N / rear_cs
    K_us_rad_per_g = a1 - a2
    K_us_deg_per_g = K_us_rad_per_g * (180 / math.pi)
    return {
        "gradient_deg_per_g": round(K_us_deg_per_g, 4),
        "gradient_rad_per_g": round(K_us_rad_per_g, 6),
        "character": "understeer" if K_us_deg_per_g > 0 else ("oversteer" if K_us_deg_per_g < 0 else "neutral"),
        "front_slip_deg_per_g": round(a1 * (180 / math.pi), 3),
        "rear_slip_deg_per_g": round(a2 * (180 / math.pi), 3)
    }

def estimate_roll_angle(lateral_g, roll_gradient_deg_per_g):
    angle = lateral_g * roll_gradient_deg_per_g
    return {
        "roll_angle_deg": round(angle, 2),
        "lateral_g": lateral_g
    }

def check_balance_sensitivity(front_arb, rear_arb, front_spring, rear_spring):
    front_total = front_arb + front_spring
    rear_total = rear_arb + rear_spring
    total = front_total + rear_total
    front_pct = front_total / total
    return {
        "front_contribution_pct": round(front_pct * 100, 1),
        "balanced": 0.4 <= front_pct <= 0.6
    }