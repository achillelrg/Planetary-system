"""Command-line entry point for running the planetary system simulation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from core.events import summarise_metrics
from core.integrators import integrate
from core.physics import compute_accelerations, compute_total_energy
from scenarios.red_dwarf_system import create_red_dwarf_system
from sim.config import DEFAULT_CONFIG, SimulationConfig


SCENARIO_LOADERS = {
    "red_dwarf_system": create_red_dwarf_system,
}


def parse_args() -> SimulationConfig:
    """Parse command-line arguments into a :class:`SimulationConfig`."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=DEFAULT_CONFIG.duration)
    parser.add_argument("--dt", type=float, default=DEFAULT_CONFIG.dt)
    parser.add_argument("--integrator", type=str, default=DEFAULT_CONFIG.integrator)
    parser.add_argument("--scenario", type=str, default=DEFAULT_CONFIG.scenario)
    parser.add_argument("--output-dir", type=str, default=DEFAULT_CONFIG.output_dir)
    parser.add_argument("--animate", action="store_true", default=DEFAULT_CONFIG.animate)

    args = parser.parse_args()
    return SimulationConfig(
        duration=args.duration,
        dt=args.dt,
        integrator=args.integrator,
        scenario=args.scenario,
        output_dir=args.output_dir,
        animate=args.animate,
    )


def load_scenario(name: str):
    """Instantiate the requested scenario."""

    try:
        loader = SCENARIO_LOADERS[name]
    except KeyError as exc:  # pragma: no cover - user error helper
        raise ValueError(f"Unknown scenario '{name}'. Available: {list(SCENARIO_LOADERS)}") from exc
    return loader()


def ensure_output_dir(path: Path) -> None:
    """Create the output directory if it does not exist."""

    path.mkdir(parents=True, exist_ok=True)


def compute_energy_profile(positions: np.ndarray, velocities: np.ndarray, masses: np.ndarray) -> np.ndarray:
    """Return the total mechanical energy of the system for each snapshot."""

    energy = np.zeros(positions.shape[0])
    for i in range(positions.shape[0]):
        kinetic, potential = compute_total_energy(positions[i], velocities[i], masses)
        energy[i] = kinetic + potential
    return energy


def save_outputs(
    output_dir: Path,
    times: np.ndarray,
    positions: np.ndarray,
    velocities: np.ndarray,
    names: Iterable[str],
    energy: np.ndarray,
    metrics_json: Dict[str, object],
) -> None:
    """Persist simulation artefacts to disk."""

    ensure_output_dir(output_dir)
    np.savez(
        output_dir / "trajectories.npz",
        times=times,
        positions=positions,
        velocities=velocities,
        names=list(names),
        energy=energy,
    )
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as fh:
        json.dump(metrics_json, fh, indent=2)


def animate_system(
    times: np.ndarray,
    positions: np.ndarray,
    names: List[str],
    metrics: Dict[str, object],
) -> None:
    """Render an animated visualisation of the simulation using Matplotlib."""

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_title("Red Dwarf Planetary System")
    ax.set_xlabel("X [arb. units]")
    ax.set_ylabel("Y [arb. units]")
    ax.set_aspect("equal", adjustable="box")

    colors = {
        "Star": "orange",
        "Planet": "#4080ff",
        "Moon": "#dddddd",
    }

    scatter_artists = {
        name: ax.plot([], [], marker="o", color=colors.get(name, "white"), markersize=10)[0]
        for name in names
    }

    trail_lines = {
        name: ax.plot([], [], color=colors.get(name, "white"), linewidth=1, alpha=0.5)[0]
        for name in names
    }

    alignment_indices = {
        int(np.searchsorted(times, alignment_time))
        for alignment_time in metrics.get("alignment_times", [])
    }

    text_box = ax.text(0.02, 0.95, "", transform=ax.transAxes, fontsize=10, va="top")
    eclipse_text = ax.text(0.5, 0.1, "", transform=ax.transAxes, color="gold", fontsize=14, ha="center")

    extent = np.max(np.abs(positions[:, :, :2])) * 1.2
    ax.set_xlim(-extent, extent)
    ax.set_ylim(-extent, extent)

    def update(frame: int):
        current_time = times[frame]
        for body_index, name in enumerate(names):
            xy = positions[: frame + 1, body_index, :2]
            scatter_artists[name].set_data(xy[-1, 0], xy[-1, 1])
            trail_lines[name].set_data(xy[:, 0], xy[:, 1])

        text_box.set_text(
            f"t = {current_time:.2f}\n"
            f"Moon orbits ≈ {metrics.get('moon_orbit_count', 0)}\n"
            f"Mean orbits/alignment ≈ {metrics.get('mean_orbits_between_alignments', 'n/a')}"
        )

        if frame in alignment_indices:
            eclipse_text.set_text("Alignment!")
        else:
            eclipse_text.set_text("")
        return list(scatter_artists.values()) + list(trail_lines.values()) + [text_box, eclipse_text]

    frames = len(times)
    interval = 1000 * (times[1] - times[0])
    FuncAnimation(fig, update, frames=frames, interval=interval, blit=True, repeat=True)
    plt.show()


def main() -> None:
    """Run the configured simulation and optionally animate the result."""

    config = parse_args()
    scenario = load_scenario(config.scenario)

    positions, velocities = integrate(
        state=scenario.state,
        duration=config.duration,
        dt=config.dt,
        method=config.integrator,
        acceleration_fn=compute_accelerations,
        precession_config=scenario.precession_config,
    )

    times = np.linspace(0.0, config.dt * (positions.shape[0] - 1), positions.shape[0])
    masses = scenario.state.masses
    energy = compute_energy_profile(positions, velocities, masses)

    metrics = summarise_metrics(
        times,
        positions[:, 0, :2],
        positions[:, 1, :2],
        positions[:, 2, :2],
    )

    metrics_json = {
        "moon_orbit_count": metrics.moon_orbit_count,
        "mean_orbits_between_alignments": metrics.mean_orbits_between_alignments,
        "alignment_times": metrics.alignment_times,
        "pericentre_times": metrics.pericentre_times,
    }

    output_dir = Path(config.output_dir)
    save_outputs(output_dir, times, positions, velocities, scenario.state.names(), energy, metrics_json)

    print("Simulation complete.")
    print(json.dumps(metrics_json, indent=2))

    if config.animate:
        animate_system(times, positions, list(scenario.state.names()), metrics_json)


if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    main()
