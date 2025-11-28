import numpy as np
from config import SimulationConfig

def compute_trajectories(cfg: SimulationConfig):
    total_time = cfg.num_planet_orbits * cfg.T_planet
    times = np.arange(0.0, total_time + cfg.dt, cfg.dt)

    omega_p = 2 * np.pi / cfg.T_planet
    omega_m = cfg.moon_orbits_per_planet_orbit * omega_p

    # --- planète : ellipse autour de l'étoile ---
    theta_p = omega_p * times
    x_p = cfg.a_planet * np.cos(theta_p)
    y_p = cfg.b_planet * np.sin(theta_p)

    # --- base radiale/tangente attachée à la planète ---
    r_vec = np.stack([x_p, y_p], axis=-1)                  # (T, 2)
    r_norm = np.linalg.norm(r_vec, axis=1, keepdims=True)  # (T, 1)

    r_hat = np.where(r_norm > 0, r_vec / r_norm, np.array([[1.0, 0.0]]))
    t_hat = np.stack([-r_hat[:, 1], r_hat[:, 0]], axis=-1)  # rotation +90°

    # --- lune : rosace dans ce repère ---
    theta_m = omega_m * times

    # distance radiale : offset + variation
    r_radial = cfg.moon_radial_base + cfg.moon_radial_amp * np.cos(theta_m)
    # composante tangentielle (épaissit la rosace)
    r_tang = cfg.b_moon * np.sin(theta_m)

    rel = r_hat * r_radial[:, None] + t_hat * r_tang[:, None]

    x_m = x_p + rel[:, 0]
    y_m = y_p + rel[:, 1]

    x_star = np.zeros_like(times)
    y_star = np.zeros_like(times)

    # --- 3D : on reste dans le plan z=0 pour l'instant pour garantir les alignements ---
    z_star = np.zeros_like(times)
    z_p = np.zeros_like(times)
    z_m = np.zeros_like(times)

    positions = np.stack(
        [
            np.stack([x_star, y_star, z_star], axis=-1),
            np.stack([x_p,    y_p,    z_p],    axis=-1),
            np.stack([x_m,    y_m,    z_m],    axis=-1),
        ],
        axis=1,
    )
    names = np.array(["Star", "Planet", "Moon"])
    return times, positions, names
