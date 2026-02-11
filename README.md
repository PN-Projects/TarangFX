
<div align="center">

# 🎵 TarangFX

### Transform Your Audio, Instantly

*A powerful Telegram bot that brings professional audio conversion and mastering to your fingertips*

[![License](https://img.shields.io/badge/license-AGPL%20v3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/agpl-3.0)
[![Telegram](https://img.shields.io/badge/Try%20Now-@TarangFXbot-2CA5E0?style=for-the-badge&logo=telegram)](https://t.me/TarangFXbot)
[![GitHub Stars](https://img.shields.io/github/stars/PN-Projects/TarangFX?style=for-the-badge&logo=github)](https://github.com/PN-Projects/TarangFX)

[Features](#-what-makes-tarangfx-special) • [Quick Start](#-quick-start) • [Deploy](#-deployment-options) • [Documentation](#-how-it-works)

</div>

---

## 🎯 What Makes TarangFX Special?

<table>
<tr>
<td width="50%">

### 🎼 Format Versatility
Convert between **20+ audio formats** including MP3, FLAC, AAC, OPUS, WAV, and more. Whether you need lossy compression or lossless quality, TarangFX handles it seamlessly.

### ⚡ Lightning Fast
Built on asynchronous **Telethon** with **Pedalboard** and **FFmpeg** for industry-standard processing. Experience rapid conversions with professional-grade effects.

</td>
<td width="50%">

### 🎛️ Professional Controls
Fine-tune your audio with precision controls for bitrate (128k–320k), sample rate (up to 96kHz), and apply studio effects like Reverb, Bass Boost, and Vocal Enhancement.

### 🔒 Privacy First
Zero database storage for files. Your files are processed in a temporary workspace and immediately deleted. No logs, no tracking (except essential user stats), no data retention.

</td>
</tr>
</table>

---

## ✨ Feature Showcase

```
📊 Audio Enhancement          🎚️ Precision Controls         🔄 Format Freedom
├─ Bass Boost                 ├─ Bitrate Selection          ├─ Lossy Formats
├─ Reverb & Delay             ├─ Sample Rate Tuning         │  • MP3, AAC, OGG
├─ Vocal Enhancement          ├─ Effect Intensity           │  • OPUS, M4A
├─ Distortion & Chorus        └─ Lossless Support           │
└─ Smart Normalization        💾 File Support               └─ Lossless Formats
                              └─ Up to 2GB per file            • FLAC, WAV, ALAC
                                                               • AIFF, PCM
```

---

## 🚀 Quick Start

### Prerequisites

<table>
<tr>
<td width="33%">

**Python 3.10+**
```bash
python --version
```

</td>
<td width="33%">

**FFmpeg**
```bash
ffmpeg -version
```

</td>
<td width="33%">

**Telegram Bot Token**

Get from [@BotFather](https://t.me/BotFather)

</td>
</tr>
</table>

### Installation Steps

<details>
<summary><b>🐧 Linux / macOS</b></summary>

```bash
# Clone the repository
git clone https://github.com/PN-Projects/TarangFX.git
cd TarangFX

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (if not already installed)
# Ubuntu/Debian:
sudo apt-get update && sudo apt-get install -y ffmpeg
# macOS:
brew install ffmpeg

# Configure environment
cp .env.example .env
nano .env  # Add your credentials

# Launch the bot
python bot.py
```

</details>

<details>
<summary><b>🪟 Windows</b></summary>

```powershell
# Clone the repository
git clone https://github.com/PN-Projects/TarangFX.git
cd TarangFX

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# Download FFmpeg from https://ffmpeg.org/download.html
# Extract and add to PATH

# Configure environment
copy .env.example .env
notepad .env  # Add your credentials

# Launch the bot
python bot.py
```

</details>

---

## ⚙️ Configuration

Create a `.env` file in the root directory:

```env
# Required: Telegram Bot Credentials
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890

# Optional: Force Subscription
FORCE_SUB_CHANNEL=YourChannelUsername
# or use channel ID: FORCE_SUB_CHANNEL=-1001234567890

# Admin
OWNER_ID=123456789
```

<details>
<summary>📖 Where to get these credentials?</summary>

- **BOT_TOKEN**: Message [@BotFather](https://t.me/BotFather) on Telegram
- **API_ID & API_HASH**: Visit [my.telegram.org](https://my.telegram.org/auth)
- **FORCE_SUB_CHANNEL**: Your channel username (without @) or channel ID

</details>

---

## 🐳 Docker Deployment

### Using Docker

```bash
# Build the image
docker build -t tarangfx-bot .

# Run the container
docker run -d \
  --name tarangfx \
  --env-file .env \
  --restart unless-stopped \
  tarangfx-bot
```

### Using Docker Compose

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

---

## ☁️ Deployment Options

Deploy TarangFX to your preferred cloud platform with one click:

<div align="center">

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/PN-Projects/TarangFX)
&nbsp;&nbsp;&nbsp;
[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?type=git&repository=github.com/PN-Projects/TarangFX)

</div>

<details>
<summary><b>🎨 Render Deployment Guide</b></summary>

1. Click the "Deploy to Render" button above
2. Connect your GitHub account if prompted
3. Select **Docker** as the environment
4. Add environment variables from your `.env` file
5. Click "Create Web Service"
6. Wait for deployment to complete (2-3 minutes)

</details>

<details>
<summary><b>🚀 Koyeb Deployment Guide</b></summary>

1. Click the "Deploy to Koyeb" button above
2. Authorize Koyeb to access the repository
3. Choose your preferred region
4. Set environment variables from your `.env` file
5. Select Docker as the builder
6. Click "Deploy"

</details>

---

## 📖 How It Works

### User Flow

```mermaid
graph LR
    A[Send Audio] --> B[Choose Action]
    B --> C[Select Format/Effect]
    C --> D[Add More Operations]
    D --> E[Process]
    E --> F[Receive File]
    
    style A fill:#e1f5ff
    style F fill:#c8e6c9
```

### Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot and display welcome message with process menu |
| `/help` | Access comprehensive help center and feature documentation |
| `/cancel` | Clear current session and reset processing state |
| `/ping` | Check bot latency |

### Processing Pipeline

1. **Upload**: Send any audio file (up to 2GB)
2. **Configure**: Choose output format, bitrate, sample rate
3. **Enhance**: Apply optional effects like bass boost, reverb, vocal enhancement
4. **Convert**: Pipeline processes your audio using Pedalboard and FFmpeg
5. **Download**: Receive your mastered file with smart naming

---

## 🏗️ Project Architecture

```
TarangFX/
│
├── 🤖 Core Components
│   ├── bot.py              # Main bot entry point
│   └── config.py           # Environment configuration
│
├── 🧠 Core Modules
│   ├── core/
│   │   ├── database.py     # SQLite/SQLAlchemy database
│   │   └── cache.py        # Redis/Memory cache
│   └── processors/
│       └── __init__.py     # Audio processing pipeline
│
├── 🎨 User Interface
│   ├── handlers/
│   │   ├── audio.py        # File handling logic
│   │   ├── ui.py           # Keyboard layouts
│   │   └── callbacks.py    # Interaction handling
│   └── models/             # Data models
│
├── 📦 Dependencies
│   ├── requirements.txt    # Python package specifications
│   └── Dockerfile          # Container configuration
│
└── 💾 Runtime
    ├── downloads/          # Temporary processing workspace
    └── logs/               # Application logs
```

---

## 🛠️ Technology Stack

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telethon](https://img.shields.io/badge/Telethon-1.x-blue?style=for-the-badge)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Latest-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)
![Pedalboard](https://img.shields.io/badge/Pedalboard-Audio-orange?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

**Core Libraries**
- `telethon` – Asynchronous Telegram client framework
- `pedalboard` – Spotify's audio effects library
- `ffmpeg-python` – FFmpeg bindings
- `pydub` – Audio manipulation
- `uvloop` – High-performance event loop

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

## 📜 License

This project is licensed under the **GNU Affero General Public License v3.0**

```
TarangFX - Audio Conversion & Mastering Bot
Copyright (C) 2024 PN Projects

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
```

See the [LICENSE](LICENSE) file for full details.

---

## 👨‍💻 Meet the Team

<table>
<tr>
<td align="center">
<a href="https://t.me/dotenv">
<img src="https://t.me/i/userpic/320/dotenv.jpg" width="100px;" alt="Parthiv Katapara"/><br />
<sub><b>Parthiv Katapara</b></sub>
</a><br />
<sub>Core Developer</sub>
</td>

<td align="center">
<a href="https://t.me/PrabodhNandini">
<img src="https://t.me/i/userpic/320/PrabodhNandini.jpg" width="100px;" alt="Avika Trivedi"/><br />
<sub><b>Avika Trivedi</b></sub>
</a><br />
<sub>Core Developer</sub>
</td>

<td align="center">
<a href="https://t.me/shhhwrma">
<img src="https://t.me/i/userpic/320/shhhwrma.jpg" width="100px;" alt="Anand Sharma"/><br />
<sub><b>Anand Sharma</b></sub>
</a><br />
<sub>Core Developer</sub>
</td>
</tr>
</table>


---

## 🌟 Support

If you find TarangFX helpful, consider:

- ⭐ **Starring** this repository
- 🐛 **Reporting** bugs or suggesting features via [Issues](https://github.com/PN-Projects/TarangFX/issues)
- 💬 **Sharing** with others who might benefit
- 📱 **Trying** the bot at [@TarangFXbot](https://t.me/TarangFXbot)

---

<div align="center">

### Made with ❤️ by PN Projects

**[Website](https://github.com/PN-Projects)** • **[Telegram](https://t.me/PnProjects)** • **[Issues](https://github.com/PN-Projects/TarangFX/issues)**

⭐ Star us on GitHub — it helps!

</div>
