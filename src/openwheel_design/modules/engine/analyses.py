from .database import get_engine, calculate_power_to_weight, list_engines
from .constraints import (
    check_engine_displacement,
    check_intake_restrictor,
    calculate_restricted_power,
    estimate_power_with_restrictor
)
from .cooling import estimate_heat_rejection, check_cooling_system
from ..utils.constants import GRAVITY

def analyze_engine(engine_name, vehicle_weight_kg=None):
    eng = get_engine(engine_name)
    if not eng:
        return {"error": f"Engine not found: {engine_name}"}
    
    result = {
        "engine": eng["name"],
        "specs": {
            "displacement": eng["displacement_cc"],
            "power": f"{eng['power_hp']} hp",
            "torque": f"{eng['torque_Nm']} Nm",
            "weight": f"{eng['weight_kg']} kg",
            "compression": eng["compression"]
        }
    }
    
    if vehicle_weight_kg:
        ptw = calculate_power_to_weight(engine_name, vehicle_weight_kg)
        result["power_to_weight"] = {
            "kW_per_kg": ptw["power_to_weight_kW_per_kg"],
            "hp_per_kg": ptw["power_to_weight_hp_per_kg"]
        }
    
    return result

def reverse_engineer_engine(target_power_hp, criteria="min_weight"):
    from .database import ENGINES
    
    results = []
    for key, eng in ENGINES.items():
        results.append({
            "name": eng["name"],
            "key": key,
            "power_hp": eng["power_hp"],
            "weight_kg": eng["weight_kg"],
            "power_to_weight": eng["power_kW"] / eng["weight_kg"]
        })
    
    if criteria == "min_weight":
        results.sort(key=lambda x: x["weight_kg"])
    elif criteria == "max_power":
        results.sort(key=lambda x: x["power_hp"], reverse=True)
    elif criteria == "max_power_to_weight":
        results.sort(key=lambda x: x["power_to_weight"], reverse=True)
    
    return {
        "target_power_hp": target_power_hp,
        "criteria": criteria,
        "recommended_engines": results[:5]
    }

def analyze_with_restrictor(engine_name, restrictor_mm=20):
    return estimate_power_with_restrictor(engine_name, restrictor_mm)

def analyze_cooling(engine_name, power_hp):
    return check_cooling_system(engine_name, power_hp)

def optimize_engine_choice(vehicle_weight_kg, optimization_target="power_to_weight"):
    from .database import ENGINES
    
    results = []
    for key, eng in ENGINES.items():
        ptw = eng["power_kW"] / vehicle_weight_kg
        results.append({
            "name": eng["name"],
            "power_kW": eng["power_kW"],
            "weight_kg": eng["weight_kg"],
            "power_to_weight": round(ptw, 3),
            "torque_Nm": eng["torque_Nm"]
        })
    
    if optimization_target == "power_to_weight":
        results.sort(key=lambda x: x["power_to_weight"], reverse=True)
    elif optimization_target == "min_weight":
        results.sort(key=lambda x: x["weight_kg"])
    elif optimization_target == "max_torque":
        results.sort(key=lambda x: x["torque_Nm"], reverse=True)
    
    return {
        "vehicle_weight_kg": vehicle_weight_kg,
        "optimization_target": optimization_target,
        "results": results[:5]
    }

import math

def calculate_0_100_estimation(engine_name, vehicle_weight_kg,
                                drivetrain_loss=0.15,
                                gear_ratio=2.5, final_drive=3.0,
                                tire_radius_m=0.26, mu=1.5):
    eng = get_engine(engine_name)
    if not eng:
        return None

    torque = eng["torque_Nm"]
    drivetrain_eff = 1.0 - drivetrain_loss
    wheel_torque = torque * gear_ratio * final_drive * drivetrain_eff
    tractive_force = wheel_torque / tire_radius_m

    traction_limit = mu * vehicle_weight_kg * GRAVITY
    tractive_force = min(tractive_force, traction_limit)

    v_target = 100.0 / 3.6
    dt = 0.01
    v = 0.0
    t = 0.0

    while v < v_target:
        a = tractive_force / vehicle_weight_kg
        v += a * dt
        t += dt

    return {
        "engine": eng["name"],
        "estimated_0_100_kmh": round(t, 2),
        "tire_radius_m": tire_radius_m,
        "gear_ratio": gear_ratio,
        "final_drive": final_drive,
        "note": "Stepwise integration, single gear, traction limited"
    }

def analyze_performance(
    engine_name, 
    vehicle_weight_kg,
    include_restrictor=False,
    restrictor_mm=20
):
    eng = get_engine(engine_name)
    if not eng:
        return {"error": f"Engine not found: {engine_name}"}
    
    result = analyze_engine(engine_name, vehicle_weight_kg)
    
    if include_restrictor:
        result["with_restrictor"] = analyze_with_restrictor(engine_name, restrictor_mm)
    
    result["performance"] = calculate_0_100_estimation(engine_name, vehicle_weight_kg)
    result["cooling"] = analyze_cooling(engine_name, eng["power_hp"])
    
    return result