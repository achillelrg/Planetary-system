import json
from dataclasses import asdict

import numpy as np

from config import SimulationConfig
from orbits import compute_trajectories


def compute_metrics(cfg: SimulationConfig, times: np.ndarray, positions: np.ndarray) -> dict:
    """Calcule quelques métriques simples : nombre de tours de la lune, temps d'alignement."""
    # Nombre de tours de la lune (théorique, vu comment on a défini la cinématique)
    moon_orbits = int(cfg.moon_orbits_per_planet_orbit * cfg.num_planet_orbits)

    # Alignements étoile-planète-lune (colinéarité avec étoile à l'origine)
    vp = positions[:, 1, :]  # vecteur planète depuis l’étoile
    vm = positions[:, 2, :]  # vecteur lune depuis l’étoile

    cross = vp[:, 0] * vm[:, 1] - vp[:, 1] * vm[:, 0]
    dot = vp[:, 0] * vm[:, 0] + vp[:, 1] * vm[:, 1]

    normp = np.linalg.norm(vp, axis=1)
    normm = np.linalg.norm(vm, axis=1)
    denom = normp * normm
    with np.errstate(divide="ignore", invalid="ignore"):
        sin_angle = np.where(denom > 0, cross / denom, 0.0)

    # "Quasi colinéaire" + même direction (dot > 0)
    mask = (np.abs(sin_angle) < 1e-3) & (dot > 0)
    alignment_times = times[mask]

    metrics = {
        "moon_orbit_count": moon_orbits,
        "alignment_times": alignment_times.tolist(),
        "config": asdict(cfg),
    }
    return metrics


def run_simulation(cfg: SimulationConfig):
    print("Computing trajectories...")
    times, positions, names = compute_trajectories(cfg)
    print("Trajectories computed.")

    if cfg.save_trajectories:
        np.savez(cfg.trajectories_file, times=times, positions=positions, names=names)
        
        # Export JSON for Web App
        # positions shape: (T, 3, 3) -> (Time, Body, Coords)
        # We want a structure like: { "times": [...], "bodies": { "Star": [[x,y,z], ...], ... } }
        
        # Downsample for web performance if needed (e.g., every 10th point)
        step = 1 
        
        data_for_json = {
            "times": times[::step].tolist(),
            "bodies": {}
        }
        
        for i, name in enumerate(names):
            # positions[:, i, :] is (T, 3)
            data_for_json["bodies"][name] = positions[::step, i, :].tolist()
            
        print("Writing trajectories.json...")
        with open("trajectories.json", "w", encoding="utf-8") as f:
            json.dump(data_for_json, f)
        print("trajectories.json written.")

    print("Computing metrics...")
    metrics = compute_metrics(cfg, times, positions)
    with open(cfg.metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    return times, positions, names, metrics
