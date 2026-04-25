MAX_POINTS = {
    "acceleration": 75,
    "skidpad": 75,
    "autocross": 125,
    "endurance": 275,
    "efficiency": 100,
    "cost": 100,
    "design": 150,
    "business": 75,
    "total": 975
}

def score_acceleration(your_time_s, min_time_s, max_time_s):
    if your_time_s <= 0 or min_time_s <= 0:
        return 0
    score = 95.5 * ((max_time_s**2 / your_time_s**2) - 1) / ((max_time_s**2 / min_time_s**2) - 1) + 4.5
    return round(max(0, min(score, 80)), 1)

def score_skidpad(your_time_s, min_time_s, max_time_s):
    if your_time_s <= 0 or min_time_s <= 0:
        return 0
    score = 71.5 * ((min_time_s / your_time_s)**2 - 1) / ((min_time_s / max_time_s)**2 - 1) + 3.5
    return round(max(0, min(score, 80)), 1)

def score_autocross(your_time_s, min_time_s, max_time_s):
    return score_acceleration(your_time_s, min_time_s, max_time_s)

def score_endurance(your_time_s, min_time_s, dnf=False):
    if dnf:
        return 0
    score = 275 * (1 - your_time_s / min_time_s) + 50
    return round(max(0, min(score, 300)), 1)

def score_efficiency(your_fuel_L, best_fuel_L, endurance_points):
    ratio = best_fuel_L / your_fuel_L if your_fuel_L > 0 else 0
    score = endurance_points * ratio
    return round(max(0, min(score, 100)), 1)

def calculate_total_score(accel, skidpad, autocross, endurance, efficiency, cost, design, business):
    return {
        "acceleration": accel,
        "skidpad": skidpad,
        "autocross": autocross,
        "endurance": endurance,
        "efficiency": efficiency,
        "cost": cost,
        "design": design,
        "business": business,
        "total": accel + skidpad + autocross + endurance + efficiency + cost + design + business
    }

def estimate_position(your_score, all_scores):
    rank = sum(1 for s in all_scores if s > your_score) + 1
    return {"rank": rank, "total_teams": len(all_scores) + 1}

def get_max_points():
    return MAX_POINTS