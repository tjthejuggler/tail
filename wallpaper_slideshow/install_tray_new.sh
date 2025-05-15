#!/bin/bash
# Wallpaper Slideshow System Tray Application Installer (New Version)
# This script installs the new tabbed wallpaper tray application and sets it up to autostart with KDE

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Installing Wallpaper Slideshow Manager (Tabbed Interface)...${NC}"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Make sure the scripts are executable
echo -e "${BLUE}Making scripts executable...${NC}"
chmod +x wallpaper_tray_new.py
chmod +x wallpaper_main_window.py
chmod +x control_slideshow.sh
chmod +x custom_wallpaper.py
chmod +x set_specific_wallpaper.py

# Create the tray icon if it doesn't exist
if [ ! -f "wallpaper_tray_icon.png" ]; then
    echo -e "${BLUE}Creating tray icon...${NC}"
    python3 create_tray_icon.py
fi

# Create the notes directory
echo -e "${BLUE}Creating notes directory...${NC}"
mkdir -p ~/.wallpaper_notes

# Install desktop file
echo -e "${BLUE}Installing desktop file...${NC}"
mkdir -p ~/.local/share/applications/
cp wallpaper-tray-new.desktop ~/.local/share/applications/

# Set up autostart
echo -e "${BLUE}Setting up autostart...${NC}"
mkdir -p ~/.config/autostart/
cp wallpaper-tray-new.desktop ~/.config/autostart/

# Check if PyQt5 is installed
echo -e "${BLUE}Checking for PyQt5...${NC}"
if python3 -c "import PyQt5" &> /dev/null; then
    echo -e "${GREEN}PyQt5 is already installed.${NC}"
else
    echo -e "${RED}PyQt5 is not installed. Installing...${NC}"
    pip install PyQt5
fi

# Check if the slideshow is running
echo -e "${BLUE}Checking if slideshow is running...${NC}"
if [ -f ~/.config/custom_wallpaper_slideshow.pid ]; then
    echo -e "${GREEN}Slideshow is already running.${NC}"
else
    echo -e "${BLUE}Starting slideshow...${NC}"
    python3 custom_wallpaper.py &
    sleep 2
fi

# Ask if the user wants to replace the old tray application
echo -e "${BLUE}Do you want to replace the old tray application with this new version? (y/n)${NC}"
read -r replace_old
if [[ $replace_old =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Stopping old tray application...${NC}"
    pkill -f wallpaper_tray.py
    
    echo -e "${BLUE}Removing old desktop files...${NC}"
    rm -f ~/.local/share/applications/wallpaper-tray.desktop
    rm -f ~/.config/autostart/wallpaper-tray.desktop
    
    echo -e "${GREEN}Old tray application removed.${NC}"
else
    echo -e "${BLUE}Keeping old tray application.${NC}"
    echo -e "${BLUE}You can run both versions, but it's recommended to use only one.${NC}"
fi

# Start the new tray application
echo -e "${GREEN}Installation complete!${NC}"
echo -e "${BLUE}Starting new tray application...${NC}"
python3 wallpaper_tray_new.py &

echo -e "${GREEN}Wallpaper Slideshow Manager has been installed and started.${NC}"
echo -e "${BLUE}The application will automatically start when you log in to KDE.${NC}"
echo -e "${BLUE}You can access it from the system tray icon.${NC}"