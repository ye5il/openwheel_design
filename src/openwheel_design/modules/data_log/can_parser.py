CAN_MESSAGES = {
    0x100: {"name": "EngineRPM", "period_ms": 10, "fields": ["rpm", "target_rpm"]},
    0x101: {"name": "Throttle", "period_ms": 10, "fields": ["position", "target"]},
    0x102: {"name": "Brake", "period_ms": 10, "fields": ["pressure_front", "pressure_rear"]},
    0x103: {"name": "Steering", "period_ms": 10, "fields": ["angle", "torque"]},
    0x200: {"name": "WheelSpeed", "period_ms": 10, "fields": ["fl", "fr", "rl", "rr"]},
    0x201: {"name": "Suspension", "period_ms": 20, "fields": ["fl_disp", "fr_disp", "rl_disp", "rr_disp"]},
    0x202: {"name": "Temperature", "period_ms": 100, "fields": ["engine", "oil", "coolant", "diff"]},
    0x300: {"name": "GPS", "period_ms": 50, "fields": ["lat", "lon", "speed", "heading"]},
    0x301: {"name": "IMU", "period_ms": 10, "fields": ["ax", "ay", "az", "gx", "gy", "gz"]},
    0x400: {"name": "Battery", "period_ms": 100, "fields": ["voltage", "current", "soc", "temp"]},
}

def parse_can_message(msg_id, data_bytes):
    msg = CAN_MESSAGES.get(msg_id)
    if not msg:
        return None
    return {
        "id": msg_id,
        "name": msg["name"],
        "data": data_bytes,
        "parsed": True
    }

def create_log_header():
    return {
        "created": "timestamp",
        "format_version": "1.0",
        "channels": list(CAN_MESSAGES.values()),
        "sample_rate": 100
    }

def calculate_sample_count(duration_s, sample_rate_hz=100):
    return duration_s * sample_rate_hz

def estimate_file_size(duration_s, num_channels=20, sample_rate_hz=100):
    bytes_per_sample = num_channels * 4
    total_bytes = duration_s * sample_rate_hz * bytes_per_sample
    return {
        "duration_s": duration_s,
        "estimated_mb": round(total_bytes / 1e6, 2),
        "bytes": total_bytes
    }

def validate_data_stream(data_points, expected_channels):
    missing = [ch for ch in expected_channels if ch not in data_points]
    return {
        "valid": len(missing) == 0,
        "missing_channels": missing,
        "total_points": len(data_points)
    }

def export_to_csv(data, filename):
    return {"file": filename, "rows": len(data), " exported": True}