"""
Tests for the 3D beam-element FEM engine (frame_fem).

Covers:
1. Cantilever beam analytical validation
2. Torsional rigidity sign and magnitude
3. Stress and safety factor checks
4. Equilibrium of reaction forces
"""

import math
import numpy as np
import pytest

from openwheel_design.simulation.frame_fem import (
    TubeSection,
    create_element_stiffness,
    assemble_global_stiffness,
    apply_boundary_conditions,
    solve_displacements,
    calculate_element_stresses,
    analyze_torsional_rigidity,
    create_simple_spaceframe,
)
from openwheel_design.modules.chassis.materials import get_material


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _steel_EG():
    """Return (E, G) for 4130 chromoly steel in MPa."""
    mat = get_material("4130")
    E = mat["youngs_modulus"]
    nu = mat["poisson"]
    G = E / (2 * (1 + nu))
    return E, G


# ---------------------------------------------------------------------------
# 1. Cantilever beam -- analytical validation
# ---------------------------------------------------------------------------

class TestCantileverBeam:
    """Single beam element fixed at one end, point load at the free end.

    Analytical deflection: delta = P * L^3 / (3 * E * I)
    """

    def test_tip_deflection_matches_analytical(self):
        """Tip deflection of a single-element cantilever should match the
        Euler-Bernoulli closed-form solution within 1%."""
        # Setup: beam along X-axis, 1000 mm long, loaded in Z at the tip.
        section = TubeSection(od_mm=25.4, wall_mm=1.6)
        E, G = _steel_EG()
        I = section.Ix_mm4
        L = 1000.0  # mm
        P = 100.0    # N  (applied in +Z direction at tip)

        nodes = np.array([
            [0.0, 0.0, 0.0],
            [L,   0.0, 0.0],
        ])
        elements = [(0, 1)]

        # Assemble
        K = assemble_global_stiffness(nodes, elements, section, "4130")
        ndof = 12
        F = np.zeros(ndof)
        F[6 * 1 + 2] = P  # Fz at node 1

        # Fix all 6 DOFs at node 0
        fixed_dofs = list(range(6))
        K_bc, F_bc = apply_boundary_conditions(K, F, fixed_dofs)
        u = solve_displacements(K_bc, F_bc)

        # Analytical
        delta_analytical = P * L**3 / (3 * E * I)

        # FEM result: vertical (z) displacement at node 1
        delta_fem = u[6 * 1 + 2]

        rel_error = abs(delta_fem - delta_analytical) / delta_analytical
        assert rel_error < 0.01, (
            f"Cantilever tip deflection error {rel_error:.4%} exceeds 1%. "
            f"FEM={delta_fem:.6f}, analytical={delta_analytical:.6f}"
        )

    def test_tip_rotation_matches_analytical(self):
        """Tip rotation of a cantilever: theta = P * L^2 / (2 * E * I)."""
        section = TubeSection(od_mm=25.4, wall_mm=1.6)
        E, G = _steel_EG()
        I = section.Ix_mm4
        L = 1000.0
        P = 100.0

        nodes = np.array([[0.0, 0.0, 0.0], [L, 0.0, 0.0]])
        elements = [(0, 1)]

        K = assemble_global_stiffness(nodes, elements, section, "4130")
        F = np.zeros(12)
        F[6 * 1 + 2] = P

        K_bc, F_bc = apply_boundary_conditions(K, F, list(range(6)))
        u = solve_displacements(K_bc, F_bc)

        # Load in Z, rotation about Y axis at tip (DOF index 6*1 + 4)
        theta_analytical = P * L**2 / (2 * E * I)
        # The sign depends on convention; bending about local-y for load in +z
        # gives negative rotation about y in the standard convention.
        theta_fem = abs(u[6 * 1 + 4])

        rel_error = abs(theta_fem - theta_analytical) / theta_analytical
        assert rel_error < 0.01, (
            f"Tip rotation error {rel_error:.4%}. "
            f"FEM={theta_fem:.6e}, analytical={theta_analytical:.6e}"
        )


# ---------------------------------------------------------------------------
# 2. Torsional rigidity -- positive value
# ---------------------------------------------------------------------------

class TestTorsionalRigidity:
    """Tests using the simple spaceframe helper."""

    @pytest.fixture
    def spaceframe_result(self):
        nodes, elements, section = create_simple_spaceframe()
        front_susp = [0, 1]
        rear_susp = [8, 9]
        return analyze_torsional_rigidity(
            nodes, elements, section, "4130",
            front_susp_nodes=front_susp,
            rear_susp_nodes=rear_susp,
            applied_force_N=1000.0,
        )

    def test_rigidity_positive(self, spaceframe_result):
        """Torsional rigidity must be a positive finite number."""
        val = spaceframe_result["torsional_rigidity_Nm_per_deg"]
        assert val > 0, f"Rigidity should be positive, got {val}"
        assert math.isfinite(val), f"Rigidity should be finite, got {val}"

    def test_rigidity_in_reasonable_range(self, spaceframe_result):
        """Typical FSAE spaceframe: 500-3000 Nm/deg."""
        val = spaceframe_result["torsional_rigidity_Nm_per_deg"]
        assert 500 <= val <= 3000, (
            f"Rigidity {val:.1f} Nm/deg outside expected FSAE range [500, 3000]"
        )

    def test_max_displacement_positive(self, spaceframe_result):
        """There should be measurable displacement under load."""
        assert spaceframe_result["max_displacement_mm"] > 0

    def test_twist_angle_positive(self, spaceframe_result):
        """Twist angle must be positive."""
        assert spaceframe_result["twist_angle_deg"] > 0


# ---------------------------------------------------------------------------
# 3. Stress below yield -- safety factor
# ---------------------------------------------------------------------------

class TestStressAndSafety:

    def test_safety_factor_above_one(self):
        """Under a typical torsion-test load (1 kN couple), stresses should be
        well below yield for a 4130 steel frame."""
        nodes, elements, section = create_simple_spaceframe()
        result = analyze_torsional_rigidity(
            nodes, elements, section, "4130",
            front_susp_nodes=[0, 1],
            rear_susp_nodes=[8, 9],
            applied_force_N=1000.0,
        )
        sf = result["safety_factor"]
        assert sf > 1.0, f"Safety factor {sf} is below 1 -- frame yields under test load"

    def test_element_stresses_populated(self):
        """Every element should have a stress result."""
        nodes, elements, section = create_simple_spaceframe()
        result = analyze_torsional_rigidity(
            nodes, elements, section, "4130",
            front_susp_nodes=[0, 1],
            rear_susp_nodes=[8, 9],
        )
        assert len(result["element_stresses"]) == len(elements)
        for s in result["element_stresses"]:
            assert "von_mises_stress_MPa" in s
            assert s["von_mises_stress_MPa"] >= 0


# ---------------------------------------------------------------------------
# 4. Equilibrium check
# ---------------------------------------------------------------------------

class TestEquilibrium:
    """Sum of reaction forces at fixed supports should equal applied forces."""

    def test_reaction_forces_balance(self):
        """Global equilibrium: sum(reactions) + sum(applied) = 0."""
        nodes, elements, section = create_simple_spaceframe()
        material = "4130"
        front_susp = [0, 1]
        rear_susp = [8, 9]
        applied_force_N = 1000.0

        n_nodes = nodes.shape[0]
        ndof = 6 * n_nodes

        K = assemble_global_stiffness(nodes, elements, section, material)

        F = np.zeros(ndof)
        front_y = nodes[front_susp, 1]
        y_min_idx = front_susp[int(np.argmin(front_y))]
        y_max_idx = front_susp[int(np.argmax(front_y))]
        F[6 * y_min_idx + 2] = -applied_force_N
        F[6 * y_max_idx + 2] = +applied_force_N

        fixed_dofs = []
        for rn in rear_susp:
            fixed_dofs.extend(range(6 * rn, 6 * rn + 6))

        K_bc, F_bc = apply_boundary_conditions(K, F, fixed_dofs)
        u = solve_displacements(K_bc, F_bc)

        # Reaction forces = K_original @ u  (at fixed DOFs, this gives reactions)
        R = K @ u

        # Sum of vertical forces (z-direction, DOF index 2 of each node)
        total_Fz = 0.0
        for n in range(n_nodes):
            total_Fz += R[6 * n + 2]

        # Should be zero (applied forces are self-balanced, reactions must also balance)
        assert abs(total_Fz) < 1e-3, (
            f"Vertical force imbalance: {total_Fz:.6f} N (should be ~0)"
        )

        # Also check horizontal equilibrium
        total_Fx = sum(R[6 * n] for n in range(n_nodes))
        total_Fy = sum(R[6 * n + 1] for n in range(n_nodes))
        assert abs(total_Fx) < 1e-3, f"Fx imbalance: {total_Fx:.6f} N"
        assert abs(total_Fy) < 1e-3, f"Fy imbalance: {total_Fy:.6f} N"


# ---------------------------------------------------------------------------
# 5. TubeSection validation
# ---------------------------------------------------------------------------

class TestTubeSection:

    def test_computed_properties(self):
        sec = TubeSection(od_mm=25.4, wall_mm=1.6)
        assert abs(sec.id_mm - 22.2) < 1e-6
        assert sec.area_mm2 > 0
        assert sec.Ix_mm4 > 0
        assert abs(sec.J_mm4 - 2 * sec.Ix_mm4) < 1e-6

    def test_invalid_wall(self):
        with pytest.raises(ValueError):
            TubeSection(od_mm=10, wall_mm=6)  # wall >= OD/2

    def test_invalid_od(self):
        with pytest.raises(ValueError):
            TubeSection(od_mm=0, wall_mm=1)
