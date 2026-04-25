import math

CAMBER_TYPICAL = {"front": (-3.5, -2.0), "rear": (-2.0, -1.0)}
TOE_TYPICAL = {"front": (0.5, 2.0), "rear": (0, 2.0)}
CASTER_TYPICAL = (3, 8)

def check_camber(camber_deg, axle="front"):
    in_range = CAMBER_TYPICAL.get(axle, (-3.5, -2.0))
    lo, hi = in_range
    return {
        "value_deg": camber_deg,
        "sign": "negative (correct)" if camber_deg < 0 else "positive (unusual)",
        "in_typical_range": lo <= camber_deg <= hi,
        "effect": "cornering grip ↑" if camber_deg < 0 else "straight grip only"
    }

def check_toe(toe_mm, axle="front"):
    in_range = TOE_TYPICAL.get(axle, (0.5, 2.0))
    lo, hi = in_range
    return {
        "value_mm": toe_mm,
        "sign": "toe-in (stable)" if toe_mm > 0 else "toe-out (agile)",
        "in_typical_range": lo <= toe_mm <= hi,
        "effect": "stability ↑, turn-in ↓" if toe_mm > 0 else "turn-in ↑, stability ↓"
    }

def check_caster(caster_deg):
    lo, hi = CASTER_TYPICAL
    return {
        "value_deg": caster_deg,
        "in_typical_range": lo <= caster_deg <= hi,
        "effect": "self-centering ↑, steering feedback ↑"
    }

def calculate_ackermann(wheelbase_mm, track_width_mm, turn_radius_mm):
    inner_angle = math.degrees(math.atan(wheelbase_mm / turn_radius_mm))
    outer_angle = math.degrees(math.atan(wheelbase_mm / (turn_radius_mm + track_width_mm)))
    return {
        "inner_angle_deg": round(inner_angle, 2),
        "outer_angle_deg": round(outer_angle, 2),
        "ackermann_percent": round((inner_angle - outer_angle) / inner_angle * 100, 1),
        "ideal": True
    }

def calculate_scrub_radius(kingpin_inclination_deg, caster_deg, wheel_offset_mm):
    kp_rad = math.radians(kingpin_inclination_deg)
    c_rad = math.radians(caster_deg)
    scrub = wheel_offset_mm * math.tan(kp_rad) * math.cos(c_rad)
    return {
        "scrub_radius_mm": round(scrub, 2),
        "effect": "low scrub = light steering" if abs(scrub) < 30 else "high scrub = stable"
    }

def check_suspension_geometry(camber, toe, caster, ride_height_mm, axle="front"):
    c = check_camber(camber, axle)
    t = check_toe(toe, axle)
    cs = check_caster(caster)
    return {
        "camber": c,
        "toe": t,
        "caster": cs,
        "ride_height_mm": ride_height_mm,
        "all_in_range": c["in_typical_range"] and t["in_typical_range"] and cs["in_typical_range"]
    }