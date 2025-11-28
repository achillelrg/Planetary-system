# 3D Red Dwarf Planetary System Simulation

This project simulates a fictional planetary system consisting of a Red Dwarf star, a tidally locked "Eyeball" planet, and a volcanic moon with a unique 5-petal rosette orbit.

## 🌟 What You Will See

When you run the visualization, you will see:
- **Center**: A glowing **Red Dwarf Star**.
- **Orbiting**: An **Eyeball Planet** (green/brown) that always faces the star.
- **Orbiting the Planet**: A **Volcanic Moon** (purple/red) following a complex flower-shaped path (rosette).

The Moon's orbit is special: it completes exactly **5 loops** around the planet for every **1 orbit** the planet makes around the star. This creates a repeating geometric pattern.

## 🚀 How to Run

### Prerequisite
You need Python installed.

### 1. Generate Data
First, run the simulation to calculate the orbits and generate the `trajectories.json` file:

```bash
python run_simulation.py --no-animate
```

### 2. View in 3D
To view the 3D visualization, you need to start a local web server (because browsers block loading local files for security).

Run this command in the project folder:

```bash
python -m http.server
```

Then open your browser and go to: **[http://localhost:8000](http://localhost:8000)**

## ⚙️ Adjusting Parameters

You can tweak the simulation physics in **`config.py`**.

| Parameter | Description | Default |
|-----------|-------------|---------|
| **Planet Orbit** | | |
| `a_planet`, `b_planet` | Size of the planet's ellipse around the star. | `2.0`, `1.5` |
| `T_planet` | Time for one full planet year. | `10.0` |
| **Moon Orbit** | | |
| `moon_orbits_per_planet_orbit` | **Crucial**: How many moon loops per planet year. | `5` |
| `moon_radial_base` | Average distance from Planet to Moon. | `0.7` |
| `moon_radial_amp` | How much the moon moves in/out (creates the petals). | `0.9` |
| `b_moon` | Width of the moon's loop (thickness of the petal). | `0.3` |
| **Simulation** | | |
| `num_planet_orbits` | How long the simulation runs (in planet years). | `6.0` |
| `dt` | Time step accuracy (lower is smoother but slower). | `0.01` |

### Command Line Options
You can also override some settings quickly without changing the file:

- Change duration: `python run_simulation.py --orbits 10 --no-animate`
- Change precision: `python run_simulation.py --dt 0.005 --no-animate`

## 🧠 How It Works

The simulation uses **Python** (`orbits.py`) to calculate the exact position of every body at every time step using parametric equations.
1.  **Planet**: Moves on a standard ellipse.
2.  **Moon**: Its position is calculated relative to the planet using a rotating frame, creating the rosette pattern.
3.  **Export**: The positions are saved to `trajectories.json`.
4.  **Visualization**: **Three.js** (JavaScript) reads this file and updates the 3D objects in the browser frame-by-frame.
