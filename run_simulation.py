import argparse
import numpy as np

from config import SimulationConfig
from simulation import run_simulation


def animate(times, positions, names, interval=30):
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_title("Red Dwarf Planetary System")
    ax.set_xlabel("X [arb. units]")
    ax.set_ylabel("Y [arb. units]")
    ax.set_aspect("equal", adjustable="box")

    # Limites globales
    x = positions[:, :, 0]
    y = positions[:, :, 1]
    margin = 0.2
    ax.set_xlim(x.min() - margin, x.max() + margin)
    ax.set_ylim(y.min() - margin, y.max() + margin)

    # Traînées + points pour étoile, planète, lune
    scatter_artists = {}
    trail_lines = {}

    colors = {"Star": "orange", "Planet": "green", "Moon": "purple"}

    for i, name in enumerate(names):
        (line,) = ax.plot([], [], "-", lw=1, color=colors.get(name, "black"))
        (pt,) = ax.plot([], [], "o", ms=6, color=colors.get(name, "black"))
        trail_lines[name] = line
        scatter_artists[name] = pt

    # Rosace : trajectoire de la lune dans le repère de la planète
    # (on la calcule UNE FOIS pour tous les temps)
    rel_all = positions[:, 2, :] - positions[:, 1, :]  # moon - planet
    (rosette_line,) = ax.plot([], [], "--", lw=1, alpha=0.6, color="violet")

    def init():
        for name in names:
            trail_lines[name].set_data([], [])
            scatter_artists[name].set_data([], [])
        rosette_line.set_data([], [])
        return [*trail_lines.values(), *scatter_artists.values(), rosette_line]

    def update(frame):
        # ----- trajectoires habituelles -----
        for i, name in enumerate(names):
            xy = positions[: frame + 1, i, :]
            trail_lines[name].set_data(xy[:, 0], xy[:, 1])
            scatter_artists[name].set_data([xy[-1, 0]], [xy[-1, 1]])

        # ----- rosace attachée à la planète -----
        planet_now = positions[frame, 1, :]       # position actuelle de la planète
        rosette_xy = planet_now + rel_all         # rosace complète centrée sur la planète
        rosette_line.set_data(rosette_xy[:, 0], rosette_xy[:, 1])

        return [*trail_lines.values(), *scatter_artists.values(), rosette_line]

    ani = FuncAnimation(
        fig,
        update,
        init_func=init,
        frames=len(times),
        interval=interval,
        blit=True,
        repeat=True,
    )
    return ani



def parse_args():
    parser = argparse.ArgumentParser(description="2D star-planet-moon orbital animation")
    parser.add_argument(
        "--orbits",
        type=float,
        default=None,
        help="Nombre d'orbites planétaires à simuler (override config)",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=None,
        help="Pas de temps (override config)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Ne pas sauvegarder trajectories.npz / metrics.json",
    )
    parser.add_argument(
        "--no-animate",
        action="store_true",
        help="Lancer la simulation sans animation",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    cfg = SimulationConfig()

    if args.orbits is not None:
        cfg.num_planet_orbits = args.orbits
    if args.dt is not None:
        cfg.dt = args.dt
    if args.no_save:
        cfg.save_trajectories = False

    times, positions, names, metrics = run_simulation(cfg)
    print("Simulation complete.")
    print(f"Moon completed {metrics['moon_orbit_count']} orbits.")
    print(f"Number of alignments detected: {len(metrics['alignment_times'])}")

    if not args.no_animate:
        ani = animate(times, positions, names)  # garder une référence !
        import matplotlib.pyplot as plt
        plt.show()



if __name__ == "__main__":
    main()
