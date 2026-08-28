"""
Scoring formula, aerodynamics, and physics calculation tests.
"""

def test_skidpad_max_points():
    """Best time should get maximum skidpad points (75)."""
    from openwheel_design.modules.scoring.events import score_skidpad
    result = score_skidpad(5.0, 5.0, 7.0)
    assert result == 75, f"Expected 75, got {result}"

def test_skidpad_min_points():
    """Worst time (at max) should get minimum skidpad points (3.5)."""
    from openwheel_design.modules.scoring.events import score_skidpad
    result = score_skidpad(7.0, 5.0, 7.0)
    assert result == 3.5, f"Expected 3.5, got {result}"

def test_endurance_max_points():
    """Best time should get maximum endurance points (275)."""
    from openwheel_design.modules.scoring.events import score_endurance
    result = score_endurance(1500, 1500, 1500 * 1.45)
    assert result == 275, f"Expected 275, got {result}"

def test_endurance_min_points():
    """Worst time (at max) should get minimum endurance points (25)."""
    from openwheel_design.modules.scoring.events import score_endurance
    result = score_endurance(1500 * 1.45, 1500, 1500 * 1.45)
    assert result == 25, f"Expected 25, got {result}"

def test_max_points_sum_to_1000():
    """MAX_POINTS total should be 1000."""
    from openwheel_design.modules.scoring.events import MAX_POINTS
    assert MAX_POINTS["total"] == 1000, f"Expected 1000, got {MAX_POINTS['total']}"
    event_sum = sum(v for k, v in MAX_POINTS.items() if k != "total")
    assert event_sum == 1000, f"Expected event sum 1000, got {event_sum}"

def test_acceleration_max_points():
    """Best time should get maximum acceleration points (100)."""
    from openwheel_design.modules.scoring.events import score_acceleration
    result = score_acceleration(4.0, 4.0, 4.0 * 1.45)
    assert result == 100, f"Expected 100, got {result}"

def test_wing_downforce_no_error():
    """calculate_wing_downforce should run without NameError."""
    from openwheel_design.modules.aerodynamics.wings import calculate_wing_downforce
    result = calculate_wing_downforce("NACA_2412", 10, 1200, 300, 80)
    assert "downforce_N" in result
    assert "drag_N" in result
    assert result["downforce_N"] > 0

def test_cornering_speed_no_double_mu():
    """estimate_cornering_speed should not double-count friction."""
    from openwheel_design.modules.aerodynamics.forces import estimate_cornering_speed
    import math
    grip_N = 1.5 * 200 * 9.81
    aero_N = 500
    radius_m = 20
    mass_kg = 200
    result_kmh = estimate_cornering_speed(grip_N, aero_N, radius_m, mass_kg)
    total_grip = grip_N + aero_N
    expected_v = math.sqrt(total_grip * radius_m / mass_kg)
    expected_kmh = round(expected_v * 3.6, 1)
    assert result_kmh == expected_kmh, f"Expected {expected_kmh}, got {result_kmh}"
