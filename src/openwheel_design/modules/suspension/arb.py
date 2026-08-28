import math

G_STEEL = 80000
G_ALUMINUM = 27000

def calculate_arb_stiffness(bar_diameter_mm, bar_length_mm, arm_length_mm, material="steel"):
    G = G_STEEL if material == "steel" else G_ALUMINUM
    J = math.pi * (bar_diameter_mm ** 4) / 32
    # K_rad = torque per radian of twist = G*J / bar_length (N*mm/rad)
    # Force at arm tip per radian = K_rad / arm_length^2
    # Convert per-radian to per-degree: divide by (pi/180)
    K_per_rad = (G * J) / (bar_length_mm * arm_length_mm ** 2)
    K_per_deg = K_per_rad * math.pi / 180
    return {
        "stiffness_N_mm_per_deg": round(K_per_deg, 2),
        "bar_diameter_mm": bar_diameter_mm,
        "bar_length_mm": bar_length_mm,
        "arm_length_mm": arm_length_mm,
        "material": material
    }

def calculate_roll_stiffness(arb_stiffness, spring_stiffness, track_width_mm):
    total = arb_stiffness + spring_stiffness
    return {
        "total_stiffness_N_mm_per_deg": round(total, 2),
        "arb_contribution_pct": round(arb_stiffness / total * 100, 1),
        "spring_contribution_pct": round(spring_stiffness / total * 100, 1)
    }

def calculate_roll_gradient(total_roll_stiffness_N_per_deg, sprung_weight_N, 
                           cog_height_mm, track_mm):
    roll_grad = (sprung_weight_N * cog_height_mm / track_mm) / total_roll_stiffness_N_per_deg
    return {
        "roll_gradient_deg_per_g": round(roll_grad, 3),
        "total_stiffness_N_per_deg": total_roll_stiffness_N_per_deg,
        "interpretation": "good" if roll_grad < 1.5 else "too stiff"
    }

def optimize_arb(front_roll_stiffness, rear_roll_stiffness, target_balance=0.55):
    total = front_roll_stiffness + rear_roll_stiffness
    front_pct = front_roll_stiffness / total
    current = front_pct * 100
    target = target_balance * 100
    
    adj = (target - current) / 100 * total
    return {
        "current_front_pct": round(current, 1),
        "target_front_pct": round(target, 1),
        "stiffness_adjustment_N_per_deg": round(adj, 2),
        "recommendation": "increase front" if current < target else "increase rear"
    }