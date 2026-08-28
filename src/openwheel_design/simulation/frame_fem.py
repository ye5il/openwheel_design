"""
3D beam-element Finite Element Method engine for chassis torsional rigidity analysis.

Implements Euler-Bernoulli beam elements with 6 DOF per node (ux, uy, uz, theta_x,
theta_y, theta_z) for structural analysis of Formula Student spaceframe chassis.

Units throughout: mm, N, MPa (N/mm^2), degrees (for rigidity output).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple, Union

import numpy as np

from openwheel_design.modules.chassis.materials import MATERIALS, get_material


# ---------------------------------------------------------------------------
# 1. TubeSection dataclass
# ---------------------------------------------------------------------------

@dataclass
class TubeSection:
    """Circular hollow tube cross-section for beam elements.

    Attributes:
        od_mm: Outer diameter in mm.
        wall_mm: Wall thickness in mm.
    """

    od_mm: float
    wall_mm: float

    def __post_init__(self) -> None:
        if self.wall_mm <= 0:
            raise ValueError("Wall thickness must be positive.")
        if self.od_mm <= 0:
            raise ValueError("Outer diameter must be positive.")
        if self.wall_mm >= self.od_mm / 2:
            raise ValueError(
                "Wall thickness must be less than the outer radius "
                f"(wall={self.wall_mm} mm >= OD/2={self.od_mm / 2} mm)."
            )

    @property
    def id_mm(self) -> float:
        """Inner diameter in mm."""
        return self.od_mm - 2 * self.wall_mm

    @property
    def area_mm2(self) -> float:
        """Cross-sectional area in mm^2."""
        ro = self.od_mm / 2
        ri = self.id_mm / 2
        return math.pi * (ro**2 - ri**2)

    @property
    def Ix_mm4(self) -> float:
        """Second moment of area (bending) in mm^4.

        I = pi/64 * (D^4 - d^4)
        """
        D = self.od_mm
        d = self.id_mm
        return math.pi / 64 * (D**4 - d**4)

    @property
    def J_mm4(self) -> float:
        """Polar moment of area (torsion) in mm^4.

        J = pi/32 * (D^4 - d^4) = 2 * Ix
        """
        D = self.od_mm
        d = self.id_mm
        return math.pi / 32 * (D**4 - d**4)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _element_length(node_i: np.ndarray, node_j: np.ndarray) -> float:
    """Euclidean distance between two 3D nodes."""
    return float(np.linalg.norm(node_j - node_i))


def _rotation_matrix_3x3(node_i: np.ndarray, node_j: np.ndarray) -> np.ndarray:
    """Build the 3x3 rotation matrix from local to global axes.

    Local x-axis runs along the element (node_i -> node_j).
    Local y and z are constructed via cross products with a reference vector.
    If the element is nearly parallel to the chosen reference vector, a
    fallback reference is used.

    Returns:
        (3, 3) rotation matrix R where each row is a local axis expressed in
        global coordinates.
    """
    dx = node_j - node_i
    L = np.linalg.norm(dx)
    if L < 1e-12:
        raise ValueError("Zero-length element (coincident nodes).")
    x_local = dx / L

    # Choose a reference vector that is not parallel to x_local.
    ref = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(x_local, ref)) > 0.99:
        ref = np.array([1.0, 0.0, 0.0])

    y_local = np.cross(ref, x_local)
    y_local = y_local / np.linalg.norm(y_local)

    z_local = np.cross(x_local, y_local)
    z_local = z_local / np.linalg.norm(z_local)

    # Rows of R are local axes in global coords
    R = np.array([x_local, y_local, z_local])
    return R


def _transformation_matrix_12x12(R3: np.ndarray) -> np.ndarray:
    """Expand a 3x3 rotation matrix into the 12x12 transformation matrix.

    The 12x12 matrix T is block-diagonal with four copies of R3:
    T = diag(R3, R3, R3, R3)
    so that  K_global = T^T @ K_local @ T.
    """
    T = np.zeros((12, 12))
    for i in range(4):
        T[3 * i : 3 * i + 3, 3 * i : 3 * i + 3] = R3
    return T


# ---------------------------------------------------------------------------
# 2. Element stiffness matrix
# ---------------------------------------------------------------------------

def create_element_stiffness(
    node_i: np.ndarray,
    node_j: np.ndarray,
    section: TubeSection,
    E: float,
    G: float,
) -> np.ndarray:
    """Build the 12x12 global stiffness matrix for a 3D Euler-Bernoulli beam element.

    DOF order per node: [ux, uy, uz, theta_x, theta_y, theta_z].
    The matrix is computed in local coordinates and then transformed to global
    coordinates via the rotation/transformation matrix.

    Args:
        node_i: (3,) coordinates of the start node in mm.
        node_j: (3,) coordinates of the end node in mm.
        section: TubeSection defining the cross-section geometry.
        E: Young's modulus in MPa (N/mm^2).
        G: Shear modulus in MPa (N/mm^2).

    Returns:
        (12, 12) global stiffness matrix in N/mm (forces) and N*mm (moments).
    """
    L = _element_length(node_i, node_j)
    A = section.area_mm2
    Iy = section.Ix_mm4  # symmetric section: Iy = Iz = Ix
    Iz = section.Ix_mm4
    J = section.J_mm4

    L2 = L * L
    L3 = L2 * L

    # ----- local stiffness matrix (12x12) -----
    # DOF order: [u1,v1,w1, rx1,ry1,rz1, u2,v2,w2, rx2,ry2,rz2]
    #            axial, bend-z, bend-y, torsion
    k = np.zeros((12, 12))

    # Axial: u1, u2  (indices 0, 6)
    ea_L = E * A / L
    k[0, 0] = ea_L
    k[0, 6] = -ea_L
    k[6, 0] = -ea_L
    k[6, 6] = ea_L

    # Torsion: rx1, rx2  (indices 3, 9)
    gj_L = G * J / L
    k[3, 3] = gj_L
    k[3, 9] = -gj_L
    k[9, 3] = -gj_L
    k[9, 9] = gj_L

    # Bending in x-y plane (loads in local y, rotations about local z):
    # v1(1), rz1(5), v2(7), rz2(11)
    c1 = 12 * E * Iz / L3
    c2 = 6 * E * Iz / L2
    c3 = 4 * E * Iz / L
    c4 = 2 * E * Iz / L

    k[1, 1] = c1
    k[1, 5] = c2
    k[1, 7] = -c1
    k[1, 11] = c2

    k[5, 1] = c2
    k[5, 5] = c3
    k[5, 7] = -c2
    k[5, 11] = c4

    k[7, 1] = -c1
    k[7, 5] = -c2
    k[7, 7] = c1
    k[7, 11] = -c2

    k[11, 1] = c2
    k[11, 5] = c4
    k[11, 7] = -c2
    k[11, 11] = c3

    # Bending in x-z plane (loads in local z, rotations about local y):
    # w1(2), ry1(4), w2(8), ry2(10)
    d1 = 12 * E * Iy / L3
    d2 = 6 * E * Iy / L2
    d3 = 4 * E * Iy / L
    d4 = 2 * E * Iy / L

    k[2, 2] = d1
    k[2, 4] = -d2
    k[2, 8] = -d1
    k[2, 10] = -d2

    k[4, 2] = -d2
    k[4, 4] = d3
    k[4, 8] = d2
    k[4, 10] = d4

    k[8, 2] = -d1
    k[8, 4] = d2
    k[8, 8] = d1
    k[8, 10] = d2

    k[10, 2] = -d2
    k[10, 4] = d4
    k[10, 8] = d2
    k[10, 10] = d3

    # ----- transform to global coordinates -----
    R3 = _rotation_matrix_3x3(node_i, node_j)
    T = _transformation_matrix_12x12(R3)
    k_global = T.T @ k @ T

    return k_global


# ---------------------------------------------------------------------------
# 3. Global stiffness assembly
# ---------------------------------------------------------------------------

def assemble_global_stiffness(
    nodes: np.ndarray,
    elements: List[Tuple[int, int]],
    sections: Union[List[TubeSection], TubeSection],
    material: str,
) -> np.ndarray:
    """Assemble the global stiffness matrix from element contributions.

    Args:
        nodes: (N, 3) array of node coordinates in mm.
        elements: List of (node_i_index, node_j_index) pairs.
        sections: A single TubeSection applied to every element, or a list
                  with one TubeSection per element.
        material: Material name recognised by ``get_material`` (e.g. ``"4130"``).

    Returns:
        (ndof, ndof) global stiffness matrix where ndof = 6 * number_of_nodes.
    """
    mat = get_material(material)
    if mat is None:
        raise ValueError(f"Unknown material: {material!r}")

    E = mat["youngs_modulus"]  # MPa
    nu = mat["poisson"]
    G = E / (2 * (1 + nu))    # Shear modulus in MPa

    n_nodes = nodes.shape[0]
    ndof = 6 * n_nodes
    K = np.zeros((ndof, ndof))

    for idx, (ni, nj) in enumerate(elements):
        sec = sections[idx] if isinstance(sections, list) else sections
        ke = create_element_stiffness(nodes[ni], nodes[nj], sec, E, G)

        # Scatter into global matrix
        dofs_i = list(range(6 * ni, 6 * ni + 6))
        dofs_j = list(range(6 * nj, 6 * nj + 6))
        dofs = dofs_i + dofs_j

        for a in range(12):
            for b in range(12):
                K[dofs[a], dofs[b]] += ke[a, b]

    return K


# ---------------------------------------------------------------------------
# 4. Boundary conditions
# ---------------------------------------------------------------------------

def apply_boundary_conditions(
    K: np.ndarray,
    F: np.ndarray,
    fixed_dofs: List[int],
) -> Tuple[np.ndarray, np.ndarray]:
    """Apply fixed (homogeneous Dirichlet) boundary conditions.

    Zeroes out the rows and columns of ``K`` for every fixed DOF, places a 1
    on the diagonal, and zeroes the corresponding entry in ``F``.

    Args:
        K: (ndof, ndof) global stiffness matrix (modified in-place on a copy).
        F: (ndof,) global force vector (modified in-place on a copy).
        fixed_dofs: Indices of the DOFs to constrain.

    Returns:
        (K_mod, F_mod) copies with boundary conditions applied.
    """
    K_mod = K.copy()
    F_mod = F.copy()

    for dof in fixed_dofs:
        K_mod[dof, :] = 0.0
        K_mod[:, dof] = 0.0
        K_mod[dof, dof] = 1.0
        F_mod[dof] = 0.0

    return K_mod, F_mod


# ---------------------------------------------------------------------------
# 5. Solver
# ---------------------------------------------------------------------------

def solve_displacements(K: np.ndarray, F: np.ndarray) -> np.ndarray:
    """Solve the linear system K * u = F for nodal displacements.

    Args:
        K: (ndof, ndof) global stiffness matrix with BCs applied.
        F: (ndof,) global force vector with BCs applied.

    Returns:
        (ndof,) displacement vector.
    """
    return np.linalg.solve(K, F)


# ---------------------------------------------------------------------------
# 6. Element stress recovery
# ---------------------------------------------------------------------------

def calculate_element_stresses(
    nodes: np.ndarray,
    elements: List[Tuple[int, int]],
    sections: Union[List[TubeSection], TubeSection],
    displacements: np.ndarray,
    material: str,
) -> List[dict]:
    """Compute internal forces and stresses for every element.

    For each element the nodal displacements are rotated into local coordinates
    and the internal force vector is obtained via ``f_local = k_local @ u_local``.
    Stresses are derived from internal forces:

    - Axial stress = N / A
    - Bending stress = M * c / I  (max at outer fibre, c = OD/2)
    - Shear stress from torsion = T * c / J
    - Von Mises (combined) = sqrt(sigma^2 + 3*tau^2)

    Args:
        nodes: (N, 3) node coordinates in mm.
        elements: Element connectivity.
        sections: TubeSection(s).
        displacements: (ndof,) global displacement vector.
        material: Material name.

    Returns:
        List of dicts, one per element, with keys:
            axial_stress_MPa, bending_stress_MPa, torsional_shear_stress_MPa,
            von_mises_stress_MPa, axial_force_N, bending_moment_Nmm,
            torque_Nmm, element_index.
    """
    mat = get_material(material)
    if mat is None:
        raise ValueError(f"Unknown material: {material!r}")

    E = mat["youngs_modulus"]
    nu = mat["poisson"]
    G = E / (2 * (1 + nu))

    results: List[dict] = []

    for idx, (ni, nj) in enumerate(elements):
        sec = sections[idx] if isinstance(sections, list) else sections

        # Extract global displacements for this element
        dofs_i = list(range(6 * ni, 6 * ni + 6))
        dofs_j = list(range(6 * nj, 6 * nj + 6))
        u_global = displacements[dofs_i + dofs_j]

        # Transform to local coordinates
        R3 = _rotation_matrix_3x3(nodes[ni], nodes[nj])
        T = _transformation_matrix_12x12(R3)
        u_local = T @ u_global

        # Build local stiffness (could cache, but clarity first)
        L = _element_length(nodes[ni], nodes[nj])
        A = sec.area_mm2
        Iy = sec.Ix_mm4
        Iz = sec.Ix_mm4
        J = sec.J_mm4

        L2 = L * L
        L3 = L2 * L

        k_loc = np.zeros((12, 12))

        ea_L = E * A / L
        k_loc[0, 0] = ea_L;  k_loc[0, 6] = -ea_L
        k_loc[6, 0] = -ea_L; k_loc[6, 6] = ea_L

        gj_L = G * J / L
        k_loc[3, 3] = gj_L;  k_loc[3, 9] = -gj_L
        k_loc[9, 3] = -gj_L; k_loc[9, 9] = gj_L

        c1 = 12 * E * Iz / L3; c2 = 6 * E * Iz / L2
        c3 = 4 * E * Iz / L;   c4 = 2 * E * Iz / L
        k_loc[1,1]=c1;  k_loc[1,5]=c2;  k_loc[1,7]=-c1;  k_loc[1,11]=c2
        k_loc[5,1]=c2;  k_loc[5,5]=c3;  k_loc[5,7]=-c2;  k_loc[5,11]=c4
        k_loc[7,1]=-c1; k_loc[7,5]=-c2; k_loc[7,7]=c1;   k_loc[7,11]=-c2
        k_loc[11,1]=c2; k_loc[11,5]=c4; k_loc[11,7]=-c2;  k_loc[11,11]=c3

        d1 = 12 * E * Iy / L3; d2 = 6 * E * Iy / L2
        d3 = 4 * E * Iy / L;   d4 = 2 * E * Iy / L
        k_loc[2,2]=d1;  k_loc[2,4]=-d2;  k_loc[2,8]=-d1;  k_loc[2,10]=-d2
        k_loc[4,2]=-d2; k_loc[4,4]=d3;   k_loc[4,8]=d2;   k_loc[4,10]=d4
        k_loc[8,2]=-d1; k_loc[8,4]=d2;   k_loc[8,8]=d1;   k_loc[8,10]=d2
        k_loc[10,2]=-d2;k_loc[10,4]=d4;  k_loc[10,8]=d2;  k_loc[10,10]=d3

        f_local = k_loc @ u_local

        # Internal forces at node i (convention: positive tension)
        N_axial = f_local[0]            # Axial force (N)
        Vy = f_local[1]                 # Shear in local y
        Vz = f_local[2]                 # Shear in local z
        T_torque = f_local[3]           # Torque (N*mm)
        My = f_local[4]                 # Bending moment about local y (N*mm)
        Mz = f_local[5]                 # Bending moment about local z (N*mm)

        c = sec.od_mm / 2.0  # distance to outer fibre

        sigma_axial = abs(N_axial) / A
        sigma_bending_y = abs(My) * c / Iy if Iy > 0 else 0.0
        sigma_bending_z = abs(Mz) * c / Iz if Iz > 0 else 0.0
        sigma_bending = sigma_bending_y + sigma_bending_z  # conservative superposition
        tau_torsion = abs(T_torque) * c / J if J > 0 else 0.0

        sigma_total = sigma_axial + sigma_bending
        von_mises = math.sqrt(sigma_total**2 + 3 * tau_torsion**2)

        results.append({
            "element_index": idx,
            "axial_stress_MPa": round(sigma_axial, 4),
            "bending_stress_MPa": round(sigma_bending, 4),
            "torsional_shear_stress_MPa": round(tau_torsion, 4),
            "von_mises_stress_MPa": round(von_mises, 4),
            "axial_force_N": round(float(N_axial), 4),
            "bending_moment_Nmm": round(float(math.sqrt(My**2 + Mz**2)), 4),
            "torque_Nmm": round(float(T_torque), 4),
        })

    return results


# ---------------------------------------------------------------------------
# 7. Torsional rigidity analysis
# ---------------------------------------------------------------------------

def analyze_torsional_rigidity(
    nodes: np.ndarray,
    elements: List[Tuple[int, int]],
    sections: Union[List[TubeSection], TubeSection],
    material: str,
    front_susp_nodes: List[int],
    rear_susp_nodes: List[int],
    applied_force_N: float = 1000.0,
) -> dict:
    """Perform an FSAE-style torsional rigidity test on a spaceframe chassis.

    The rear suspension pickup points are fully fixed (all 6 DOFs). A force
    couple is applied at the front suspension pickups: equal and opposite
    vertical forces that create a pure torque about the longitudinal axis.

    Torsional rigidity = T / theta  [Nm/deg]

    where T is the applied torque and theta is the twist angle computed from
    the differential vertical displacement at the front nodes.

    Args:
        nodes: (N, 3) node coordinates in mm.
        elements: Element connectivity list.
        sections: TubeSection(s).
        material: Material key (e.g. ``"4130"``).
        front_susp_nodes: Node indices at the front suspension pickups (>= 2).
        rear_susp_nodes: Node indices at the rear suspension pickups (>= 2).
        applied_force_N: Magnitude of each vertical force in the couple (default 1000 N).

    Returns:
        Dict with keys: torsional_rigidity_Nm_per_deg, max_stress_MPa,
        max_displacement_mm, safety_factor, element_stresses, node_displacements_mm.
    """
    mat = get_material(material)
    if mat is None:
        raise ValueError(f"Unknown material: {material!r}")

    n_nodes = nodes.shape[0]
    ndof = 6 * n_nodes

    # ---- Assemble K ----
    K = assemble_global_stiffness(nodes, elements, sections, material)

    # ---- Force vector ----
    F = np.zeros(ndof)

    # Determine the lateral (Y) span at the front to compute the couple arm.
    front_y_coords = nodes[front_susp_nodes, 1]
    y_min_idx = front_susp_nodes[int(np.argmin(front_y_coords))]
    y_max_idx = front_susp_nodes[int(np.argmax(front_y_coords))]

    # Apply +F_z on one side and -F_z on the other (vertical couple).
    # DOF index for vertical (z) displacement of a node n is 6*n + 2.
    F[6 * y_min_idx + 2] = -applied_force_N
    F[6 * y_max_idx + 2] = +applied_force_N

    # ---- Boundary conditions: fix all rear pickup DOFs ----
    fixed_dofs: List[int] = []
    for rn in rear_susp_nodes:
        fixed_dofs.extend(range(6 * rn, 6 * rn + 6))

    K_bc, F_bc = apply_boundary_conditions(K, F, fixed_dofs)

    # ---- Solve ----
    u = solve_displacements(K_bc, F_bc)

    # ---- Twist angle ----
    dz_min = u[6 * y_min_idx + 2]   # vertical displacement of bottom side
    dz_max = u[6 * y_max_idx + 2]   # vertical displacement of top side
    delta_z = dz_max - dz_min       # differential vertical displacement

    lever_arm_mm = abs(nodes[y_max_idx, 1] - nodes[y_min_idx, 1])
    if lever_arm_mm < 1e-6:
        raise ValueError("Front suspension nodes must be separated laterally.")

    theta_rad = math.atan2(abs(delta_z), lever_arm_mm)
    theta_deg = math.degrees(theta_rad)

    # Applied torque: T = F * lever_arm (N * mm -> convert to N*m for result)
    T_Nmm = applied_force_N * lever_arm_mm
    T_Nm = T_Nmm / 1000.0

    torsional_rigidity = T_Nm / theta_deg if theta_deg > 1e-12 else float("inf")

    # ---- Stress recovery ----
    elem_stresses = calculate_element_stresses(
        nodes, elements, sections, u, material
    )

    max_vm = max(s["von_mises_stress_MPa"] for s in elem_stresses)
    yield_strength = mat["yield_strength"]
    safety_factor = yield_strength / max_vm if max_vm > 1e-12 else float("inf")

    # ---- Displacement summary ----
    disp_magnitudes = []
    for i in range(n_nodes):
        dx = u[6 * i]
        dy = u[6 * i + 1]
        dz = u[6 * i + 2]
        mag = math.sqrt(dx**2 + dy**2 + dz**2)
        disp_magnitudes.append(round(mag, 6))

    max_disp = max(disp_magnitudes)

    return {
        "torsional_rigidity_Nm_per_deg": round(torsional_rigidity, 2),
        "max_stress_MPa": round(max_vm, 4),
        "max_displacement_mm": round(max_disp, 6),
        "safety_factor": round(safety_factor, 2),
        "twist_angle_deg": round(theta_deg, 6),
        "applied_torque_Nm": round(T_Nm, 2),
        "element_stresses": elem_stresses,
        "node_displacements_mm": disp_magnitudes,
    }


# ---------------------------------------------------------------------------
# 8. Simple spaceframe geometry helper
# ---------------------------------------------------------------------------

def create_simple_spaceframe() -> Tuple[np.ndarray, List[Tuple[int, int]], TubeSection]:
    """Create a simplified FSAE spaceframe chassis for testing.

    The geometry has 12 nodes in a 3-bay rectangular frame loosely resembling
    a Formula Student chassis: front bulkhead, front hoop, main hoop, and
    rear bulkhead.  The frame is roughly 2800 mm long, 550 mm wide, and
    350 mm tall, built from 25.4 mm OD x 1.25 mm wall 4130 chromoly tubing.

    Side panels and some floor/roof panels carry single diagonals.  The front
    cockpit bay is deliberately left un-braced on the roof (cockpit opening)
    so that overall torsional rigidity lands in the 500-3000 Nm/deg range
    typical of real student-car spaceframes.

    Coordinate convention: X = longitudinal (forward +), Y = lateral (left +),
    Z = vertical (up +).

    Returns:
        (nodes, elements, section) where
        - nodes: (12, 3) float array of node coordinates in mm
        - elements: list of (i, j) index pairs
        - section: TubeSection (25.4 mm OD, 1.25 mm wall)

    Front suspension nodes: [0, 1]  (front bottom corners)
    Rear suspension nodes: [8, 9]   (rear bottom corners)
    """
    # Frame dimensions chosen so that rigidity ends up in the FSAE range.
    # Longer bays lower bending stiffness (proportional to 1/L^3), and
    # selectively omitting diagonals mimics the cockpit cutout.
    hw = 275.0  # half-width (550 mm total)
    H = 350.0   # height

    nodes = np.array([
        # Front bulkhead (x = 0)
        [   0, -hw,   0],   # 0  front-bottom-left
        [   0,  hw,   0],   # 1  front-bottom-right
        [   0, -hw,   H],   # 2  front-top-left
        [   0,  hw,   H],   # 3  front-top-right
        # Front hoop (x = 900)
        [ 900, -hw,   0],   # 4  fhoop-bottom-left
        [ 900,  hw,   0],   # 5  fhoop-bottom-right
        [ 900, -hw,   H],   # 6  fhoop-top-left
        [ 900,  hw,   H],   # 7  fhoop-top-right
        # Main hoop / rear bulkhead (x = 2800)
        [2800, -hw,   0],   # 8  rear-bottom-left
        [2800,  hw,   0],   # 9  rear-bottom-right
        [2800, -hw,   H],   # 10 rear-top-left
        [2800,  hw,   H],   # 11 rear-top-right
    ], dtype=float)

    elements = [
        # --- Bulkhead / hoop rings ---
        # Front bulkhead ring + X-brace
        (0, 1), (1, 3), (3, 2), (2, 0),
        (0, 3), (1, 2),
        # Front hoop ring + single diagonal
        (4, 5), (5, 7), (7, 6), (6, 4),
        (4, 7),
        # Rear / main-hoop ring + single diagonal
        (8, 9), (9, 11), (11, 10), (10, 8),
        (8, 11),

        # --- Longitudinals (bottom rails) ---
        (0, 4), (1, 5), (4, 8), (5, 9),

        # --- Longitudinals (top rails) ---
        (2, 6), (3, 7), (6, 10), (7, 11),

        # --- Side panel diagonals (one per bay per side) ---
        (0, 6),   # left  front bay
        (4, 10),  # left  rear bay
        (1, 7),   # right front bay
        (5, 11),  # right rear bay

        # --- Floor diagonal (rear bay only) ---
        (4, 9),

        # --- Roof diagonal (rear bay only -- front bay is cockpit opening) ---
        (6, 11),
    ]

    section = TubeSection(od_mm=25.4, wall_mm=1.25)

    return nodes, elements, section
