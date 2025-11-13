"""Core physics routines for the planetary simulation."""
from __future__ import annotations

from typing import Dict, Iterable, Tuple

import numpy as np

from .bodies import SystemState
from .constants import CONSTANTS


def compute_pairwise_gravity(positions: np.ndarray, masses: np.ndarray) -> np.ndarray:
    """Compute the gravitational acceleration on each body due to all others."""

    n_bodies = positions.shape[0]
    accelerations = np.zeros_like(positions)
    for i in range(n_bodies):
        displacement = positions[i] - positions
        distance_sq = np.sum(displacement**2, axis=1)
        with np.errstate(divide="ignore"):
            inv_dist_cubed = np.where(
                distance_sq > 0.0, distance_sq ** -1.5, 0.0
            )
        force = -CONSTANTS.gravitational_constant * (
            masses[:, np.newaxis] * displacement * inv_dist_cubed[:, np.newaxis]
        )
        accelerations[i] = force.sum(axis=0)
    return accelerations


def apply_precession(
    system: SystemState,
    accelerations: np.ndarray,
    precession_config: Dict[str, float],
) -> None:
    """Apply an artificial precession term to the moon's acceleration.

    The perturbation is modelled as a small, velocity-dependent force that is
    orthogonal to the radial vector between the planet and the moon.  This term
    mimics a weak non-Keplerian potential (analogous to an oblate planet or
    relativistic precession) and gently rotates the lunar periapsis, producing a
    multi-petal rosette over successive orbits.  The perturbation strength is
    intentionally tiny so that the overall dynamics remain close to Newtonian
    gravity while achieving the desired visual effect.
    """

    strength = precession_config.get("moon_precession_strength", 0.0)
    if strength == 0.0:
        return

    try:
        planet_index = next(i for i, body in enumerate(system.bodies) if body.name == "Planet")
        moon_index = next(i for i, body in enumerate(system.bodies) if body.name == "Moon")
    except StopIteration as exc:  # pragma: no cover - configuration error helper
        raise ValueError("Precession requires bodies named 'Planet' and 'Moon'.") from exc

    planet_pos = system.bodies[planet_index].position
    moon_pos = system.bodies[moon_index].position
    relative_vector = moon_pos - planet_pos
    radius = np.linalg.norm(relative_vector)
    if radius == 0.0:
        return

    tangential_direction = np.array([-relative_vector[1], relative_vector[0]]) / radius
    accelerations[moon_index] += strength * tangential_direction


def compute_accelerations(
    system: SystemState,
    precession_config: Dict[str, float] | None = None,
) -> np.ndarray:
    """Return accelerations for each body including optional precession terms."""

    positions = system.positions
    masses = system.masses
    accelerations = compute_pairwise_gravity(positions, masses)

    if precession_config:
        apply_precession(system, accelerations, precession_config)

    return accelerations


def compute_total_energy(positions: np.ndarray, velocities: np.ndarray, masses: np.ndarray) -> Tuple[float, float]:
    """Compute kinetic and potential energy of the system."""

    kinetic = 0.5 * np.sum(masses[:, np.newaxis] * velocities**2)
    potential = 0.0
    n_bodies = len(masses)
    for i in range(n_bodies):
        for j in range(i + 1, n_bodies):
            r = np.linalg.norm(positions[i] - positions[j])
            potential -= CONSTANTS.gravitational_constant * masses[i] * masses[j] / r
    return kinetic, potential
