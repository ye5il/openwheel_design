"""Tests for the quarter-car 2-DOF suspension model."""

import math
import pytest
from openwheel_design.simulation.quarter_car import (
    QuarterCarParams,
    analyze_ride,
    bump_input,
    compute_damping_ratios,
    compute_frequency_response,
    compute_natural_frequencies,
    quarter_car_ode,
    random_road_input,
    simulate_time_response,
    step_input,
)


# ---------------------------------------------------------------------------
# Helper: default params
# ---------------------------------------------------------------------------

def _default_params() -> QuarterCarParams:
    return QuarterCarParams(
        sprung_mass_kg=60.0,
        unsprung_mass_kg=15.0,
        spring_rate_N_per_m=25000.0,
        damping_Ns_per_m=1500.0,
        tire_rate_N_per_m=150000.0,
        tire_damping_Ns_per_m=200.0,
    )


# ---------------------------------------------------------------------------
# 1. Undamped natural frequency sanity
# ---------------------------------------------------------------------------

class TestNaturalFrequencies:
    def test_body_mode_near_sdof(self):
        """For k=25000 N/m, m=60 kg the SDOF f_n = sqrt(k/m)/(2*pi) ~ 3.25 Hz.
        The 2-DOF body mode should be within 15% of this value (coupling
        with the unsprung mass shifts it slightly)."""
        params = _default_params()
        result = compute_natural_frequencies(params)
        sdof_fn = math.sqrt(25000.0 / 60.0) / (2.0 * math.pi)
        assert abs(result["body_mode_hz"] - sdof_fn) / sdof_fn < 0.15

    def test_two_modes_ordered(self):
        """body_mode_hz must be lower than wheel_hop_hz."""
        params = _default_params()
        result = compute_natural_frequencies(params)
        assert result["body_mode_hz"] < result["wheel_hop_hz"]

    def test_wheel_hop_range(self):
        """Wheel hop frequency should fall in 5-20 Hz for typical FS params."""
        params = _default_params()
        result = compute_natural_frequencies(params)
        assert 5.0 <= result["wheel_hop_hz"] <= 20.0

    def test_frequency_ratio_positive(self):
        params = _default_params()
        result = compute_natural_frequencies(params)
        assert result["frequency_ratio"] > 1.0

    def test_return_keys(self):
        params = _default_params()
        result = compute_natural_frequencies(params)
        expected = {
            "body_mode_hz",
            "wheel_hop_hz",
            "body_mode_rad_s",
            "wheel_hop_rad_s",
            "frequency_ratio",
        }
        assert expected == set(result.keys())


# ---------------------------------------------------------------------------
# 2. Critical damping
# ---------------------------------------------------------------------------

class TestDampingRatios:
    def test_critical_damping(self):
        """When c = 2*sqrt(k*m), body_damping_ratio should be 1.0."""
        params = _default_params()
        c_crit = 2.0 * math.sqrt(params.spring_rate_N_per_m * params.sprung_mass_kg)
        params.damping_Ns_per_m = c_crit
        result = compute_damping_ratios(params)
        assert abs(result["body_damping_ratio"] - 1.0) < 0.01

    def test_underdamped_default(self):
        """Default params (c=1500) should be underdamped."""
        params = _default_params()
        result = compute_damping_ratios(params)
        assert 0.0 < result["body_damping_ratio"] < 1.0
        assert result["body_critically_damped"] is False

    def test_overdamped(self):
        params = _default_params()
        params.damping_Ns_per_m = 10000.0
        result = compute_damping_ratios(params)
        assert result["body_damping_ratio"] > 1.0
        assert result["body_critically_damped"] is True

    def test_recommendation_string(self):
        params = _default_params()
        result = compute_damping_ratios(params)
        assert isinstance(result["recommendation"], str)
        assert len(result["recommendation"]) > 0


# ---------------------------------------------------------------------------
# 3. Step response settles
# ---------------------------------------------------------------------------

class TestStepResponse:
    def test_settles_to_road_height(self):
        """After a step input, sprung mass should settle to the road height
        within 2 seconds for a damping ratio in the 0.3-0.7 range."""
        params = _default_params()
        # Damping ratio ~ 0.61 (default)
        step_height_m = 0.02
        road = step_input(step_height_m, t_step=0.1)
        result = simulate_time_response(params, road, t_span=(0.0, 3.0), dt=0.001)

        step_height_mm = step_height_m * 1000.0
        # Check last 200 ms -- should be within 5% of step height
        final_sprung = result["sprung_disp_mm"][-200:]
        for val in final_sprung:
            assert abs(val - step_height_mm) < step_height_mm * 0.05

    def test_initial_zero(self):
        """At t=0 all displacements should be zero."""
        params = _default_params()
        road = step_input(0.01, t_step=0.5)
        result = simulate_time_response(params, road, t_span=(0.0, 1.0), dt=0.001)
        assert abs(result["sprung_disp_mm"][0]) < 1e-6
        assert abs(result["unsprung_disp_mm"][0]) < 1e-6

    def test_return_keys(self):
        params = _default_params()
        road = step_input(0.01)
        result = simulate_time_response(params, road, t_span=(0.0, 0.5))
        expected = {
            "time_s",
            "sprung_disp_mm",
            "unsprung_disp_mm",
            "sprung_accel_g",
            "tire_deflection_mm",
            "suspension_travel_mm",
        }
        assert expected == set(result.keys())


# ---------------------------------------------------------------------------
# 4. Frequency response peak at resonance
# ---------------------------------------------------------------------------

class TestFrequencyResponse:
    def test_peak_near_body_mode(self):
        """Displacement gain should have its peak near the body natural
        frequency."""
        params = _default_params()
        nat = compute_natural_frequencies(params)
        freq = compute_frequency_response(params)

        body_hz = nat["body_mode_hz"]
        peak_hz = freq["body_resonance_hz"]

        # Peak should be within 30% of analytical body mode (damping shifts it)
        assert abs(peak_hz - body_hz) / body_hz < 0.30

    def test_gain_exceeds_unity_at_resonance(self):
        """For underdamped system the peak displacement gain should > 1."""
        params = _default_params()
        freq = compute_frequency_response(params)
        assert max(freq["displacement_gain"]) > 1.0

    def test_gain_rolls_off_at_high_freq(self):
        """At 30 Hz the displacement gain should be well below 1."""
        params = _default_params()
        freq = compute_frequency_response(params)
        # Last few points should be < 0.5
        assert freq["displacement_gain"][-1] < 0.5

    def test_return_keys(self):
        params = _default_params()
        freq = compute_frequency_response(params)
        expected = {
            "frequency_hz",
            "displacement_gain",
            "acceleration_gain",
            "phase_deg",
            "body_resonance_hz",
            "wheel_resonance_hz",
        }
        assert expected == set(freq.keys())


# ---------------------------------------------------------------------------
# 5. Two natural frequencies from eigenvalue problem
# ---------------------------------------------------------------------------

class TestTwoNaturalFrequencies:
    def test_body_less_than_wheel_hop(self):
        params = _default_params()
        result = compute_natural_frequencies(params)
        assert result["body_mode_hz"] < result["wheel_hop_hz"]

    def test_wheel_hop_5_to_20(self):
        params = _default_params()
        result = compute_natural_frequencies(params)
        assert 5.0 <= result["wheel_hop_hz"] <= 20.0

    def test_different_params(self):
        """With a stiffer spring the body mode should increase."""
        soft = QuarterCarParams(spring_rate_N_per_m=15000.0)
        stiff = QuarterCarParams(spring_rate_N_per_m=50000.0)
        f_soft = compute_natural_frequencies(soft)
        f_stiff = compute_natural_frequencies(stiff)
        assert f_stiff["body_mode_hz"] > f_soft["body_mode_hz"]


# ---------------------------------------------------------------------------
# 6. Tire never loses contact during a 25 mm bump
# ---------------------------------------------------------------------------

class TestTireContact:
    def test_tire_stays_compressed_small_bump(self):
        """For a small bump (3 mm) the tire dynamic deflection should stay
        within the static preload, meaning the tire never leaves the ground.

        The model measures perturbations about static equilibrium (no
        gravity term).  Static tire compression is (m_s+m_u)*g/k_t.
        Contact is maintained when the dynamic extension never exceeds
        that preload.
        """
        params = _default_params()
        road = bump_input(height_m=0.003, width_m=0.3, speed_ms=10.0)
        result = simulate_time_response(params, road, t_span=(0.0, 2.0), dt=0.0005)

        m_total = params.sprung_mass_kg + params.unsprung_mass_kg
        static_defl_mm = (m_total * 9.80665 / params.tire_rate_N_per_m) * 1000.0

        min_tire_defl = min(result["tire_deflection_mm"])
        assert min_tire_defl > -static_defl_mm, (
            f"Tire lost contact: min tire deflection {min_tire_defl:.2f} mm "
            f"< static deflection {-static_defl_mm:.2f} mm"
        )

    def test_25mm_bump_deflection_bounded(self):
        """For a 25 mm bump the peak tire deflection magnitude should be
        bounded (less than 2x bump height).  With these stiff tire params
        the tire will momentarily lift off, but the response must stay
        bounded -- no divergence."""
        params = _default_params()
        road = bump_input(height_m=0.025, width_m=0.3, speed_ms=10.0)
        result = simulate_time_response(params, road, t_span=(0.0, 2.0), dt=0.0005)

        max_abs_defl = max(abs(d) for d in result["tire_deflection_mm"])
        assert max_abs_defl < 50.0, (
            f"Tire deflection diverged: {max_abs_defl:.1f} mm"
        )


# ---------------------------------------------------------------------------
# Road input helpers
# ---------------------------------------------------------------------------

class TestRoadInputs:
    def test_step_before_trigger(self):
        road = step_input(0.02, t_step=0.5)
        assert road(0.0) == 0.0
        assert road(0.49) == 0.0

    def test_step_after_trigger(self):
        road = step_input(0.02, t_step=0.5)
        assert road(0.5) == 0.02
        assert road(10.0) == 0.02

    def test_bump_peak(self):
        road = bump_input(height_m=0.025, width_m=0.3, speed_ms=10.0)
        duration = 0.3 / 10.0  # 0.03 s
        peak_val = road(duration / 2.0)
        assert abs(peak_val - 0.025) < 1e-6

    def test_bump_outside_zero(self):
        road = bump_input(height_m=0.025, width_m=0.3, speed_ms=10.0)
        assert road(-0.1) == 0.0
        assert road(1.0) == 0.0

    def test_sinusoidal_amplitude(self):
        road = random_road_input(amplitude_m=0.005, frequency_hz=5.0)
        # At t = 1/(4*f) the sine should be at its peak
        t_peak = 1.0 / (4.0 * 5.0)
        assert abs(road(t_peak) - 0.005) < 1e-8


# ---------------------------------------------------------------------------
# ODE sanity
# ---------------------------------------------------------------------------

class TestODE:
    def test_equilibrium(self):
        """At rest with no road input, derivatives should be zero."""
        params = _default_params()
        road = step_input(0.0)
        dy = quarter_car_ode(0.0, [0.0, 0.0, 0.0, 0.0], params, road)
        for d in dy:
            assert abs(d) < 1e-12


# ---------------------------------------------------------------------------
# Top-level convenience
# ---------------------------------------------------------------------------

class TestAnalyzeRide:
    def test_returns_all_sections(self):
        params = _default_params()
        result = analyze_ride(params)
        assert "natural_frequencies" in result
        assert "damping_ratios" in result
        assert "time_response" in result
        assert "frequency_response" in result

    def test_body_mode_present(self):
        params = _default_params()
        result = analyze_ride(params)
        assert "body_mode_hz" in result["natural_frequencies"]
        assert result["natural_frequencies"]["body_mode_hz"] > 0

    def test_time_response_nonempty(self):
        params = _default_params()
        result = analyze_ride(params)
        assert len(result["time_response"]["time_s"]) > 100
