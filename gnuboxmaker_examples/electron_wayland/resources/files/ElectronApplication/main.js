const { app, BrowserWindow, globalShortcut, ipcMain } = require('electron');
const path = require('path');

function createWindow () {
  const win = new BrowserWindow({
    frame: false,
    fullscreen: true,
    webPreferences: {
      devTools: false, // DON'T FORGET TO TURN OFF THE DAMN DEVTOOLS!
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  globalShortcut.register('F11', () => {});

  win.loadFile(path.join(__dirname, 'main.html'));
}

ipcMain.on('quit-app', () => {
  app.quit();
});

app.whenReady().then(createWindow);