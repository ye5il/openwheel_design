"""Tests for the 2D vortex panel method solver."""

import numpy as np
import pytest

from openwheel_design.simulation.panel_2d import (
    analyze_airfoil,
    compute_cl_curve,
    estimate_drag_friction,
    generate_naca4,
    solve_panel,
)


# -----------------------------------------------------------------------
# Coordinate generation
# -----------------------------------------------------------------------


class TestNACA4Generation:
    """Tests for generate_naca4."""

    def test_coordinate_shape(self):
        """Output should be (n_panels + 1, 2)."""
        coords = generate_naca4("0012", n_panels=100)
        assert coords.shape == (101, 2)

    def test_odd_panels_rounded_up(self):
        """An odd n_panels should be rounded up to the next even number."""
        coords = generate_naca4("0012", n_panels=99)
        assert coords.shape == (101, 2)

    def test_symmetric_airfoil_symmetry(self):
        """NACA 0012: upper y = -lower y for matching x stations."""
        coords = generate_naca4("0012", n_panels=100)
        n_half = (coords.shape[0] - 1) // 2

        lower = coords[: n_half + 1]   # TE -> LE (51 pts)
        upper = coords[n_half:]        # LE -> TE (51 pts)

        # Reverse lower so both run LE -> TE
        lower_rev = lower[::-1]

        np.testing.assert_allclose(upper[:, 0], lower_rev[:, 0], atol=1e-10)
        np.testing.assert_allclose(upper[:, 1], -lower_rev[:, 1], atol=1e-10)

    def test_coordinate_x_range(self):
        """x coordinates should stay within [0, 1] (with small tolerance
        for the thickness-normal offset of cambered profiles)."""
        coords = generate_naca4("4415", n_panels=120)
        assert np.all(coords[:, 0] >= -0.02)
        assert np.all(coords[:, 0] <= 1.02)

    def test_leading_edge_at_origin(self):
        """For a symmetric airfoil the LE node should be at (0, 0)."""
        coords = generate_naca4("0012", n_panels=100)
        n_half = (coords.shape[0] - 1) // 2
        le = coords[n_half]
        np.testing.assert_allclose(le, [0.0, 0.0], atol=1e-14)

    def test_invalid_code_raises(self):
        """Non-numeric or wrong-length codes should raise ValueError."""
        with pytest.raises(ValueError):
            generate_naca4("abcd")
        with pytest.raises(ValueError):
            generate_naca4("12345")
        with pytest.raises(ValueError):
            generate_naca4("12")


# -----------------------------------------------------------------------
# Panel solver
# -----------------------------------------------------------------------


class TestSolvePanel:
    """Tests for solve_panel."""

    def test_symmetric_zero_alpha_cl(self):
        """NACA 0012 at alpha = 0 should give CL approx 0."""
        coords = generate_naca4("0012", n_panels=100)
        result = solve_panel(coords, 0.0)
        assert abs(result["CL"]) < 0.01

    def test_cambered_zero_alpha_positive_cl(self):
        """NACA 2412 at alpha = 0 should produce positive CL."""
        coords = generate_naca4("2412", n_panels=100)
        result = solve_panel(coords, 0.0)
        assert result["CL"] > 0.0

    def test_cl_alpha_near_thin_airfoil_theory(self):
        """CL_alpha for NACA 0012 should be near 2*pi/rad, thickness-corrected."""
        coords = generate_naca4("0012", n_panels=100)
        curve = compute_cl_curve(coords, alpha_range=(-5, 10), alpha_step=1.0)

        # Thickness-corrected thin-airfoil theory: 2*pi*(1+0.77*t) per rad.
        # For 12% thick airfoil this is ~6.86/rad = 0.1198/deg.
        t = 0.12
        expected = 2.0 * np.pi * (1.0 + 0.77 * t) / np.degrees(1.0)
        relative_err = abs(curve["CL_alpha"] - expected) / expected
        assert relative_err < 0.05, (
            f"CL_alpha = {curve['CL_alpha']:.5f}/deg, "
            f"expected ~{expected:.5f}/deg (error {relative_err:.1%})"
        )

    def test_cl_linearity(self):
        """CL at 5 deg should be approx 5 * CL_alpha (within 10 %)."""
        coords = generate_naca4("0012", n_panels=100)
        result_5 = solve_panel(coords, 5.0)

        r_p = solve_panel(coords, 2.0)
        r_m = solve_panel(coords, -2.0)
        cl_alpha = (r_p["CL"] - r_m["CL"]) / 4.0

        expected = 5.0 * cl_alpha
        relative_err = abs(result_5["CL"] - expected) / abs(expected)
        assert relative_err < 0.10, (
            f"CL(5) = {result_5['CL']:.4f}, "
            f"expected {expected:.4f} (error {relative_err:.1%})"
        )

    def test_stagnation_cp(self):
        """At least one Cp value should be close to 1.0 (stagnation)."""
        coords = generate_naca4("0012", n_panels=100)
        result = solve_panel(coords, 5.0)

        all_cp = result["Cp_upper"] + result["Cp_lower"]
        max_cp = max(all_cp)
        assert max_cp > 0.90, f"Max Cp = {max_cp:.3f}; expected > 0.90"

    def test_result_dict_keys(self):
        """Return dict must contain all documented keys."""
        coords = generate_naca4("0012")
        result = solve_panel(coords, 0.0)
        expected = {"CL", "Cm_c4", "Cp_upper", "Cp_lower",
                    "x_upper", "x_lower", "alpha_deg"}
        assert set(result.keys()) == expected

    def test_symmetric_zero_alpha_cm(self):
        """Cm about c/4 for a symmetric airfoil at alpha = 0 should be ~0."""
        coords = generate_naca4("0012", n_panels=100)
        result = solve_panel(coords, 0.0)
        assert abs(result["Cm_c4"]) < 0.01


# -----------------------------------------------------------------------
# CL curve
# -----------------------------------------------------------------------


class TestCLCurve:
    """Tests for compute_cl_curve."""

    def test_output_structure(self):
        """Returned dict must have the right keys and consistent lengths."""
        coords = generate_naca4("0012", n_panels=60)
        curve = compute_cl_curve(coords, alpha_range=(-2, 8), alpha_step=2.0)

        for key in ("alpha_deg", "CL", "Cm", "CL_alpha"):
            assert key in curve
        assert len(curve["alpha_deg"]) == len(curve["CL"])
        assert len(curve["alpha_deg"]) == len(curve["Cm"])

    def test_increasing_cl_with_alpha(self):
        """CL should increase with angle of attack in the linear range."""
        coords = generate_naca4("0012", n_panels=80)
        curve = compute_cl_curve(coords, alpha_range=(0, 10), alpha_step=2.0)
        cl = curve["CL"]
        for i in range(1, len(cl)):
            assert cl[i] > cl[i - 1]


# -----------------------------------------------------------------------
# Top-level analysis
# -----------------------------------------------------------------------


class TestAnalyzeAirfoil:
    """Tests for analyze_airfoil."""

    def test_naca0012_at_5_deg(self):
        """Basic sanity check on the convenience wrapper."""
        result = analyze_airfoil("0012", alpha_deg=5.0, n_panels=80)

        assert result["CL"] > 0.0
        assert "CL_alpha_per_deg" in result
        assert "CL_alpha_per_rad" in result

        # CL_alpha should be near 2*pi per radian
        rel = abs(result["CL_alpha_per_rad"] - 2.0 * np.pi) / (2.0 * np.pi)
        assert rel < 0.10, (
            f"CL_alpha = {result['CL_alpha_per_rad']:.3f}/rad, "
            f"expected ~{2*np.pi:.3f}/rad"
        )

    def test_cambered_has_positive_lift_at_zero(self):
        """NACA 2412 at alpha = 0 should show camber-induced lift."""
        result = analyze_airfoil("2412", alpha_deg=0.0, n_panels=100)
        assert result["CL"] > 0.0


# -----------------------------------------------------------------------
# Friction drag
# -----------------------------------------------------------------------


class TestFrictionDrag:
    """Tests for estimate_drag_friction."""

    def test_laminar_at_low_re(self):
        """At Re < 5e5 the BL should be fully laminar."""
        coords = generate_naca4("0012", n_panels=60)
        result = estimate_drag_friction(coords, 0.0, Re=1e5)

        assert result["Cd_friction"] > 0.0
        assert result["transition_x_upper"] >= 1.0

    def test_transition_at_high_re(self):
        """At Re >> 5e5 the BL should transition on the airfoil."""
        coords = generate_naca4("0012", n_panels=60)
        result = estimate_drag_friction(coords, 0.0, Re=1e7)

        assert result["Cd_friction"] > 0.0
        assert result["transition_x_upper"] < 1.0

    def test_negative_re_raises(self):
        """Negative Reynolds number should raise ValueError."""
        coords = generate_naca4("0012")
        with pytest.raises(ValueError):
            estimate_drag_friction(coords, 0.0, Re=-100)
