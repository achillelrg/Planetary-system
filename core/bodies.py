"""Definitions of the celestial bodies used in the simulation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

import numpy as np


@dataclass
class Body:
    """Representation of a celestial body in the 2D simulation plane."""

    name: str
    mass: float
    position: np.ndarray
    velocity: np.ndarray
    color: str = "white"

    def copy(self) -> "Body":
        """Return a deep copy of the body, cloning position and velocity arrays."""

        return Body(
            name=self.name,
            mass=self.mass,
            position=self.position.copy(),
            velocity=self.velocity.copy(),
            color=self.color,
        )


@dataclass
class SystemState:
    """Aggregate container for all bodies participating in the simulation."""

    bodies: List[Body] = field(default_factory=list)

    def copy(self) -> "SystemState":
        """Return a deep copy of the complete system state."""

        return SystemState([body.copy() for body in self.bodies])

    @property
    def positions(self) -> np.ndarray:
        """Return the stacked positions as an ``(N, 2)`` NumPy array."""

        return np.stack([body.position for body in self.bodies], axis=0)

    @property
    def velocities(self) -> np.ndarray:
        """Return the stacked velocities as an ``(N, 2)`` NumPy array."""

        return np.stack([body.velocity for body in self.bodies], axis=0)

    @property
    def masses(self) -> np.ndarray:
        """Return the masses of each body as a 1D NumPy array."""

        return np.array([body.mass for body in self.bodies])

    def update(self, positions: np.ndarray, velocities: np.ndarray) -> None:
        """Update the state of every body from stacked position/velocity arrays."""

        for body, pos, vel in zip(self.bodies, positions, velocities):
            body.position[...] = pos
            body.velocity[...] = vel

    def names(self) -> Iterable[str]:
        """Return an iterable of the body names in order."""

        return (body.name for body in self.bodies)
