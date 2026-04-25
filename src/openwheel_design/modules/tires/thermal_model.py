TIRE_OPTIMAL_TEMP = {
    "soft": {"min": 75, "peak": 90, "max": 105},
    "medium": {"min": 80, "peak": 100, "max": 115},
    "hard": {"min": 85, "peak": 105, "max": 120},
}

def check_tire_temperature(temp_C, compound="medium"):
    window = TIRE_OPTIMAL_TEMP.get(compound, TIRE_OPTIMAL_TEMP["medium"])
    if temp_C < window["min"]:
        status = "too_cold"
    elif temp_C > window["max"]:
        status = "overheating"
    else:
        status = "optimal"
    return {"temp_C": temp_C, "status": status, "window": window}

def estimate_cold_pressure(hot_bar, ambient_C=20, operating_C=90):
    T_cold = ambient_C + 273.15
    T_hot = operating_C + 273.15
    return round(hot_bar * T_cold / T_hot, 2)

def check_tire_pressure(bar, axle="front"):
    ranges = {"front": (1.1, 1.8), "rear": (0.9, 1.6)}
    lo, hi = ranges.get(axle, (1.1, 1.8))
    return {
        "pressure_bar": bar,
        "in_range": lo <= bar <= hi,
        "recommended": f"{lo}-{hi} bar"
    }