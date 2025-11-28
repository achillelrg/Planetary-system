from dataclasses import dataclass

@dataclass
class SimulationConfig:
    # Planète autour de l'étoile
    a_planet: float = 2.0
    b_planet: float = 1.5
    T_planet: float = 10.0

    # Lune autour de la planète (repère radial/tangent)
    moon_radial_base: float = 0.9   # offset moyen (distance moyenne planète-lune)
    moon_radial_amp: float = 0.9    # variation autour de ce moyen
    b_moon: float = 0.3             # amplitude tangente (épaisseur de la rosace)

    moon_orbits_per_planet_orbit: int = 5

    num_planet_orbits: float = 6.0
    dt: float = 0.01

    save_trajectories: bool = True
    trajectories_file: str = "trajectories.npz"
    metrics_file: str = "metrics.json"
