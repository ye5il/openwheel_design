"""Vehicle profile — JSON save/load for all design parameters."""

import json
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_PROFILE: Dict[str, Any] = {
    "meta": {"name": "Yeni Arac", "team": "", "season": ""},
    "chassis": {
        "tube_od_mm": 25.4,
        "wall_mm": 1.6,
        "length_mm": 5000.0,
        "material": "4130",
    },
    "engine": {
        "engine_key": "Honda_CBR600RR",
        "restrictor_mm": 20.0,
        "gear_ratio": 2.5,
        "final_drive": 3.5,
        "tire_radius_m": 0.26,
    },
    "suspension": {
        "track_width_mm": 1200.0,
        "wheelbase_mm": 1550.0,
        "turn_radius_mm": 4500.0,
        "front_roll_stiffness": 60.0,
        "rear_roll_stiffness": 40.0,
    },
    "aerodynamics": {
        "naca_code": "2412",
        "alpha_deg": 5.0,
        "n_panels": 100,
        "wing_area_m2": 0.5,
        "speed_kmh": 80.0,
    },
    "tires": {
        "hot_pressure_bar": 0.83,
        "hot_temp_c": 80.0,
        "cold_temp_c": 20.0,
    },
    "dynamics": {
        "mass_kg": 300.0,
        "cog_height_mm": 300.0,
        "front_weight_pct": 0.48,
    },
    "brakes": {
        "mc_bore_mm": 15.875,
        "caliper_bore_mm": 30.0,
        "caliper_pistons": 2,
        "pad_area_mm2": 1200.0,
        "rotor_diameter_mm": 220.0,
    },
    "scoring": {
        "accel_time_s": 4.5,
        "skidpad_time_s": 5.5,
        "autocross_time_s": 60.0,
        "endurance_time_s": 1500.0,
    },
    "fem": {
        "tube_od_mm": 25.4,
        "wall_mm": 1.6,
        "material": "4130",
    },
    "vibration": {
        "sprung_mass_kg": 60.0,
        "unsprung_mass_kg": 15.0,
        "spring_rate_N_mm": 25.0,
        "tire_rate_N_mm": 150.0,
        "damping_Ns_mm": 1.5,
        "bump_height_mm": 25.0,
    },
}


def new_profile() -> Dict[str, Any]:
    """Return a deep copy of the default profile."""
    return json.loads(json.dumps(DEFAULT_PROFILE))


def load_profile(path: Path) -> Dict[str, Any]:
    """Load a vehicle profile from *path*, filling missing keys from defaults."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    merged = new_profile()
    for section, defaults in merged.items():
        if section in data and isinstance(defaults, dict):
            defaults.update(data[section])
        elif section in data:
            merged[section] = data[section]
    return merged


def save_profile(profile: Dict[str, Any], path: Path) -> None:
    """Save a vehicle profile to *path* as pretty-printed JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
