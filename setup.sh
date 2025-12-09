#!/bin/bash

# PnProjects Audio Bot Setup Script
# Automated setup for all dependencies

echo "=========================================="
echo "  PnProjects Audio Bot - Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Linux or macOS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
else
    echo -e "${RED}Unsupported OS. This script supports Linux and macOS.${NC}"
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python installation
echo "Checking Python installation..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check pip installation
echo "Checking pip installation..."
if command_exists pip3; then
    echo -e "${GREEN}✓ pip3 found${NC}"
else
    echo -e "${RED}✗ pip3 not found. Installing pip...${NC}"
    python3 -m ensurepip --upgrade
fi

# Check FFmpeg installation
echo ""
echo "Checking FFmpeg installation..."
if command_exists ffmpeg; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
    echo -e "${GREEN}✓ FFmpeg found: $FFMPEG_VERSION${NC}"
else
    echo -e "${YELLOW}✗ FFmpeg not found. Installing FFmpeg...${NC}"

    if [ "$OS" = "linux" ]; then
        if command_exists apt-get; then
            sudo apt-get update
            sudo apt-get install -y ffmpeg libsndfile1
        elif command_exists yum; then
            sudo yum install -y ffmpeg libsndfile
        else
            echo -e "${RED}Package manager not supported. Please install FFmpeg manually.${NC}"
            exit 1
        fi
    elif [ "$OS" = "mac" ]; then
        if command_exists brew; then
            brew install ffmpeg libsndfile
        else
            echo -e "${RED}Homebrew not found. Please install Homebrew first or install FFmpeg manually.${NC}"
            exit 1
        fi
    fi

    if command_exists ffmpeg; then
        echo -e "${GREEN}✓ FFmpeg installed successfully${NC}"
    else
        echo -e "${RED}✗ FFmpeg installation failed. Please install manually.${NC}"
        exit 1
    fi
fi

# Create virtual environment
echo ""
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All Python dependencies installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install some dependencies${NC}"
    exit 1
fi

# Create .env file if not exists
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please edit .env file and add your bot credentials${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

# Create downloads directory
echo ""
echo "Creating downloads directory..."
mkdir -p downloads
echo -e "${GREEN}✓ Downloads directory created${NC}"

# Setup complete
echo ""
echo "=========================================="
echo -e "${GREEN}Setup completed successfully!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your credentials:"
echo "   - BOT_TOKEN (from @BotFather)"
echo "   - API_ID (from https://my.telegram.org/apps)"
echo "   - API_HASH (from https://my.telegram.org/apps)"
echo ""
echo "2. Run the bot:"
echo "   source venv/bin/activate  # Activate virtual environment"
echo "   python bot.py             # Start the bot"
echo ""
echo "Or use Docker:"
echo "   docker build -t pnprojects-audio-bot ."
echo "   docker run -d --env-file .env pnprojects-audio-bot"
echo ""
echo "=========================================="
