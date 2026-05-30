let debug = false

const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')

function createWindow () {
    const win = new BrowserWindow({
        frame: debug,
        fullscreen: !debug,
        width: 1280,
        height: 720,
        show: false,
        webPreferences: {
            devTools: debug, // DON'T FORGET TO TURN OFF THE DAMN DEVTOOLS!
            nodeIntegration: true,
            contextIsolation: false
        }
    })

    if (!debug) {
        win.webContents.on('before-input-event', (event, input) => {
            let isBlocked = false

            if (input.code === 'F5' || input.code === 'F11' || input.code === 'F12') {
                isBlocked = true
            }

            const ctrlOrCmd = input.control || input.meta
            if (ctrlOrCmd) {
                isBlocked = input.code === 'KeyR' ||
                    input.code === 'KeyW' ||
                    input.code === 'KeyQ' ||
                    input.code === 'KeyM'
            }

            if (isBlocked) {
                event.preventDefault()
            }
        })
    }

    win.once('ready-to-show', () => {
        win.show()
    })

    win.loadFile(path.join(__dirname, 'main.html'))

    if (debug) win.openDevTools()
}

ipcMain.on('quit-app', () => {
    app.quit()
})

app.whenReady().then(createWindow)