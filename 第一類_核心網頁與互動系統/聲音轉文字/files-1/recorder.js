const { BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

let overlayWindow = null;

// 建立狀態浮動視窗
function createOverlay() {
  if (overlayWindow) return overlayWindow;

  overlayWindow = new BrowserWindow({
    width: 200,
    height: 60,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    focusable: false,
    webPreferences: {
      preload: path.join(__dirname, 'overlay-preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  overlayWindow.loadFile(path.join(__dirname, 'overlay.html'));
  overlayWindow.setIgnoreMouseEvents(true);

  const { screen } = require('electron');
  const display = screen.getPrimaryDisplay();
  const { width, height } = display.workAreaSize;
  overlayWindow.setPosition(width - 220, height - 80);

  overlayWindow.on('closed', () => {
    overlayWindow = null;
  });

  return overlayWindow;
}

function showOverlay(status) {
  const win = createOverlay();
  win.webContents.send('update-status', status);
  win.show();
}

function hideOverlay() {
  if (overlayWindow) {
    overlayWindow.hide();
  }
}

// 依照 mimeType 決定副檔名
function getExtFromMime(mimeType) {
  if (!mimeType) return '.ogg';
  if (mimeType.includes('ogg')) return '.ogg';
  if (mimeType.includes('mp4')) return '.mp4';
  if (mimeType.includes('webm')) return '.webm';
  return '.ogg';
}

let tempAudioPath = null;
let currentExt = '.ogg';

function getTempAudioPath() {
  return path.join(os.tmpdir(), `notype-recording${currentExt}`);
}

function saveAudioBuffer(buffer, mimeType) {
  currentExt = getExtFromMime(mimeType);
  const filePath = path.join(os.tmpdir(), `notype-recording${currentExt}`);
  fs.writeFileSync(filePath, Buffer.from(buffer));
  console.log('[recorder] 暫存檔:', filePath, '格式:', mimeType);
  return filePath;
}

function cleanupTempAudio() {
  const filePath = getTempAudioPath();
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
  }
}

module.exports = {
  createOverlay,
  showOverlay,
  hideOverlay,
  getTempAudioPath,
  saveAudioBuffer,
  cleanupTempAudio,
};
