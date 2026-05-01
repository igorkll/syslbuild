let debug = false

const { app, BrowserWindow, globalShortcut, ipcMain } = require('electron')
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
        globalShortcut.register('F5', () => {});
        globalShortcut.register('F11', () => {})
        globalShortcut.register('F12', () => {})
        globalShortcut.register('CommandOrControl+R', () => {});
        globalShortcut.register('CommandOrControl+Shift+R', () => {});
        globalShortcut.register('CommandOrControl+W', () => {});
        globalShortcut.register('CommandOrControl+Q', () => {});
    }

    win.once('ready-to-show', () => {
        win.show();
    });

    win.loadFile(path.join(__dirname, 'main.html'))

    if (debug) win.openDevTools()
}

ipcMain.on('quit-app', () => {
    app.quit()
})

app.whenReady().then(createWindow)