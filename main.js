const { app, BrowserWindow } = require("electron")
require('electron-reload')(__dirname)

function createWindow() {
    const mainWindow = new BrowserWindow({
        width: 1366,
        height: 720
    })

    mainWindow.webContents.openDevTools()

    mainWindow.setMinimumSize(300, 500)
    mainWindow.setAspectRatio(0.75)
    mainWindow.loadFile('src/ui/index.html')
    mainWindow.removeMenu()
    mainWindow.maximize()

}

app.whenReady().then(() => {
    createWindow()
})