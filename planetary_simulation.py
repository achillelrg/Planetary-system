"""Planetary system simulation with rosette moon orbit and eclipse events.

This module visualizes a stylized planetary system composed of a central red dwarf,
a mother planet, and a moon following a rosette-like trajectory. The animation is
implemented with Matplotlib and is fully parameterized so that orbital dynamics
and visual styling can be adjusted easily.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation


# ---------------------------------------------------------------------------
# Simulation parameters (modifiable)
# ---------------------------------------------------------------------------
TIME_STEP = 0.05  # Simulation time step (arbitrary units)
SPEED_MULTIPLIER = 1.0  # Global speed scaling for the animation

STAR_RADIUS = 0.35  # Visual radius of the central star
PLANET_MASS_RATIO = 9.0  # Mass of mother planet divided by the moon mass
PLANET_RADIUS_RATIO = 3.0  # Radius of mother planet divided by the moon radius
PLANET_ORBIT_RADIUS = 10.0  # Distance between star and mother planet
MOON_ORBIT_RADIUS = 3.0  # Base distance between mother planet and moon

ROSETTE_LOBES = 5  # Number of lobes in the rosette orbit
ROSETTE_ECCENTRICITY = 0.25  # Radial modulation amplitude for the rosette
ROSETTE_ANGULAR_MODULATION = 0.35  # Angular modulation amplitude for the rosette

MOTHER_ORBIT_PERIOD = 20.0  # Period of mother planet around the star
ECLIPSE_PERIOD = 5  # Number of mother orbits between consecutive eclipses
MOON_ORBIT_SPEED_FACTOR = 1.0  # Scaling applied to the moon angular speed

SHOW_TRAILS = True  # Toggle orbital trails
TRAIL_LENGTH = 1200  # Maximum number of trail points to retain

COLORS = {
    "star": "orange",
    "mother": "#4080ff",
    "moon": "#dddddd",
    "orbit": "#444444",
    "trail": "#aaaaaa",
    "eclipse": "#ff5555",
}

BACKGROUND_COLOR = "#060606"
AXIS_COLOR = "#444444"
TEXT_COLOR = "#f0f0f0"

ECLIPSE_PHASE_THRESHOLD = 0.08  # Phase tolerance around the ideal alignment
ECLIPSE_TEXT_DURATION = 200  # Number of frames for which the eclipse label stays visible

# Derived constants
MOTHER_ANGULAR_SPEED = 2.0 * math.pi / MOTHER_ORBIT_PERIOD
# Moon angular speed chosen to ensure alignment every `ECLIPSE_PERIOD` orbits
MOON_ANGULAR_SPEED = (
    (math.pi + 2.0 * math.pi * ROSETTE_LOBES)
    / (ECLIPSE_PERIOD * MOTHER_ORBIT_PERIOD)
) * MOON_ORBIT_SPEED_FACTOR

# Ratio between radii converted to actual drawing sizes
MOTHER_RADIUS = 0.6  # Base radius for drawing the mother planet
MOON_RADIUS = MOTHER_RADIUS / PLANET_RADIUS_RATIO


@dataclass(frozen=True)
class OrbitalState:
    """Container storing positions of the mother planet and moon."""

    mother: Tuple[float, float]
    moon: Tuple[float, float]


def mother_position(sim_time: float) -> Tuple[float, float]:
    """Return the mother planet position in Cartesian coordinates.

    Parameters
    ----------
    sim_time:
        Simulation time in arbitrary units.

    Returns
    -------
    tuple of float
        Coordinates (x, y) of the mother planet relative to the star.
    """

    theta = MOTHER_ANGULAR_SPEED * SPEED_MULTIPLIER * sim_time
    x = PLANET_ORBIT_RADIUS * math.cos(theta)
    y = PLANET_ORBIT_RADIUS * math.sin(theta)
    return x, y


def _moon_relative(sim_time: float) -> Tuple[float, float]:
    """Compute the moon position relative to the mother planet.

    The motion combines a mean circular orbit with radial and angular
    modulations to produce a rosette-like trajectory, while ensuring that the
    moon aligns with the star and mother planet every ``ECLIPSE_PERIOD``
    revolutions of the mother planet.
    """

    theta_base = MOON_ANGULAR_SPEED * SPEED_MULTIPLIER * sim_time
    radial_component = MOON_ORBIT_RADIUS * (1.0 + ROSETTE_ECCENTRICITY * math.cos(ROSETTE_LOBES * theta_base))
    angular_component = theta_base + ROSETTE_ANGULAR_MODULATION * math.sin(ROSETTE_LOBES * theta_base)
    rel_x = radial_component * math.cos(angular_component)
    rel_y = radial_component * math.sin(angular_component)
    return rel_x, rel_y


def moon_position(sim_time: float) -> Tuple[float, float]:
    """Return the moon position in Cartesian coordinates relative to the star."""

    mother_x, mother_y = mother_position(sim_time)
    rel_x, rel_y = _moon_relative(sim_time)
    return mother_x + rel_x, mother_y + rel_y


def is_eclipse(sim_time: float) -> bool:
    """Determine whether the system is currently in an eclipse configuration.

    An eclipse is considered to occur when the moon is aligned between the star
    and the mother planet. The detection checks that the moon is closer to the
    star than the mother planet and that its orbital phase is within a small
    tolerance of the expected alignment phase.
    """

    theta_base = MOON_ANGULAR_SPEED * SPEED_MULTIPLIER * sim_time
    # Compute angular difference from the ideal alignment phase (pi).
    phase = (theta_base - math.pi) % (2.0 * math.pi)
    if phase > math.pi:
        phase -= 2.0 * math.pi

    if abs(phase) > ECLIPSE_PHASE_THRESHOLD:
        return False

    mother = np.array(mother_position(sim_time))
    moon = np.array(moon_position(sim_time))
    star_to_mother = np.linalg.norm(mother)
    star_to_moon = np.linalg.norm(moon)

    # Moon must be between the star and the mother planet along roughly the same line.
    if star_to_moon >= star_to_mother:
        return False

    alignment = np.dot(moon, mother) / (star_to_moon * star_to_mother + 1e-9)
    return alignment > 0.995  # Ensure both vectors point almost in the same direction


def _prepare_static_elements(ax: plt.Axes) -> None:
    """Configure plot aesthetics and static decorations for the animation."""

    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_aspect("equal", adjustable="box")
    ax.spines["bottom"].set_color(AXIS_COLOR)
    ax.spines["top"].set_color(AXIS_COLOR)
    ax.spines["left"].set_color(AXIS_COLOR)
    ax.spines["right"].set_color(AXIS_COLOR)
    ax.tick_params(colors=AXIS_COLOR)

    max_radius = PLANET_ORBIT_RADIUS + MOON_ORBIT_RADIUS * (1.0 + ROSETTE_ECCENTRICITY) + 2.0
    ax.set_xlim(-max_radius, max_radius)
    ax.set_ylim(-max_radius, max_radius)
    ax.set_xlabel("Position X (ua)", color=TEXT_COLOR)
    ax.set_ylabel("Position Y (ua)", color=TEXT_COLOR)
    ax.set_title("Système planétaire : Oculaire Providence", color=TEXT_COLOR)

    legend_handles = [
        ax.plot([], [], color=COLORS["star"], marker="o", linestyle="", label="Naine rouge")[0],
        ax.plot([], [], color=COLORS["mother"], marker="o", linestyle="", label="Planète mère")[0],
        ax.plot([], [], color=COLORS["moon"], marker="o", linestyle="", label="Planète fille")[0],
    ]
    legend = ax.legend(handles=legend_handles, loc="upper right")
    for text in legend.get_texts():
        text.set_color(TEXT_COLOR)


def _precompute_rosette_path(samples: int = 2000) -> Tuple[np.ndarray, np.ndarray]:
    """Return coordinates of the full rosette trajectory for visualization."""

    times = np.linspace(0.0, ECLIPSE_PERIOD * MOTHER_ORBIT_PERIOD, samples)
    mother_points = np.array([mother_position(t) for t in times])
    rel_points = np.array([_moon_relative(t) for t in times])
    path = mother_points + rel_points
    return path[:, 0], path[:, 1]


def main() -> None:
    """Create the animation representing the planetary system."""

    fig, ax = plt.subplots(figsize=(8, 8))
    _prepare_static_elements(ax)

    # Draw static orbits
    star = plt.Circle((0, 0), STAR_RADIUS, color=COLORS["star"], zorder=3)
    ax.add_patch(star)
    orbit_circle = plt.Circle((0, 0), PLANET_ORBIT_RADIUS, color=COLORS["orbit"], fill=False, linestyle="--", alpha=0.4)
    ax.add_patch(orbit_circle)

    rosette_x, rosette_y = _precompute_rosette_path()
    ax.plot(rosette_x, rosette_y, color=COLORS["orbit"], linewidth=0.8, alpha=0.3, label="Trajectoire rosette")

    # Dynamic artists
    mother_marker = plt.Circle((0, 0), MOTHER_RADIUS, color=COLORS["mother"], zorder=5)
    moon_marker = plt.Circle((0, 0), MOON_RADIUS, color=COLORS["moon"], zorder=6)
    ax.add_patch(mother_marker)
    ax.add_patch(moon_marker)

    mother_trail, = ax.plot([], [], color=COLORS["mother"], linewidth=1.2, alpha=0.7)
    moon_trail, = ax.plot([], [], color=COLORS["trail"], linewidth=1.0, alpha=0.7)

    time_text = ax.text(0.02, 0.90, "", transform=ax.transAxes, color=TEXT_COLOR)
    eclipse_text = ax.text(0.5, 0.07, "", transform=ax.transAxes, color=COLORS["eclipse"],
                           ha="center", va="center", fontsize=14, fontweight="bold")

    mother_points: list[Tuple[float, float]] = []
    moon_points: list[Tuple[float, float]] = []
    eclipse_timer = 0

    def update(frame: int) -> None:
        """Update the animation frame by frame."""

        nonlocal eclipse_timer
        sim_time = frame * TIME_STEP
        state = OrbitalState(
            mother=mother_position(sim_time),
            moon=moon_position(sim_time),
        )

        mother_marker.center = state.mother
        moon_marker.center = state.moon

        if SHOW_TRAILS:
            mother_points.append(state.mother)
            moon_points.append(state.moon)

            if len(mother_points) > TRAIL_LENGTH:
                del mother_points[:-TRAIL_LENGTH]
            if len(moon_points) > TRAIL_LENGTH:
                del moon_points[:-TRAIL_LENGTH]

            if mother_points:
                mx, my = zip(*mother_points)
                mother_trail.set_data(mx, my)
            if moon_points:
                sx, sy = zip(*moon_points)
                moon_trail.set_data(sx, sy)
        else:
            mother_trail.set_data([], [])
            moon_trail.set_data([], [])

        total_time = frame * TIME_STEP * SPEED_MULTIPLIER
        elapsed_orbits = total_time / MOTHER_ORBIT_PERIOD
        time_text.set_text(
            f"Temps simulé : {total_time:6.2f} unités\nOrbites mère : {elapsed_orbits:5.2f}"
        )

        if is_eclipse(sim_time):
            eclipse_timer = ECLIPSE_TEXT_DURATION
        else:
            eclipse_timer = max(0, eclipse_timer - 1)

        if eclipse_timer > 0:
            eclipse_text.set_text("Éclipse !")
            moon_marker.set_facecolor(COLORS["eclipse"])
        else:
            eclipse_text.set_text("")
            moon_marker.set_facecolor(COLORS["moon"])

        return mother_marker, moon_marker, mother_trail, moon_trail, time_text, eclipse_text

    anim = FuncAnimation(
        fig,
        update,
        interval=30,
        blit=False,
        frames=10_000,
        repeat=True,
    )

    plt.show()


if __name__ == "__main__":
    main()
