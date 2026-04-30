{

const { app } = require('electron')
const afs = require('fs').promises
const path = require('path')
const { spawn } = require('child_process')

const AUTOMOUNTS_DIR = '/automounts'
const PROGRAM_LOADER_FILE = 'programloader'
const AUDIO_FILE = 'audio.mp3'
const VIDEO_FILE = 'video.mp4'

// ----------------------

const splashText = document.getElementById("splash-text")
const usbImage = document.getElementById("usb-image")
const mediaImg = document.getElementById("media-img")
const overlay = document.getElementById("overlay")
const videoplayer = document.getElementById("videoplayer")
const mediaImgContainer = document.getElementById("media-img-container")

function setStatus(status) {
    usbImage.style.display = ''
    mediaImg.src = 'media.png'
    overlay.style.display = 'none'
    mediaImgContainer.classList.remove("rotationAnimation")

    switch (status) {
        case 0:
            splashText.textContent = 'Insert game or music media'
            break;

        case 1:
            splashText.textContent = 'Launching program...'
            break;

        case 2:
            mediaImgContainer.classList.add("rotationAnimation")
            splashText.textContent = 'Music playing'
            mediaImg.src = 'music.png'
            usbImage.style.display = 'none'
            break;

        case 3:
            overlay.style.display = ''
            break;
    }
}

async function isFile(path) {
    try {
        const stats = await afs.stat(path)
        return stats.isFile()
    } catch (err) {
        return false
    }
}

async function isDirectory(path) {
    try {
        const stats = await afs.stat(path)
        return stats.isDirectory()
    } catch (err) {
        return false
    }
}

// ---------------------- runProgram

let currentProcess

async function runProgram(programPath) {
    currentProcess = spawn(programPath, [], {
        stdio: 'inherit',
        cwd: path.dirname(programPath)
    })

    const exitPromise = new Promise((resolve) => {
        currentProcess.on('close', (code) => {
            currentProcess = null
            resolve()
        })
        currentProcess.on('error', (err) => {
            currentProcess = null
            resolve()
        })
    })

    await exitPromise
}

// ---------------------- refreshDisks

let isScanning = false
let currentMountPath

async function waitMediaDetach() {
    while (true) {
        try {
            await afs.access(currentMountPath);
            await new Promise(resolve => setTimeout(resolve, 500));
        } catch (err) {
            if (err.code === 'ENOENT') {
                console.log(`Media detached ${currentMountPath}`);
                break;
            } else {
                console.error(`Failed check ${currentMountPath}:`, err);
                break;
            }
        }
    }
}

async function refreshDisks() {
    if (isScanning) return
    isScanning = true

    try {
        const entries = await afs.readdir(AUTOMOUNTS_DIR, { withFileTypes: true })

        for (const entry of entries) {
            if (entry.isDirectory()) {
                const mountPath = path.join(AUTOMOUNTS_DIR, entry.name)
                const programloaderPath = path.join(mountPath, PROGRAM_LOADER_FILE)
                const audioPath = path.join(mountPath, AUDIO_FILE)
                const videoPath = path.join(mountPath, VIDEO_FILE)

                if (await isFile(programloaderPath)) {
                    currentMountPath = mountPath
                    setStatus(1)
                    await runProgram(programloaderPath)
                    setStatus(0)
                    break
                } else if (await isFile(audioPath)) {
                    currentMountPath = mountPath
                    videoplayer.src = audioPath
                    videoplayer.play()
                    setStatus(2)
                    await waitMediaDetach()
                    setStatus(0)
                    videoplayer.pause()
                    break
                } else if (await isFile(videoPath)) {
                    currentMountPath = mountPath
                    videoplayer.src = videoPath
                    videoplayer.play()
                    setStatus(3)
                    await waitMediaDetach()
                    setStatus(0)
                    videoplayer.pause()
                    break
                }
            }
        }
    } catch (err) {
        console.error(err.message)
    }

    isScanning = false
}

setStatus(0)

refreshDisks()
setInterval(refreshDisks, 1000)

async function checkMediaValid() {
    if (currentProcess && !(await isDirectory(currentMountPath))) {
        currentProcess.kill()
    }
}

setInterval(checkMediaValid, 1000)

}