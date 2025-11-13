"""Physical constants and default units for the planetary system simulation."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicalConstants:
    """Container for the normalized gravitational constants used in the simulation.

    The simulation operates in a non-dimensionalized unit system to keep the
    numerical values near unity and avoid floating-point precision issues.  The
    chosen scale implicitly sets the gravitational constant ``G`` to one and
    measures mass in units of the central star's mass, distance in astronomical
    units of convenience, and time in a scaled day.  These relative units allow
    the integrator to remain stable while still producing visually convincing
    orbital motion.
    """

    gravitational_constant: float = 1.0
    star_mass: float = 1.0
    planet_mass: float = 2.5e-3
    moon_mass: float = 3.0e-5


CONSTANTS = PhysicalConstants()
"""Default instance with normalized gravitational parameters."""
