{

const { app, BrowserWindow } = require('electron')
const fs = require('fs')
const path = require('path')
const { spawn } = require('child_process')

const AUTOMOUNTS_DIR = '/automounts'
const PROGRAM_LOADER_FILE = 'programloader'

let isScanning = false

async function refreshDisks() {
    if (isScanning) return
    isScanning = true

    

    isScanning = false
}

refreshDisks()
setTimeout(refreshDisks, 1000)

}