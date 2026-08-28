"""Quarter-car 2-DOF suspension vibration model for Formula Student vehicles.

Implements a two-degree-of-freedom (sprung mass + unsprung mass) vertical
dynamics model with suspension spring/damper and tire stiffness/damping.
All public functions return dicts with unit-suffixed keys following the
project convention.

Typical usage
-------------
>>> from openwheel_design.simulation.quarter_car import (
...     QuarterCarParams, analyze_ride, bump_input,
... )
>>> params = QuarterCarParams(sprung_mass_kg=65, damping_Ns_per_m=1800)
>>> result = analyze_ride(params)
>>> print(result["natural_frequencies"]["body_mode_hz"])
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from scipy.integrate import solve_ivp


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class QuarterCarParams:
    """Parameters for the quarter-car 2-DOF model.

    Attributes
    ----------
    sprung_mass_kg : float
        Quarter of total sprung mass (body, engine, driver share).
    unsprung_mass_kg : float
        Unsprung mass per corner (wheel, hub, upright, brake).
    spring_rate_N_per_m : float
        Suspension spring rate at the wheel (after motion ratio).
    damping_Ns_per_m : float
        Suspension damper coefficient.
    tire_rate_N_per_m : float
        Tire vertical stiffness.
    tire_damping_Ns_per_m : float
        Tire structural damping (typically small).
    """

    sprung_mass_kg: float = 60.0
    unsprung_mass_kg: float = 15.0
    spring_rate_N_per_m: float = 25000.0
    damping_Ns_per_m: float = 1500.0
    tire_rate_N_per_m: float = 150000.0
    tire_damping_Ns_per_m: float = 200.0


# ---------------------------------------------------------------------------
# Road input helpers
# ---------------------------------------------------------------------------

def step_input(height_m: float, t_step: float = 0.0) -> Callable[[float], float]:
    """Return a function that produces a step road displacement.

    Parameters
    ----------
    height_m : float
        Step height in metres.
    t_step : float
        Time at which the step occurs (seconds).

    Returns
    -------
    Callable[[float], float]
        ``road(t)`` returning displacement in metres.
    """

    def road(t: float) -> float:
        return height_m if t >= t_step else 0.0

    return road


def bump_input(
    height_m: float, width_m: float, speed_ms: float
) -> Callable[[float], float]:
    """Return a half-sine bump road input function.

    The bump starts when the contact patch reaches it (``t_start = 0``) and
    lasts ``width_m / speed_ms`` seconds.

    Parameters
    ----------
    height_m : float
        Peak bump height (metres).
    width_m : float
        Bump length along the road (metres).
    speed_ms : float
        Vehicle forward speed (m/s).

    Returns
    -------
    Callable[[float], float]
        ``road(t)`` returning displacement in metres.
    """
    duration = width_m / speed_ms

    def road(t: float) -> float:
        if 0.0 <= t <= duration:
            return height_m * math.sin(math.pi * t / duration)
        return 0.0

    return road


def random_road_input(
    amplitude_m: float, frequency_hz: float
) -> Callable[[float], float]:
    """Return a sinusoidal road excitation function.

    Parameters
    ----------
    amplitude_m : float
        Peak amplitude (metres).
    frequency_hz : float
        Excitation frequency (Hz).

    Returns
    -------
    Callable[[float], float]
        ``road(t)`` returning displacement in metres.
    """
    omega = 2.0 * math.pi * frequency_hz

    def road(t: float) -> float:
        return amplitude_m * math.sin(omega * t)

    return road


# ---------------------------------------------------------------------------
# ODE
# ---------------------------------------------------------------------------

def quarter_car_ode(
    t: float,
    y: List[float],
    params: QuarterCarParams,
    road_input_func: Callable[[float], float],
) -> List[float]:
    """Right-hand side of the quarter-car 2-DOF equations of motion.

    State vector ``y = [x_s, x_u, v_s, v_u]`` where *s* is sprung and *u* is
    unsprung.  Positive displacements are upward.

    Parameters
    ----------
    t : float
        Current time (s).
    y : list of float
        State vector ``[x_s, x_u, v_s, v_u]``.
    params : QuarterCarParams
        System parameters.
    road_input_func : callable
        ``road(t) -> float`` returning road surface displacement (m).

    Returns
    -------
    list of float
        State derivatives ``[v_s, v_u, a_s, a_u]``.
    """
    x_s, x_u, v_s, v_u = y

    x_road = road_input_func(t)

    # Estimate road velocity via small finite difference for tire damping
    dt_fd = 1e-7
    v_road = (road_input_func(t + dt_fd) - road_input_func(t - dt_fd)) / (2.0 * dt_fd)

    m_s = params.sprung_mass_kg
    m_u = params.unsprung_mass_kg
    k_s = params.spring_rate_N_per_m
    c_s = params.damping_Ns_per_m
    k_t = params.tire_rate_N_per_m
    c_t = params.tire_damping_Ns_per_m

    # Sprung mass: m_s * a_s = -k_s*(x_s - x_u) - c_s*(v_s - v_u)
    a_s = (-k_s * (x_s - x_u) - c_s * (v_s - v_u)) / m_s

    # Unsprung mass:
    # m_u * a_u = k_s*(x_s - x_u) + c_s*(v_s - v_u)
    #             - k_t*(x_u - x_road) - c_t*(v_u - v_road)
    a_u = (
        k_s * (x_s - x_u)
        + c_s * (v_s - v_u)
        - k_t * (x_u - x_road)
        - c_t * (v_u - v_road)
    ) / m_u

    return [v_s, v_u, a_s, a_u]


# ---------------------------------------------------------------------------
# Time-domain simulation
# ---------------------------------------------------------------------------

def simulate_time_response(
    params: QuarterCarParams,
    road_input_func: Callable[[float], float],
    t_span: Tuple[float, float],
    dt: float = 0.001,
) -> Dict[str, Union[List[float], np.ndarray]]:
    """Simulate the quarter-car model in the time domain.

    Uses ``scipy.integrate.solve_ivp`` with the RK45 method.

    Parameters
    ----------
    params : QuarterCarParams
        System parameters.
    road_input_func : callable
        ``road(t) -> float`` returning road displacement (m).
    t_span : tuple of (float, float)
        Start and end times (seconds).
    dt : float
        Maximum output time step (seconds).

    Returns
    -------
    dict
        ``time_s``            -- time array (s)
        ``sprung_disp_mm``    -- sprung mass displacement (mm)
        ``unsprung_disp_mm``  -- unsprung mass displacement (mm)
        ``sprung_accel_g``    -- sprung mass acceleration (g)
        ``tire_deflection_mm`` -- tire deflection = x_road - x_u (mm)
        ``suspension_travel_mm`` -- suspension travel = x_s - x_u (mm)
    """
    t_eval = np.arange(t_span[0], t_span[1], dt)

    sol = solve_ivp(
        fun=lambda t, y: quarter_car_ode(t, y, params, road_input_func),
        t_span=t_span,
        y0=[0.0, 0.0, 0.0, 0.0],
        method="RK45",
        t_eval=t_eval,
        rtol=1e-8,
        atol=1e-10,
    )

    if not sol.success:
        raise RuntimeError(f"ODE integration failed: {sol.message}")

    time_s = sol.t
    x_s = sol.y[0]
    x_u = sol.y[1]
    v_s = sol.y[2]

    # Compute sprung acceleration from the EOM (more accurate than
    # numerical differentiation of velocity)
    k_s = params.spring_rate_N_per_m
    c_s = params.damping_Ns_per_m
    m_s = params.sprung_mass_kg
    v_u = sol.y[3]
    a_s = (-k_s * (x_s - x_u) - c_s * (v_s - v_u)) / m_s

    # Road profile at each time step
    x_road = np.array([road_input_func(t) for t in time_s])

    GRAVITY = 9.80665

    return {
        "time_s": time_s.tolist(),
        "sprung_disp_mm": (x_s * 1000.0).tolist(),
        "unsprung_disp_mm": (x_u * 1000.0).tolist(),
        "sprung_accel_g": (a_s / GRAVITY).tolist(),
        "tire_deflection_mm": ((x_road - x_u) * 1000.0).tolist(),
        "suspension_travel_mm": ((x_s - x_u) * 1000.0).tolist(),
    }


# ---------------------------------------------------------------------------
# Frequency-domain analysis
# ---------------------------------------------------------------------------

def compute_frequency_response(
    params: QuarterCarParams,
    freq_range: Tuple[float, float] = (0.5, 30.0),
    n_points: int = 200,
) -> Dict[str, Union[List[float], float]]:
    """Compute the analytical frequency response of the 2-DOF model.

    Builds the complex transfer function H(jw) = X_s / X_road from the
    equations of motion in matrix form and evaluates it over *freq_range*.

    Parameters
    ----------
    params : QuarterCarParams
        System parameters.
    freq_range : tuple of (float, float)
        Min and max frequency in Hz.
    n_points : int
        Number of evaluation points (logarithmically spaced).

    Returns
    -------
    dict
        ``frequency_hz``       -- frequency array (Hz)
        ``displacement_gain``  -- |X_s / X_road|
        ``acceleration_gain``  -- |a_s / X_road| normalised to g/mm
        ``phase_deg``          -- phase of X_s / X_road (degrees)
        ``body_resonance_hz``  -- frequency of peak displacement gain
        ``wheel_resonance_hz`` -- frequency of peak in unsprung response
    """
    m_s = params.sprung_mass_kg
    m_u = params.unsprung_mass_kg
    k_s = params.spring_rate_N_per_m
    c_s = params.damping_Ns_per_m
    k_t = params.tire_rate_N_per_m
    c_t = params.tire_damping_Ns_per_m

    freqs_hz = np.logspace(
        np.log10(freq_range[0]), np.log10(freq_range[1]), n_points
    )
    omega = 2.0 * np.pi * freqs_hz

    disp_gain = np.empty(n_points)
    accel_gain = np.empty(n_points)
    phase_deg = np.empty(n_points)
    unsprung_gain = np.empty(n_points)

    for i, w in enumerate(omega):
        jw = 1j * w

        # Impedance matrix [Z]{X} = {F_road}
        # Row 1 (sprung):  (-m_s*w^2 + jw*c_s + k_s)*X_s - (jw*c_s + k_s)*X_u = 0
        # Row 2 (unsprung): -(jw*c_s + k_s)*X_s +
        #                   (-m_u*w^2 + jw*(c_s+c_t) + k_s + k_t)*X_u
        #                   = (jw*c_t + k_t)*X_road
        z11 = -m_s * w**2 + jw * c_s + k_s
        z12 = -(jw * c_s + k_s)
        z21 = -(jw * c_s + k_s)
        z22 = -m_u * w**2 + jw * (c_s + c_t) + k_s + k_t

        f_road = jw * c_t + k_t  # force coefficient from road input

        det_z = z11 * z22 - z12 * z21

        # X_s / X_road  (Cramer's rule, column 1 replaced by [0, f_road])
        H_xs = (z12 * (-f_road)) / det_z  # z11*0 - z12*(-f_road) ... but
        # Actually: replace col1 -> [0, f_road]:
        #   det_num_xs = 0*z22 - z12*f_road = -z12*f_road
        H_xs = (-z12 * f_road) / det_z

        # X_u / X_road (replace col2 -> [0, f_road]):
        #   det_num_xu = z11*f_road - 0*z21 = z11*f_road
        H_xu = (z11 * f_road) / det_z

        disp_gain[i] = abs(H_xs)
        accel_gain[i] = abs(H_xs) * w**2  # |a_s/X_road| in (m/s^2)/m = 1/s^2
        phase_deg[i] = np.degrees(np.angle(H_xs))
        unsprung_gain[i] = abs(H_xu)

    body_res_idx = int(np.argmax(disp_gain))
    wheel_res_idx = int(np.argmax(unsprung_gain))

    return {
        "frequency_hz": freqs_hz.tolist(),
        "displacement_gain": disp_gain.tolist(),
        "acceleration_gain": accel_gain.tolist(),
        "phase_deg": phase_deg.tolist(),
        "body_resonance_hz": round(float(freqs_hz[body_res_idx]), 2),
        "wheel_resonance_hz": round(float(freqs_hz[wheel_res_idx]), 2),
    }


# ---------------------------------------------------------------------------
# Natural frequencies (undamped eigenvalue problem)
# ---------------------------------------------------------------------------

def compute_natural_frequencies(
    params: QuarterCarParams,
) -> Dict[str, Union[float, str]]:
    """Compute undamped natural frequencies of the 2-DOF system.

    Solves ``det([K] - w^2 [M]) = 0`` for the two eigenvalues.

    Parameters
    ----------
    params : QuarterCarParams
        System parameters.

    Returns
    -------
    dict
        ``body_mode_hz``      -- lower natural frequency (Hz)
        ``wheel_hop_hz``      -- higher natural frequency (Hz)
        ``body_mode_rad_s``   -- lower natural frequency (rad/s)
        ``wheel_hop_rad_s``   -- higher natural frequency (rad/s)
        ``frequency_ratio``   -- wheel_hop_hz / body_mode_hz
    """
    m_s = params.sprung_mass_kg
    m_u = params.unsprung_mass_kg
    k_s = params.spring_rate_N_per_m
    k_t = params.tire_rate_N_per_m

    # Mass and stiffness matrices
    M = np.array([[m_s, 0.0], [0.0, m_u]])
    K = np.array([[k_s, -k_s], [-k_s, k_s + k_t]])

    # Generalised eigenvalue problem K*phi = w^2*M*phi
    # Equivalent to M^{-1}*K*phi = w^2*phi
    M_inv = np.linalg.inv(M)
    eigenvalues = np.linalg.eigvals(M_inv @ K)

    # eigenvalues = omega^2, take positive real parts
    omega_sq = np.sort(np.real(eigenvalues))
    omega = np.sqrt(np.maximum(omega_sq, 0.0))

    body_rad = float(omega[0])
    wheel_rad = float(omega[1])
    body_hz = body_rad / (2.0 * math.pi)
    wheel_hz = wheel_rad / (2.0 * math.pi)

    ratio = wheel_hz / body_hz if body_hz > 0 else float("inf")

    return {
        "body_mode_hz": round(body_hz, 2),
        "wheel_hop_hz": round(wheel_hz, 2),
        "body_mode_rad_s": round(body_rad, 3),
        "wheel_hop_rad_s": round(wheel_rad, 3),
        "frequency_ratio": round(ratio, 2),
    }


# ---------------------------------------------------------------------------
# Damping ratios
# ---------------------------------------------------------------------------

def compute_damping_ratios(
    params: QuarterCarParams,
) -> Dict[str, Union[float, bool, str]]:
    """Compute approximate damping ratios for the two modes.

    Uses the classic single-DOF approximation for each mode.

    Parameters
    ----------
    params : QuarterCarParams
        System parameters.

    Returns
    -------
    dict
        ``body_damping_ratio``      -- zeta for the body mode
        ``wheel_damping_ratio``     -- zeta for the wheel hop mode
        ``body_critically_damped``  -- True if zeta_body >= 1.0
        ``recommendation``          -- plain-text tuning note
    """
    m_s = params.sprung_mass_kg
    m_u = params.unsprung_mass_kg
    k_s = params.spring_rate_N_per_m
    k_t = params.tire_rate_N_per_m
    c_s = params.damping_Ns_per_m
    c_t = params.tire_damping_Ns_per_m

    # Body damping ratio (SDOF approximation treating unsprung as ground)
    zeta_body = c_s / (2.0 * math.sqrt(k_s * m_s))

    # Wheel hop damping ratio (SDOF approximation: unsprung on tire spring)
    zeta_wheel = (c_s + c_t) / (2.0 * math.sqrt((k_s + k_t) * m_u))

    critically_damped = zeta_body >= 1.0

    if zeta_body < 0.2:
        rec = "Under-damped: excessive body oscillation, increase damping"
    elif zeta_body < 0.3:
        rec = "Lightly damped: acceptable for smooth tracks only"
    elif 0.3 <= zeta_body <= 0.7:
        rec = "Good range for Formula Student (typical 0.3-0.7)"
    elif zeta_body <= 1.0:
        rec = "Heavily damped: good transient control, may feel harsh"
    else:
        rec = "Over-damped: slow response, reduce damping"

    return {
        "body_damping_ratio": round(zeta_body, 4),
        "wheel_damping_ratio": round(zeta_wheel, 4),
        "body_critically_damped": critically_damped,
        "recommendation": rec,
    }


# ---------------------------------------------------------------------------
# Top-level convenience
# ---------------------------------------------------------------------------

def analyze_ride(params: QuarterCarParams) -> Dict[str, dict]:
    """Run a full ride analysis with default inputs.

    Steps:
      1. Compute undamped natural frequencies.
      2. Compute damping ratios.
      3. Simulate time response for a standard bump (25 mm high, 300 mm wide,
         10 m/s forward speed).
      4. Compute frequency response (0.5 -- 30 Hz).

    Parameters
    ----------
    params : QuarterCarParams
        System parameters.

    Returns
    -------
    dict
        ``natural_frequencies`` -- from :func:`compute_natural_frequencies`
        ``damping_ratios``      -- from :func:`compute_damping_ratios`
        ``time_response``       -- from :func:`simulate_time_response`
        ``frequency_response``  -- from :func:`compute_frequency_response`
    """
    nat_freq = compute_natural_frequencies(params)
    damp = compute_damping_ratios(params)

    road = bump_input(height_m=0.025, width_m=0.3, speed_ms=10.0)
    time_resp = simulate_time_response(params, road, t_span=(0.0, 2.0), dt=0.001)

    freq_resp = compute_frequency_response(params)

    return {
        "natural_frequencies": nat_freq,
        "damping_ratios": damp,
        "time_response": time_resp,
        "frequency_response": freq_resp,
    }
