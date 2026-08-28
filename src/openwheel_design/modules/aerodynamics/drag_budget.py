DRAG_COMPONENTS = {
    "front_wing": 0.15,
    "rear_wing": 0.25,
    "open_wheels": 0.35,
    "body_cockpit": 0.15,
    "cooling_inlets": 0.05,
    "suspension_exposed": 0.05,
}

def calculate_drag_budget(CD_total):
    result = {}
    for component, pct in DRAG_COMPONENTS.items():
        result[component] = round(CD_total * pct, 3)
    return result

def estimate_power_loss(drag_N, speed_kmh):
    v = speed_kmh / 3.6
    return round(drag_N * v / 1000, 2)

def compare_configs(config_a_CD, config_b_CD, speed_kmh, area_m2=1.2):
    rho = 1.225
    v = speed_kmh / 3.6
    drag_a_N = 0.5 * rho * v**2 * config_a_CD * area_m2
    drag_b_N = 0.5 * rho * v**2 * config_b_CD * area_m2
    return {
        "config_a_CD": config_a_CD,
        "config_b_CD": config_b_CD,
        "config_a_drag_N": round(drag_a_N, 1),
        "config_b_drag_N": round(drag_b_N, 1),
        "power_savings_kW": round(estimate_power_loss(drag_b_N, speed_kmh) - estimate_power_loss(drag_a_N, speed_kmh), 2)
    }