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
        const stats = await afs.stat(path);
        return !stats.isDirectory()
    } catch (err) {
        return false;
    }
}

let isScanning = false

async function refreshDisks() {
    if (isScanning) return
    isScanning = true

    try {
        const entries = await afs.readdir(AUTOMOUNTS_DIR, { withFileTypes: true });

        for (const entry of entries) {
            if (entry.isDirectory()) {
                const mountPath = path.join(AUTOMOUNTS_DIR, entry.name)
                const programloaderPath = path.join(mountPath, PROGRAM_LOADER_FILE)
                if (await isFile(programloaderPath)) {
                    
                }
            }
        }
    } catch (err) {
        console.error(err.message);
    }

    isScanning = false
}

refreshDisks()
setInterval(refreshDisks, 1000)

}