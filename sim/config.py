"""Default configuration values for the simulation pipeline."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SimulationConfig:
    """Container for high-level runtime parameters."""

    duration: float = 50.0
    dt: float = 0.002
    integrator: str = "leapfrog"
    scenario: str = "red_dwarf_system"
    animate: bool = False
    output_dir: str = "output"


DEFAULT_CONFIG = SimulationConfig()
