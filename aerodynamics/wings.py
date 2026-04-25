import math

WING_PROFILES = {
    "NACA_0012": {"CL_per_deg": 0.095, "CD_base": 0.008, "stall_deg": 16},
    "NACA_2412": {"CL_per_deg": 0.100, "CD_base": 0.009, "stall_deg": 14},
    "NACA_4412": {"CL_per_deg": 0.105, "CD_base": 0.010, "stall_deg": 13},
}

def estimate_wing_CL(profile_name, angle_deg):
    profile = WING_PROFILES.get(profile_name, WING_PROFILES["NACA_2412"])
    stall = profile["stall_deg"]
    if abs(angle_deg) >= stall:
        return {"CL_estimated": profile["CL_per_deg"] * stall, "status": "stalled"}
    return {"CL_estimated": profile["CL_per_deg"] * angle_deg, "status": "linear"}

def estimate_wing_CD(profile_name, angle_deg):
    profile = WING_PROFILES.get(profile_name, WING_PROFILES["NACA_2412"])
    cl_data = estimate_wing_CL(profile_name, angle_deg)
    CL = cl_data["CL_estimated"]
    CD = profile["CD_base"] + 0.04 * CL**2
    return {"CD_estimated": round(CD, 4), "profile": profile_name}

def calculate_wing_downforce(profile_name, aoa_deg, span_mm, chord_mm, speed_kmh):
    area = (span_mm * chord_mm) / 1e6
    cl = estimate_wing_CL(profile_name, aoa_deg)
    df = calculate_downforce(cl["CL_estimated"], area, speed_kmh)
    cd = estimate_wing_CD(profile_name, aoa_deg)
    dr = calculate_drag(cd["CD_estimated"], area, speed_kmh)
    return {
        "downforce_N": df,
        "drag_N": dr,
        "area_m2": round(area, 4),
        "CL": cl["CL_estimated"],
        "CD": cd["CD_estimated"]
    }

def check_wing_stall(profile_name, aoa_deg):
    profile = WING_PROFILES.get(profile_name, WING_PROFILES["NACA_2412"])
    return {
        "stall_deg": profile["stall_deg"],
        "current_deg": aoa_deg,
        "stalled": abs(aoa_deg) >= profile["stall_deg"]
    }

def list_profiles():
    return list(WING_PROFILES.keys())