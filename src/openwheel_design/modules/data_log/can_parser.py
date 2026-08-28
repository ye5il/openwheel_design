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

def parse_can_message(msg_id, data_bytes, dbc_entry=None):
    """Parse a CAN message from raw bytes.

    Args:
        msg_id: CAN message identifier (int).
        data_bytes: Raw CAN payload (bytes, up to 8 bytes).
        dbc_entry: Optional dict describing signal layout. Keys:
            - "signals": list of dicts, each with:
                "name" (str), "start_bit" (int), "length" (int, in bits),
                "scale" (float, default 1), "offset" (float, default 0),
                "byte_order" (str, "little_endian" or "big_endian", default "little_endian").
            If omitted, returns a raw byte breakdown.

    Returns:
        dict with parsed signal values, or raw breakdown if no dbc_entry.
    """
    import struct

    if not isinstance(data_bytes, (bytes, bytearray)):
        raise TypeError("data_bytes must be bytes or bytearray")

    if dbc_entry is not None:
        signals = dbc_entry.get("signals", [])
        result = {"id": msg_id, "signals": {}}

        # Convert data_bytes to a single 64-bit integer for bit extraction
        padded = bytes(data_bytes) + b'\x00' * (8 - len(data_bytes))
        data_le = struct.unpack('<Q', padded)[0]
        data_be = struct.unpack('>Q', padded)[0]

        for sig in signals:
            name = sig["name"]
            start_bit = sig["start_bit"]
            length = sig["length"]
            scale = sig.get("scale", 1)
            offset = sig.get("offset", 0)
            byte_order = sig.get("byte_order", "little_endian")

            if byte_order == "big_endian":
                raw_val = (data_be >> start_bit) & ((1 << length) - 1)
            else:
                raw_val = (data_le >> start_bit) & ((1 << length) - 1)

            result["signals"][name] = round(raw_val * scale + offset, 6)
        return result

    # No dbc_entry: return raw byte breakdown plus CAN_MESSAGES metadata if available
    msg = CAN_MESSAGES.get(msg_id)
    raw = {"id": msg_id, "raw_bytes": [b for b in data_bytes], "length": len(data_bytes)}
    if msg:
        raw["name"] = msg["name"]
        raw["fields"] = msg["fields"]
    return raw

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

def export_to_csv(data, filepath):
    """Export a list of dicts to a CSV file.

    Args:
        data: list of dicts. All dicts should have the same keys.
        filepath: path string for the output CSV file.

    Returns:
        dict with "exported" (bool), "filepath" (str), "rows" (int).
    """
    import csv

    if not data:
        with open(filepath, 'w', newline='') as f:
            pass
        return {"exported": True, "filepath": filepath, "rows": 0}

    fieldnames = list(data[0].keys())
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    return {"exported": True, "filepath": filepath, "rows": len(data)}