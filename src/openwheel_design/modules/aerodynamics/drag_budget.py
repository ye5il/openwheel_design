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

def compare_configs(config_a, config_b, speed_kmh, mass_kg):
    return {
        "config_a_CD": config_a,
        "config_b_CD": config_b,
        "power_savings_kW": round(estimate_power_loss(config_b, speed_kmh) - estimate_power_loss(config_a, speed_kmh), 2)
    }