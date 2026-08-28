"""Tests for the Quasi-Steady-State lap simulation engine."""

import math

import pytest

from openwheel_design.simulation.lap_qss import (
    DEFAULT_AUTOCROSS_TRACK,
    discretize_track,
    generate_ggv_envelope,
    simulate_lap,
    solve_velocity_profile,
)


# ---- helpers ----------------------------------------------------------------

SIMPLE_VEHICLE = {
    "mass_kg": 300,
    "CL": 1.8,
    "CD": 0.9,
    "frontal_area_m2": 1.1,
    "mu": 1.4,
    "engine_power_kW": 55,
    "gear_ratio": 3.0,
    "final_drive": 3.5,
    "tire_radius_m": 0.228,
    "brake_mu": 1.1,
}

GRAVITY = 9.81


# ---- 1. Skidpad analytical -------------------------------------------------

def test_skidpad_analytical():
    """On a flat circle (no aero), v = sqrt(mu * g * R).

    For mu=1.5, R=7.625 m the analytical speed is ~10.6 m/s.
    A single-corner "track" should produce a speed within 5 % of this.
    """
    R = 7.625
    mu = 1.5
    v_analytical = math.sqrt(mu * GRAVITY * R)  # ~10.6 m/s

    # Build a no-aero, single-corner track
    skidpad_vehicle = {
        "mass_kg": 280,
        "CL": 0.0,    # no aero
        "CD": 0.0,
        "frontal_area_m2": 1.1,
        "mu": mu,
        "engine_power_kW": 60,
        "gear_ratio": 3.0,
        "final_drive": 3.5,
        "tire_radius_m": 0.228,
        "brake_mu": 1.2,
    }

    skidpad_track = [{"radius_m": R, "length_m": 2 * math.pi * R}]

    result = simulate_lap(skidpad_vehicle, skidpad_track)

    # Most of the speed profile should hover near v_analytical.
    # Use the average speed as the representative value.
    avg_ms = result["avg_speed_kmh"] / 3.6
    assert abs(avg_ms - v_analytical) / v_analytical < 0.05, (
        f"Expected ~{v_analytical:.2f} m/s, got {avg_ms:.2f} m/s"
    )


# ---- 2. Lap time reasonable ------------------------------------------------

def test_lap_time_reasonable():
    """Full autocross lap time should fall in 50-90 s."""
    result = simulate_lap(SIMPLE_VEHICLE)
    assert 50 <= result["lap_time_s"] <= 90, (
        f"Lap time {result['lap_time_s']:.1f} s is outside 50-90 s window"
    )


# ---- 3. GGV envelope shape -------------------------------------------------

def test_ggv_lat_g_increases_with_speed():
    """Max lateral g should increase with speed (more downforce)."""
    ggv = generate_ggv_envelope(SIMPLE_VEHICLE)
    lat = ggv["max_lat_g"]
    # At least the last value should be larger than the first
    assert lat[-1] > lat[0], (
        f"max_lat_g at 130 km/h ({lat[-1]}) should exceed "
        f"max_lat_g at 10 km/h ({lat[0]})"
    )
    # Check monotonically non-decreasing
    for i in range(1, len(lat)):
        assert lat[i] >= lat[i - 1], (
            f"max_lat_g dropped at index {i}: {lat[i-1]} -> {lat[i]}"
        )


# ---- 4. Energy positive ----------------------------------------------------

def test_energy_positive():
    """Energy consumed must be positive (drag * distance > 0)."""
    result = simulate_lap(SIMPLE_VEHICLE)
    assert result["energy_consumption_kWh"] > 0


# ---- 5. Speed profile has variation ----------------------------------------

def test_speed_profile_has_variation():
    """Max speed should exceed min speed — we have straights and corners."""
    result = simulate_lap(SIMPLE_VEHICLE)
    assert result["max_speed_kmh"] > result["min_speed_kmh"], (
        "Speed profile is flat — max equals min"
    )


# ---- bonus: discretize_track sanity ----------------------------------------

def test_discretize_preserves_total_length():
    """Total length of discretised segments should match the input."""
    segments = discretize_track(DEFAULT_AUTOCROSS_TRACK)
    total_input = sum(c["length_m"] for c in DEFAULT_AUTOCROSS_TRACK)
    total_output = sum(s["length_m"] for s in segments)
    assert abs(total_output - total_input) < 0.5, (
        f"Length mismatch: input={total_input:.1f}, output={total_output:.1f}"
    )
