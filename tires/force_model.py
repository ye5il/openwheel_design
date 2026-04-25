import math

TIRE_COMPOUNDS = {
    "soft": {"peak_slip_deg": 8, "mu": 1.6},
    "medium": {"peak_slip_deg": 10, "mu": 1.5},
    "hard": {"peak_slip_deg": 13, "mu": 1.4},
}

def calculate_max_lateral_force(normal_force_N, mu=1.5):
    return round(normal_force_N * mu, 0)

def calculate_traction_circle(lat_N, long_N, max_N):
    combined = math.sqrt(lat_N**2 + long_N**2)
    return {
        "combined_force_N": round(combined),
        "max_force_N": max_N,
        "utilization_pct": round(combined / max_N * 100, 1),
        "within_limit": combined <= max_N
    }

def estimate_slip_angle_peak(compound="medium"):
    spec = TIRE_COMPOUNDS.get(compound, TIRE_COMPOUNDS["medium"])
    return {
        "peak_slip_deg": spec["peak_slip_deg"],
        "compound": compound,
        "mu": spec["mu"]
    }

def simple_pacejka(slip_deg, Fz_N, B=10, C=1.9, D=1.5, E=0.97):
    alpha = math.radians(slip_deg)
    Fy = Fz_N * D * math.sin(C * math.atan(B * alpha - E * (B * alpha - math.atan(B * alpha))))
    return round(Fy, 1)

def calculate_load_sensitivity(Fz_N, mu_ref=1.6, sensitivity=0.05, Fz_ref=2000):
    mu_eff = mu_ref - sensitivity * (Fz_N / Fz_ref - 1)
    return {
        "mu_effective": round(mu_eff, 3),
        "sensitivity": sensitivity
    }

def list_compounds():
    return list(TIRE_COMPOUNDS.keys())