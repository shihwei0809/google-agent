const { app, BrowserWindow, globalShortcut, ipcMain } = require('electron');
const path = require('path');
const { createTray } = require('./tray');
const { getStore } = require('./store');
const { registerShortcut, unregisterShortcut, handleAudioData, createRecorderWindow } = require('./shortcut');

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
}

app.setLoginItemSettings({ openAtLogin: false });

let settingsWindow = null;

function createSettingsWindow() {
  if (settingsWindow) {
    settingsWindow.focus();
    return settingsWindow;
  }

  settingsWindow = new BrowserWindow({
    width: 600,
    height: 520,
    resizable: false,
    title: 'NoType 設定',
    icon: path.join(__dirname, '..', 'assets', 'icon.svg'),
    webPreferences: {
      preload: path.join(__dirname, 'settings', 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  settingsWindow.loadFile(path.join(__dirname, 'settings', 'index.html'));
  settingsWindow.setMenuBarVisibility(false);

  settingsWindow.on('closed', () => {
    settingsWindow = null;
  });

  return settingsWindow;
}

app.whenReady().then(() => {
  const store = getStore();

  ipcMain.handle('get-settings', () => store.store);

  ipcMain.handle('save-settings', (_event, settings) => {
    for (const [key, value] of Object.entries(settings)) {
      store.set(key, value);
    }
    app.setLoginItemSettings({ openAtLogin: settings.launchAtStartup ?? false });
    registerShortcut();
    return true;
  });

  ipcMain.handle('test-api-key', async (_event, provider, apiKey) => {
    try {
      if (provider === 'openai') {
        const res = await fetch('https://api.openai.com/v1/models', {
          headers: { Authorization: `Bearer ${apiKey}` },
        });
        return res.ok;
      } else if (provider === 'groq') {
        const res = await fetch('https://api.groq.com/openai/v1/models', {
          headers: { Authorization: `Bearer ${apiKey}` },
        });
        return res.ok;
      }
      return false;
    } catch {
      return false;
    }
  });

  // ✅ 接收音訊資料，同時接收 mimeType
  ipcMain.on('audio-data', async (_event, audioBuffer, mimeType) => {
    await handleAudioData(audioBuffer, mimeType);
  });

  createTray({
    onSettings: () => createSettingsWindow(),
    onQuit: () => app.quit(),
  });

  createRecorderWindow();
  registerShortcut();
});

app.on('window-all-closed', (e) => {
  e.preventDefault();
});

app.on('will-quit', () => {
  unregisterShortcut();
  globalShortcut.unregisterAll();
});

module.exports = { createSettingsWindow };
