#!/bin/bash
# Wallpaper Slideshow System Tray Application Uninstaller (New Version)
# This script removes the new tabbed wallpaper tray application and its autostart entry

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Uninstalling Wallpaper Slideshow Manager (Tabbed Interface)...${NC}"

# Stop the tray application if it's running
echo -e "${BLUE}Stopping tray application...${NC}"
pkill -f wallpaper_tray_new.py

# Remove desktop files
echo -e "${BLUE}Removing desktop files...${NC}"
rm -f ~/.local/share/applications/wallpaper-tray-new.desktop
rm -f ~/.config/autostart/wallpaper-tray-new.desktop

# Ask if the user wants to remove notes
echo -e "${BLUE}Do you want to remove all wallpaper notes? (y/n)${NC}"
read -r remove_notes
if [[ $remove_notes =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Removing wallpaper notes...${NC}"
    rm -rf ~/.wallpaper_notes
    echo -e "${GREEN}Wallpaper notes removed.${NC}"
else
    echo -e "${BLUE}Keeping wallpaper notes.${NC}"
    echo -e "${BLUE}Notes are stored in ~/.wallpaper_notes${NC}"
fi

# Ask if the user wants to stop the slideshow
echo -e "${BLUE}Do you want to stop the wallpaper slideshow? (y/n)${NC}"
read -r stop_slideshow
if [[ $stop_slideshow =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Stopping wallpaper slideshow...${NC}"
    
    # Get the script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"
    
    # Stop the slideshow
    ./control_slideshow.sh stop
    
    echo -e "${GREEN}Wallpaper slideshow stopped.${NC}"
else
    echo -e "${BLUE}Keeping wallpaper slideshow running.${NC}"
    echo -e "${BLUE}You can stop it later with: ./control_slideshow.sh stop${NC}"
fi

# Ask if the user wants to restore the old tray application
echo -e "${BLUE}Do you want to restore the old tray application? (y/n)${NC}"
read -r restore_old
if [[ $restore_old =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Restoring old tray application...${NC}"
    
    # Get the script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"
    
    # Install old desktop files
    cp wallpaper-tray.desktop ~/.local/share/applications/
    cp wallpaper-tray.desktop ~/.config/autostart/
    
    # Start the old tray application
    python3 wallpaper_tray.py &
    
    echo -e "${GREEN}Old tray application restored.${NC}"
else
    echo -e "${BLUE}Not restoring old tray application.${NC}"
fi

echo -e "${GREEN}Uninstallation complete!${NC}"
echo -e "${BLUE}The Wallpaper Slideshow Manager has been removed.${NC}"