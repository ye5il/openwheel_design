from utils.constants import FS_MAX_LENGTH, FS_MAX_WIDTH

TUBE_DIAMETERS = [
    "19.05x1.2", "19.05x1.6", "22.22x1.2", "22.22x1.6", 
    "25.4x1.2", "25.4x1.6", "25.4x2.0", "25.4x2.5",
    "31.75x1.6", "31.75x2.0", "31.75x2.5", "38.1x2.0"
]

MONOCOQUE_THICKNESS = {
    "al7075": [0.8, 1.0, 1.2, 1.5, 2.0],
    "carbon_fiber": [1.0, 1.5, 2.0, 2.5, 3.0]
}

def parse_tube_spec(spec):
    if isinstance(spec, tuple):
        od, wall = spec[0], spec[1]
        length = spec[2] if len(spec) > 2 else 1000
    else:
        parts = spec.lower().replace("x", " ").split()
        od = float(parts[0])
        wall = float(parts[1]) if len(parts) > 1 else 1.6
        length = float(parts[2]) if len(parts) > 2 else 1000
    return {"od": od, "wall": wall, "length": length}

def get_tube_od(spec):
    return parse_tube_spec(spec)["od"]

def get_tube_wall(spec):
    return parse_tube_spec(spec)["wall"]

def calculate_standard_weight(od_mm, wall_mm, length_mm, material_type="4130"):
    from chassis.materials import calculate_tube_weight
    return calculate_tube_weight(od_mm, wall_mm, length_mm, material_type)

def check_fs_dimensions(length_mm, width_mm, height_mm=None):
    result = {
        "length_ok": length_mm <= FS_MAX_LENGTH,
        "width_ok": width_mm <= FS_MAX_WIDTH,
        "length_mm": length_mm,
        "width_mm": width_mm
    }
    if height_mm:
        result["height_mm"] = height_mm
    
    result["passed"] = result["length_ok"] and result["width_ok"]
    return result

def list_tube_sizes():
    return TUBE_DIAMETERS

def get_monocoque_thicknesses(material):
    return MONOCOQUE_THICKNESS.get(material, [])