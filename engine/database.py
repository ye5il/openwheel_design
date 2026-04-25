ENGINES = {
    "Yamaha_YZF_R6": {
        "name": "Yamaha YZF-R6",
        "year": "2006-2020",
        "displacement_cc": 599,
        "power_hp": 117,
        "power_kW": 87.1,
        "torque_Nm": 61.7,
        "torque_rpm": 10500,
        "power_rpm": 14500,
        "weight_kg": 185,
        "bore_mm": 67.0,
        "stroke_mm": 42.5,
        "compression": 13.1,
        "cylinders": 4,
        "valves": 16,
        "cooling": "liquid",
        "fuel_system": "fuel injection",
        "common_in_fs": True,
        "notes": "Most common FS engine, excellent parts availability"
    },
    "Honda_CBR600RR": {
        "name": "Honda CBR600RR",
        "year": "2003-2024",
        "displacement_cc": 599,
        "power_hp": 119,
        "power_kW": 88,
        "torque_Nm": 63,
        "torque_rpm": 11500,
        "power_rpm": 14000,
        "weight_kg": 187,
        "bore_mm": 67.0,
        "stroke_mm": 42.5,
        "compression": 12.2,
        "cylinders": 4,
        "valves": 16,
        "cooling": "liquid",
        "fuel_system": "fuel injection",
        "common_in_fs": True,
        "notes": "Honda reliability, widely used in FS"
    },
    "Suzuki_GSXR600": {
        "name": "Suzuki GSX-R600",
        "year": "2001-2024",
        "displacement_cc": 599,
        "power_hp": 124,
        "power_kW": 92.5,
        "torque_Nm": 69.6,
        "torque_rpm": 11500,
        "power_rpm": 13500,
        "weight_kg": 187,
        "bore_mm": 67.0,
        "stroke_mm": 42.5,
        "compression": 12.9,
        "cylinders": 4,
        "valves": 16,
        "cooling": "liquid",
        "fuel_system": "fuel injection",
        "common_in_fs": True,
        "notes": "Highest stock power among 600cc class"
    },
    "Kawasaki_ZX6R": {
        "name": "Kawasaki ZX-6R",
        "year": "1995-2024",
        "displacement_cc": 599,
        "power_hp": 115,
        "power_kW": 85.8,
        "torque_Nm": 66,
        "torque_rpm": 11000,
        "power_rpm": 13500,
        "weight_kg": 190,
        "bore_mm": 67.0,
        "stroke_mm": 42.5,
        "compression": 12.9,
        "cylinders": 4,
        "valves": 16,
        "cooling": "liquid",
        "fuel_system": "fuel injection",
        "common_in_fs": True,
        "notes": "Strong mid-range torque"
    },
    "Triumph_TT600": {
        "name": "Triumph TT600",
        "year": "2000-2003",
        "displacement_cc": 599,
        "power_hp": 108,
        "power_kW": 80.5,
        "torque_Nm": 54,
        "torque_rpm": 10500,
        "power_rpm": 12000,
        "weight_kg": 175,
        "bore_mm": 66.0,
        "stroke_mm": 43.5,
        "compression": 12.0,
        "cylinders": 4,
        "valves": 16,
        "cooling": "liquid",
        "fuel_system": "fuel injection",
        "common_in_fs": False,
        "notes": "Lighter option, less common"
    },
    "Yamaha_YZF_R1": {
        "name": "Yamaha YZF-R1",
        "year": "2015-2024",
        "displacement_cc": 998,
        "power_hp": 200,
        "power_kW": 149,
        "torque_Nm": 112,
        "torque_rpm": 11500,
        "power_rpm": 14000,
        "weight_kg": 197,
        "bore_mm": 79.0,
        "stroke_mm": 50.9,
        "compression": 13.1,
        "cylinders": 4,
        "valves": 16,
        "cooling": "liquid",
        "fuel_system": "fuel injection",
        "common_in_fs": False,
        "notes": "1000cc class, high power, requires more tuning"
    },
    "Kawasaki_ZX10R": {
        "name": "Kawasaki ZX-10R",
        "year": "2016-2024",
        "displacement_cc": 998,
        "power_hp": 203,
        "power_kW": 151,
        "torque_Nm": 115,
        "torque_rpm": 11700,
        "power_rpm": 14000,
        "weight_kg": 207,
        "bore_mm": 76.0,
        "stroke_mm": 55.0,
        "compression": 13.1,
        "cylinders": 4,
        "valves": 16,
        "cooling": "liquid",
        "fuel_system": "fuel injection",
        "common_in_fs": False,
        "notes": "1000cc class, very high power"
    },
    "Suzuki_S1000RR": {
        "name": "Suzuki S1000RR",
        "year": "2011-2024",
        "displacement_cc": 999,
        "power_hp": 205,
        "power_kW": 153,
        "torque_Nm": 117,
        "torque_rpm": 11000,
        "power_rpm": 13500,
        "weight_kg": 203,
        "bore_mm": 76.0,
        "stroke_mm": 55.0,
        "compression": 13.1,
        "cylinders": 4,
        "valves": 16,
        "cooling": "liquid",
        "fuel_system": "fuel injection",
        "common_in_fs": False,
        "notes": "1000cc class, race focused"
    }
}

_custom_engines = {}

def get_engine(name):
    name = name.replace(" ", "_").replace("-", "_")
    if name in _custom_engines:
        return _custom_engines[name]
    return ENGINES.get(name)

def add_engine(name, specs):
    _custom_engines[name] = specs

def list_engines(common_only=False):
    result = {}
    for key, val in ENGINES.items():
        if common_only and not val.get("common_in_fs", False):
            continue
        result[key] = val["name"]
    return result

def get_engine_specs(name):
    eng = get_engine(name)
    if not eng:
        return None
    return {
        "name": eng["name"],
        "displacement": f"{eng['displacement_cc']}cc",
        "power": f"{eng['power_hp']} HP",
        "torque": f"{eng['torque_Nm']} Nm",
        "weight": f"{eng['weight_kg']} kg",
        "power_to_weight": round(eng["power_kW"] / eng["weight_kg"], 3)
    }

def calculate_power_to_weight(engine_name, vehicle_weight_kg):
    eng = get_engine(engine_name)
    if not eng:
        raise ValueError(f"Engine not found: {engine_name}")
    
    kW = eng["power_kW"]
    kg = vehicle_weight_kg
    
    return {
        "engine": eng["name"],
        "vehicle_weight_kg": kg,
        "engine_power_kW": kW,
        "power_to_weight_kW_per_kg": round(kW / kg, 3),
        "power_to_weight_hp_per_kg": round(eng["power_hp"] / kg, 3)
    }

def search_engines(**criteria):
    results = []
    for key, eng in ENGINES.items():
        match = True
        for crit_key, crit_val in criteria.items():
            if eng.get(crit_key) != crit_val:
                match = False
                break
        if match:
            results.append((key, eng))
    return dict(results)