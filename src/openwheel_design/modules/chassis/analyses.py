from .materials import get_material, calculate_tube_weight
from .geometry import parse_tube_spec
from .constraints import check_fs_compliance
from ..utils.constants import GRAVITY

def analyze_weight(tubes, material="4130"):
    mat = get_material(material)
    if not mat:
        raise ValueError(f"Unknown material: {material}")
    
    result = {
        "tubes": [],
        "total_weight": 0,
        "total_length": 0,
        "material": mat["name"]
    }
    
    for tube_spec in tubes:
        parsed = parse_tube_spec(tube_spec)
        od = parsed["od"]
        wall = parsed["wall"]
        length = parsed.get("length", 1000)
        
        weight_data = calculate_tube_weight(od, wall, length, material)
        result["tubes"].append({
            "spec": tube_spec,
            "weight": weight_data["weight"]
        })
        result["total_weight"] += weight_data["weight"]
        result["total_length"] += length
    
    return result

def reverse_engineer_weight(target_weight, material="4130", tube_od_mm=25.4):
    mat = get_material(material)
    if not mat:
        raise ValueError(f"Unknown material: {material}")
    
    wall_thicknesses = [1.2, 1.6, 2.0, 2.5]
    results = []
    
    for wall in wall_thicknesses:
        try:
            data = calculate_tube_weight(tube_od_mm, wall, 1000, material)
            weight_per_m = data["weight"]
            
            required_length = target_weight / weight_per_m if weight_per_m > 0 else 0
            results.append({
                "od": tube_od_mm,
                "wall": wall,
                "weight_per_m": weight_per_m,
                "total_length_mm": required_length
            })
        except (ValueError, KeyError, ZeroDivisionError):
            pass
    
    return {
        "target_weight": target_weight,
        "material": mat["name"],
        "possible_configurations": results
    }

def reverse_engineer_target(
    target_weight, 
    material="4130", 
    category="FS",
    constraints=None
):
    results = []
    
    tube_sizes = [19.05, 22.22, 25.4, 31.75, 38.1]
    wall_sizes = [1.2, 1.6, 2.0, 2.5]
    
    for od in tube_sizes:
        for wall in wall_sizes:
            try:
                weight_per_m = calculate_tube_weight(od, wall, 1000, material)["weight"]
                if weight_per_m > 0:
                    total_length = target_weight / weight_per_m
                    results.append({
                        "tube_od": od,
                        "tube_wall": wall,
                        "weight_per_m": weight_per_m,
                        "total_length_m": total_length
                    })
            except (ValueError, KeyError, ZeroDivisionError):
                pass
    
    results.sort(key=lambda x: x["weight_per_m"])
    
    return {
        "target_weight": target_weight,
        "category": category,
        "material": material,
        "configurations": results[:10]
    }

def analyze_stress(force_N, area_mm2, material="4130"):
    mat = get_material(material)
    if not mat:
        raise ValueError(f"Unknown material: {material}")
    yield_strength = mat["yield_strength"]
    stress_MPa = force_N / area_mm2
    return {
        "force_N": force_N,
        "area_mm2": area_mm2,
        "stress_MPa": stress_MPa,
        "yield_check": stress_MPa < yield_strength,
        "yield_strength_MPa": yield_strength,
        "safety_factor": yield_strength / stress_MPa if stress_MPa > 0 else float('inf')
    }

def optimize_weight(target_weight, max_cost=None):
    results = []
    
    materials = ["4130", "al7075"]
    
    for mat in materials:
        try:
            config = reverse_engineer_target(target_weight, material=mat)
            for cfg in config["configurations"][:3]:
                results.append({
                    "material": mat,
                    "od": cfg["tube_od"],
                    "wall": cfg["tube_wall"],
                    "total_length_m": cfg["total_length_m"]
                })
        except (ValueError, KeyError, ZeroDivisionError):
            pass
    
    results.sort(key=lambda x: x.get("od", 0))
    
    return {
        "target_weight": target_weight,
        "optimal_configurations": results[:6]
    }

def optimize_cost(target_performance, budget):
    raise NotImplementedError(
        "optimize_cost is a stub with no real cost model. "
        "Needs material pricing data to produce valid results."
    )

def calculate_bending_stress(M, c, I):
    stress = (M * c) / I
    return stress

def calculate_section_modulus(d, t):
    from math import pi
    Do = d
    Di = d - 2*t
    I = pi/64 * (Do**4 - Di**4)
    c = Do/2
    return I/c

def analyze_structure(tubes, material="4130", apply_fs_check=False, vehicle_weight=None):
    result = analyze_weight(tubes, material)
    
    if apply_fs_check and vehicle_weight:
        fs_result = check_fs_compliance(
            weight=vehicle_weight,
            length=2100,
            width=1200
        )
        result["fs_compliance"] = fs_result
    
    result["warnings"] = []
    if result["total_weight"] > 30:
        result["warnings"].append("Weight exceeds typical FS spaceframe. Consider optimization.")
    
    return result