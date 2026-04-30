{

const { app } = require('electron')
const afs = require('fs').promises
const path = require('path')
const { spawn } = require('child_process')

const AUTOMOUNTS_DIR = '/automounts'
const PROGRAM_LOADER_FILE = 'programloader'
const AUDIO_FILE = 'audio.mp3'
const VIDEO_FILE = 'video.mp4'

async function isFile(path) {
    try {
        const stats = await afs.stat(path)
        return !stats.isDirectory()
    } catch (err) {
        return false
    }
}

// ---------------------- runProgram

let isRunning = false

async function runProgram(programPath) {
    if (isRunning) return
    isRunning = true

    currentProcess = spawn(programPath, [], {
        stdio: 'inherit',
        shell: true
    })

    const exitPromise = new Promise((resolve) => {
        currentProcess.on('close', (code) => {
            console.log(`[Монитор] Процесс завершён с кодом ${code}`)
            isRunning = false
            currentProcess = null
            resolve()
        })
        currentProcess.on('error', (err) => {
            console.error(`[Монитор] Ошибка при запуске процесса: ${err.message}`)
            isRunning = false
            currentProcess = null
            resolve()
        })
    })

    await exitPromise
}

// ---------------------- refreshDisks

let isScanning = false

async function refreshDisks() {
    if (isScanning || isRunning) return
    isScanning = true

    try {
        const entries = await afs.readdir(AUTOMOUNTS_DIR, { withFileTypes: true })

        for (const entry of entries) {
            if (entry.isDirectory()) {
                const mountPath = path.join(AUTOMOUNTS_DIR, entry.name)
                const programloaderPath = path.join(mountPath, PROGRAM_LOADER_FILE)
                if (await isFile(programloaderPath)) {
                    runProgram(programloaderPath)
                    break
                }
            }
        }
    } catch (err) {
        console.error(err.message)
    }

    isScanning = false
}

refreshDisks()
setInterval(refreshDisks, 1000)

}