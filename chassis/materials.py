from utils.constants import (
    STEEL_DENSITY, ALUMINUM_DENSITY, CARBON_FIBER_DENSITY,
    CHROMOLY_YIELD, CHROMOLY_ULTIMATE, AL7075_YIELD, AL7075_ULTIMATE, CF_TENSILE,
    E_STEEL, E_ALUMINUM, E_CF_TOW
)

MATERIALS = {
    "4130": {
        "name": "AISI 4130 Chromoly Steel",
        "density": STEEL_DENSITY,
        "yield_strength": CHROMOLY_YIELD,
        "ultimate_strength": CHROMOLY_ULTIMATE,
        "youngs_modulus": E_STEEL,
        "poisson": 0.29,
        "common": True,
        "applications": ["spaceframe", "rollbar"]
    },
    "al7075": {
        "name": "Aluminum 7075-T6",
        "density": ALUMINUM_DENSITY,
        "yield_strength": AL7075_YIELD,
        "ultimate_strength": AL7075_ULTIMATE,
        "youngs_modulus": E_ALUMINUM,
        "poisson": 0.33,
        "common": True,
        "applications": ["monocoque", "hub", "upright"]
    },
    "carbon_fiber": {
        "name": "Carbon Fiber Prepreg",
        "density": CARBON_FIBER_DENSITY,
        "tensile_strength": CF_TENSILE,
        "youngs_modulus": E_CF_TOW,
        "poisson": 0.28,
        "common": True,
        "applications": ["monocoque", "bodywork", "wing"]
    }
}

def get_material(name):
    name = name.lower()
    if name in ["4130", "chromoly", "aisi 4130"]:
        name = "4130"
    elif name in ["7075", "al7075", "aluminum"]:
        name = "al7075"
    elif name in ["cf", "carbon", "carbon fiber"]:
        name = "carbon_fiber"
    return MATERIALS.get(name)

def calculate_tube_weight(od_mm, wall_mm, length_mm, material):
    mat = get_material(material)
    if not mat:
        raise ValueError(f"Unknown material: {material}")
    
    od = od_mm / 1000
    wall = wall_mm / 1000
    length = length_mm / 1000
    
    outer_radius = od / 2
    inner_radius = outer_radius - wall
    
    if inner_radius <= 0:
        raise ValueError("Wall thickness too large for given OD")
    
    area = 3.14159 * (outer_radius**2 - inner_radius**2)
    volume = area * length
    
    return {
        "weight": volume * mat["density"],
        "volume": volume,
        "cross_section_area": area,
        "material": mat["name"]
    }

def list_materials():
    return {k: v["name"] for k, v in MATERIALS.items()}