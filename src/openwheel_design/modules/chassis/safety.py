from ..utils.constants import GRAVITY

ROLLCAGE_MIN_HEIGHT = 50

FIREWALL_THICKNESS = {
    "aluminum": 1.5,
    "steel": 1.0,
    "carbon": 2.0
}

def calculate_rollbar_force(weight_kg, safety_factor=2.5):
    return weight_kg * GRAVITY * safety_factor

def calculate_harness_force(weight_kg, accel_g=3.0):
    return weight_kg * GRAVITY * accel_g

def calculate_rollbar_size(height_mm, tube_od_mm=38.1):
    return {
        "min_height": height_mm + ROLLCAGE_MIN_HEIGHT,
        "recommended_od": tube_od_mm,
        "formula": "T45 Chromoly or equivalent"
    }

def check_rollbar_clearance(rollbar_height_mm, driver_height_mm, seat_angle=45):
    required = driver_height_mm + ROLLCAGE_MIN_HEIGHT + 50
    return {
        "required_height": required,
        "actual_height": rollbar_height_mm,
        "meets_requirement": rollbar_height_mm >= required
    }

def calculate_firewall_area(width_mm, height_mm):
    return width_mm * height_mm

def get_firewall_spec(material):
    return {
        "thickness": FIREWALL_THICKNESS.get(material.lower(), 1.5),
        "material": material,
        "note": "Minimum 1.5mm aluminum or steel equivalent"
    }

def calculate_fuel_cell_volume(fuel_capacity_liters):
    return fuel_capacity_liters * 1.1

def check_firewall_material(material):
    mat = material.lower()
    return {
        "approved": mat in FIREWALL_THICKNESS,
        "thickness": FIREWALL_THICKNESS.get(mat, 1.5)
    }