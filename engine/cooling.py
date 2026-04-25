from engine.database import get_engine

COOLING_REQUIRED_HP = {
    "water_pump_flow_lpm": 40,
    "radiator_capacity_kw": 30,
    "coolant_capacity_liters": 3
}

def estimate_heat_rejection(engine_name, power_hp, efficiency=0.25):
    eng = get_engine(engine_name)
    if not eng:
        return None
    
    heat_power_kw = power_hp * 0.7457 * efficiency
    return {
        "engine_name": eng["name"],
        "engine_power_hp": power_hp,
        "thermal_efficiency": efficiency,
        "heat_rejected_kw": round(heat_power_kw, 2),
        "heat_rejected_btu_min": round(heat_power_kw * 56.9, 1)
    }

def calculate_radiator_size(heat_rejection_kw, delta_t=40):
    ua = heat_rejection_kw / delta_t
    return {
        "heat_rejection_kw": heat_rejection_kw,
        "delta_t_c": delta_t,
        "ua_value": round(ua, 3),
        "recommended_radiator_area_m2": round(ua * 0.015, 3),
        "note": "Typical FS radiator: 200x150x40mm core"
    }

def calculate_water_pump_flow(Engine_cc, flow_rate_per_cc=0.067):
    lpm = Engine_cc * flow_rate_per_cc
    return {
        "Engine_cc": Engine_cc,
        "flow_rate_lpm": round(lpm, 1),
        "flow_rate_gpm": round(lpm * 0.264, 1)
    }

def calculate_thermostat_size(opening_temp_c=82):
    return {
        "opening_temp_c": opening_temp_c,
        "full_open_temp_c": opening_temp_c + 10,
        "type": "Wax pellet or electronic"
    }

def calculate_coolant_volume(Engine_cc):
    liters = Engine_cc * 0.005
    return {
        "Engine_cc": Engine_cc,
        "coolant_liters": round(liters, 2),
        "note": "Including radiator + hoses + engine"
    }

def check_cooling_system(engine_name, power_hp):
    eng = get_engine(engine_name)
    if not eng:
        return None
    
    heat = estimate_heat_rejection(engine_name, power_hp)
    rad = calculate_radiator_size(heat["heat_rejected_kw"])
    flow = calculate_water_pump_flow(eng["displacement_cc"])
    vol = calculate_coolant_volume(eng["displacement_cc"])
    
    return {
        "engine": eng["name"],
        "estimated_heat_rejection_kw": heat["heat_rejected_kw"],
        "recommended_radiator": rad,
        "pump_flow_lpm": flow["flow_rate_lpm"],
        "coolant_volume_liters": vol["coolant_liters"]
    }