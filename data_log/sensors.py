SENSOR_TYPES = {
    "wheel_speed": {"unit": "km/h", "range": (0, 300), "accuracy": 0.1},
    "suspension_travel": {"unit": "mm", "range": (0, 100), "accuracy": 0.5},
    "steering_angle": {"unit": "deg", "range": (-180, 180), "accuracy": 0.5},
    "brake_pressure": {"unit": "bar", "range": (0, 150), "accuracy": 0.5},
    "throttle_position": {"unit": "%", "range": (0, 100), "accuracy": 0.5},
    "engine_rpm": {"unit": "rpm", "range": (0, 15000), "accuracy": 50},
    "engine_temp": {"unit": "C", "range": (-40, 150), "accuracy": 1},
    "oil_pressure": {"unit": "bar", "range": (0, 10), "accuracy": 0.1},
    "tire_temp": {"unit": "C", "range": (0, 150), "accuracy": 1},
    "tire_pressure": {"unit": "bar", "range": (0, 5), "accuracy": 0.01},
    "gforce_lateral": {"unit": "g", "range": (-3, 3), "accuracy": 0.01},
    "gforce_longitudinal": {"unit": "g", "range": (-3, 3), "accuracy": 0.01},
    "yaw_rate": {"unit": "deg/s", "range": (-100, 100), "accuracy": 0.1},
}

def read_sensor(sensor_type, raw_value):
    spec = SENSOR_TYPES.get(sensor_type)
    if not spec:
        return None
    return {
        "type": sensor_type,
        "raw": raw_value,
        "unit": spec["unit"],
        "in_range": spec["range"][0] <= raw_value <= spec["range"][1]
    }

def calibrate_sensor(sensor_type, measured, reference):
    spec = SENSOR_TYPES.get(sensor_type)
    if not spec:
        return None
    error = measured - reference
    scale_factor = reference / measured if measured != 0 else 1
    return {
        "sensor_type": sensor_type,
        "measured": measured,
        "reference": reference,
        "error": error,
        "scale_factor": round(scale_factor, 4),
        "note": "Apply scale_factor to correct readings"
    }

def check_sensor_health(sensor_type, reading):
    spec = SENSOR_TYPES.get(sensor_type)
    if not spec:
        return {"error": "Unknown sensor type"}
    return {
        "type": sensor_type,
        "value": reading,
        "unit": spec["unit"],
        "healthy": spec["range"][0] <= reading <= spec["range"][1],
        "error": None
    }

def list_sensors():
    return list(SENSOR_TYPES.keys())

def get_sensor_spec(sensor_type):
    return SENSOR_TYPES.get(sensor_type)