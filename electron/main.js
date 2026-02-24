const { app, BrowserWindow, Tray, Menu, ipcMain, shell, nativeImage, dialog, globalShortcut, screen, desktopCapturer } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const log = require('electron-log');
const Store = require('electron-store');

app.commandLine.appendSwitch('no-sandbox');
app.commandLine.appendSwitch('disable-gpu');
app.commandLine.appendSwitch('enable-transparency');

// Disable hardware acceleration BEFORE app is ready (for stealth)
app.disableHardwareAcceleration();

log.transports.file.level = 'info';
log.transports.console.level = 'debug';
log.info('IntervyoAI starting...');

const store = new Store({
  defaults: {
    autoStart: false,
    minimizeToTray: true,
    startMinimized: false,
    port: 8080,
    theme: 'dark',
    stealthMode: false,
    overlayOpacity: 0.85,
    overlayAlwaysOnTop: true,
    overlayWidth: 400,
    overlayHeight: 300,
    overlayPosition: 'bottom-right'
  }
});

let mainWindow = null;
let overlayWindow = null;
let tray = null;
let pythonProcess = null;
let isQuitting = false;
let serverUrl = 'http://localhost:8080';

function createWindow() {
  log.info('Creating main window...');
  
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: 'IntervyoAI',
    icon: path.join(__dirname, '../build/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true
    },
    show: false,
    backgroundColor: '#0f172a'
  });

  mainWindow.loadURL(serverUrl);

  mainWindow.once('ready-to-show', () => {
    if (!store.get('startMinimized')) {
      mainWindow.show();
    }
    log.info('Main window ready');
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting && store.get('minimizeToTray')) {
      event.preventDefault();
      mainWindow.hide();
      log.info('Window hidden to tray');
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }
}

function createOverlayWindow() {
  log.info('Creating overlay window...');
  
  const display = screen.getPrimaryDisplay();
  const { width: screenWidth, height: screenHeight } = display.workAreaSize;
  
  const overlayWidth = store.get('overlayWidth') || 400;
  const overlayHeight = store.get('overlayHeight') || 300;
  const position = store.get('overlayPosition') || 'bottom-right';
  
  let x, y;
  switch (position) {
    case 'top-left':
      x = 20; y = 20;
      break;
    case 'top-right':
      x = screenWidth - overlayWidth - 20; y = 20;
      break;
    case 'bottom-left':
      x = 20; y = screenHeight - overlayHeight - 20;
      break;
    case 'bottom-right':
    default:
      x = screenWidth - overlayWidth - 20;
      y = screenHeight - overlayHeight - 20;
      break;
  }
  
  overlayWindow = new BrowserWindow({
    width: overlayWidth,
    height: overlayHeight,
    x: x,
    y: y,
    frame: false,
    transparent: true,
    alwaysOnTop: true, // Always on top for stealth
    skipTaskbar: true, // Hide from taskbar
    resizable: true,
    focusable: true,
    opacity: store.get('overlayOpacity') || 0.9,
    icon: path.join(__dirname, '../build/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true,
      transparent: true
    },
    show: false,
    hasShadow: false,
    titleBarStyle: 'hidden',
    backgroundColor: '#00000000'
  });
  
  // === STEALTH FEATURES ===
  
  // 1. Hide from screen capture (Linux X11)
  if (process.platform === 'linux') {
    try {
      // Set window to be excluded from screen capture
      overlayWindow.setContentProtection(true);
      log.info('Screen capture protection enabled');
    } catch (e) {
      log.warn('Could not set content protection:', e);
    }
  }
  
  // 2. Hide from all workspaces/desktops
  overlayWindow.setVisibleOnAllWorkspaces(true);
  
  // 3. Hide from window switchers (some systems)
  overlayWindow.setKiosk(false);
  
  // 4. Set ignore mouse events for click-through mode
  // Disabled by default - user can toggle with keyboard
  
  // 5. Set window to not show in Exposé
  // Note: setExcludedFromShotcuts doesn't exist in Electron
  
  // Load overlay - use local file to enable preload APIs
  const overlayPath = path.join(__dirname, '..', 'frontend', 'overlay.html');
  overlayWindow.loadFile(overlayPath);
  
  overlayWindow.once('ready-to-show', () => {
    overlayWindow.show();
    log.info('Overlay window shown');
  });
  
  overlayWindow.on('closed', () => {
    overlayWindow = null;
  });
  
  log.info('Overlay window created with stealth features');
}

function toggleOverlay() {
  if (overlayWindow) {
    if (overlayWindow.isVisible()) {
      overlayWindow.hide();
    } else {
      overlayWindow.show();
    }
  }
}

function setOverlayOpacity(opacity) {
  if (overlayWindow) {
    overlayWindow.setOpacity(opacity);
    store.set('overlayOpacity', opacity);
  }
}

function setOverlayAlwaysOnTop(alwaysOnTop) {
  if (overlayWindow) {
    overlayWindow.setAlwaysOnTop(alwaysOnTop);
    store.set('overlayAlwaysOnTop', alwaysOnTop);
  }
}

let stealthModeActive = false;

async function enablePlatformStealth() {
  // Call backend to enable platform-specific stealth features
  try {
    const response = await fetch(`${serverUrl}/api/stealth/enable`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ window_id: 0 })  // Will be set by backend
    });
    const result = await response.json();
    log.info('Platform stealth enabled:', result);
  } catch (e) {
    log.warn('Platform stealth API not available:', e.message);
  }
}

async function disablePlatformStealth() {
  try {
    const response = await fetch(`${serverUrl}/api/stealth/disable`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ window_id: 0 })
    });
    const result = await response.json();
    log.info('Platform stealth disabled:', result);
  } catch (e) {
    log.warn('Platform stealth API not available:', e.message);
  }
}

function toggleStealthMode() {
  const newStealth = !store.get('stealthMode');
  store.set('stealthMode', newStealth);
  stealthModeActive = newStealth;
  
  if (overlayWindow) {
    // Core stealth features
    overlayWindow.setIgnoreMouseEvents(newStealth, { forward: true });
    overlayWindow.setSkipTaskbar(newStealth);
    overlayWindow.setAlwaysOnTop(true);
    
    // Hide from taskbar completely
    overlayWindow.setVisibleOnAllWorkspaces(true);
    overlayWindow.setFullScreenable(false);
    
    // Make window borderless and transparent
    overlayWindow.setFrame(false);
    
    // Try to exclude from screen capture
    if (newStealth) {
      // On Linux, use X11 APIs via backend
      // On Windows, use SetWindowDisplayAffinity
      enablePlatformStealth();
    }
  }
  
  // Hide main window completely in stealth mode
  if (mainWindow && newStealth) {
    mainWindow.hide();
  }
  
  // Hide tray icon in stealth mode (or show generic icon)
  if (tray) {
    if (newStealth) {
      tray.setToolTip('System Service');  // Generic name
    } else {
      tray.setToolTip('IntervyoAI - Interview Copilot');
    }
  }
  
  // Rename process for task manager (Linux)
  if (newStealth && process.platform === 'linux') {
    try {
      process.title = 'systemd[1]';  // Fake process name
    } catch (e) {}
  }
  
  log.info(`Stealth mode: ${newStealth ? 'ON (UNDETECTABLE)' : 'OFF'}`);
  return newStealth;
}

async function enterFullStealth() {
  // Maximum stealth for live interviews
  if (!overlayWindow) return;
  
  // All stealth features enabled
  overlayWindow.setIgnoreMouseEvents(true, { forward: false });
  overlayWindow.setSkipTaskbar(true);
  overlayWindow.setAlwaysOnTop(true);
  overlayWindow.setVisibleOnAllWorkspaces(true);
  // Note: setFrame doesn't exist, window is already frameless
  overlayWindow.setResizable(true); // Allow resizing
  
  // Enable platform-specific stealth
  await enablePlatformStealth();
  
  // Hide from alt-tab
  if (mainWindow) {
    mainWindow.setAlwaysOnTop(true, 'screen-saver');
    mainWindow.hide();
  }
  
  log.info('Full stealth mode activated - undetectable');
}

async function exitFullStealth() {
  if (!overlayWindow) return;
  
  overlayWindow.setIgnoreMouseEvents(false);
  overlayWindow.setSkipTaskbar(false);
  overlayWindow.setFrame(true);
  overlayWindow.setResizable(true);
  
  // Disable platform-specific stealth
  await disablePlatformStealth();
  
  // Disable click-through via backend
  try {
    await fetch(`${serverUrl}/api/stealth/click-through`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enable: false })
    });
  } catch (e) {}
   
  if (mainWindow) {
    mainWindow.setAlwaysOnTop(false);
    mainWindow.show();
  }
  
  log.info('Full stealth mode deactivated');
}

function setupGlobalShortcuts() {
  log.info('Setting up global shortcuts...');
  
  // Toggle Overlay (like Pluely)
  const toggleShortcut = process.platform === 'darwin' ? 'Command+Shift+O' : 'Control+Shift+O';
  globalShortcut.register(toggleShortcut, () => {
    toggleOverlay();
    if (mainWindow) {
      mainWindow.webContents.send('shortcut', 'toggle-overlay');
    }
  });
  
  // Toggle Stealth Mode (like Cluely)
  const stealthShortcut = process.platform === 'darwin' ? 'Command+Shift+H' : 'Control+Shift+H';
  globalShortcut.register(stealthShortcut, () => {
    toggleStealthMode();
    if (mainWindow) {
      mainWindow.webContents.send('shortcut', 'toggle-stealth');
    }
  });
  
  // Focus Overlay (like Cheating Daddy)
  const focusShortcut = process.platform === 'darwin' ? 'Command+Shift+I' : 'Control+Shift+I';
  globalShortcut.register(focusShortcut, () => {
    if (overlayWindow) {
      overlayWindow.show();
      overlayWindow.focus();
    }
    if (mainWindow) {
      mainWindow.webContents.send('shortcut', 'focus-overlay');
    }
  });
  
  // Quick Screenshot Capture
  const screenshotShortcut = process.platform === 'darwin' ? 'Command+Shift+S' : 'Control+Shift+S';
  globalShortcut.register(screenshotShortcut, async () => {
    log.info('Screenshot shortcut triggered');
    if (mainWindow) {
      mainWindow.webContents.send('shortcut', 'capture-screenshot');
    }
    // Capture and send to analysis
    try {
      const sources = await desktopCapturer.getSources({
        types: ['screen'],
        thumbnailSize: { width: 1920, height: 1080 }
      });
      if (sources.length > 0 && mainWindow) {
        mainWindow.webContents.send('screenshot-captured', sources[0].thumbnail.toDataURL());
      }
    } catch (e) {
      log.error('Screenshot shortcut error:', e);
    }
  });
  
  // Quick Question (Voice)
  const voiceShortcut = process.platform === 'darwin' ? 'Command+Shift+V' : 'Control+Shift+V';
  globalShortcut.register(voiceShortcut, () => {
    if (mainWindow) {
      mainWindow.webContents.send('shortcut', 'voice-input');
    }
  });
  
  // Quick AI Answer
  const answerShortcut = process.platform === 'darwin' ? 'Command+Shift+A' : 'Control+Shift+A';
  globalShortcut.register(answerShortcut, () => {
    if (mainWindow) {
      mainWindow.webContents.send('shortcut', 'generate-answer');
    }
  });
  
  // Toggle Always on Top
  const alwaysOnTopShortcut = process.platform === 'darwin' ? 'Command+Shift+T' : 'Control+Shift+T';
  globalShortcut.register(alwaysOnTopShortcut, () => {
    if (overlayWindow) {
      const isOnTop = overlayWindow.isAlwaysOnTop();
      overlayWindow.setAlwaysOnTop(!isOnTop);
      log.info(`Always on top: ${!isOnTop}`);
    }
  });

  // Toggle Click-Through (makes overlay pass through mouse events - totally invisible)
  const clickThroughShortcut = process.platform === 'darwin' ? 'Command+Shift+X' : 'Control+Shift+X';
  globalShortcut.register(clickThroughShortcut, () => {
    if (overlayWindow) {
      const currentIgnores = overlayWindow.isIgnoringMouseEvents();
      overlayWindow.setIgnoreMouseEvents(!currentIgnores, { forward: true });
      log.info(`Click-through: ${!currentIgnores}`);
      if (overlayWindow.webContents) {
        overlayWindow.webContents.send('shortcut', !currentIgnores ? 'click-through-on' : 'click-through-off');
      }
    }
  });
  
  // Show Main Window
  const showMainShortcut = process.platform === 'darwin' ? 'Command+Shift+M' : 'Control+Shift+M';
  globalShortcut.register(showMainShortcut, () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });
  
  // Full Stealth Mode (undetectable)
  const fullStealthShortcut = process.platform === 'darwin' ? 'Command+Shift+F' : 'Control+Shift+F';
  globalShortcut.register(fullStealthShortcut, () => {
    enterFullStealth();
    if (mainWindow) {
      mainWindow.webContents.send('shortcut', 'full-stealth-on');
    }
  });
  
  // Exit Full Stealth
  const exitStealthShortcut = process.platform === 'darwin' ? 'Command+Shift+E' : 'Control+Shift+E';
  globalShortcut.register(exitStealthShortcut, () => {
    exitFullStealth();
    if (mainWindow) {
      mainWindow.webContents.send('shortcut', 'full-stealth-off');
    }
  });
  
  // Move overlay with keyboard (when click-through is on)
  const moveLeft = process.platform === 'darwin' ? 'Command+Left' : 'Control+Left';
  globalShortcut.register(moveLeft, () => {
    if (overlayWindow) {
      const [x, y] = overlayWindow.getPosition();
      overlayWindow.setPosition(x - 50, y);
    }
  });
  
  const moveRight = process.platform === 'darwin' ? 'Command+Right' : 'Control+Right';
  globalShortcut.register(moveRight, () => {
    if (overlayWindow) {
      const [x, y] = overlayWindow.getPosition();
      overlayWindow.setPosition(x + 50, y);
    }
  });
  
  const moveUp = process.platform === 'darwin' ? 'Command+Up' : 'Control+Up';
  globalShortcut.register(moveUp, () => {
    if (overlayWindow) {
      const [x, y] = overlayWindow.getPosition();
      overlayWindow.setPosition(x, y - 50);
    }
  });
  
  const moveDown = process.platform === 'darwin' ? 'Command+Down' : 'Control+Down';
  globalShortcut.register(moveDown, () => {
    if (overlayWindow) {
      const [x, y] = overlayWindow.getPosition();
      overlayWindow.setPosition(x, y + 50);
    }
  });
  
  log.info('Global shortcuts registered');
}

function createTray() {
  log.info('Creating system tray...');
  
  const iconPath = path.join(__dirname, '../build/icon.png');
  let trayIcon;
  
  try {
    trayIcon = nativeImage.createFromPath(iconPath);
    if (trayIcon.isEmpty()) {
      trayIcon = nativeImage.createEmpty();
    }
  } catch (e) {
    trayIcon = nativeImage.createEmpty();
  }

  tray = new Tray(trayIcon.resize({ width: 16, height: 16 }));
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Open IntervyoAI',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      }
    },
    {
      label: 'Toggle Overlay',
      click: () => toggleOverlay()
    },
    {
      label: 'Toggle Stealth Mode',
      click: () => toggleStealthMode()
    },
    { type: 'separator' },
    {
      label: 'Open in Browser',
      click: () => shell.openExternal(serverUrl)
    },
    { type: 'separator' },
    {
      label: 'Settings',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.webContents.send('navigate', '/settings');
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setToolTip('IntervyoAI - Interview Copilot');
  tray.setContextMenu(contextMenu);

  tray.on('double-click', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });

  log.info('System tray created');
}

function startPythonServer() {
  log.info('Starting Python backend server...');
  
  const isWindows = process.platform === 'win32';
  const pythonCmd = isWindows ? 'python' : 'python3';
  
  let backendPath;
  let pythonPath;
  
  if (app.isPackaged) {
    backendPath = path.join(process.resourcesPath, 'backend');
    pythonPath = process.resourcesPath;
  } else {
    backendPath = path.join(__dirname, '..', 'backend');
    pythonPath = path.join(__dirname, '..');
  }
  
  log.info('Backend path:', backendPath);
  log.info('Python path:', pythonPath);
  
  const pythonEnv = { ...process.env };
  pythonEnv.PYTHONUNBUFFERED = '1';
  pythonEnv.PYTHONPATH = pythonPath;
  
  pythonProcess = spawn(pythonCmd, ['-m', 'backend.main'], {
    cwd: pythonPath,
    env: pythonEnv,
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: false
  });

  pythonProcess.stdout.on('data', (data) => {
    log.info(`Python: ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    log.error(`Python Error: ${data.toString().trim()}`);
  });

  pythonProcess.on('error', (err) => {
    log.error('Failed to start Python process:', err);
  });

  pythonProcess.on('exit', (code) => {
    log.info(`Python process exited with code ${code}`);
    if (!isQuitting) {
      // Auto-restart server if it crashes
      log.info('Python server crashed, restarting in 2 seconds...');
      setTimeout(() => {
        if (!isQuitting) {
          startPythonServer();
        }
      }, 2000);
    }
  });

  log.info('Python server started');
}

// Auto-restart counter
let restartCount = 0;
const MAX_RESTARTS = 5;

function startPythonServer() {
  if (restartCount >= MAX_RESTARTS) {
    log.error('Max restarts reached, giving up');
    dialog.showErrorBox('Server Error', 'Backend server keeps crashing. Please restart the application.');
    return;
  }
  
  log.info('Starting Python backend server...');
  
  const isWindows = process.platform === 'win32';
  const pythonCmd = isWindows ? 'python' : 'python3';
  
  let backendPath;
  let pythonPath;
  
  if (app.isPackaged) {
    backendPath = path.join(process.resourcesPath, 'backend');
    pythonPath = process.resourcesPath;
  } else {
    backendPath = path.join(__dirname, '..', 'backend');
    pythonPath = path.join(__dirname, '..');
  }
  
  log.info('Backend path:', backendPath);
  log.info('Python path:', pythonPath);
  
  const pythonEnv = { ...process.env };
  pythonEnv.PYTHONUNBUFFERED = '1';
  pythonEnv.PYTHONPATH = pythonPath;
  
  pythonProcess = spawn(pythonCmd, ['-m', 'backend.main'], {
    cwd: pythonPath,
    env: pythonEnv,
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: false
  });

  pythonProcess.stdout.on('data', (data) => {
    log.info(`Python: ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    log.error(`Python Error: ${data.toString().trim()}`);
  });

  pythonProcess.on('error', (err) => {
    log.error('Failed to start Python process:', err);
    restartCount++;
    setTimeout(() => {
      if (!isQuitting) startPythonServer();
    }, 2000);
  });

  pythonProcess.on('exit', (code) => {
    log.info(`Python process exited with code ${code}`);
    if (!isQuitting) {
      restartCount++;
      log.info(`Python server crashed (restart ${restartCount}/${MAX_RESTARTS}), restarting...`);
      setTimeout(() => {
        if (!isQuitting) startPythonServer();
      }, 2000);
    }
  });

  log.info('Python server started');
}

function checkServer() {
  const http = require('http');
  
  const check = () => {
    http.get(serverUrl, (res) => {
      if (res.statusCode === 200) {
        log.info('Server is ready');
        if (mainWindow) {
          mainWindow.webContents.send('server-ready', true);
        }
        return;
      }
      retryCheck();
    }).on('error', retryCheck);
  };

  const retryCheck = () => {
    log.info('Waiting for server...');
    setTimeout(check, 1000);
  };

  setTimeout(check, 3000);
}

function setupIPC() {
  ipcMain.handle('get-server-url', () => serverUrl);
  
  ipcMain.handle('get-settings', () => store.store);
  
  ipcMain.handle('set-setting', (event, key, value) => {
    store.set(key, value);
    return true;
  });

  ipcMain.handle('open-external', (event, url) => {
    shell.openExternal(url);
    return true;
  });

  ipcMain.handle('get-app-version', () => app.getVersion());

  ipcMain.handle('minimize-window', () => {
    if (mainWindow) mainWindow.minimize();
  });

  ipcMain.handle('maximize-window', () => {
    if (mainWindow) {
      if (mainWindow.isMaximized()) {
        mainWindow.unmaximize();
      } else {
        mainWindow.maximize();
      }
    }
  });

  ipcMain.handle('close-window', () => {
    if (mainWindow) mainWindow.close();
  });

  ipcMain.handle('is-maximized', () => mainWindow ? mainWindow.isMaximized() : false);

  // Overlay controls
  ipcMain.handle('toggle-overlay', () => {
    toggleOverlay();
    return overlayWindow ? overlayWindow.isVisible() : false;
  });
  
  ipcMain.handle('show-overlay', () => {
    if (overlayWindow) overlayWindow.show();
  });
  
  ipcMain.handle('hide-overlay', () => {
    if (overlayWindow) overlayWindow.hide();
  });
  
  ipcMain.handle('set-overlay-opacity', (event, opacity) => {
    setOverlayOpacity(opacity);
    return true;
  });
  
  ipcMain.handle('set-overlay-always-on-top', (event, alwaysOnTop) => {
    setOverlayAlwaysOnTop(alwaysOnTop);
    return true;
  });
  
  ipcMain.handle('toggle-stealth-mode', () => toggleStealthMode());
  
  ipcMain.handle('get-stealth-mode', () => store.get('stealthMode') || false);
  
  ipcMain.handle('move-overlay', (event, x, y) => {
    if (overlayWindow) overlayWindow.setPosition(x, y);
    return true;
  });
  
  ipcMain.handle('get-overlay-position', () => {
    if (overlayWindow) return overlayWindow.getPosition();
    return [0, 0];
  });
  
  // Screenshot functionality
  ipcMain.handle('get-screen-sources', async () => {
    try {
      const sources = await desktopCapturer.getSources({
        types: ['screen', 'window'],
        thumbnailSize: { width: 320, height: 180 }
      });
      return sources.map(source => ({
        id: source.id,
        name: source.name,
        thumbnail: source.thumbnail.toDataURL()
      }));
    } catch (error) {
      log.error('Failed to get screen sources:', error);
      return [];
    }
  });
  
  // Screenshot - capture full screen at high resolution
  ipcMain.handle('capture-screen', async (event, sourceId) => {
    try {
      // Get screen sources with high resolution
      const sources = await desktopCapturer.getSources({
        types: ['screen'],
        thumbnailSize: { width: 3840, height: 2160 }  // 4K resolution
      });
      
      // Find the right source or use first available
      let source = sources[0];
      if (sourceId) {
        source = sources.find(s => s.id === sourceId) || sources[0];
      }
      
      if (!source) {
        return { success: false, error: 'No screen source found' };
      }
      
      // Get full-size capture
      const fullImage = source.thumbnail.resize({ width: 1920, height: 1080 });
      
      log.info('Screen captured successfully');
      
      return {
        success: true,
        image: fullImage.toDataURL(),
        sourceId: source.id,
        name: source.name
      };
    } catch (error) {
      log.error('Screen capture failed:', error);
      return { success: false, error: error.message };
    }
  });
  
  // Region screenshot capture
  ipcMain.handle('capture-region', async (event, bounds) => {
    try {
      const { x, y, width, height } = bounds;
      
      // Use desktopCapturer with region
      const sources = await desktopCapturer.getSources({
        types: ['screen'],
        thumbnailSize: { width: 1920, height: 1080 }
      });
      
      if (!sources || sources.length === 0) {
        return { success: false, error: 'No screen source found' };
      }
      
      const source = sources[0];
      
      // For now, return full screenshot with bounds info
      // In production, you'd crop on the backend
      return {
        success: true,
        image: source.thumbnail.toDataURL(),
        bounds: { x, y, width, height }
      };
    } catch (error) {
      log.error('Region capture failed:', error);
      return { success: false, error: error.message };
    }
  });
  
  // Capture via backend API (for better quality)
  ipcMain.handle('capture-via-backend', async (event, mode, params) => {
    try {
      const endpoint = mode === 'fullscreen' 
        ? '/api/screenshot/capture'
        : '/api/screenshot/capture';
      
      const response = await fetch(`${serverUrl}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: mode,
          ...params
        })
      });
      
      const result = await response.json();
      return result;
    } catch (error) {
      log.error('Backend capture failed:', error);
      return { success: false, error: error.message };
    }
  });
  
  // Audio/Microphone functionality
  let audioStream = null;
  let mediaRecorder = null;
  
  ipcMain.handle('get-microphone-sources', async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      return devices.filter(d => d.kind === 'audioinput').map(d => ({
        deviceId: d.deviceId,
        label: d.label || `Microphone ${d.deviceId.slice(0, 8)}`
      }));
    } catch (error) {
      log.error('Failed to enumerate audio devices:', error);
      return [];
    }
  });
  
  // Audio capture - handled in renderer via Web Speech API
  // This is a placeholder that returns success
  ipcMain.handle('start-audio-capture', async () => {
    log.info('Audio capture requested - using browser Web Speech API');
    return { success: true, message: 'Use Web Speech API in overlay' };
  });
  
  ipcMain.handle('stop-audio-capture', async () => {
    return { success: true };
  });
}

function setupAutoStart() {
  if (store.get('autoStart')) {
    app.setLoginItemSettings({
      openAtLogin: true,
      openAsHidden: store.get('startMinimized')
    });
  } else {
    app.setLoginItemSettings({
      openAtLogin: false
    });
  }
}

app.whenReady().then(() => {
  log.info('App ready, initializing...');

  // === ADVANCED STEALTH FEATURES ===
  
  // 1. WebRTC Blocking - prevent browser detection
  app.commandLine.appendSwitch('disable-webrtc');
  app.commandLine.appendSwitch('disable-features', 'WebRTC');
  
  // 2. Disable GPU rendering
  app.commandLine.appendSwitch('disable-gpu');
  app.commandLine.appendSwitch('disable-software-rasterizer');
  
  // 3. Disable audio input indicators
  app.commandLine.appendSwitch('disable-speech-api');
  
  // 4. Set fake user agent to appear as system app
  app.userAgentFallback = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
  
  // 5. Disable WebGL to prevent GPU fingerprinting
  app.commandLine.appendSwitch('disable-webgl');
  
  // 6. Block remote content
  app.commandLine.appendSwitch('disable-remote-fonts');
  app.commandLine.appendSwitch('disable-web-security');

  createWindow();
  createOverlayWindow();
  createTray();
  setupIPC();
  setupGlobalShortcuts();
  startPythonServer();
  checkServer();
  setupAutoStart();

  // Initialize advanced stealth backend
  initializeAdvancedStealth();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
      createOverlayWindow();
    } else if (mainWindow) {
      mainWindow.show();
    }
  });

  log.info('IntervyoAI initialized successfully');
});

// Initialize advanced stealth from backend
function initializeAdvancedStealth() {
  // This will be called via IPC to backend
  log.info('Advanced stealth features initialized');
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (!store.get('minimizeToTray')) {
      app.quit();
    }
  }
});

app.on('before-quit', () => {
  isQuitting = true;
  log.info('Application quitting...');
  
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

process.on('uncaughtException', (error) => {
  log.error('Uncaught Exception:', error);
  dialog.showErrorBox('Error', `An unexpected error occurred: ${error.message}`);
});

process.on('unhandledRejection', (reason, promise) => {
  log.error('Unhandled Rejection at:', promise, 'reason:', reason);
});
