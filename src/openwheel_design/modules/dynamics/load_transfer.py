from ..utils.constants import GRAVITY

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
                        wheelbase_mm, lat_g=0, long_g=0,
                        front_roll_stiffness_pct=50):
    total_weight = mass_kg * GRAVITY
    front_axle = total_weight * front_weight_pct / 100
    rear_axle = total_weight * (100 - front_weight_pct) / 100

    # Static load per corner
    fl_static = front_axle / 2
    fr_static = front_axle / 2
    rl_static = rear_axle / 2
    rr_static = rear_axle / 2

    # Total lateral load transfer (N), split between axles by roll stiffness
    total_lat = calculate_lateral_load_transfer(
        mass_kg, lat_g, cog_height_mm, track_mm)["load_transfer_N"]
    front_lat = total_lat * front_roll_stiffness_pct / 100
    rear_lat = total_lat * (100 - front_roll_stiffness_pct) / 100

    # Longitudinal load transfer (N), shared equally between left/right
    long_tr = calculate_longitudinal_load_transfer(
        mass_kg, long_g, cog_height_mm, wheelbase_mm)["load_transfer_N"]

    # Positive lat_g = turning right => left wheels loaded
    # Positive long_g = accelerating => rear wheels loaded
    fl = fl_static + front_lat - long_tr / 2
    fr = fr_static - front_lat - long_tr / 2
    rl = rl_static + rear_lat + long_tr / 2
    rr = rr_static - rear_lat + long_tr / 2

    return {
        "FL_N": round(fl, 0),
        "FR_N": round(fr, 0),
        "RL_N": round(rl, 0),
        "RR_N": round(rr, 0)
    }