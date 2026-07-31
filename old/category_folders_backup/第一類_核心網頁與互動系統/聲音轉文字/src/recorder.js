const { BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

let overlayWindow = null;

// 監聽並轉發實時音量數據給懸浮視窗
ipcMain.on('volume-data', (_event, volume) => {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send('update-volume', volume);
  }
});

// 建立狀態浮動視窗
function createOverlay() {
  if (overlayWindow) return overlayWindow;

  const winWidth = 280;
  const winHeight = 50;

  overlayWindow = new BrowserWindow({
    width: winWidth,
    height: winHeight,
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
  
  // 置於螢幕底部正中央，距離底部約 40 像素
  overlayWindow.setPosition(
    Math.round((width - winWidth) / 2),
    Math.round(height - winHeight - 40)
  );

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
