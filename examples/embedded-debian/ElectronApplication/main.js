const { app, BrowserWindow, globalShortcut } = require('electron');
const path = require('path');

function createWindow () {
  const win = new BrowserWindow({
    frame: false,
    fullscreen: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  globalShortcut.register('F11', () => {});

  win.loadFile(path.join(__dirname, 'main.html'));
}

app.whenReady().then(createWindow);