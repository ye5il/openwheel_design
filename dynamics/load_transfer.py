from utils.constants import GRAVITY

def calculate_lateral_load_transfer(mass_kg, lateral_g, cog_height_mm, track_mm):
    ay = lateral_g * GRAVITY
    ltr = mass_kg * ay * (cog_height_mm / 1000) / (track_mm / 1000)
    return {
        "load_transfer_N": round(ltr, 0),
        "lateral_g": lateral_g,
        "cog_height_mm": cog_height_mm,
        "track_mm": track_mm
    }

def calculate_longitudinal_load_transfer(mass_kg, accel_g, cog_height_mm, wheelbase_mm):
    ax = accel_g * GRAVITY
    ltr = mass_kg * ax * (cog_height_mm / 1000) / (wheelbase_mm / 1000)
    return {
        "load_transfer_N": round(ltr, 0),
        "accel_g": accel_g,
        "cog_height_mm": cog_height_mm,
        "wheelbase_mm": wheelbase_mm
    }

def calculate_wheel_loads(mass_kg, front_weight_pct, cog_height_mm, track_mm, 
                        wheelbase_mm, lat_g=0, long_g=0):
    front_static = mass_kg * GRAVITY * front_weight_pct / 100
    rear_static = mass_kg * GRAVITY * (100 - front_weight_pct) / 100
    
    lat_transfer = calculate_lateral_load_transfer(mass_kg, lat_g, cog_height_mm, track_mm)
    long_transfer = calculate_longitudinal_load_transfer(mass_kg, long_g, cog_height_mm, wheelbase_mm)
    
    fl = front_static + lat_transfer["load_transfer_N"] - long_transfer["load_transfer_N"] / 2
    fr = front_static - lat_transfer["load_transfer_N"] - long_transfer["load_transfer_N"] / 2
    rl = rear_static + lat_transfer["load_transfer_N"] + long_transfer["load_transfer_N"] / 2
    rr = rear_static - lat_transfer["load_transfer_N"] + long_transfer["load_transfer_N"] / 2
    
    return {
        "FL_N": round(fl, 0),
        "FR_N": round(fr, 0),
        "RL_N": round(rl, 0),
        "RR_N": round(rr, 0)
    }