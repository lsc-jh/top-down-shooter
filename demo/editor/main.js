import * as THREE from "three";
import {OrbitControls} from "three/addons/controls/OrbitControls.js";

const WIDTH = 10;
const HEIGHT = 5;
const TILE_SIZE = 1;
const LAYERS = 3;

const layerLabel = document.getElementById("layerLabel");
const tileLabel = document.getElementById("tileLabel");

const layers = Array.from({length: LAYERS}, () =>
    Array.from({length: HEIGHT}, () =>
        Array.from({length: WIDTH}, () => ({
            index: 0,
            rotation: 0,
        }))
    )
);

let selectedLayer = 0;
let selectedTile = 1;
let hideEmpty = false;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000);

const camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    100
);
camera.position.set(8, 10, 12);

const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
document.getElementById("three").appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(5, 0, 2);
controls.update();

const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(5, 10, 5);
scene.add(light);

const COLORS = [
    0x444444,
    0xff5555,
    0x55ff55,
    0x5555ff,
    0xffff55,
];

const tileMeshes = [];

function createGrid(layerIndex) {
    const points = [];

    const width = WIDTH * TILE_SIZE;
    const height = HEIGHT * TILE_SIZE;
    const y = layerIndex * 0.6 + 0.01;

    const offset = TILE_SIZE / 2;

    for (let x = 0; x <= WIDTH; x++) {
        const xPos = x * TILE_SIZE - offset;

        points.push(
            new THREE.Vector3(xPos, y, -offset),
            new THREE.Vector3(xPos, y, height - offset)
        );
    }

    for (let z = 0; z <= HEIGHT; z++) {
        const zPos = z * TILE_SIZE - offset;

        points.push(
            new THREE.Vector3(-offset, y, zPos),
            new THREE.Vector3(width - offset, y, zPos)
        );
    }

    const geometry = new THREE.BufferGeometry().setFromPoints(points);

    const material = new THREE.LineBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.2,
    });

    const grid = new THREE.LineSegments(geometry, material);
    scene.add(grid);
}

function buildScene() {
    tileMeshes.length = 0;

    for (let l = 0; l < LAYERS; l++) {
        createGrid(l);

        for (let y = 0; y < HEIGHT; y++) {
            for (let x = 0; x < WIDTH; x++) {
                const geo = new THREE.PlaneGeometry(TILE_SIZE, TILE_SIZE);
                const mat = new THREE.MeshStandardMaterial({
                    color: COLORS[0],
                    side: THREE.DoubleSide,
                    transparent: true,
                    opacity: 1,
                });

                const mesh = new THREE.Mesh(geo, mat);
                mesh.rotation.x = -Math.PI / 2;

                mesh.position.set(
                    x * TILE_SIZE,
                    l * 0.6,
                    y * TILE_SIZE
                );

                scene.add(mesh);

                tileMeshes.push({mesh, x, y, l});
            }
        }
    }
}

buildScene();

function updateScene() {
    for (const {mesh, x, y, l} of tileMeshes) {
        const tile = layers[l][y][x];
        if (tile.index === 0 && hideEmpty) {
            mesh.visible = false;
            continue;
        }

        mesh.visible = true;

        mesh.material.color.setHex(COLORS[tile.index]);

        if (l === selectedLayer) {
            mesh.material.opacity = 1;
        } else {
            mesh.material.opacity = 0.65;
        }
    }
}

const canvas = document.getElementById("map2d");
const ctx = canvas.getContext("2d");

const CELL_W = canvas.width / WIDTH;
const CELL_H = canvas.height / HEIGHT;

function draw2D() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (let y = 0; y < HEIGHT; y++) {
        for (let x = 0; x < WIDTH; x++) {
            const tile = layers[selectedLayer][y][x];

            ctx.fillStyle = "#" + COLORS[tile.index].toString(16).padStart(6, "0");
            ctx.fillRect(x * CELL_W, y * CELL_H, CELL_W, CELL_H);

            ctx.strokeStyle = "#000";
            ctx.strokeRect(x * CELL_W, y * CELL_H, CELL_W, CELL_H);
        }
    }

    ctx.fillStyle = "white";
    ctx.fillText(`Layer: ${selectedLayer}`, 5, 10);
}

draw2D();

canvas.addEventListener("click", (e) => {
    const rect = canvas.getBoundingClientRect();

    const x = Math.floor((e.clientX - rect.left) / CELL_W);
    const y = Math.floor((e.clientY - rect.top) / CELL_H);

    if (x < 0 || y < 0 || x >= WIDTH || y >= HEIGHT) return;

    layers[selectedLayer][y][x].index = selectedTile;

    updateScene();
    draw2D();
});

window.addEventListener("keydown", (e) => {
    if (e.key === "1") selectedLayer = 0;
    if (e.key === "2") selectedLayer = 1;
    if (e.key === "3") selectedLayer = 2;

    if (e.key === "q") selectedTile = 0;
    if (e.key === "w") selectedTile = 1;
    if (e.key === "e") selectedTile = 2;
    if (e.key === "r") selectedTile = 3;

    if (e.key === "h") hideEmpty = !hideEmpty;

    layerLabel.textContent = selectedLayer;
    tileLabel.textContent = selectedTile;

    updateScene();
    draw2D();
});

function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}

animate();

window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});