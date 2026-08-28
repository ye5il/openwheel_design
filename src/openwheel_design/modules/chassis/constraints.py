from ..utils.constants import (
    TEAM_TARGET_WEIGHT, TEAM_TARGET_LENGTH, TEAM_TARGET_WIDTH,
    FS_MAX_DISPLACEMENT, FS_RESTRICTOR
)

# These are team design targets, not FSAE mandated limits
FS_MIN_WEIGHT = TEAM_TARGET_WEIGHT
FS_MAX_LENGTH = TEAM_TARGET_LENGTH
FS_MAX_WIDTH = TEAM_TARGET_WIDTH

FS_CONSTRAINTS = {
    "weight": {
        "min": FS_MIN_WEIGHT,
        "unit": "kg",
        "description": "Minimum vehicle weight with driver"
    },
    "length": {
        "max": FS_MAX_LENGTH,
        "unit": "mm",
        "description": "Maximum overall length"
    },
    "width": {
        "max": FS_MAX_WIDTH,
        "unit": "mm",
        "description": "Maximum overall width"
    },
    "displacement": {
        "max": FS_MAX_DISPLACEMENT,
        "unit": "cc",
        "description": "Maximum engine displacement"
    },
    "intake_restrictor": {
        "max": FS_RESTRICTOR,
        "unit": "mm",
        "description": "Maximum intake restrictor diameter"
    },
    "fuel_tank": {
        "max": 10,
        "unit": "L",
        "description": "Maximum fuel tank capacity"
    },
    "rollbar_od": {
        "min": 25.4,
        "unit": "mm",
        "description": "Minimum rollbar OD"
    },
    "rollbar_wall": {
        "min": 2.4,
        "unit": "mm",
        "description": "Minimum rollbar wall thickness"
    },
    "sound_limit": {
        "max": 110,
        "unit": "dB",
        "description": "Maximum sound level at 0.5m"
    },
    "cockpit_width": {
        "min": 330,
        "unit": "mm",
        "description": "Minimum cockpit opening width"
    },
    "cockpit_height": {
        "min": 550,
        "unit": "mm",
        "description": "Minimum cockpit opening height"
    }
}

def check_fs_compliance(weight, length, width, displacement=None, restrictor=None):
    results = {}
    results["weight"] = {
        "value": weight,
        "constraint": FS_MIN_WEIGHT,
        "compliant": weight >= FS_MIN_WEIGHT
    }
    results["length"] = {
        "value": length,
        "constraint": FS_MAX_LENGTH,
        "compliant": length <= FS_MAX_LENGTH
    }
    results["width"] = {
        "value": width,
        "constraint": FS_MAX_WIDTH,
        "compliant": width <= FS_MAX_WIDTH
    }
    
    if displacement:
        results["displacement"] = {
            "value": displacement,
            "constraint": FS_MAX_DISPLACEMENT,
            "compliant": displacement <= FS_MAX_DISPLACEMENT
        }
    if restrictor:
        results["intake_restrictor"] = {
            "value": restrictor,
            "constraint": FS_RESTRICTOR,
            "compliant": restrictor <= FS_RESTRICTOR
        }
    
    all_compliant = all(r["compliant"] for r in results.values())
    return {"passed": all_compliant, "checks": results}

def get_fs_constraints():
    return FS_CONSTRAINTS

def get_constraint_value(key):
    return FS_CONSTRAINTS.get(key, {}).get("max") or FS_CONSTRAINTS.get(key, {}).get("min")

def check_rollbar_spec(od_mm, wall_mm):
    return {
        "od_mm": od_mm,
        "wall_mm": wall_mm,
        "od_ok": od_mm >= FS_CONSTRAINTS["rollbar_od"]["min"],
        "wall_ok": wall_mm >= FS_CONSTRAINTS["rollbar_wall"]["min"],
        "compliant": od_mm >= FS_CONSTRAINTS["rollbar_od"]["min"] and wall_mm >= FS_CONSTRAINTS["rollbar_wall"]["min"]
    }

def check_cockpit_opening(width_mm, height_mm):
    return {
        "width_mm": width_mm,
        "height_mm": height_mm,
        "width_ok": width_mm >= FS_CONSTRAINTS["cockpit_width"]["min"],
        "height_ok": height_mm >= FS_CONSTRAINTS["cockpit_height"]["min"],
        "compliant": width_mm >= FS_CONSTRAINTS["cockpit_width"]["min"] and height_mm >= FS_CONSTRAINTS["cockpit_height"]["min"]
    }

def check_fuel_system(fuel_L):
    return {
        "fuel_L": fuel_L,
        "compliant": fuel_L <= FS_CONSTRAINTS["fuel_tank"]["max"],
        "max_L": FS_CONSTRAINTS["fuel_tank"]["max"]
    }

def check_sound_level(db, test_rpm_pct=50):
    return {
        "sound_db": db,
        "test_rpm_pct": test_rpm_pct,
        "compliant": db <= FS_CONSTRAINTS["sound_limit"]["max"],
        "max_db": FS_CONSTRAINTS["sound_limit"]["max"]
    }

def full_fs_compliance_check(vehicle_params):
    results = {}
    results["weight"] = {"value": vehicle_params.get("weight", 0), "passed": vehicle_params.get("weight", 0) >= FS_MIN_WEIGHT}
    results["length"] = {"value": vehicle_params.get("length", 0), "passed": vehicle_params.get("length", 0) <= FS_MAX_LENGTH}
    results["width"] = {"value": vehicle_params.get("width", 0), "passed": vehicle_params.get("width", 0) <= FS_MAX_WIDTH}
    results["displacement"] = {"value": vehicle_params.get("displacement", 0), "passed": vehicle_params.get("displacement", 0) <= FS_MAX_DISPLACEMENT}
    results["intake_restrictor"] = {"value": vehicle_params.get("restrictor", 0), "passed": vehicle_params.get("restrictor", 0) <= FS_RESTRICTOR}
    results["fuel_tank"] = check_fuel_system(vehicle_params.get("fuel_tank", 0))
    results["rollbar"] = check_rollbar_spec(vehicle_params.get("rollbar_od", 0), vehicle_params.get("rollbar_wall", 0))
    results["cockpit"] = check_cockpit_opening(vehicle_params.get("cockpit_width", 0), vehicle_params.get("cockpit_height", 0))
    
    all_passed = all(r.get("passed", r.get("compliant", False)) for r in results.values())
    return {"passed": all_passed, "checks": results}