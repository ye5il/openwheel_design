import math


def _line_intersection(p1, p2, p3, p4):
    """Find intersection of line through (p1,p2) and line through (p3,p4).
    Each point is (x, y). Returns (x, y) or None if parallel."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-12:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    ix = x1 + t * (x2 - x1)
    iy = y1 + t * (y2 - y1)
    return (ix, iy)


def calculate_instant_center(upper_inner, upper_outer, lower_inner, lower_outer):
    """Find instant center as intersection of upper and lower A-arm lines.
    Each argument is an (x, y) tuple in mm (side view / front view coordinates).
    """
    ic = _line_intersection(upper_inner, upper_outer, lower_inner, lower_outer)
    if ic is None:
        return {"ic_x_mm": 0.0, "ic_z_mm": 0.0, "note": "parallel arms, IC at infinity"}
    return {
        "ic_x_mm": round(ic[0], 1),
        "ic_z_mm": round(ic[1], 1)
    }


def calculate_roll_center(upper_inner, upper_outer, lower_inner, lower_outer,
                          track_width_mm):
    """Roll center from front-view double-wishbone geometry.
    Points are (x, y) in mm. x = lateral, y = vertical.
    Tire contact patch is at (track_width_mm / 2, 0).
    Roll center = intersection of line from contact patch through IC with
    the vehicle centerline (x = 0).
    """
    ic = _line_intersection(upper_inner, upper_outer, lower_inner, lower_outer)
    if ic is None:
        return {
            "roll_center_height_mm": 0.0,
            "ic_x_mm": 0.0,
            "ic_z_mm": 0.0,
            "interpretation": "parallel arms, roll center at ground"
        }

    contact_patch = (track_width_mm / 2, 0)
    centerline_pt = (0, 0)

    # Line from contact patch through IC, intersected with x = 0
    ic_x, ic_z = ic
    if abs(contact_patch[0] - ic_x) < 1e-12:
        rc_height = ic_z
    else:
        slope = (ic_z - contact_patch[1]) / (ic_x - contact_patch[0])
        rc_height = contact_patch[1] + slope * (centerline_pt[0] - contact_patch[0])

    interp = "good" if 0 <= rc_height <= 80 else "check geometry"
    return {
        "roll_center_height_mm": round(rc_height, 1),
        "ic_x_mm": round(ic_x, 1),
        "ic_z_mm": round(ic_z, 1),
        "interpretation": interp
    }


def calculate_camber_gain(upper_inner, upper_outer, lower_inner, lower_outer,
                          travel_mm=1.0):
    """Camber gain as degrees per mm of vertical wheel travel.
    Uses small-displacement approximation on a 2D double-wishbone.
    Positive travel = bump (wheel moves up).
    """
    ux1, uy1 = upper_inner
    ux2, uy2 = upper_outer
    lx1, ly1 = lower_inner
    lx2, ly2 = lower_outer

    upper_len = math.hypot(ux2 - ux1, uy2 - uy1)
    lower_len = math.hypot(lx2 - lx1, ly2 - ly1)

    # Current angles of arms (from horizontal)
    upper_angle = math.atan2(uy2 - uy1, ux2 - ux1)
    lower_angle = math.atan2(ly2 - ly1, lx2 - lx1)

    # Upright length (distance between outer points)
    upright_len = math.hypot(ux2 - lx2, uy2 - ly2)

    # Current camber = angle of upright from vertical
    upright_angle = math.atan2(ux2 - lx2, uy2 - ly2)
    camber_0 = math.degrees(upright_angle)

    # Displace outer points by travel_mm vertically, recalculate
    dt = travel_mm
    # Lower outer moves up by dt; recalculate where upper outer ends up
    new_ly2 = ly2 + dt
    # Lower arm keeps its length, so new lx2:
    dl = lower_len**2 - (new_ly2 - ly1)**2
    if dl < 0:
        dl = 0
    new_lx2 = lx1 + math.sqrt(dl) * (1 if lx2 >= lx1 else -1)

    # Upper outer also moves up by approx dt; recalculate with arm length
    new_uy2 = uy2 + dt
    du = upper_len**2 - (new_uy2 - uy1)**2
    if du < 0:
        du = 0
    new_ux2 = ux1 + math.sqrt(du) * (1 if ux2 >= ux1 else -1)

    new_upright_angle = math.atan2(new_ux2 - new_lx2, new_uy2 - new_ly2)
    camber_1 = math.degrees(new_upright_angle)

    gain = (camber_1 - camber_0) / dt if abs(dt) > 1e-12 else 0
    return {
        "gain_deg_per_mm": round(gain, 3),
        "effect": "good camber gain" if gain < 0 else "poor camber gain"
    }


def calculate_anti_dive(side_view_angle_deg, brake_bias_front, wheelbase_mm,
                        cog_height_mm):
    """Anti-dive percentage for front suspension.
    anti_dive % = tan(side_view_swing_arm_angle) * brake_bias * wheelbase / cog_height * 100
    """
    angle_rad = math.radians(side_view_angle_deg)
    anti_dive = (math.tan(angle_rad) * brake_bias_front *
                 wheelbase_mm / cog_height_mm) * 100
    if anti_dive < 20:
        interp = "low anti-dive, more dive under braking"
    elif anti_dive > 50:
        interp = "high anti-dive, harsh ride under braking"
    else:
        interp = "acceptable"
    return {
        "anti_dive_percent": round(anti_dive, 1),
        "interpretation": interp
    }


def calculate_anti_squat(side_view_angle_deg, drive_weight_pct_rear,
                         wheelbase_mm, cog_height_mm):
    """Anti-squat percentage for rear suspension.
    anti_squat % = tan(side_view_swing_arm_angle) * rear_weight_pct/100 * wheelbase / cog_height * 100
    """
    angle_rad = math.radians(side_view_angle_deg)
    anti_squat = (math.tan(angle_rad) * (drive_weight_pct_rear / 100) *
                  wheelbase_mm / cog_height_mm) * 100
    if anti_squat < 20:
        interp = "low anti-squat, more squat under acceleration"
    elif anti_squat > 50:
        interp = "high anti-squat, harsh ride under acceleration"
    else:
        interp = "acceptable"
    return {
        "anti_squat_percent": round(anti_squat, 1),
        "interpretation": interp
    }
