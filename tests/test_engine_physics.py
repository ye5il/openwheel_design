import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from openwheel_design.modules.engine.constraints import calculate_restricted_power
from openwheel_design.modules.engine.cooling import estimate_heat_rejection
from openwheel_design.modules.engine.analyses import calculate_0_100_estimation
from openwheel_design.modules.engine.database import ENGINES, get_engine
from openwheel_design.modules.transmission.gearbox import optimize_gear_ratios


def test_restricted_power_20mm():
    result = calculate_restricted_power(20, 119)
    assert 55 <= result <= 75, f"Expected 55-75 hp, got {result:.1f}"


def test_restricted_power_caps_at_stock():
    result = calculate_restricted_power(50, 60)
    assert result == 60, f"Should cap at stock power, got {result:.1f}"


def test_heat_rejection_119hp():
    result = estimate_heat_rejection("Honda_CBR600RR", 119)
    kw = result["heat_rejected_kw"]
    assert 60 <= kw <= 100, f"Expected 60-100 kW, got {kw}"


def test_0_100_estimation():
    result = calculate_0_100_estimation("Honda_CBR600RR", 300)
    t = result["estimated_0_100_kmh"]
    assert 3 <= t <= 6, f"Expected 3-6 s, got {t}"


def test_bmw_s1000rr_in_database():
    assert "BMW_S1000RR" in ENGINES, "BMW_S1000RR should be in ENGINES"
    eng = ENGINES["BMW_S1000RR"]
    assert eng["name"] == "BMW S1000RR"
    assert eng["bore_mm"] == 80.0
    assert eng["stroke_mm"] == 49.7


def test_suzuki_s1000rr_removed():
    assert "Suzuki_S1000RR" not in ENGINES, "Suzuki_S1000RR should not exist"


def test_optimize_gear_ratios_uses_params():
    r1 = optimize_gear_ratios(max_rpm=12000, num_gears=4,
                               first_ratio=3.0, top_ratio=1.0)
    r2 = optimize_gear_ratios(max_rpm=12000, num_gears=6,
                               first_ratio=4.0, top_ratio=0.8)
    assert r1["ratios"] != r2["ratios"], "Different inputs should give different ratios"
    assert r1["num_gears"] == 4
    assert r2["num_gears"] == 6
    assert len(r1["ratios"]) == 4
    assert len(r2["ratios"]) == 6
