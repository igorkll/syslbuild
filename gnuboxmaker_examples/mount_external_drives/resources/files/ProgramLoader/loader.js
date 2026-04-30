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

function setStatus(status) {
    switch (status) {
        case 0:
            splashText.textContent = 'Insert game or music media'
            break;

        case 1:
            splashText.textContent = 'Launching program...'
            break;
    }
}

async function isFile(path) {
    try {
        const stats = await afs.stat(path)
        return !stats.isDirectory()
    } catch (err) {
        return false
    }
}

// ---------------------- runProgram

async function runProgram(programPath) {
    const currentProcess = spawn(programPath, [], {
        stdio: 'inherit',
        shell: true
    })

    const exitPromise = new Promise((resolve) => {
        currentProcess.on('close', (code) => {
            resolve()
        })
        currentProcess.on('error', (err) => {
            resolve()
        })
    })

    await exitPromise
}

// ---------------------- refreshDisks

let isScanning = false

async function refreshDisks() {
    if (isScanning) return
    isScanning = true

    try {
        const entries = await afs.readdir(AUTOMOUNTS_DIR, { withFileTypes: true })

        for (const entry of entries) {
            if (entry.isDirectory()) {
                const mountPath = path.join(AUTOMOUNTS_DIR, entry.name)
                const programloaderPath = path.join(mountPath, PROGRAM_LOADER_FILE)
                if (await isFile(programloaderPath)) {
                    setStatus(1)
                    await runProgram(programloaderPath)
                    setStatus(0)
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

}