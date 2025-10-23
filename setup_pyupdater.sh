#!/bin/bash
# PyUpdater Setup Script for YSA GUI
# This script helps set up PyUpdater for the first time

set -e  # Exit on error

echo "========================================="
echo "PyUpdater Setup for YSA GUI"
echo "========================================="
echo ""

# Check if pyupdater is installed
if ! command -v pyupdater &> /dev/null; then
    echo "Error: pyupdater not found. Installing..."
    pip install -r src/helpers/update/requirements.txt
fi

# Check if .pyupdater directory exists
if [ -d ".pyupdater" ]; then
    echo "Warning: .pyupdater directory already exists."
    echo "If you want to start fresh, delete it first: rm -rf .pyupdater"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Generate keys if they don't exist
if [ ! -f ".pyupdater/keypack.pyu" ]; then
    echo "Step 1: Generating signing keys..."
    pyupdater keys -c
    echo "Keys generated!"
    echo ""
else
    echo "Step 1: Keys already exist, skipping..."
    echo ""
fi

# Show public key
echo "Step 2: Your public key:"
echo "----------------------------------------"
pyupdater keys --show
echo "----------------------------------------"
echo ""
echo "Copy the public key above and paste it into:"
echo "  src/helpers/update/Updater.py"
echo "  in the CLIENT_CONFIG['PUBLIC_KEY'] field"
echo ""
read -p "Press Enter when you've updated the code..."
echo ""

# Initialize PyUpdater config
if [ ! -f ".pyupdater/config.pyu" ]; then
    echo "Step 3: Initializing PyUpdater config..."
    echo ""
    echo "Use these values when prompted:"
    echo "  - App name: YsaGUI"
    echo "  - Company name: ParrishLab"
    echo "  - Update URLs: https://github.com/ParrishLab/ysa-gui/releases/download/latest/"
    echo "  - Plugins: (leave blank, press Enter)"
    echo ""
    read -p "Press Enter to continue..."
    pyupdater init
else
    echo "Step 3: Config already exists, skipping..."
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Ensure .pyupdater/ is in .gitignore"
echo "2. Update CI/CD pipeline to use PyUpdater (see PYUPDATER_SETUP.md)"
echo "3. Test locally with: ./test_pyupdater_build.sh"
echo ""
echo "For more details, see PYUPDATER_SETUP.md"
