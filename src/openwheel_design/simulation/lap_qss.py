"""
Quasi-Steady-State (QSS) Lap Time Simulation Engine

Forward-backward integration method for computing a velocity profile
around a discretised track, using a GG-V performance envelope derived
from the vehicle's aero, powertrain and tyre parameters.

Designed for Formula Student (FSAE) autocross / endurance events.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np
from scipy.interpolate import interp1d

from openwheel_design.modules.aerodynamics.forces import (
    calculate_downforce,
    calculate_drag,
)
from openwheel_design.modules.utils.constants import GRAVITY


# ---------------------------------------------------------------------------
# Default autocross track (~800 m, 14 corners)
# ---------------------------------------------------------------------------

DEFAULT_AUTOCROSS_TRACK: List[Dict[str, float]] = [
    # Start straight
    {"radius_m": 0, "length_m": 75},
    # Tight hairpin
    {"radius_m": 4.5, "length_m": 7.1},
    # Short straight
    {"radius_m": 0, "length_m": 30},
    # Medium corner
    {"radius_m": 9.0, "length_m": 14.1},
    # Straight
    {"radius_m": 0, "length_m": 55},
    # Sweeper
    {"radius_m": 20.0, "length_m": 31.4},
    # Short link
    {"radius_m": 0, "length_m": 20},
    # Tight corner
    {"radius_m": 5.0, "length_m": 7.9},
    # Medium straight
    {"radius_m": 0, "length_m": 45},
    # Fast sweeper
    {"radius_m": 25.0, "length_m": 39.3},
    # Short straight
    {"radius_m": 0, "length_m": 25},
    # Chicane entry
    {"radius_m": 6.0, "length_m": 9.4},
    # Chicane link
    {"radius_m": 0, "length_m": 10},
    # Chicane exit
    {"radius_m": 6.0, "length_m": 9.4},
    # Straight
    {"radius_m": 0, "length_m": 55},
    # Medium corner
    {"radius_m": 12.0, "length_m": 18.8},
    # Short straight
    {"radius_m": 0, "length_m": 20},
    # Tight hairpin
    {"radius_m": 4.5, "length_m": 7.1},
    # Link
    {"radius_m": 0, "length_m": 35},
    # Sweeper
    {"radius_m": 15.0, "length_m": 23.6},
    # Short straight
    {"radius_m": 0, "length_m": 25},
    # Medium corner
    {"radius_m": 10.0, "length_m": 15.7},
    # Straight
    {"radius_m": 0, "length_m": 40},
    # Fast corner
    {"radius_m": 18.0, "length_m": 28.3},
    # Short straight
    {"radius_m": 0, "length_m": 25},
    # Tight corner
    {"radius_m": 5.5, "length_m": 8.6},
    # Transition straight
    {"radius_m": 0, "length_m": 30},
    # Extra tight hairpin
    {"radius_m": 4.5, "length_m": 7.1},
    # Short link
    {"radius_m": 0, "length_m": 15},
    # Medium corner
    {"radius_m": 8.0, "length_m": 12.6},
    # Final straight back to start
    {"radius_m": 0, "length_m": 65},
]
"""Typical FSAE autocross layout: ~810 m total, 15 corners (radii 4.5-25 m)."""


# ---------------------------------------------------------------------------
# Default vehicle parameters (representative FS car)
# ---------------------------------------------------------------------------

_DEFAULT_VEHICLE: Dict[str, float] = {
    "mass_kg": 300,
    "wheelbase_mm": 1550,
    "front_weight_pct": 45,
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fill_defaults(params: Dict[str, Any]) -> Dict[str, Any]:
    """Return *params* with missing keys filled from ``_DEFAULT_VEHICLE``."""
    merged = dict(_DEFAULT_VEHICLE)
    merged.update(params)
    return merged


def _speed_kmh(v_ms: float) -> float:
    """Convert m/s to km/h."""
    return v_ms * 3.6


def _speed_ms(v_kmh: float) -> float:
    """Convert km/h to m/s."""
    return v_kmh / 3.6


def _engine_force(v_ms: float, params: Dict[str, Any]) -> float:
    """Traction force at the contact patch for a given road speed.

    Uses P = F * v, capped by the engine's peak power.  At very low
    speeds a torque-limited clamp prevents infinite force.
    """
    power_w = params["engine_power_kW"] * 1000.0
    if v_ms < 0.5:
        v_ms = 0.5  # avoid division by zero; treat crawl as 0.5 m/s
    force_from_power = power_w / v_ms
    # Rough torque limit at the wheel (low gear stall torque)
    overall_ratio = params["gear_ratio"] * params["final_drive"]
    # Assume peak engine torque ~ power/peak_rpm; approximate peak_rpm ~10500
    peak_torque_nm = power_w / (10500 * 2 * math.pi / 60)
    max_wheel_torque = peak_torque_nm * overall_ratio
    max_traction_force = max_wheel_torque / params["tire_radius_m"]
    return min(force_from_power, max_traction_force)


# ---------------------------------------------------------------------------
# 1. GGV envelope
# ---------------------------------------------------------------------------

def generate_ggv_envelope(vehicle_params: dict) -> dict:
    """Generate the GG-V (lateral-g vs longitudinal-g vs velocity) envelope.

    For each velocity step (10-130 km/h, step 10) the function computes
    the maximum lateral, longitudinal-acceleration and braking capability
    of the vehicle, expressed in multiples of *g*.

    Parameters
    ----------
    vehicle_params : dict
        Vehicle specification.  See module docstring for required keys.

    Returns
    -------
    dict
        ``speeds_kmh``  -- list of velocity steps (km/h).
        ``max_lat_g``   -- max lateral acceleration at each speed (g).
        ``max_accel_g`` -- max longitudinal acceleration at each speed (g).
        ``max_brake_g`` -- max braking deceleration (positive, g).
    """
    p = _fill_defaults(vehicle_params)
    mass = p["mass_kg"]
    mu = p["mu"]
    brake_mu = p["brake_mu"]
    cl = p["CL"]
    cd = p["CD"]
    area = p["frontal_area_m2"]

    speeds: List[float] = list(range(10, 131, 10))
    max_lat: List[float] = []
    max_acc: List[float] = []
    max_brk: List[float] = []

    for v_kmh in speeds:
        v_ms = _speed_ms(v_kmh)
        df_n = float(calculate_downforce(cl, area, v_kmh))
        drag_n = float(calculate_drag(cd, area, v_kmh))

        weight_n = mass * GRAVITY

        # Lateral: total normal force (weight + downforce) times mu, over mass
        a_lat = mu * (weight_n + df_n) / (mass)  # m/s^2
        a_lat_g = round(a_lat / GRAVITY, 3)

        # Longitudinal acceleration: min of engine traction, tyre traction
        engine_f = _engine_force(v_ms, p)
        net_engine_f = engine_f - drag_n
        traction_limit = mu * (weight_n + df_n)
        accel_force = min(net_engine_f, traction_limit)
        a_long = max(accel_force / mass, 0.0)
        a_long_g = round(a_long / GRAVITY, 3)

        # Braking: mu * (g + aero_lift_equiv) — downforce helps braking
        a_brake = brake_mu * (weight_n + df_n) / mass  # m/s^2
        a_brake_g = round(a_brake / GRAVITY, 3)

        max_lat.append(a_lat_g)
        max_acc.append(a_long_g)
        max_brk.append(a_brake_g)

    return {
        "speeds_kmh": speeds,
        "max_lat_g": max_lat,
        "max_accel_g": max_acc,
        "max_brake_g": max_brk,
    }


# ---------------------------------------------------------------------------
# 2. Track discretisation
# ---------------------------------------------------------------------------

_SEGMENT_LENGTH: float = 1.0  # metre — resolution of distance mesh


def discretize_track(corners: List[Dict[str, float]]) -> List[Dict[str, Any]]:
    """Convert a high-level corner list into 1-m distance-based segments.

    Each input element is ``{"radius_m": float, "length_m": float}``.
    A ``radius_m`` of 0 (or >= 500) is treated as a straight.

    Parameters
    ----------
    corners : list[dict]
        Ordered list of corners / straights.

    Returns
    -------
    list[dict]
        One dict per metre of track:
        ``distance_m``, ``radius_m``, ``is_corner``, ``length_m``.
    """
    segments: List[Dict[str, Any]] = []
    cumulative_dist = 0.0

    for corner in corners:
        radius = corner.get("radius_m", 0)
        length = corner.get("length_m", 0)
        is_corner = 0 < radius < 500

        n_segs = max(1, int(round(length / _SEGMENT_LENGTH)))
        seg_len = length / n_segs

        for _ in range(n_segs):
            segments.append({
                "distance_m": round(cumulative_dist, 2),
                "radius_m": radius if is_corner else 0,
                "is_corner": is_corner,
                "length_m": round(seg_len, 3),
            })
            cumulative_dist += seg_len

    return segments


# ---------------------------------------------------------------------------
# 3. Velocity-profile solver (forward-backward integration)
# ---------------------------------------------------------------------------

def _interp_ggv(ggv: dict, field: str) -> interp1d:
    """Build an interpolator for a GGV field, extrapolating beyond bounds."""
    return interp1d(
        ggv["speeds_kmh"],
        ggv[field],
        kind="linear",
        fill_value="extrapolate",
    )


def solve_velocity_profile(
    track: List[Dict[str, Any]],
    ggv: dict,
    vehicle_params: dict,
) -> dict:
    """Compute the velocity profile by forward-backward integration.

    Algorithm
    ---------
    1. **Cornering limit** -- at every segment, ``v_corner = sqrt(a_lat_max * g * R)``.
       Straights get a high cap (200 m/s).
    2. **Forward pass** -- integrate forward: from each point, accelerate at
       the GGV-limited longitudinal-g until the next point's cornering cap.
    3. **Backward pass** -- integrate backward: brake at max deceleration-g.
    4. **Final profile** = element-wise minimum of the three arrays.

    Parameters
    ----------
    track : list[dict]
        Output of :func:`discretize_track`.
    ggv : dict
        Output of :func:`generate_ggv_envelope`.
    vehicle_params : dict
        Same as for :func:`generate_ggv_envelope`.

    Returns
    -------
    dict
        ``lap_time_s``, ``distance_m``, ``speed_ms``, ``speed_kmh``,
        ``lat_g``, ``long_g``, ``sector_times_s``.
    """
    p = _fill_defaults(vehicle_params)
    n = len(track)

    lat_interp = _interp_ggv(ggv, "max_lat_g")
    acc_interp = _interp_ggv(ggv, "max_accel_g")
    brk_interp = _interp_ggv(ggv, "max_brake_g")

    # ------ step 1: cornering speed limit ------
    v_corner = np.full(n, 200.0)  # m/s — large default for straights
    for i, seg in enumerate(track):
        if seg["is_corner"] and seg["radius_m"] > 0:
            # v = sqrt(a_lat_max_ms2 * R)
            # Use a reference a_lat at moderate speed first, then iterate once
            v_guess_kmh = 60.0
            a_lat_g = float(lat_interp(v_guess_kmh))
            a_lat_ms2 = a_lat_g * GRAVITY
            v_corner_ms = math.sqrt(a_lat_ms2 * seg["radius_m"])
            # Refine with the actual speed
            v_ref_kmh = _speed_kmh(v_corner_ms)
            v_ref_kmh = max(10.0, min(v_ref_kmh, 130.0))
            a_lat_g2 = float(lat_interp(v_ref_kmh))
            a_lat_ms2_2 = a_lat_g2 * GRAVITY
            v_corner[i] = math.sqrt(a_lat_ms2_2 * seg["radius_m"])

    # ------ step 2: forward pass (acceleration) ------
    v_forward = np.copy(v_corner)
    v_forward[0] = min(v_corner[0], 5.0)  # standing-ish start

    for i in range(1, n):
        ds = track[i]["length_m"]
        v_prev = v_forward[i - 1]
        v_kmh = max(_speed_kmh(v_prev), 10.0)
        v_kmh = min(v_kmh, 130.0)
        a_g = float(acc_interp(v_kmh))
        a_ms2 = a_g * GRAVITY
        # v^2 = v0^2 + 2*a*ds
        v_new_sq = v_prev ** 2 + 2.0 * a_ms2 * ds
        v_new = math.sqrt(max(v_new_sq, 0.0))
        v_forward[i] = min(v_new, v_corner[i])

    # ------ step 3: backward pass (braking) ------
    v_backward = np.copy(v_corner)
    v_backward[-1] = v_forward[-1]  # end at forward-pass final speed

    for i in range(n - 2, -1, -1):
        ds = track[i + 1]["length_m"]
        v_next = v_backward[i + 1]
        v_kmh = max(_speed_kmh(v_next), 10.0)
        v_kmh = min(v_kmh, 130.0)
        a_g = float(brk_interp(v_kmh))
        a_ms2 = a_g * GRAVITY
        # braking backward: v^2 = v_next^2 + 2*a*ds
        v_new_sq = v_next ** 2 + 2.0 * a_ms2 * ds
        v_new = math.sqrt(max(v_new_sq, 0.0))
        v_backward[i] = min(v_new, v_corner[i])

    # ------ step 4: composite minimum ------
    v_profile = np.minimum(np.minimum(v_forward, v_backward), v_corner)
    # Ensure no zero speeds (clamp to 0.5 m/s)
    v_profile = np.maximum(v_profile, 0.5)

    # ------ derived quantities ------
    distances = np.array([seg["distance_m"] for seg in track])
    ds_arr = np.array([seg["length_m"] for seg in track])

    # Time per segment: dt = ds / v  (use average of entry and exit speed)
    dt = np.zeros(n)
    for i in range(n):
        dt[i] = ds_arr[i] / v_profile[i]

    lap_time = float(np.sum(dt))

    # Lateral g at each point
    lat_g = np.zeros(n)
    for i, seg in enumerate(track):
        if seg["is_corner"] and seg["radius_m"] > 0:
            lat_g[i] = (v_profile[i] ** 2 / seg["radius_m"]) / GRAVITY
    lat_g = np.round(lat_g, 3)

    # Longitudinal g (finite difference on speed)
    long_g = np.zeros(n)
    for i in range(1, n):
        dv = v_profile[i] - v_profile[i - 1]
        if dt[i] > 0:
            long_g[i] = (dv / dt[i]) / GRAVITY
    long_g = np.round(long_g, 3)

    # Sector times — split track into 3 roughly equal sectors
    total_dist = float(distances[-1] + ds_arr[-1])
    sector_len = total_dist / 3.0
    sector_times: List[float] = []
    sector_time_accum = 0.0
    sector_idx = 1

    for i in range(n):
        sector_time_accum += dt[i]
        if distances[i] + ds_arr[i] >= sector_len * sector_idx:
            sector_times.append(round(sector_time_accum, 3))
            sector_time_accum = 0.0
            sector_idx += 1

    # Flush remaining time
    if sector_time_accum > 0:
        if sector_times:
            sector_times[-1] += round(sector_time_accum, 3)
        else:
            sector_times.append(round(sector_time_accum, 3))

    return {
        "lap_time_s": round(lap_time, 3),
        "distance_m": np.round(distances, 2).tolist(),
        "speed_ms": np.round(v_profile, 3).tolist(),
        "speed_kmh": np.round(v_profile * 3.6, 2).tolist(),
        "lat_g": lat_g.tolist(),
        "long_g": long_g.tolist(),
        "sector_times_s": sector_times,
    }


# ---------------------------------------------------------------------------
# 4. Top-level lap simulation
# ---------------------------------------------------------------------------

def simulate_lap(
    vehicle_params: dict,
    track: Optional[List[Dict[str, float]]] = None,
) -> dict:
    """Run a full QSS lap simulation.

    Combines :func:`generate_ggv_envelope`, :func:`discretize_track` and
    :func:`solve_velocity_profile`, and appends summary statistics.

    Parameters
    ----------
    vehicle_params : dict
        Vehicle specification (see :func:`generate_ggv_envelope`).
    track : list[dict] | None
        Track definition.  Defaults to :data:`DEFAULT_AUTOCROSS_TRACK`.

    Returns
    -------
    dict
        Full velocity-profile result plus:
        ``avg_speed_kmh``, ``max_speed_kmh``, ``min_speed_kmh``,
        ``energy_consumption_kWh``, ``ggv``, ``track_length_m``.
    """
    if track is None:
        track = DEFAULT_AUTOCROSS_TRACK

    p = _fill_defaults(vehicle_params)

    # 1. GGV envelope
    ggv = generate_ggv_envelope(p)

    # 2. Discretise track
    segments = discretize_track(track)

    # 3. Solve velocity profile
    result = solve_velocity_profile(segments, ggv, p)

    # 4. Summary statistics
    speeds_ms = np.array(result["speed_ms"])
    speeds_kmh = np.array(result["speed_kmh"])
    ds_arr = np.array([seg["length_m"] for seg in segments])

    avg_speed_kmh = round(float(np.mean(speeds_kmh)), 2)
    max_speed_kmh = round(float(np.max(speeds_kmh)), 2)
    min_speed_kmh = round(float(np.min(speeds_kmh)), 2)

    # Energy consumption: integral of F_drag * v * dt
    # dt_i = ds_i / v_i, so energy_i = F_drag_i * v_i * (ds_i / v_i) = F_drag_i * ds_i
    energy_j = 0.0
    for i in range(len(segments)):
        v_kmh_i = float(speeds_kmh[i])
        drag_n = float(calculate_drag(p["CD"], p["frontal_area_m2"], v_kmh_i))
        energy_j += drag_n * ds_arr[i]

    energy_kwh = round(energy_j / 3_600_000, 4)

    track_length = round(float(np.sum(ds_arr)), 1)

    result.update({
        "avg_speed_kmh": avg_speed_kmh,
        "max_speed_kmh": max_speed_kmh,
        "min_speed_kmh": min_speed_kmh,
        "energy_consumption_kWh": energy_kwh,
        "ggv": ggv,
        "track_length_m": track_length,
    })

    return result
