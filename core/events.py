"""Event detection utilities for the planetary system simulation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import numpy as np


@dataclass
class OrbitalMetrics:
    """Container summarising derived orbital metrics from a simulation run."""

    moon_orbit_count: int
    mean_orbits_between_alignments: float | None
    alignment_times: List[float]
    pericentre_times: List[float]


def detect_pericentre_passages(times: Sequence[float], moon_positions: np.ndarray, planet_positions: np.ndarray) -> List[float]:
    """Detect pericentre passages of the moon relative to the planet."""

    radial_distances = np.linalg.norm(moon_positions - planet_positions, axis=1)
    pericentre_times: List[float] = []
    for i in range(1, len(radial_distances) - 1):
        if radial_distances[i] < radial_distances[i - 1] and radial_distances[i] < radial_distances[i + 1]:
            pericentre_times.append(times[i])
    return pericentre_times


def detect_alignments(
    times: Sequence[float],
    star_positions: np.ndarray,
    planet_positions: np.ndarray,
    moon_positions: np.ndarray,
    angle_threshold: float = np.deg2rad(1.5),
) -> List[float]:
    """Detect star-planet-moon alignments within an angular threshold."""

    alignments: List[float] = []
    for idx in range(len(times)):
        sp_vector = planet_positions[idx] - star_positions[idx]
        pm_vector = moon_positions[idx] - planet_positions[idx]
        sp_norm = np.linalg.norm(sp_vector)
        pm_norm = np.linalg.norm(pm_vector)
        if sp_norm == 0.0 or pm_norm == 0.0:
            continue
        cos_angle = np.dot(sp_vector, pm_vector) / (sp_norm * pm_norm)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)
        if angle <= angle_threshold:
            alignments.append(times[idx])
    return alignments


def summarise_metrics(
    times: Sequence[float],
    star_positions: np.ndarray,
    planet_positions: np.ndarray,
    moon_positions: np.ndarray,
) -> OrbitalMetrics:
    """Compute derived orbital metrics and return a structured summary."""

    pericentre_times = detect_pericentre_passages(times, moon_positions, planet_positions)
    alignments = detect_alignments(times, star_positions, planet_positions, moon_positions)

    orbit_count = len(pericentre_times)
    if len(alignments) >= 2 and orbit_count > 0:
        moon_orbits_between = []
        last_alignment_time = alignments[0]
        last_alignment_index = np.searchsorted(times, last_alignment_time)
        last_pericentre_count = np.searchsorted(pericentre_times, last_alignment_time)
        for next_alignment_time in alignments[1:]:
            next_alignment_index = np.searchsorted(times, next_alignment_time)
            next_pericentre_count = np.searchsorted(pericentre_times, next_alignment_time)
            moon_orbits_between.append(max(0, next_pericentre_count - last_pericentre_count))
            last_alignment_index = next_alignment_index
            last_pericentre_count = next_pericentre_count
        mean_orbits = float(np.mean(moon_orbits_between)) if moon_orbits_between else None
    else:
        mean_orbits = None

    return OrbitalMetrics(
        moon_orbit_count=orbit_count,
        mean_orbits_between_alignments=mean_orbits,
        alignment_times=alignments,
        pericentre_times=pericentre_times,
    )
