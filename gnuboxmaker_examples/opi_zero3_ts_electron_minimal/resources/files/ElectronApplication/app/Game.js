import * as Three from 'three';
import * as Main from './Main.js';
import * as Consts from './Consts.js';
import * as Utils from './Utils.js';
import * as Gui from './Gui.js';

const number_block = document.getElementById("number_block")

// --------------------------------- ball

const texture = new Three.TextureLoader().load('./textures/ball.png');
const vertexShader = await fetch('./shaders/ball.vert').then(res => res.text());
const fragmentShader = await fetch('./shaders/ball.frag').then(res => res.text());

const material = new Three.ShaderMaterial({
    uniforms: {
        map: { value: texture },
        color1: { value: new Three.Color(0) },
        color2: { value: new Three.Color(0) }
    },

    vertexShader: vertexShader,
    fragmentShader: fragmentShader
});

const ball = new Three.Mesh(
    new Three.SphereGeometry(Consts.SPHERE_DIAMETER / 2, Consts.SPHERE_SEGMENTS, Consts.SPHERE_SEGMENTS),
    material
);

// --------------------------------- ball

const platform_texture = new Three.TextureLoader().load('./textures/ball.png');
const platform_vertexShader = await fetch('./shaders/ball.vert').then(res => res.text());
const platform_fragmentShader = await fetch('./shaders/ball.frag').then(res => res.text());

const platform_material = new Three.ShaderMaterial({
    uniforms: {
        map: { value: platform_texture }
    },

    vertexShader: platform_vertexShader,
    fragmentShader: platform_fragmentShader
});

// --------------------------------- main

let platform_geometry;
let platform_geometry_long;
let platforms = [];

let firstJump;

let current_rhythm = 0;
let current_platform_width_mul = 0;
let current_ball_diameter_mul = 0;
let current_platform_speed_mul = 0;

let current_pos = 0;
let current_running = false;
let current_height_pos = 0;
let current_height_vel = 0;
let current_time = 0;
let old_change_background_time = 0;

let platform_height;
let platform_width;

let current_platform_offset_z;

let current_palette;
let old_smoothed_ambient_color;
const palettes = [0x29074b, 0x074d1e, 0x07464d, 0x4d071e, 0x3c3a03];

let gameover_end;

function selectPalette() {
    let index;

    for (let i = 0; i < 50; i++) {
        index = Utils.randomInt(0, palettes.length - 1);
        if (index != current_palette) break;
    }

    return [palettes[index], index];
}

function updateAmbientColor(color) {
    document.body.style.backgroundColor = color.clone().multiplyScalar(0.2).getStyle();
    Main.canvasItem.style.boxShadow = `0px 0px 15px 5px ${color.clone().multiplyScalar(1.2).getStyle()}`;
    Main.scene.background = color.clone().multiplyScalar(0.4);
    material.uniforms.color1.value.copy(color).multiplyScalar(10);
    material.uniforms.color2.value.copy(color).multiplyScalar(2);
    old_smoothed_ambient_color = color;
}

let smoothedUpdateAmbientColor_intervalId;

function smoothedUpdateAmbientColor(color) {
    let old_color = old_smoothed_ambient_color;
    let value = 0;
    let needSteps = (1000 / Consts.CHANGE_BACKGROUND_SMOOTHED_TIMER) * Consts.CHANGE_BACKGROUND_SMOOTHED_SECONDS;
    let currentStep = 0;

    if (smoothedUpdateAmbientColor_intervalId)
        clearInterval(smoothedUpdateAmbientColor_intervalId);

    smoothedUpdateAmbientColor_intervalId = setInterval(() => {
        currentStep++;
        value += 1 / needSteps;
        updateAmbientColor(old_color.clone().lerp(color, value));
        if (currentStep >= needSteps) {
            clearInterval(smoothedUpdateAmbientColor_intervalId);
            smoothedUpdateAmbientColor_intervalId = null;
        }
    }, Consts.CHANGE_BACKGROUND_SMOOTHED_TIMER);

    old_smoothed_ambient_color = color;
}

function autoSelectAmbientColor() {
    const arr = selectPalette();
    current_palette = arr[1];

    const color = new Three.Color(arr[0]);

    if (old_smoothed_ambient_color) {
        smoothedUpdateAmbientColor(color);
    } else {
        updateAmbientColor(color);
    }
}

export function init() {
    Main.scene.add(ball);

    autoSelectAmbientColor();
}

function getJumpForce() {
    return Consts.JUMP_FORCE * Math.min(current_rhythm, Consts.MAX_RHYTHM_FOR_MATH_JUMP_FORCE);
}

function getGravity() {
    return Consts.GRAVITY * current_rhythm;
}

function getSphereDiameter() {
    return Consts.SPHERE_DIAMETER * current_ball_diameter_mul;
}

function getDefaultSpeed() {
    return Consts.DEFAULT_PLATFORM_SPEED * current_platform_speed_mul * Math.max((((current_rhythm - 1) * Consts.PLATFORM_SPEED_DEPENDENT_FROM_RHYTHM) + 1), Consts.PLATFORM_SPEED_MIN);
}

function jump() {
    current_height_vel = getJumpForce();
}

function getBallLandingTime(platformY) {
    const y = current_height_pos;
    const v = current_height_vel;
    const g = getGravity();

    const discriminant = v * v + 2 * g * (y - platformY);

    if (discriminant < 0 || g <= 0) return null;

    const t = (v + Math.sqrt(discriminant)) / g;

    return t;
}

function getFullJumpTime() {
    const v = getJumpForce();
    const g = getGravity();

    return 2 * v / g;
}

function getPlatformDistance() {
    return getDefaultSpeed() * getFullJumpTime();
}

function checkPlatformCollision(platform) {
    const SPHERE_DIAMETER = getSphereDiameter();
    const ballRadius = SPHERE_DIAMETER / 2;

    const ballX = ball.position.x;
    const ballZ = ball.position.z;
    const ballY = ball.position.y - ballRadius;

    const platformTop = platform.position.y + platform_height / 2;

    if (current_height_vel > 0) return false;

    if (ballY - platformTop > 0) return false;
    if (ballY - platformTop < -ballRadius * 2) return false;

    const dx = Math.abs(ballX - platform.position.x);
    const dz = Math.abs(ballZ - platform.position.z);

    //if (dx > platform_width / 2 + ballRadius) return false;
    //if (dz > platform_width / 2 + ballRadius) return false;

    //if (dx > platform_width / 2) return false;
    //if (dz > platform_width / 2) return false;

    let checkAdd = (SPHERE_DIAMETER * Consts.BALL_DIAMETER_MUL_CHECK) / 2
    if (dx > platform_width / 2 + checkAdd) return false;
    if (dz > platform_width / 2 + checkAdd) return false;

    return true;
}

export function render(delta) {
    current_time += delta;

    if (current_time > old_change_background_time + Consts.CHANGE_BACKGROUND_AFTER_TIME) {
        autoSelectAmbientColor();
        old_change_background_time = current_time;
    }

    Main.camera.position.set(Consts.CAMERA_POS.x, Consts.CAMERA_POS.y + Main.additionalCameraOffset, Consts.CAMERA_POS.z);
    Main.camera.lookAt(new Three.Vector3(Consts.CAMERA_LOOK.x, Consts.CAMERA_LOOK.y + Main.additionalCameraOffset, Consts.CAMERA_LOOK.z));

    if (current_running) {
        let platformCollide = firstJump;
        firstJump = false;

        for (let i = platforms.length - 1; i >= 0; i--) {
            const platform = platforms[i];
            platform.position.z += getDefaultSpeed() * delta;
            if (!platformCollide && checkPlatformCollision(platform)) platformCollide = true;

            if (platform.position.z >= Consts.PLATFORM_DELETE_POSITION) {
                Main.scene.remove(platforms[i]);
                platforms.splice(i, 1);
            }
        }
        
        if (current_height_pos <= Consts.GROUND_Y) {
            if (platformCollide) {
                jump();
                spawnPlatform(current_platform_offset_z);
                current_height_pos = Consts.GROUND_Y;
            } else if (current_height_pos <= Consts.GAMEOVER_Y) {
                Gui.gameover();
                gameover_end = true;
            }
        }
    }

    current_height_vel -= getGravity() * delta;
    current_height_pos += current_height_vel * delta;

    if (!current_running) {
        let lockPos = gameover_end ? Consts.GAMEOVER_Y : Consts.GROUND_Y;
        if (current_height_pos < lockPos) current_height_pos = lockPos;
    }

    ball.position.set(current_pos * Consts.HOR_VIEW_SIZE, current_height_pos + (getSphereDiameter() / 2), 0);
}

export function setData(musicItem) {
    current_rhythm = musicItem.rhythm ?? Consts.DEFAULT_TRACK_RHYTHM;
    current_platform_width_mul = musicItem.platform_width_mul ?? Consts.DEFAULT_TRACK_PLATFORM_WIDTH_MUL;
    current_ball_diameter_mul = musicItem.ball_diameter_mul ?? Consts.DEFAULT_TRACK_BALL_DIAMETER_MUL;
    current_platform_speed_mul = musicItem.platform_speed_mul ?? Consts.DEFAULT_TRACK_PLATFORM_SPEED_MUL;

    ball.scale.setScalar(current_ball_diameter_mul);
}

export function setPos(pos) {
    current_pos = pos;
}

function spawnPlatform(offsetZ=0, longPlatform=false) {
    const maxOffset = (Consts.HOR_VIEW_SIZE / 2) - (platform_width / 2);
    const platform = new Three.Mesh(longPlatform ? platform_geometry_long : platform_geometry, platform_material);
    platform.position.set(0, -(platform_height / 2), 0)
    platform.position.z = -offsetZ;
    if (!longPlatform) {
        platform.position.x = Utils.randomFloat(-maxOffset, maxOffset);
    }
    Main.scene.add(platform);
    platforms.push(platform);
    return platform;
}

function deletePlatforms() {
    platforms.forEach(platform => {
        Main.scene.remove(platform);
    });
    platforms = [];
}

function recreatePlatforms() {
    current_platform_offset_z = 0;
    deletePlatforms();

    const platformDist = getPlatformDistance();
    for (let i = 0; i < Consts.DEFAULT_PLATFORMS_COUNT; i++) {
        spawnPlatform(current_platform_offset_z, i == 0);
        current_platform_offset_z += platformDist;
    }
}

function prepairPlatforms() {
    platform_width = Consts.DEFAULT_PLATFORM_WIDTH * current_platform_width_mul;
    platform_height = Consts.DEFAULT_PLATFORM_HEIGHT;

    if (platform_geometry) platform_geometry.dispose()
    platform_geometry = new Three.BoxGeometry(platform_width, platform_height, platform_width)

    if (platform_geometry_long) platform_geometry_long.dispose()
    platform_geometry_long = new Three.BoxGeometry(Consts.LONG_PLATFORM_SIZE, platform_height, platform_width)
    
    recreatePlatforms();
}

function realStart() {
    current_running = true;
    firstJump = true;
    current_height_pos = 0;
    current_height_vel = 0;
    current_time = 0;
    old_change_background_time = 0;
    number_block.textContent = '';
}

let startIntervalId;

export function start() {
    prepairPlatforms();

    current_time = 0;
    old_change_background_time = 0;

    gameover_end = false;
    current_height_pos = Consts.GROUND_Y;

    autoSelectAmbientColor();

    let timer = 4;
    const callback = () => {
        timer = timer - 1;
        number_block.textContent = timer;
        if (timer <= 0) {
            clearInterval(startIntervalId);
            startIntervalId = null;
            realStart();
        }
    };
    callback();
    startIntervalId = setInterval(callback, 1000);
}

export function stop() {
    current_running = false;
    if (startIntervalId) {
        clearInterval(startIntervalId);
        startIntervalId = null;
    }
}
