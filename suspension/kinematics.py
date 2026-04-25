import math

def calculate_roll_center(upper_wishbone_length, lower_wishbone_length,
                          upper_angle_deg, lower_angle_deg, track_width_mm):
    upper_rad = math.radians(upper_angle_deg)
    lower_rad = math.radians(lower_angle_deg)
    
    upper_z = upper_wishbone_length * math.cos(upper_rad)
    lower_z = lower_wishbone_length * math.cos(lower_rad)
    
    if upper_z != lower_z:
        roll_center_height = (upper_wishbone_length * lower_wishbone_length * 
                           math.sin(upper_rad - lower_rad)) / (upper_z - lower_z)
    else:
        roll_center_height = 0
    
    return {
        "roll_center_height_mm": round(roll_center_height, 1),
        "upper_ic_z_mm": round(upper_z, 1),
        "lower_ic_z_mm": round(lower_z, 1),
        "interpretation": "good" if 30 <= roll_center_height <= 80 else "check geometry"
    }

def calculate_camber_gain(upper_wishbone_length, lower_wishbone_length, travel_mm):
    upper_angle = math.atan(upper_wishbone_length / 1000)
    lower_angle = math.atan(lower_wishbone_length / 1000)
    
    gain = (math.tan(lower_angle) - math.tan(upper_angle)) / (travel_mm / 1000)
    return {
        "gain_deg_per_mm": round(math.degrees(gain), 3),
        "effect": "good camber gain" if gain < 0 else "poor camber gain"
    }

def calculate_anti_dive(front_geometry, brake_bias_front):
    return {
        "anti_dive_percent": round(front_geometry * 100, 1),
        "interpretation": "acceptable" if 20 <= front_geometry * 100 <= 50 else "too harsh or soft"
    }

def calculate_anti_squat(rear_geometry, weight_distribution_rear):
    return {
        "anti_squat_percent": round(rear_geometry * 100, 1),
        "interpretation": "acceptable" if 20 <= rear_geometry * 100 <= 50 else "too harsh or soft"
    }

def calculate_instant_center(upper_wishbone, lower_wishbone):
    if upper_wishbone[0] != lower_wishbone[0]:
        t = upper_wishbone[1] / (upper_wishbone[0] - lower_wishbone[0])
        ic_x = upper_wishbone[0] + t * (upper_wishbone[0] - lower_wishbone[0])
        ic_z = upper_wishbone[1] - t * upper_wishbone[1]
    else:
        ic_x, ic_z = upper_wishbone[0], 0
    
    return {
        "ic_x_mm": round(ic_x, 1),
        "ic_z_mm": round(ic_z, 1)
    }