const { globalShortcut, BrowserWindow } = require('electron');
const path = require('path');
const koffi = require('koffi');
const { getStore } = require('./store');
const { showOverlay, hideOverlay, saveAudioBuffer, cleanupTempAudio } = require('./recorder');
const { transcribeWithWhisper } = require('./api/whisper');
const { transcribeWithGroq } = require('./api/groq');
const { polishText } = require('./api/llm');
const { typeText, copyToClipboard } = require('./typer');

let recorderWindow = null;
let isRecording = false;
let keyPollTimer = null;

// Windows API: GetAsyncKeyState
const user32 = koffi.load('user32.dll');
const GetAsyncKeyState = user32.func('short __stdcall GetAsyncKeyState(int vKey)');

// 虛擬鍵碼映射表
const VK_MAP = {
  'Alt': 0x12,      // VK_MENU
  'Ctrl': 0x11,     // VK_CONTROL
  'Shift': 0x10,    // VK_SHIFT
  'Super': 0x5B,    // VK_LWIN (Windows Key)
  'Space': 0x20,    // VK_SPACE
  'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45, 'F': 0x46, 'G': 0x47,
  'H': 0x48, 'I': 0x49, 'J': 0x4A, 'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E,
  'O': 0x4F, 'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54, 'U': 0x55,
  'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59, 'Z': 0x5A
};

function isKeyDown(vk) {
  return (GetAsyncKeyState(vk) & 0x8000) !== 0;
}

// 解析快捷鍵字串為 Windows 虛擬按鍵碼陣列
function getVKsFromShortcut(shortcutStr) {
  const parts = shortcutStr.split('+');
  const vkeys = [];
  for (const part of parts) {
    const trimmed = part.trim();
    const mapped = VK_MAP[trimmed];
    if (mapped !== undefined) {
      vkeys.push(mapped);
    } else if (trimmed.length === 1) {
      const code = trimmed.toUpperCase().charCodeAt(0);
      if (code >= 65 && code <= 90) {
        vkeys.push(code);
      }
    }
  }
  return vkeys;
}

// 建立隱藏錄音視窗
function createRecorderWindow() {
  if (recorderWindow) return recorderWindow;

  recorderWindow = new BrowserWindow({
    show: false,
    width: 1,
    height: 1,
    webPreferences: {
      preload: path.join(__dirname, 'recorder-preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  recorderWindow.loadFile(path.join(__dirname, 'recorder-page.html'));

  recorderWindow.on('closed', () => {
    recorderWindow = null;
  });

  return recorderWindow;
}

// 註冊全域快捷鍵
function registerShortcut() {
  globalShortcut.unregisterAll();
  
  const store = getStore();
  const shortcut = store.get('shortcut') || 'Alt+Space';

  const success = globalShortcut.register(shortcut, () => {
    if (!isRecording) {
      startRecording(shortcut);
    }
  });

  if (success) {
    console.log(`快捷鍵已註冊：按住 ${shortcut} 錄音，放開停止`);
  } else {
    console.error(`快捷鍵 ${shortcut} 註冊失敗`);
  }

  return success;
}

function startRecording(shortcut) {
  if (isRecording) return;
  isRecording = true;
  showOverlay('recording');

  const win = createRecorderWindow();
  win.webContents.send('start-recording');
  console.log('開始錄音');

  // 解析當前快捷鍵對應的虛擬按鍵碼
  const vkeys = getVKsFromShortcut(shortcut);

  keyPollTimer = setInterval(() => {
    // 檢查是否所有組合鍵都還被按著；只要有任一按鍵被放開，就停止錄音
    const allDown = vkeys.every(vk => isKeyDown(vk));
    if (!allDown) {
      stopRecordingAndProcess();
    }
  }, 80);
}

function stopRecordingAndProcess() {
  if (!isRecording) return;
  isRecording = false;

  if (keyPollTimer) {
    clearInterval(keyPollTimer);
    keyPollTimer = null;
  }

  const win = createRecorderWindow();
  win.webContents.send('stop-recording');
  console.log('停止錄音，開始處理');
}

// 處理音訊資料（接收 mimeType）
async function handleAudioData(audioBuffer, mimeType) {
  const store = getStore();

  try {
    if (!audioBuffer || mimeType === 'silent') {
      console.log('[shortcut] 檢測為無效或靜音錄音，略過後續處理');
      hideOverlay();
      return;
    }

    // 傳入 mimeType，讓 saveAudioBuffer 決定副檔名
    const audioPath = saveAudioBuffer(audioBuffer, mimeType);

    showOverlay('processing');
    const provider = store.get('sttProvider') || 'openai';
    let rawText;

    if (provider === 'groq') {
      rawText = await transcribeWithGroq(audioPath);
    } else {
      rawText = await transcribeWithWhisper(audioPath);
    }

    console.log('STT 結果:', rawText);

    if (!rawText || rawText.trim() === '') {
      showOverlay('done');
      setTimeout(hideOverlay, 1500);
      cleanupTempAudio();
      return;
    }

    showOverlay('polishing');
    const polishedText = await polishText(rawText);
    console.log('潤飾結果:', polishedText);

    const copyOnly = store.get('copyToClipboard');
    if (copyOnly) {
      copyToClipboard(polishedText);
    } else {
      await typeText(polishedText);
    }

    showOverlay('done');
    setTimeout(hideOverlay, 1500);
  } catch (err) {
    console.error('處理錄音失敗:', err);
    showOverlay('error');
    setTimeout(hideOverlay, 3000);
  } finally {
    cleanupTempAudio();
  }
}

function unregisterShortcut() {
  if (keyPollTimer) {
    clearInterval(keyPollTimer);
    keyPollTimer = null;
  }
  globalShortcut.unregisterAll();
}

module.exports = { registerShortcut, unregisterShortcut, handleAudioData, createRecorderWindow };
