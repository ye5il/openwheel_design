MAX_POINTS = {
    "acceleration": 100,
    "skidpad": 75,
    "autocross": 125,
    "endurance": 275,
    "efficiency": 100,
    "cost": 100,
    "design": 150,
    "presentation": 75,
    "total": 1000
}

def score_acceleration(your_time_s, min_time_s, max_time_s=None):
    if your_time_s <= 0 or min_time_s <= 0:
        return 0
    if max_time_s is None:
        max_time_s = min_time_s * 1.45
    if your_time_s >= max_time_s:
        return 4.5
    score = 95.5 * ((max_time_s / your_time_s) - 1) / ((max_time_s / min_time_s) - 1) + 4.5
    return round(max(4.5, min(score, MAX_POINTS["acceleration"])), 1)

def score_skidpad(your_time_s, min_time_s, max_time_s=None):
    if your_time_s <= 0 or min_time_s <= 0:
        return 0
    if max_time_s is None:
        max_time_s = min_time_s * 1.45
    if your_time_s >= max_time_s:
        return 3.5
    score = 71.5 * ((max_time_s / your_time_s)**2 - 1) / ((max_time_s / min_time_s)**2 - 1) + 3.5
    return round(max(3.5, min(score, MAX_POINTS["skidpad"])), 1)

def score_autocross(your_time_s, min_time_s, max_time_s=None):
    if your_time_s <= 0 or min_time_s <= 0:
        return 0
    if max_time_s is None:
        max_time_s = min_time_s * 1.45
    if your_time_s >= max_time_s:
        return 6.5
    score = 118.5 * ((max_time_s / your_time_s) - 1) / ((max_time_s / min_time_s) - 1) + 6.5
    return round(max(6.5, min(score, MAX_POINTS["autocross"])), 1)

def score_endurance(your_time_s, min_time_s, max_time_s=None, dnf=False):
    if dnf:
        return 25
    if your_time_s <= 0 or min_time_s <= 0:
        return 0
    if max_time_s is None:
        max_time_s = min_time_s * 1.45
    if your_time_s >= max_time_s:
        return 25
    score = 250 * ((max_time_s / your_time_s) - 1) / ((max_time_s / min_time_s) - 1) + 25
    return round(max(25, min(score, MAX_POINTS["endurance"])), 1)

def score_efficiency(your_fuel_L, best_fuel_L, endurance_points):
    ratio = best_fuel_L / your_fuel_L if your_fuel_L > 0 else 0
    score = endurance_points * ratio
    return round(max(0, min(score, MAX_POINTS["efficiency"])), 1)

def calculate_total_score(accel, skidpad, autocross, endurance, efficiency, cost, design, presentation):
    return {
        "acceleration": accel,
        "skidpad": skidpad,
        "autocross": autocross,
        "endurance": endurance,
        "efficiency": efficiency,
        "cost": cost,
        "design": design,
        "presentation": presentation,
        "total": accel + skidpad + autocross + endurance + efficiency + cost + design + presentation
    }

def estimate_position(your_score, all_scores):
    rank = sum(1 for s in all_scores if s > your_score) + 1
    return {"rank": rank, "total_teams": len(all_scores) + 1}

def get_max_points():
    return MAX_POINTS
