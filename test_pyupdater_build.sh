#!/bin/bash
# Test script for PyUpdater builds
# This helps you test the update flow locally before deploying

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "PyUpdater Build Test Script"
echo "========================================="
echo ""

# Check if PyUpdater is configured
if [ ! -d ".pyupdater" ]; then
    echo -e "${RED}Error: .pyupdater directory not found${NC}"
    echo "Run ./setup_pyupdater.sh first"
    exit 1
fi

if [ ! -f ".pyupdater/keypack.pyu" ]; then
    echo -e "${RED}Error: keypack.pyu not found${NC}"
    echo "Run ./setup_pyupdater.sh to generate keys"
    exit 1
fi

# Get current version
VERSION=$(grep -E '^__version__\s*=\s*["\x27]' src/helpers/Constants.py | sed -E 's/.*["\x27]([^"\x27]+)["\x27].*/\1/')
if [ -z "$VERSION" ]; then
    echo -e "${RED}Error: Could not extract version from Constants.py${NC}"
    exit 1
fi

echo -e "${GREEN}Building version: $VERSION${NC}"
echo ""

# Step 1: Build with PyInstaller
echo "Step 1: Building with PyInstaller..."
pyinstaller --noconfirm main.spec

# Check if build succeeded
if [ "$(uname)" == "Darwin" ]; then
    if [ ! -d "dist/YsaGUI.app" ]; then
        echo -e "${RED}Error: PyInstaller build failed - YsaGUI.app not found${NC}"
        exit 1
    fi
    BUILD_PATH="dist/YsaGUI.app"
else
    if [ ! -d "dist/YsaGUI" ]; then
        echo -e "${RED}Error: PyInstaller build failed - YsaGUI not found${NC}"
        exit 1
    fi
    BUILD_PATH="dist/YsaGUI"
fi

echo -e "${GREEN}PyInstaller build successful!${NC}"
echo ""

# Step 2: Package with PyUpdater
echo "Step 2: Packaging with PyUpdater..."
pyupdater pkg --process "$BUILD_PATH" --app-version "$VERSION"

echo -e "${GREEN}Packaging successful!${NC}"
echo ""

# Step 3: Sign with PyUpdater
echo "Step 3: Signing package..."
pyupdater pkg --sign

echo -e "${GREEN}Signing successful!${NC}"
echo ""

# Step 4: Show what was created
echo "========================================="
echo "Build Complete!"
echo "========================================="
echo ""
echo "Created files:"
ls -lh pyu-data/deploy/
echo ""

# Step 5: Offer to start local server
echo -e "${YELLOW}To test updates locally:${NC}"
echo ""
echo "1. Start a local server:"
echo -e "   ${GREEN}cd pyu-data/deploy && python -m http.server 8000${NC}"
echo ""
echo "2. Update Updater.py to use local server (temporarily):"
echo -e "   ${GREEN}UPDATE_URLS = [\"http://localhost:8000/\"]${NC}"
echo ""
echo "3. Run the app with an older version number"
echo ""
echo "4. The app should detect the update and offer to install it"
echo ""

read -p "Start local server now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting server on http://localhost:8000"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    cd pyu-data/deploy
    python3 -m http.server 8000
fi
