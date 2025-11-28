import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// --- Configuration State ---
const config = {
    // Simulation
    speed: 1.0,

    // Star
    starRadius: 0.4,
    starBrightness: 3.0,

    // Planet
    planetRadius: 0.15,
    planetA: 2.0, // Semi-major axis
    planetB: 1.5, // Semi-minor axis
    planetPeriod: 10.0,

    // Moon
    moonRadius: 0.05,
    moonDistBase: 0.9,
    moonDistAmp: 0.9,
    moonB: 0.3, // Tangential amplitude
    moonRatio: 5, // Orbits per planet orbit
};

// --- Globals ---
let scene, camera, renderer, controls;
let starMesh, planetMesh, moonMesh, sunLight;
let planetTrail, moonTrail;
let time = 0;
const TRAIL_LENGTH = 500;

// --- Initialization ---
async function init() {
    // 1. Scene Setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050505);

    addBackgroundStars();

    // 2. Camera
    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, -5, 3);
    camera.up.set(0, 0, 1);

    // 3. Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    document.body.appendChild(renderer.domElement);

    // 4. Controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0x333333);
    scene.add(ambientLight);

    sunLight = new THREE.PointLight(0xffaa00, config.starBrightness, 50);
    sunLight.position.set(0, 0, 0);
    scene.add(sunLight);

    // 6. Load Assets & Create Objects
    await createObjects();

    // 7. UI Setup
    setupUI();

    // 8. Start Animation
    document.getElementById('loading').style.opacity = 0;
    animate();
}

function addBackgroundStars() {
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    for (let i = 0; i < 2000; i++) {
        vertices.push(THREE.MathUtils.randFloatSpread(100));
        vertices.push(THREE.MathUtils.randFloatSpread(100));
        vertices.push(THREE.MathUtils.randFloatSpread(100));
    }
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    const material = new THREE.PointsMaterial({ color: 0xffffff, size: 0.1, transparent: true, opacity: 0.8 });
    const points = new THREE.Points(geometry, material);
    scene.add(points);
}

async function createObjects() {
    const textureLoader = new THREE.TextureLoader();

    const starTexture = await textureLoader.loadAsync('red_dwarf_texture.png');
    const planetTexture = await textureLoader.loadAsync('eyeball_planet_texture.png');
    const moonTexture = await textureLoader.loadAsync('moon_texture.png');

    // Star
    const starGeo = new THREE.SphereGeometry(1, 32, 32); // Base radius 1, scaled later
    const starMat = new THREE.MeshBasicMaterial({ map: starTexture });
    starMesh = new THREE.Mesh(starGeo, starMat);
    scene.add(starMesh);

    // Glow sprite
    const spriteMaterial = new THREE.SpriteMaterial({
        map: new THREE.CanvasTexture(generateGlowTexture()),
        color: 0xff4400,
        transparent: true,
        blending: THREE.AdditiveBlending
    });
    const sprite = new THREE.Sprite(spriteMaterial);
    sprite.scale.set(2, 2, 1); // Relative to star size
    starMesh.add(sprite);

    // Planet
    const planetGeo = new THREE.SphereGeometry(1, 32, 32);
    const planetMat = new THREE.MeshStandardMaterial({ map: planetTexture, roughness: 0.7 });
    planetMesh = new THREE.Mesh(planetGeo, planetMat);
    scene.add(planetMesh);

    // Moon
    const moonGeo = new THREE.SphereGeometry(1, 32, 32);
    const moonMat = new THREE.MeshStandardMaterial({ map: moonTexture, roughness: 0.8 });
    moonMesh = new THREE.Mesh(moonGeo, moonMat);
    scene.add(moonMesh);

    // Trails
    planetTrail = createTrail(0x00ff00);
    moonTrail = createTrail(0xff00ff);
    scene.add(planetTrail);
    scene.add(moonTrail);
}

function generateGlowTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 64;
    const context = canvas.getContext('2d');
    const gradient = context.createRadialGradient(32, 32, 0, 32, 32, 32);
    gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
    gradient.addColorStop(0.2, 'rgba(255, 100, 0, 0.5)');
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    context.fillStyle = gradient;
    context.fillRect(0, 0, 64, 64);
    return canvas;
}

function createTrail(color) {
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(TRAIL_LENGTH * 3);
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.LineBasicMaterial({ color: color, transparent: true, opacity: 0.5 });
    return new THREE.Line(geometry, material);
}

function updateTrail(trail, position) {
    const positions = trail.geometry.attributes.position.array;
    for (let i = 0; i < (TRAIL_LENGTH - 1) * 3; i++) {
        positions[i] = positions[i + 3];
    }
    positions[(TRAIL_LENGTH - 1) * 3] = position.x;
    positions[(TRAIL_LENGTH - 1) * 3 + 1] = position.y;
    positions[(TRAIL_LENGTH - 1) * 3 + 2] = position.z;
    trail.geometry.attributes.position.needsUpdate = true;
}

// --- Physics Logic (Ported from orbits.py) ---
function calculatePositions(t) {
    // Planet Orbit
    const omega_p = 2 * Math.PI / config.planetPeriod;
    const theta_p = omega_p * t;

    const x_p = config.planetA * Math.cos(theta_p);
    const y_p = config.planetB * Math.sin(theta_p);
    const z_p = 0;

    // Planet Basis Vectors
    const r_vec = new THREE.Vector3(x_p, y_p, 0);
    const r_norm = r_vec.length();

    let r_hat, t_hat;
    if (r_norm > 0) {
        r_hat = r_vec.clone().normalize();
        t_hat = new THREE.Vector3(-r_hat.y, r_hat.x, 0);
    } else {
        r_hat = new THREE.Vector3(1, 0, 0);
        t_hat = new THREE.Vector3(0, 1, 0);
    }

    // Moon Orbit (Rosette)
    const omega_m = config.moonRatio * omega_p;
    const theta_m = omega_m * t;

    const r_radial = config.moonDistBase + config.moonDistAmp * Math.cos(theta_m);
    const r_tang = config.moonB * Math.sin(theta_m);

    // Moon Position relative to Planet
    const rel_pos = r_hat.clone().multiplyScalar(r_radial).add(t_hat.clone().multiplyScalar(r_tang));

    const x_m = x_p + rel_pos.x;
    const y_m = y_p + rel_pos.y;
    const z_m = 0;

    return {
        planet: new THREE.Vector3(x_p, y_p, z_p),
        moon: new THREE.Vector3(x_m, y_m, z_m)
    };
}

// --- UI Handling ---
function setupUI() {
    const inputs = [
        'simSpeed', 'starRadius', 'starBrightness',
        'planetRadius', 'planetA', 'planetB', 'planetPeriod',
        'moonRadius', 'moonDistBase', 'moonDistAmp', 'moonB', 'moonRatio'
    ];

    inputs.forEach(id => {
        const el = document.getElementById(id);
        const valDisplay = document.getElementById('val-' + id);

        // Init value from config
        if (config[id] !== undefined) {
            el.value = config[id];
            valDisplay.textContent = config[id];
        }

        // Listener
        el.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            config[id] = val;
            valDisplay.textContent = val;

            // Immediate updates for static props
            if (id === 'starRadius') starMesh.scale.setScalar(val);
            if (id === 'planetRadius') planetMesh.scale.setScalar(val);
            if (id === 'moonRadius') moonMesh.scale.setScalar(val);
            if (id === 'starBrightness') sunLight.intensity = val;
        });
    });

    // Initial scale set
    starMesh.scale.setScalar(config.starRadius);
    planetMesh.scale.setScalar(config.planetRadius);
    moonMesh.scale.setScalar(config.moonRadius);
}

// --- Animation Loop ---
function animate() {
    requestAnimationFrame(animate);

    // Update Time
    // dt = 0.01 (base) * speed
    time += 0.01 * config.speed;

    // Calculate Positions
    const positions = calculatePositions(time);

    // Update Meshes
    planetMesh.position.copy(positions.planet);
    moonMesh.position.copy(positions.moon);

    // Rotations
    planetMesh.lookAt(starMesh.position);
    moonMesh.rotation.y += 0.01 * config.speed;

    // Trails
    // Only update trails if speed > 0 to avoid stacking points
    if (config.speed > 0) {
        updateTrail(planetTrail, planetMesh.position);
        updateTrail(moonTrail, moonMesh.position);
    }

    controls.update();
    renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

init();
