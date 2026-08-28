"""Physics-based validation tests for dynamics, suspension, and tire calculations."""
import math
import pytest


def test_wheel_loads_sum_to_vehicle_weight():
    """For a 200 kg car, all 4 corner loads must sum to mass * g = 1962 N."""
    from openwheel_design.modules.dynamics.load_transfer import calculate_wheel_loads

    result = calculate_wheel_loads(
        mass_kg=200, front_weight_pct=50, cog_height_mm=300,
        track_mm=1200, wheelbase_mm=1550, lat_g=0, long_g=0
    )
    total = result["FL_N"] + result["FR_N"] + result["RL_N"] + result["RR_N"]
    assert abs(total - 200 * 9.81) < 10, f"Total {total} != 1962 N"


def test_wheel_loads_sum_preserved_under_lateral():
    """Sum must stay constant even with lateral g."""
    from openwheel_design.modules.dynamics.load_transfer import calculate_wheel_loads

    result = calculate_wheel_loads(
        mass_kg=200, front_weight_pct=45, cog_height_mm=300,
        track_mm=1200, wheelbase_mm=1550, lat_g=1.5, long_g=0
    )
    total = result["FL_N"] + result["FR_N"] + result["RL_N"] + result["RR_N"]
    assert abs(total - 200 * 9.81) < 10, f"Total {total} != 1962 N under lateral g"


def test_wheel_loads_sum_preserved_under_combined():
    """Sum must stay constant under combined lat + long g."""
    from openwheel_design.modules.dynamics.load_transfer import calculate_wheel_loads

    result = calculate_wheel_loads(
        mass_kg=200, front_weight_pct=48, cog_height_mm=280,
        track_mm=1200, wheelbase_mm=1550, lat_g=1.2, long_g=0.8
    )
    total = result["FL_N"] + result["FR_N"] + result["RL_N"] + result["RR_N"]
    assert abs(total - 200 * 9.81) < 10, f"Total {total} != 1962 N under combined g"


def test_ackermann_inner_greater_than_outer():
    """Inner wheel must steer more than outer wheel for correct Ackermann."""
    from openwheel_design.modules.suspension.geometry import calculate_ackermann

    result = calculate_ackermann(
        wheelbase_mm=1550, track_width_mm=1200, turn_radius_mm=5000
    )
    assert result["inner_angle_deg"] > result["outer_angle_deg"], (
        f"Inner {result['inner_angle_deg']} should be > outer {result['outer_angle_deg']}"
    )
    assert result["ackermann_percent"] > 0


def test_cold_pressure_absolute_conversion():
    """Cold pressure must use absolute pressure (gauge + atm) for Gay-Lussac.
    hot=1.4 bar gauge at 80C, cold at 25C:
    P_cold = (1.4 + 1.013) * (298.15/353.15) - 1.013 = ~1.02 bar gauge.
    The old bug applied the ratio to gauge directly:
    1.4 * 298.15/353.15 = 1.18 (wrong, too high because it ignores atm offset).
    """
    from openwheel_design.modules.tires.thermal_model import estimate_cold_pressure

    result = estimate_cold_pressure(1.4, ambient_C=25, operating_C=80)
    naive = 1.4 * (25 + 273.15) / (80 + 273.15)
    # Correct absolute conversion gives DIFFERENT result than naive gauge scaling
    assert abs(result - naive) > 0.05, (
        f"Result {result} too close to naive {naive:.3f}, absolute conversion not applied"
    )
    # Physics check: (hot_gauge + atm) * T_cold/T_hot - atm
    expected = (1.4 + 1.01325) * (298.15 / 353.15) - 1.01325
    assert abs(result - expected) < 0.02, f"Cold pressure {result} != {expected:.3f}"


def test_roll_center_height_reasonable():
    """Roll center should be in 0-100 mm range for typical FSAE geometry."""
    from openwheel_design.modules.suspension.kinematics import calculate_roll_center

    # Typical FSAE front-view double-wishbone geometry (mm)
    # Upper arm: inner at (200, 300), outer at (550, 280)
    # Lower arm: inner at (150, 150), outer at (580, 130)
    result = calculate_roll_center(
        upper_inner=(200, 300), upper_outer=(550, 280),
        lower_inner=(150, 150), lower_outer=(580, 130),
        track_width_mm=1200
    )
    h = result["roll_center_height_mm"]
    assert 0 <= h <= 100, f"Roll center height {h} mm outside 0-100 range"


def test_anti_dive_varies_with_brake_bias():
    """Anti-dive must change when brake bias changes."""
    from openwheel_design.modules.suspension.kinematics import calculate_anti_dive

    r1 = calculate_anti_dive(
        side_view_angle_deg=10, brake_bias_front=0.6,
        wheelbase_mm=1550, cog_height_mm=300
    )
    r2 = calculate_anti_dive(
        side_view_angle_deg=10, brake_bias_front=0.8,
        wheelbase_mm=1550, cog_height_mm=300
    )
    assert r1["anti_dive_percent"] != r2["anti_dive_percent"], (
        "Anti-dive should change with brake bias"
    )
    assert r2["anti_dive_percent"] > r1["anti_dive_percent"], (
        "Higher brake bias front should increase anti-dive"
    )


def test_check_torque_capacity_real_check():
    """check_torque_capacity must fail when torque exceeds material limits."""
    from openwheel_design.modules.transmission.differential import check_torque_capacity

    # Small shaft, high torque should fail
    result = check_torque_capacity(
        input_torque_Nm=500, shaft_diameter_mm=10,
        material_shear_strength_MPa=350, safety_factor=2.0
    )
    assert result["adequate"] is False, "Small shaft should not handle 500 Nm"

    # Large shaft, low torque should pass
    result2 = check_torque_capacity(
        input_torque_Nm=50, shaft_diameter_mm=30,
        material_shear_strength_MPa=350, safety_factor=2.0
    )
    assert result2["adequate"] is True, "Large shaft should handle 50 Nm"
