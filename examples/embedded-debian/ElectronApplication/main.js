const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow () {
  const win = new BrowserWindow({
    width: 800,
    height: 600
  });

  win.loadFile(path.join(__dirname, 'main.html'));
}

app.whenReady().then(createWindow);