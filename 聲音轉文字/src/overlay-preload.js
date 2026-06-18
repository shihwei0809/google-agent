const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronOverlay', {
  onStatusUpdate: (callback) => {
    ipcRenderer.on('update-status', (_event, status) => callback(status));
  },
  onVolumeUpdate: (callback) => {
    ipcRenderer.on('update-volume', (_event, volume) => callback(volume));
  },
});
