---
title: TarangFX
emoji: 🎵
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

<div align="center">

# 🎵 TarangFX v2.0.0-beta

### The Modern Audio Mastering Bot

*Professional-grade audio processing pipeline built on Telethon & Spotify's Pedalboard.*

[![License](https://img.shields.io/badge/license-AGPL%20v3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/agpl-3.0)
[![Version](https://img.shields.io/badge/version-v2.0.0--beta-orange?style=for-the-badge)](https://github.com/PN-Projects/TarangFX/releases)
[![Tech](https://img.shields.io/badge/Powered%20By-Pedalboard-green?style=for-the-badge)](https://github.com/spotify/pedalboard)
[![Telegram](https://img.shields.io/badge/Try%20Now-@TarangFXbot-2CA5E0?style=for-the-badge&logo=telegram)](https://t.me/TarangFXbot)

[Features](#-key-features) • [Installation](#-complete-installation-guide) • [Configuration](#-configuration-env) • [Deploy](#-deployment)

</div>

---

## 🚀 About v2.0.0-beta

TarangFX v2 is a complete rewrite focusing on **speed**, **quality**, and **stackable effects**. Unlike the previous version, v2 allows you to chain multiple operations (e.g., "Convert to FLAC" + "Bass Boost" + "Reverb") into a single processing session.

**Key Upgrades in v2:**
*   **Engine**: Switched from pure FFmpeg to **Spotify's Pedalboard** for studio-quality effects (VST-like processing).
*   **Core**: Migrated from Pyrogram to **Telethon** for better async handling and session management.
*   **Workflow**: New "Session" system. Configure everything first, then process once.
*   **Performance**: Redis caching for rate limits and session state.

---

## ✨ Key Features

### 🎧 Audio Processing
*   **Format Conversion**:
    *   **Free**: MP3, AAC, OGG, OPUS
    *   **Premium**: FLAC, WAV, AIFF, ALAC (Lossless)
*   **Bitrate Control**: 128kbps, 192kbps, 256kbps, 320kbps, and **Original** (Pass-through).
*   **Sample Rate**:
    *   **Free**: 22.05kHz, 44.1kHz
    *   **Premium**: 48kHz, 96kHz (High-Res)

### 🎛️ Studio Effects (Premium)
Powered by **Pedalboard**, allowing granular control:
*   **Bass Boost**: Frequency-targeted boosting (20Hz - 120Hz).
*   **Vocal Enhancement**: Presets for Male and Female vocals.
*   **Standard FX**: Reverb, Delay, Distortion, Chorus.
*   **Smart Normalization**: Available to all users.

### ⚡ Infrastructure
*   **Async Operations**: Non-blocking downloads and uploads.
*   **Concurrency Control**: Limits active operations per user to prevent server overload.
*   **Privacy**: Temp files are isolated by User ID and auto-deleted after processing.

---

## 🛠️ Complete Installation Guide

There are two primary ways to deploy TarangFX:
1. **Zero-Cost Cloud Deployment (No Credit Card required)** - Perfect for users wanting a 24/7 bot for free using Hugging Face Spaces.
2. **Standard VPS or Local Deployment** - For those who have their own Linux server or Windows PC.

---

### Method 1: Zero-Cost Cloud Deployment (Hugging Face + Neon + Upstash)
This stack provides a robust production environment absolutely free forever.

**Step 1: Get a free PostgreSQL Database (Neon.tech)**
1. Go to [Neon.tech](https://neon.tech) and sign up (no card required).
2. Create a new project and copy the **Connection String** (e.g., `postgres://user:pass@ep-restless...`).
3. This is your `DATABASE_URL`.

**Step 2: Get a free Redis Database (Upstash)**
1. Go to [Upstash](https://upstash.com) and sign up (no card required).
2. Create a Redis database. Scroll down to the **REST API** section.
3. You will need the **UPSTASH_REDIS_REST_URL** and **UPSTASH_REDIS_REST_TOKEN**.

**Step 3: Deploy to Hugging Face Spaces (Compute)**
Hugging Face provides 16GB RAM and 2 vCPUs completely free!

1. Go to [Hugging Face](https://huggingface.co/) and create an account.
2. Go to **Spaces** -> **Create new Space**.
3. Space name: `tarangfx` (or whatever you like).
4. License: `MIT`.
5. Select the **Docker** space SDK.
6. Choose the **Blank** template and create the space.
7. Clone the Space repository to your computer and copy all files from this TarangFX codebase into it. Push it back, OR upload the files manually via the Hugging Face web interface.
8. Go to your Space settings -> **Variables and secrets**.
9. Add all your `.env` variables as **Secrets**:
   - `API_ID`
   - `API_HASH`
   - `BOT_TOKEN`
   - `SUDO_USERS`
   - `DATABASE_URL` (From Step 1)
   - `UPSTASH_REDIS_REST_URL` (From Step 2)
   - `UPSTASH_REDIS_REST_TOKEN` (From Step 2)

**Step 4: Keep it Awake 24/7**
Hugging Face spaces sleep after 48 hours. To keep it awake forever:
1. Go to [cron-job.org](https://cron-job.org) (free).
2. Create a cron job that pings your Hugging Face Space URL (e.g., `https://username-tarangfx.hf.space`) every 60 minutes.

---

### Method 2: Standard VPS or Local Deployment

Follow these steps to set up TarangFX on your local machine or server.

### 1. Prerequisites
Ensure you have the following installed:
*   **Python 3.10+**: [Download Here](https://www.python.org/downloads/)
*   **Git**: [Download Here](https://git-scm.com/downloads)

### 2. Clone the Repository
Open your terminal (Command Prompt/PowerShell on Windows, Terminal on Linux) and run:
```bash
git clone https://github.com/PN-Projects/TarangFX.git
cd TarangFX
```

### 3. Install FFmpeg
FFmpeg is required for audio format conversion.

#### 🪟 Windows
1.  Download the **essential build** from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z).
2.  Extract the `.7z` file (using 7-Zip or WinRAR) to a folder, e.g., `C:\ffmpeg`.
3.  Add FFmpeg to your System PATH:
    *   Search for **"Edit the system environment variables"**.
    *   Click **"Environment Variables"**.
    *   Under "System variables", select **Path** and click **Edit**.
    *   Click **New** and paste the path to the `bin` folder inside your extracted ffmpeg folder (e.g., `C:\ffmpeg\bin`).
    *   Click **OK** on all windows.
4.  Verify by typing `ffmpeg -version` in a **new** command prompt.

#### 🐧 Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
ffmpeg -version
```

### 4. Setup Database (PostgreSQL)
You need a PostgreSQL database to store user data.

#### ☁️ Option A: Free Cloud Database (Neon.tech) - *Recommended*
1.  Go to [Neon.tech](https://neon.tech/) and sign up.
2.  Create a new project.
3.  On the dashboard, copy the **Connection String** (it looks like `postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require`).
4.  Save this for your `.env` file later.

#### 🏠 Option B: Local Setup
*   **Windows**: Download and install [PostgreSQL for Windows](https://www.postgresql.org/download/windows/). During install, set a password for the `postgres` user.
    *   Your URL will be: `postgresql://postgres:YOUR_PASSWORD@localhost:5432/postgres`
*   **Linux**:
    ```bash
    sudo apt install postgresql postgresql-contrib
    sudo -u postgres psql
    # Inside psql shell:
    ALTER USER postgres PASSWORD 'your_password';
    \q
    ```

### 5. Setup Cache (Redis)
Redis is used for handling user sessions and rate limiting.

#### ☁️ Option A: Free Cloud Redis (Redis Labs) - *Recommended*
1.  Go to [Redis.com](https://redis.com/try-free/) and sign up.
2.  Create a free subscription.
3.  Copy the **Public Endpoint** (e.g., `redis-12345.c1.us-east-1-2.ec2.cloud.redislabs.com:12345`).
4.  Copy the **Default User Password**.
5.  Your URL format: `redis://default:PASSWORD@ENDPOINT` (e.g., `redis://default:password123@redis-12345...:12345`).

#### 🏠 Option B: Local Setup
*   **Windows**: Redis is not officially supported on Windows.
    *   *Alternative*: Use [Memurai Developer Edition](https://www.memurai.com/get-memurai) OR run Redis via WSL 2 (Windows Subsystem for Linux).
*   **Linux**:
    ```bash
    sudo apt install redis-server
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
    ```
    *   Your URL: `redis://localhost:6379/0`

---

## ⚙️ Configuration (.env)

Create a file named `.env` in the root folder and fill in the following details.

### How to get the variables?
*   **API_ID & API_HASH**:
    1.  Log in to [my.telegram.org](https://my.telegram.org).
    2.  Go to **API development tools**.
    3.  Create an app (any name works). Copy the `App api_id` and `App api_hash`.
*   **BOT_TOKEN**:
    1.  Open Telegram and chat with [@BotFather](https://t.me/BotFather).
    2.  Send `/newbot`, name your bot, and get the token.
*   **OWNER_ID**:
    1.  Chat with [@userinfobot](https://t.me/userinfobot) on Telegram.
    2.  Copy the `Id`.

### `.env` File Template
```ini
# --- Telegram Defaults ---
API_ID=12345678
API_HASH=abcdef1234567890abcdef
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
OWNER_ID=123456789 (Your Telegram ID)

# --- Database & Cache ---
# neon.tech or local postgres url
DATABASE_URL=postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require

# redis labs or local redis url
REDIS_URL=redis://default:pass@redis-endpoint:port

# --- Limits & Settings ---
TEMP_DIR=./tmp_downloads
MAX_FILE_SIZE_MB=2000
SESSION_TIMEOUT_MINUTES=10
```

---

## ▶️ Running the Bot

### 🪟 Windows
1.  **Create Virtual Environment**:
    ```powershell
    python -m venv venv
    ```
2.  **Activate Environment**:
    ```powershell
    .\venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```powershell
    pip install -r requirements.txt
    ```
4.  **Run**:
    ```powershell
    python bot.py
    ```

### 🐧 Linux / macOS
1.  **Create Virtual Environment**:
    ```bash
    python3 -m venv venv
    ```
2.  **Activate Environment**:
    ```bash
    source venv/bin/activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    # If you face issues with pedalboard, ensure you have build tools installed:
    # sudo apt install build-essential python3-dev
    ```
4.  **Run**:
    ```bash
    python3 bot.py
    ```

---

## � Deployment (Docker)

If you prefer using Docker (easy deployment on VPS):

```yaml
# docker-compose.yml
version: '3.8'
services:
  bot:
    build: .
    restart: always
    env_file: .env
    depends_on:
      - redis
  
  # Only needed if you want local redis. 
  # If using Redis Labs, remove this service and the depends_on block above.
  redis:
    image: redis:alpine
    restart: always
```

**Command to run:**
```bash
docker-compose up -d --build
```

---

## 🤝 Contributing

We welcome contributions!
1. **Fork** the repository.
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`).
3. **Commit** your changes (`git commit -m 'Add amazing feature'`).
4. **Push** to the branch (`git push origin feature/amazing-feature`).
5. **Open** a Pull Request.

---

<div align="center">
Made with ❤️ by <b>PN Projects</b>
</div>
