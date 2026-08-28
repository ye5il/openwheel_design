"""
2D panel method solver for airfoil analysis.

Implements a Hess-Smith (constant source + constant vortex) panel method
for computing pressure distributions and aerodynamic coefficients of
NACA 4-digit airfoils.  Designed for Formula Student vehicle aerodynamic
preliminary design.

Inviscid solver.  CL is accurate for attached flow (alpha < ~12 deg).
No viscous drag prediction from the panel method.  Stall behaviour is
not captured.  An optional flat-plate friction drag estimate is provided
via ``estimate_drag_friction``.
"""

from typing import Dict, List, Optional, Tuple, Union

import numpy as np


# ---------------------------------------------------------------------------
# Airfoil geometry
# ---------------------------------------------------------------------------

def generate_naca4(code: str, n_panels: int = 100) -> np.ndarray:
    """Generate NACA 4-digit airfoil coordinates with cosine spacing.

    Produces coordinates ordered counter-clockwise starting from the
    trailing-edge lower surface, around the leading edge, and back to the
    trailing-edge upper surface.

    Args:
        code: NACA 4-digit designation string (e.g. ``"0012"``,
            ``"2412"``, ``"4415"``).  The first digit is the maximum
            camber in percent chord, the second digit is the location of
            maximum camber in tenths of chord, and the last two digits
            are the thickness in percent chord.
        n_panels: Number of panels.  Rounded up to the next even number
            if odd.  Default ``100``.

    Returns:
        ``np.ndarray`` of shape ``(n_panels + 1, 2)`` containing
        ``(x, y)`` coordinates normalised to unit chord (x in [0, 1]).

    Raises:
        ValueError: If *code* is not a valid 4-digit numeric string.
    """
    if len(code) != 4 or not code.isdigit():
        raise ValueError(
            f"Invalid NACA 4-digit code: '{code}'.  "
            "Expected 4 numeric characters (e.g. '0012')."
        )

    m = int(code[0]) / 100.0   # max camber
    p = int(code[1]) / 10.0    # max camber position
    t = int(code[2:]) / 100.0  # thickness ratio

    if n_panels % 2 != 0:
        n_panels += 1

    n_half = n_panels // 2

    # Cosine spacing — dense near LE and TE
    beta = np.linspace(0.0, np.pi, n_half + 1)
    x = (1.0 + np.cos(beta)) / 2.0  # x from 1.0 to 0.0

    # NACA 4-digit half-thickness distribution
    y_t = (t / 0.20) * (
        0.2969 * np.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x ** 2
        + 0.2843 * x ** 3
        - 0.1015 * x ** 4
    )

    if m == 0.0 or p == 0.0:
        # Symmetric airfoil — no camber
        x_upper = x.copy()
        y_upper = y_t.copy()
        x_lower = x.copy()
        y_lower = -y_t.copy()
    else:
        # Camber line and slope
        y_c = np.where(
            x < p,
            (m / p ** 2) * (2.0 * p * x - x ** 2),
            (m / (1.0 - p) ** 2) * ((1.0 - 2.0 * p) + 2.0 * p * x - x ** 2),
        )
        dyc_dx = np.where(
            x < p,
            (2.0 * m / p ** 2) * (p - x),
            (2.0 * m / (1.0 - p) ** 2) * (p - x),
        )
        theta_c = np.arctan(dyc_dx)

        # Apply thickness normal to the camber line
        x_upper = x - y_t * np.sin(theta_c)
        y_upper = y_c + y_t * np.cos(theta_c)
        x_lower = x + y_t * np.sin(theta_c)
        y_lower = y_c - y_t * np.cos(theta_c)

    # Assemble counter-clockwise: TE_lower -> LE -> TE_upper
    # x_lower already runs from TE (1) to LE (0).
    # x_upper runs from TE (1) to LE (0) — reverse it (skipping the
    # duplicate LE node) to go from LE to TE.
    coords_x = np.concatenate([x_lower, x_upper[-2::-1]])
    coords_y = np.concatenate([y_lower, y_upper[-2::-1]])

    return np.column_stack([coords_x, coords_y])


# ---------------------------------------------------------------------------
# Hess-Smith panel method
# ---------------------------------------------------------------------------

def solve_panel(coords: np.ndarray, alpha_deg: float) -> dict:
    """Solve inviscid flow around an airfoil with the Hess-Smith method.

    Uses constant-strength source panels with a single constant-strength
    vortex distribution and the Kutta condition to compute the pressure
    distribution and aerodynamic coefficients.

    Limitations:
        Inviscid solver.  CL is accurate for attached flow
        (alpha < ~12 deg).  No viscous drag prediction.  Stall
        behaviour is not captured.

    Args:
        coords: Airfoil coordinates of shape ``(N+1, 2)``, ordered
            counter-clockwise (TE lower -> LE -> TE upper).
        alpha_deg: Angle of attack in degrees.

    Returns:
        ``dict`` with keys:

        * ``CL`` — lift coefficient (``float``).
        * ``Cm_c4`` — pitching-moment coefficient about quarter-chord,
          positive nose-up (``float``).
        * ``Cp_upper`` — pressure coefficients on the upper surface,
          ordered from LE to TE (``list[float]``).
        * ``Cp_lower`` — pressure coefficients on the lower surface,
          ordered from LE to TE (``list[float]``).
        * ``x_upper`` — control-point *x*-coordinates on the upper
          surface (``list[float]``).
        * ``x_lower`` — control-point *x*-coordinates on the lower
          surface (``list[float]``).
        * ``alpha_deg`` — angle of attack in degrees (``float``).
    """
    alpha = np.radians(alpha_deg)
    cos_a = np.cos(alpha)
    sin_a = np.sin(alpha)

    n_panels = len(coords) - 1
    n_half = n_panels // 2

    # ---- panel geometry ----
    x1 = coords[:-1, 0]
    y1 = coords[:-1, 1]
    x2 = coords[1:, 0]
    y2 = coords[1:, 1]

    dx = x2 - x1
    dy = y2 - y1
    lengths = np.sqrt(dx ** 2 + dy ** 2)
    theta = np.arctan2(dy, dx)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    # control points (panel midpoints)
    xm = 0.5 * (x1 + x2)
    ym = 0.5 * (y1 + y2)

    # ---- influence coefficients (N x N) ----
    # Transform every control point *i* into every panel *j*'s local
    # coordinate system.
    dxij = xm[:, np.newaxis] - x1[np.newaxis, :]  # (N, N)
    dyij = ym[:, np.newaxis] - y1[np.newaxis, :]

    xi = dxij * cos_t[np.newaxis, :] + dyij * sin_t[np.newaxis, :]
    eta = -dxij * sin_t[np.newaxis, :] + dyij * cos_t[np.newaxis, :]

    S = lengths[np.newaxis, :]  # (1, N) for broadcasting

    r1_sq = xi ** 2 + eta ** 2
    r2_sq = (xi - S) ** 2 + eta ** 2

    # Clamp to avoid log(0) at panel endpoints
    r1_sq = np.maximum(r1_sq, 1e-30)
    r2_sq = np.maximum(r2_sq, 1e-30)

    log_ratio = np.log(r1_sq / r2_sq)
    dbeta = np.arctan2(eta, xi - S) - np.arctan2(eta, xi)

    # Source local velocities (per unit strength)
    u_s_local = log_ratio / (4.0 * np.pi)
    v_s_local = dbeta / (2.0 * np.pi)

    # Transform source velocities to global frame
    u_s = u_s_local * cos_t[np.newaxis, :] - v_s_local * sin_t[np.newaxis, :]
    v_s = u_s_local * sin_t[np.newaxis, :] + v_s_local * cos_t[np.newaxis, :]

    # Vortex local: u_v = v_s_local,  v_v = -u_s_local
    # Transform vortex velocities to global frame
    u_v = v_s_local * cos_t[np.newaxis, :] + u_s_local * sin_t[np.newaxis, :]
    v_v = v_s_local * sin_t[np.newaxis, :] - u_s_local * cos_t[np.newaxis, :]

    # Project onto panel *i*'s normal  n_i = (-sin theta_i, cos theta_i)
    #                 and tangent       t_i = ( cos theta_i, sin theta_i)
    sin_i = sin_t[:, np.newaxis]
    cos_i = cos_t[:, np.newaxis]

    A_n = -u_s * sin_i + v_s * cos_i   # source  -> normal
    A_t = u_s * cos_i + v_s * sin_i    # source  -> tangential
    B_n = -u_v * sin_i + v_v * cos_i   # vortex  -> normal
    B_t = u_v * cos_i + v_v * sin_i    # vortex  -> tangential

    # Self-influence: the general formula has a singularity (arctan2 of
    # zero eta) whose sign depends on floating-point noise.  The
    # analytical values are known exactly:
    #   source  → outward normal = +1/2, tangential = 0
    #   vortex  → normal = 0,           tangential = +1/2
    np.fill_diagonal(A_n, 0.5)
    np.fill_diagonal(A_t, 0.0)
    np.fill_diagonal(B_n, 0.0)
    np.fill_diagonal(B_t, 0.5)

    # ---- assemble (N+1) x (N+1) linear system ----
    M = np.zeros((n_panels + 1, n_panels + 1))

    # rows 0 .. N-1: flow tangency (normal velocity = 0)
    M[:n_panels, :n_panels] = A_n
    M[:n_panels, n_panels] = np.sum(B_n, axis=1)

    # row N: Kutta condition  V_t(panel 0) + V_t(panel N-1) = 0
    M[n_panels, :n_panels] = A_t[0, :] + A_t[n_panels - 1, :]
    M[n_panels, n_panels] = np.sum(B_t[0, :]) + np.sum(B_t[n_panels - 1, :])

    # right-hand side
    rhs = np.zeros(n_panels + 1)
    # -V_inf . n_i  =  sin(theta_i - alpha)
    rhs[:n_panels] = sin_t * cos_a - cos_t * sin_a
    # -(V_inf . t_0 + V_inf . t_{N-1})
    rhs[n_panels] = -(
        cos_t[0] * cos_a + sin_t[0] * sin_a
        + cos_t[n_panels - 1] * cos_a + sin_t[n_panels - 1] * sin_a
    )

    # ---- solve ----
    solution = np.linalg.solve(M, rhs)
    sigma = solution[:n_panels]
    gamma = solution[n_panels]

    # ---- tangential velocity & Cp ----
    V_t = (
        A_t @ sigma
        + gamma * np.sum(B_t, axis=1)
        + cos_a * cos_t + sin_a * sin_t   # V_inf . t_i
    )
    Cp = 1.0 - V_t ** 2

    # ---- force coefficients (pressure integration) ----
    # CL (lift normal to freestream)
    CL = float(-np.sum(Cp * lengths * np.cos(theta - alpha)))

    # Cm about quarter-chord (0.25, 0), positive = nose-up
    Cm_c4 = float(
        np.sum(Cp * lengths * ((xm - 0.25) * cos_t + ym * sin_t))
    )

    # ---- split upper / lower Cp ----
    # panels 0 .. n_half-1  : lower surface (TE -> LE order)
    # panels n_half .. N-1  : upper surface (LE -> TE order)
    x_lower = xm[:n_half][::-1].tolist()
    Cp_lower = Cp[:n_half][::-1].tolist()
    x_upper = xm[n_half:].tolist()
    Cp_upper = Cp[n_half:].tolist()

    return {
        "CL": round(CL, 6),
        "Cm_c4": round(Cm_c4, 6),
        "Cp_upper": Cp_upper,
        "Cp_lower": Cp_lower,
        "x_upper": x_upper,
        "x_lower": x_lower,
        "alpha_deg": float(alpha_deg),
    }


# ---------------------------------------------------------------------------
# Multi-alpha sweep
# ---------------------------------------------------------------------------

def compute_cl_curve(
    coords: np.ndarray,
    alpha_range: tuple = (-5, 15),
    alpha_step: float = 1.0,
) -> dict:
    """Compute CL and Cm over a range of angles of attack.

    Args:
        coords: Airfoil coordinates of shape ``(N+1, 2)`` (counter-
            clockwise ordering, as returned by :func:`generate_naca4`).
        alpha_range: ``(alpha_min, alpha_max)`` in degrees.
            Default ``(-5, 15)``.
        alpha_step: Step size in degrees.  Default ``1.0``.

    Returns:
        ``dict`` with keys:

        * ``alpha_deg`` — list of angles of attack (degrees).
        * ``CL`` — list of lift coefficients.
        * ``Cm`` — list of moment coefficients about c/4.
        * ``CL_alpha`` — lift-curve slope in **1/deg** (``float``),
          from a linear fit over the supplied range.
    """
    alphas = np.arange(
        alpha_range[0],
        alpha_range[1] + alpha_step * 0.5,
        alpha_step,
    )

    cl_list: List[float] = []
    cm_list: List[float] = []

    for a in alphas:
        result = solve_panel(coords, float(a))
        cl_list.append(result["CL"])
        cm_list.append(result["Cm_c4"])

    # Linear fit for CL_alpha over the whole range
    coeffs = np.polyfit(alphas, np.array(cl_list), 1)
    cl_alpha = float(coeffs[0])  # slope in 1/deg

    return {
        "alpha_deg": alphas.tolist(),
        "CL": cl_list,
        "Cm": cm_list,
        "CL_alpha": round(cl_alpha, 6),
    }


# ---------------------------------------------------------------------------
# Top-level convenience
# ---------------------------------------------------------------------------

def analyze_airfoil(
    naca_code: str,
    alpha_deg: float = 5.0,
    n_panels: int = 100,
) -> dict:
    """Analyse a NACA 4-digit airfoil: generate, solve, compute CL slope.

    Generates the airfoil geometry, solves the panel method at the given
    angle of attack, and estimates the lift-curve slope from a +/-2 deg
    perturbation.

    Limitations:
        Inviscid solver.  CL is accurate for attached flow
        (alpha < ~12 deg).  No viscous drag prediction.  Stall
        behaviour is not captured.

    Args:
        naca_code: NACA 4-digit code (e.g. ``"0012"``, ``"2412"``).
        alpha_deg: Angle of attack in degrees.  Default ``5.0``.
        n_panels: Number of panels.  Default ``100``.

    Returns:
        ``dict`` with keys:

        * ``naca_code`` — the input NACA code.
        * ``n_panels`` — number of panels used.
        * ``alpha_deg`` — angle of attack (degrees).
        * ``CL`` — lift coefficient at *alpha_deg*.
        * ``Cm_c4`` — moment coefficient about c/4 at *alpha_deg*.
        * ``CL_alpha_per_deg`` — lift-curve slope (1/deg).
        * ``CL_alpha_per_rad`` — lift-curve slope (1/rad).
        * ``Cp_upper``, ``Cp_lower`` — pressure-coefficient lists.
        * ``x_upper``, ``x_lower`` — control-point x-coordinates.
        * ``coords`` — airfoil coordinates, shape ``(N+1, 2)``.
    """
    coords = generate_naca4(naca_code, n_panels=n_panels)
    result = solve_panel(coords, alpha_deg)

    # CL_alpha from +/-2 deg perturbation
    r_plus = solve_panel(coords, alpha_deg + 2.0)
    r_minus = solve_panel(coords, alpha_deg - 2.0)
    cl_alpha_deg = (r_plus["CL"] - r_minus["CL"]) / 4.0
    cl_alpha_rad = cl_alpha_deg * 180.0 / np.pi

    return {
        "naca_code": naca_code,
        "n_panels": n_panels,
        "alpha_deg": alpha_deg,
        "CL": result["CL"],
        "Cm_c4": result["Cm_c4"],
        "CL_alpha_per_deg": round(cl_alpha_deg, 6),
        "CL_alpha_per_rad": round(cl_alpha_rad, 4),
        "Cp_upper": result["Cp_upper"],
        "Cp_lower": result["Cp_lower"],
        "x_upper": result["x_upper"],
        "x_lower": result["x_lower"],
        "coords": coords,
    }


# ---------------------------------------------------------------------------
# Friction drag estimate
# ---------------------------------------------------------------------------

def estimate_drag_friction(
    coords: np.ndarray,
    alpha_deg: float,
    Re: float,
) -> dict:
    """Estimate skin-friction drag using flat-plate analogy.

    Uses the Blasius formula (laminar) and the Prandtl one-seventh-power
    law (turbulent) with a simple transition criterion
    (Re_x_crit = 5 x 10^5).  The friction coefficient is scaled by the
    actual wetted perimeter of the airfoil (sum of panel lengths on both
    surfaces), which is slightly larger than ``2c``.

    This is a rough engineering estimate; the real friction drag depends
    on the pressure gradient, which this method ignores.

    Args:
        coords: Airfoil coordinates of shape ``(N+1, 2)``.
        alpha_deg: Angle of attack in degrees (included for API
            consistency; the flat-plate model does not use it).
        Re: Chord Reynolds number (must be positive).

    Returns:
        ``dict`` with keys:

        * ``Cd_friction`` — total friction-drag coefficient.
        * ``Cf_laminar`` — laminar skin-friction coefficient.
        * ``Cf_turbulent`` — turbulent skin-friction coefficient
          (``0.0`` if fully laminar).
        * ``transition_x_upper`` — estimated transition x/c on upper
          surface.
        * ``transition_x_lower`` — estimated transition x/c on lower
          surface.
        * ``Re`` — Reynolds number used.
    """
    Re = float(Re)
    if Re <= 0:
        raise ValueError(f"Reynolds number must be positive, got {Re}")

    RE_CRIT = 5.0e5  # critical Re_x for transition on a flat plate

    # Transition location as fraction of chord
    x_tr = min(RE_CRIT / Re, 1.0)

    # Wetted perimeter ratio (for unit chord, ~2 for thin airfoils)
    panel_dx = np.diff(coords[:, 0])
    panel_dy = np.diff(coords[:, 1])
    wetted = float(np.sum(np.sqrt(panel_dx ** 2 + panel_dy ** 2)))

    # Skin-friction coefficients (flat plate)
    Cf_lam = 1.328 / np.sqrt(Re)

    if Re > RE_CRIT:
        Cf_turb_full = 0.074 / Re ** 0.2
        # Prandtl-Schlichting mixed BL correction
        Cf_mixed = Cf_turb_full - (RE_CRIT / Re) * (
            0.074 / RE_CRIT ** 0.2 - 1.328 / np.sqrt(RE_CRIT)
        )
        Cd_f = Cf_mixed * wetted
    else:
        Cf_turb_full = 0.0
        Cd_f = Cf_lam * wetted

    return {
        "Cd_friction": round(float(Cd_f), 6),
        "Cf_laminar": round(float(Cf_lam), 6),
        "Cf_turbulent": round(float(Cf_turb_full), 6),
        "transition_x_upper": round(x_tr, 4),
        "transition_x_lower": round(x_tr, 4),
        "Re": Re,
    }
