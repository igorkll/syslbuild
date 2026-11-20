import * as Three from 'three';
import * as Game from './Game.js';
import * as Consts from './Consts.js';
import * as Gui from './Gui.js';

import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

// ------------------------------------- init

export let additionalCameraOffset = 0;

export const clock = new Three.Clock();

export const scene = new Three.Scene()

export const renderer = new Three.WebGLRenderer({
    antialias: true,
    preserveDrawingBuffer: true
})

export const composer = new EffectComposer(renderer);

export const canvasItem = renderer.domElement;

document.body.appendChild(renderer.domElement);
Gui.setupCanvas(renderer.domElement);

// ------------------------------------- camera

function getVerticalFov(horizontalFov, aspect) {
    const hFov = Three.MathUtils.degToRad(horizontalFov);

    return Three.MathUtils.radToDeg(
        2 * Math.atan(Math.tan(hFov / 2) / aspect)
    );
}

export const camera = new Three.PerspectiveCamera(1, 1, 0.1, 1000);

composer.addPass(
    new RenderPass(scene, camera)
);

const bloomPass = new UnrealBloomPass(
    new Three.Vector2(1, 1),
    0.2,
    0.1,
    0
);

composer.addPass(bloomPass);

function resize() {
    let width = window.innerWidth;
    if (width > Consts.MAX_WIDTH) width = Consts.MAX_WIDTH;

    renderer.setSize(width, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);

    composer.setPixelRatio(window.devicePixelRatio);
    composer.setSize(width, window.innerHeight);

    const aspect = width / window.innerHeight;
    camera.aspect = aspect;
    camera.fov = getVerticalFov(Consts.FOV, aspect);

    //additionalCameraOffset = Consts.HOR_VIEW_SIZE / 2 / aspect + 1.5;

    camera.updateProjectionMatrix();
}

resize();

// -------------------------------------

window.addEventListener('resize', resize);

let firstFrame = true;

function animate() {
    requestAnimationFrame(animate);

    const delta = Math.min(clock.getDelta(), Consts.MAX_DELTA);

    if (firstFrame) {
        Game.init();
        Gui.init();
        firstFrame = false;
    }

    Game.render(delta);

    composer.render();
}

animate();
