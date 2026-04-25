def calculate_gps_speed(lat1, lon1, t1, lat2, lon2, t2):
    import math
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    distance = 2 * R * math.asin(math.sqrt(a))
    dt = t2 - t1
    speed = distance / dt if dt > 0 else 0
    return round(speed * 3.6, 1)

def calculate_lap_time(gps_data):
    if not gps_data:
        return None
    times = [p["timestamp"] for p in gps_data]
    return {
        "lap_time_s": max(times) - min(times),
        "start_time": min(times),
        "end_time": max(times)
    }

def calculate_corner_speed(data, corner_index):
    return {"speed_kmh": data[corner_index].get("speed", 0)}

def analyze_racing_line(gps_data):
    speeds = [p.get("speed", 0) for p in gps_data]
    return {
        "min_speed": min(speeds),
        "max_speed": max(speeds),
        "avg_speed": round(sum(speeds) / len(speeds), 1)
    }

def detect_driver_inputs(accel_data, brake_data, steering_data):
    events = []
    for i, acc in enumerate(accel_data):
        if acc > 90 and brake_data[i] > 5:
            events.append({"timestamp": i, "event": "crossing", "severity": "high"})
    return events