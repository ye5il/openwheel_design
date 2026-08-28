"""Chassis module physics/calculation tests."""

from openwheel_design.modules.chassis.analyses import calculate_section_modulus, analyze_stress
from openwheel_design.modules.chassis.materials import MATERIALS


def test_section_modulus_25_4_od_1_6_wall():
    """Bending section modulus for 25.4mm OD x 1.6mm wall tube should be ~670 mm^3."""
    Z = calculate_section_modulus(25.4, 1.6)
    assert 620 <= Z <= 720, f"Section modulus {Z:.1f} mm^3 outside expected range 620-720"


def test_analyze_stress_al7075_uses_correct_yield():
    """analyze_stress with al7075 must use the material's own yield, not hardcoded 560."""
    result = analyze_stress(1000, 10, material="al7075")
    expected_yield = MATERIALS["al7075"]["yield_strength"]
    assert result["yield_strength_MPa"] == expected_yield
    assert result["yield_strength_MPa"] != 560, "Still using hardcoded CHROMOLY_YIELD"


def test_analyze_stress_default_4130():
    """analyze_stress with default material='4130' still works (backward compat)."""
    result = analyze_stress(1000, 10)
    expected_yield = MATERIALS["4130"]["yield_strength"]
    assert result["yield_strength_MPa"] == expected_yield
    assert result["safety_factor"] == expected_yield / (1000 / 10)


def test_carbon_fiber_has_yield_strength():
    """carbon_fiber entry in MATERIALS must have a yield_strength key."""
    assert "yield_strength" in MATERIALS["carbon_fiber"]
    assert MATERIALS["carbon_fiber"]["yield_strength"] == 600
