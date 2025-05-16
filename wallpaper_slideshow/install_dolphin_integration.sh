#!/bin/bash
# Wallpaper Slideshow Dolphin Integration Installer
# This script installs the KDE Dolphin service menu integration for the wallpaper slideshow

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Installing Wallpaper Slideshow Dolphin Integration...${NC}"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Make sure the script is executable
echo -e "${BLUE}Making scripts executable...${NC}"
chmod +x open_notes_for_wallpaper.py

# Check if psutil is installed
echo -e "${BLUE}Checking for psutil Python package...${NC}"
if python3 -c "import psutil" &> /dev/null; then
    echo -e "${GREEN}psutil is already installed.${NC}"
else
    echo -e "${RED}psutil is not installed. Installing...${NC}"
    pip install psutil
fi

# Create the service menu directory if it doesn't exist
SERVICE_MENU_DIR="$HOME/.local/share/kservices5/ServiceMenus"
echo -e "${BLUE}Creating service menu directory at $SERVICE_MENU_DIR...${NC}"
mkdir -p "$SERVICE_MENU_DIR"

# Copy and update the service menu file
echo -e "${BLUE}Installing service menu file...${NC}"
cp wallpaper-notes.desktop "$SERVICE_MENU_DIR/"

# Update the Exec path in the service menu file
sed -i "s|SCRIPT_DIR|$SCRIPT_DIR|g" "$SERVICE_MENU_DIR/wallpaper-notes.desktop"

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${BLUE}You can now right-click on image files in Dolphin and select 'Add a note to this wallpaper'${NC}"
echo -e "${BLUE}to open the wallpaper slideshow tray app's notes tab for that image.${NC}"