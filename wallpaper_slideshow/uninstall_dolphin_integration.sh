#!/bin/bash
# Wallpaper Slideshow Dolphin Integration Uninstaller
# This script removes the KDE Dolphin service menu integration for the wallpaper slideshow

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Uninstalling Wallpaper Slideshow Dolphin Integration...${NC}"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Service menu file location
SERVICE_MENU_FILE="$HOME/.local/share/kservices5/ServiceMenus/wallpaper-notes.desktop"

# Remove the service menu file if it exists
if [ -f "$SERVICE_MENU_FILE" ]; then
    echo -e "${BLUE}Removing service menu file...${NC}"
    rm -f "$SERVICE_MENU_FILE"
    echo -e "${GREEN}Service menu file removed.${NC}"
else
    echo -e "${BLUE}Service menu file not found, nothing to remove.${NC}"
fi

echo -e "${GREEN}Uninstallation complete!${NC}"
echo -e "${BLUE}The Dolphin right-click menu integration has been removed.${NC}"