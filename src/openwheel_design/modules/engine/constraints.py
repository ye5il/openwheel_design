from ..utils.constants import FS_MAX_DISPLACEMENT, FS_RESTRICTOR

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
        "description": "Typical maximum RPM for FS engines (not an FSAE rule limit)"
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
    Cd = 0.9
    d_m = restrictor_mm / 1000.0
    A = math.pi * (d_m / 2) ** 2
    P0 = 101325.0
    T0 = 298.0
    gamma = 1.4
    R_air = 287.0

    mdot = (Cd * A * P0
            * math.sqrt(gamma / (R_air * T0))
            * (2.0 / (gamma + 1)) ** ((gamma + 1) / (2 * (gamma - 1))))

    AFR = 14.7
    LHV = 43.0e6
    eta_thermal = 0.30
    eta_mech = 0.85

    fuel_flow = mdot / AFR
    restricted_power_W = fuel_flow * LHV * eta_thermal * eta_mech
    restricted_power_hp = restricted_power_W / 745.7

    return min(restricted_power_hp, stock_power_hp)

def get_engine_constraints():
    return ENGINE_CONSTRAINTS

def estimate_power_with_restrictor(engine_name, restrictor_mm=20):
    from .database import get_engine
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