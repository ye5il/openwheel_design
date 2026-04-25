def identify_weak_events(scores_dict):
    max_loss = {}
    for event, points in scores_dict.items():
        max_pts = {"acceleration": 75, "skidpad": 75, "autocross": 125, 
                  "endurance": 275, "efficiency": 100}.get(event, 0)
        if max_pts > 0:
            max_loss[event] = max_pts - points
    sorted_events = sorted(max_loss.items(), key=lambda x: x[1], reverse=True)
    return sorted_events[:3]

def calculate_point_sensitivity(param_name, change_percent, event="endurance"):
    sensitivity_table = {
        ("weight", 1, "endurance"): 0.5,
        ("power", 1, "acceleration"): 0.3,
        ("weight", 1, "autocross"): 0.4,
    }
    key = (param_name, change_percent, event)
    points = sensitivity_table.get(key, 0)
    return {
        "parameter": param_name,
        "change_percent": change_percent,
        "event": event,
        "estimated_points": points,
        "note": "Based on typical FS data"
    }

def suggest_priorities(resources_remaining, scores_dict):
    weak = identify_weak_events(scores_dict)
    priorities = []
    for event, loss in weak[:3]:
        priorities.append({
            "event": event,
            "potential_gain": loss,
            "recommendation": f"Improve {event} first"
        })
    return priorities