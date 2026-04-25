from utils.constants import FS_MAX_DISPLACEMENT, FS_RESTRICTOR

ENGINE_CONSTRAINTS = {
    "displacement": {
        "max": 710,
        "unit": "cc",
        "description": "Maximum engine displacement per cycle"
    },
    "intake_restrictor": {
        "max": 20,
        "unit": "mm",
        "description": "Maximum intake restrictor diameter"
    },
    "rpm_max": {
        "typical": 10000,
        "unit": "rpm",
        "description": "Maximum allowable RPM ( FSAE rules)"
    }
}

def check_engine_displacement(cc):
    return {
        "value": cc,
        "max_allowed": FS_MAX_DISPLACEMENT,
        "compliant": cc <= FS_MAX_DISPLACEMENT
    }

def check_intake_restrictor(diameter_mm):
    return {
        "value": diameter_mm,
        "max_allowed": FS_RESTRICTOR,
        "compliant": diameter_mm <= FS_RESTRICTOR,
        "estimated_power_loss": "20-30% due to restriction"
    }

import math

def calculate_restricted_power(restrictor_mm, stock_power_hp, throttle_body_mm=44):
    Cd = 0.82
    A_r = math.pi * (restrictor_mm / 2000) ** 2
    A_t = math.pi * (throttle_body_mm / 2000) ** 2
    flow_ratio = (Cd * A_r) / A_t
    power_ratio = min(flow_ratio, 1.0)
    return stock_power_hp * power_ratio

def get_engine_constraints():
    return ENGINE_CONSTRAINTS

def estimate_power_with_restrictor(engine_name, restrictor_mm=20):
    from engine.database import get_engine
    eng = get_engine(engine_name)
    if not eng:
        return None
    
    stock_hp = eng["power_hp"]
    restricted = calculate_restricted_power(restrictor_mm, stock_hp)
    
    return {
        "engine": eng["name"],
        "stock_power_hp": stock_hp,
        "restrictor_mm": restrictor_mm,
        "estimated_power_hp": round(restricted, 1),
        "power_lost_percent": round(100 - (restricted / stock_hp * 100), 1)
    }