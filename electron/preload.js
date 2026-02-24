const { contextBridge, ipcRenderer, desktopCapturer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  isElectron: true,
  
  getServerUrl: () => ipcRenderer.invoke('get-server-url'),
  
  getSettings: () => ipcRenderer.invoke('get-settings'),
  
  setSetting: (key, value) => ipcRenderer.invoke('set-setting', key, value),
  
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  
  maximizeWindow: () => ipcRenderer.invoke('maximize-window'),
  
  closeWindow: () => ipcRenderer.invoke('close-window'),
  
  isMaximized: () => ipcRenderer.invoke('is-maximized'),
  
  // Overlay controls
  toggleOverlay: () => ipcRenderer.invoke('toggle-overlay'),
  showOverlay: () => ipcRenderer.invoke('show-overlay'),
  hideOverlay: () => ipcRenderer.invoke('hide-overlay'),
  setOverlayOpacity: (opacity) => ipcRenderer.invoke('set-overlay-opacity', opacity),
  setOverlayAlwaysOnTop: (alwaysOnTop) => ipcRenderer.invoke('set-overlay-always-on-top', alwaysOnTop),
  toggleStealthMode: () => ipcRenderer.invoke('toggle-stealth-mode'),
  getStealthMode: () => ipcRenderer.invoke('get-stealth-mode'),
  moveOverlay: (x, y) => ipcRenderer.invoke('move-overlay', x, y),
  getOverlayPosition: () => ipcRenderer.invoke('get-overlay-position'),
  
  // Screenshot functionality
  captureScreen: () => ipcRenderer.invoke('capture-screen'),
  captureRegion: (bounds) => ipcRenderer.invoke('capture-region', bounds),
  getScreenSources: () => ipcRenderer.invoke('get-screen-sources'),
  
  // Audio/Microphone functionality
  startAudioCapture: () => ipcRenderer.invoke('start-audio-capture'),
  stopAudioCapture: () => ipcRenderer.invoke('stop-audio-capture'),
  getMicrophoneSources: () => ipcRenderer.invoke('get-microphone-sources'),
  
  onServerReady: (callback) => {
    ipcRenderer.on('server-ready', (event, ready) => callback(ready));
  },
  
  onNavigate: (callback) => {
    ipcRenderer.on('navigate', (event, path) => callback(path));
  },
  
  onAudioTranscription: (callback) => {
    ipcRenderer.on('audio-transcription', (event, text) => callback(text));
  },
  
  // Keyboard Shortcuts (Pluely, Cheating Daddy, Cluely style)
  onShortcut: (callback) => {
    ipcRenderer.on('shortcut', (event, action) => callback(action));
  },
  
  onScreenshotCaptured: (callback) => {
    ipcRenderer.on('screenshot-captured', (event, dataUrl) => callback(dataUrl));
  }
});
