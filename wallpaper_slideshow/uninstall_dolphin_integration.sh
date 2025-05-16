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

# Service menu file locations (check both old and new KDE paths)
OLD_SERVICE_MENU_FILE="$HOME/.local/share/kservices5/ServiceMenus/wallpaper-notes.desktop"
NEW_SERVICE_MENU_FILE="$HOME/.local/share/kio/servicemenus/wallpaper-notes.desktop"

# Remove the service menu file if it exists in either location
removed=false

if [ -f "$OLD_SERVICE_MENU_FILE" ]; then
    echo -e "${BLUE}Removing service menu file from old location...${NC}"
    rm -f "$OLD_SERVICE_MENU_FILE"
    echo -e "${GREEN}Service menu file removed from old location.${NC}"
    removed=true
fi

if [ -f "$NEW_SERVICE_MENU_FILE" ]; then
    echo -e "${BLUE}Removing service menu file from new location...${NC}"
    rm -f "$NEW_SERVICE_MENU_FILE"
    echo -e "${GREEN}Service menu file removed from new location.${NC}"
    removed=true
fi

if [ "$removed" = false ]; then
    echo -e "${BLUE}Service menu file not found in any location, nothing to remove.${NC}"
fi

echo -e "${GREEN}Uninstallation complete!${NC}"
echo -e "${BLUE}The Dolphin right-click menu integration has been removed.${NC}"