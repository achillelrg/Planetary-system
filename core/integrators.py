"""Numerical integrators for the planetary system."""
from __future__ import annotations

from typing import Callable, Dict, Tuple

import numpy as np

from .bodies import SystemState

AccelerationFunc = Callable[[SystemState, Dict[str, float] | None], np.ndarray]


def leapfrog(
    state: SystemState,
    duration: float,
    dt: float,
    acceleration_fn: AccelerationFunc,
    precession_config: Dict[str, float] | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Integrate the system using the velocity Verlet (leapfrog) method."""

    n_steps = int(np.ceil(duration / dt))
    n_bodies = len(state.bodies)
    positions = np.zeros((n_steps + 1, n_bodies, 2))
    velocities = np.zeros_like(positions)

    positions[0] = state.positions
    velocities[0] = state.velocities

    temp_state = state.copy()

    accel = acceleration_fn(temp_state, precession_config)
    for step in range(1, n_steps + 1):
        new_positions = positions[step - 1] + velocities[step - 1] * dt + 0.5 * accel * dt * dt
        temp_state.update(new_positions, velocities[step - 1])
        new_accel = acceleration_fn(temp_state, precession_config)
        new_velocities = velocities[step - 1] + 0.5 * (accel + new_accel) * dt

        positions[step] = new_positions
        velocities[step] = new_velocities
        accel = new_accel

    return positions, velocities


def rk4(
    state: SystemState,
    duration: float,
    dt: float,
    acceleration_fn: AccelerationFunc,
    precession_config: Dict[str, float] | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Fourth-order Runge-Kutta integrator for comparison and validation."""

    n_steps = int(np.ceil(duration / dt))
    n_bodies = len(state.bodies)
    positions = np.zeros((n_steps + 1, n_bodies, 2))
    velocities = np.zeros_like(positions)

    positions[0] = state.positions
    velocities[0] = state.velocities

    temp_state = state.copy()

    for step in range(1, n_steps + 1):
        pos = positions[step - 1]
        vel = velocities[step - 1]

        temp_state.update(pos, vel)
        a1 = acceleration_fn(temp_state, precession_config)
        k1_pos = vel
        k1_vel = a1

        temp_state.update(pos + 0.5 * dt * k1_pos, vel + 0.5 * dt * k1_vel)
        a2 = acceleration_fn(temp_state, precession_config)
        k2_pos = vel + 0.5 * dt * k1_vel
        k2_vel = a2

        temp_state.update(pos + 0.5 * dt * k2_pos, vel + 0.5 * dt * k2_vel)
        a3 = acceleration_fn(temp_state, precession_config)
        k3_pos = vel + 0.5 * dt * k2_vel
        k3_vel = a3

        temp_state.update(pos + dt * k3_pos, vel + dt * k3_vel)
        a4 = acceleration_fn(temp_state, precession_config)
        k4_pos = vel + dt * k3_vel
        k4_vel = a4

        positions[step] = pos + (dt / 6.0) * (k1_pos + 2 * k2_pos + 2 * k3_pos + k4_pos)
        velocities[step] = vel + (dt / 6.0) * (k1_vel + 2 * k2_vel + 2 * k3_vel + k4_vel)

    return positions, velocities


def integrate(
    state: SystemState,
    duration: float,
    dt: float,
    method: str,
    acceleration_fn: AccelerationFunc,
    precession_config: Dict[str, float] | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generic integration dispatcher that returns positions and velocities."""

    integrators = {
        "leapfrog": leapfrog,
        "verlet": leapfrog,
        "rk4": rk4,
    }

    try:
        integrator = integrators[method.lower()]
    except KeyError as exc:  # pragma: no cover - invalid user input helper
        raise ValueError(f"Unknown integration method '{method}'.") from exc

    return integrator(state.copy(), duration, dt, acceleration_fn, precession_config)
