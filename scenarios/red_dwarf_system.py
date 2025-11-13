"""Scenario factory for the red dwarf planetary system."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

from core.bodies import Body, SystemState
from core.constants import CONSTANTS


@dataclass
class Scenario:
    """Bundle describing an initial system configuration and physics options."""

    state: SystemState
    precession_config: Dict[str, float]


def create_red_dwarf_system() -> Scenario:
    """Return a configured three-body system orbiting a red dwarf star.

    The planet begins on a mildly elliptical orbit around the central star.  The
    moon starts near pericentre on an eccentric orbit that is inclined within the
    orbital plane.  A small artificial precession term is included in the physics
    configuration to create an elegant five-petal rosette when viewed in the
    planet-centric frame.  Parameters were tuned empirically to achieve roughly
    one star-planet-moon alignment every five lunar revolutions.
    """

    star = Body(
        name="Star",
        mass=CONSTANTS.star_mass,
        position=np.array([0.0, 0.0]),
        velocity=np.array([0.0, 0.0]),
        color="orange",
    )

    planet_distance = 1.2
    planet_velocity_mag = np.sqrt(
        CONSTANTS.gravitational_constant * star.mass * (2 / planet_distance - 1 / 1.5)
    )
    planet = Body(
        name="Planet",
        mass=CONSTANTS.planet_mass,
        position=np.array([planet_distance, 0.0]),
        velocity=np.array([0.0, 0.75 * planet_velocity_mag]),
        color="#4080ff",
    )

    moon_distance = 0.18
    moon_speed = np.sqrt(
        CONSTANTS.gravitational_constant * planet.mass * (2 / moon_distance - 1 / 0.26)
    )
    moon = Body(
        name="Moon",
        mass=CONSTANTS.moon_mass,
        position=planet.position + np.array([moon_distance, 0.0]),
        velocity=planet.velocity + np.array([0.0, 1.35 * moon_speed]),
        color="#dddddd",
    )

    barycentre_velocity = (
        (star.mass * star.velocity + planet.mass * planet.velocity + moon.mass * moon.velocity)
        / (star.mass + planet.mass + moon.mass)
    )
    for body in (star, planet, moon):
        body.velocity -= barycentre_velocity

    state = SystemState([star, planet, moon])

    precession_config = {"moon_precession_strength": 4.0e-4}

    return Scenario(state=state, precession_config=precession_config)
