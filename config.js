export const CONFIG = {
    // Simulation
    simSpeed: { default: 0.1, min: 0, max: 5, step: 0.01 },

    // Star
    starRadius: { default: 0.2, min: 0.1, max: 2.0, step: 0.1 },
    starBrightness: { default: 50.0, min: 0.1, max: 100.0, step: 0.1 },

    // Planet
    planetRadius: { default: 0.15, min: 0.05, max: 0.5, step: 0.01 },
    planetA: { default: 3.3, min: 1.0, max: 10.0, step: 0.1 }, // Semi-major axis
    planetB: { default: 3.3, min: 1.0, max: 10.0, step: 0.1 }, // Semi-minor axis
    planetPeriod: { default: 10.0, min: 1, max: 50, step: 0.5 },

    // Moon
    moonRadius: { default: 0.08, min: 0.01, max: 0.2, step: 0.01 },
    moonDistBase: { default: 0.95, min: 0.2, max: 3.0, step: 0.05 },
    moonDistAmp: { default: 1.5, min: 0.0, max: 3.0, step: 0.05 },
    moonB: { default: 1.0, min: 0.0, max: 2.0, step: 0.05 }, // Tangential amplitude
    moonRatio: { default: 5, min: 1, max: 50, step: 1 }, // Orbits per planet orbit
};
