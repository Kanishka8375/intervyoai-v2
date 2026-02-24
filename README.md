# IntervyoAI 🚀

<p align="center">
  <strong>AI Interview Copilot - 100% Local, 100% Undetectable</strong>
</p>

<p align="center">
  <a href="https://github.com/lovethelove339-ctrl/intervyoAI/stargazers">
    <img src="https://img.shields.io/github/stars/lovethelove339-ctrl/intervyoAI?style=flat" alt="Stars">
  </a>
  <a href="https://github.com/lovethelove339-ctrl/intervyoAI/releases">
    <img src="https://img.shields.io/github/downloads/lovethelove339-ctrl/intervyoAI/total" alt="Downloads">
  </a>
  <a href="https://github.com/lovethelove339-ctrl/intervyoAI/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/lovethelove339-ctrl/intervyoAI" alt="License">
  </a>
  <a href="https://github.com/lovethelove339-ctrl/intervyoAI/issues">
    <img src="https://img.shields.io/github/issues/lovethelove339-ctrl/intervyoAI" alt="Issues">
  </a>
</p>

---

## Features

### 🎯 Interview Modes
- **General** - Standard interview questions
- **Coding Copilot** - Technical coding interviews
- **Phone Interview** - Phone screening interviews  
- **HireVue** - Recorded video interviews

### 🤖 AI Providers
- **OpenAI** (GPT-4, GPT-3.5)
- **Anthropic** (Claude)
- **Google** (Gemini)
- **Groq** (Fast inference)
- **DeepSeek**
- **Ollama** (Local)
- **And more...**

### 🌐 Multi-Language Support
- **42+ languages** with regional accent recognition
- Real-time translation
- Language-specific STT models

### 🔒 Privacy & Security
- **100% Local** - Your data never leaves your device
- **Undetectable** - Works stealthily during interviews
- **No cloud dependency** - Works offline

### 📊 Advanced Features
- **Bias Detection** - Identifies potentially biased interview questions
- **Dual-Layer AI** - Cross-verified answers (GPT + Claude)
- **Job Tracker** - Manage your job applications
- **Resume Builder** - Generate optimized resumes
- **Cover Letter Generator** - AI-powered cover letters
- **ATS Optimization** - Score your resume against job descriptions
- **Progress Tracking** - Week-by-week improvement charts

---

## Installation

### Linux
```bash
# Download .deb package
sudo dpkg -i intervyoai_1.0.0_amd64.deb

# Or use AppImage
chmod +x IntervyoAI-1.0.0.AppImage
./IntervyoAI-1.0.0.AppImage
```

### macOS
```bash
# Download .dmg and install
# Or use ZIP
unzip IntervyoAI-1.0.0-mac.zip
./IntervyoAI.app/Contents/MacOS/IntervyoAI
```

### Windows
```bash
# Download .exe or .msi and install
```

---

## Development

### Prerequisites
- Node.js 18+
- Python 3.8+
- Electron

### Setup
```bash
# Install dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt

# Run in development mode
npm run dev
```

### Build
```bash
# Build for all platforms
npm run build:all

# Build for specific platform
npm run build:linux:deb    # Debian/Ubuntu
npm run build:linux:rpm    # Fedora/RHEL
npm run build:mac:dmg      # macOS
npm run build:win:nsis     # Windows
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/generate` | Generate AI answer |
| `GET /api/interview/modes` | List interview modes |
| `POST /api/session/start` | Start interview session |
| `POST /api/session/pause` | Pause session |
| `POST /api/detect-bias` | Detect question bias |
| `POST /api/verify/answer` | Dual-layer verification |
| `GET /api/jobs` | Job tracker |
| `POST /api/resume/optimize` | ATS optimization |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+O` | Toggle overlay |
| `Ctrl+Shift+V` | Voice input |
| `Ctrl+Shift+S` | Screenshot |
| `Ctrl+Shift+A` | Generate answer |
| `Ctrl+Shift+H` | Stealth mode |

---

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (FastAPI)
- **Desktop**: Electron
- **AI**: OpenAI, Anthropic, Google Gemini, Ollama
- **STT**: Whisper, Web Speech API

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=lovethelove339-ctrl/intervyoAI&type=Date)](https://star-history.com/#lovethelove339-ctrl/intervyoAI&Date)

---

<p align="center">
  Made with ❤️ for interview preparation
</p>
