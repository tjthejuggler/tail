#!/bin/bash
# Cleanup script to remove redundant files after consolidation

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Cleaning up redundant files after consolidation...${NC}"

# Remove redundant files
echo -e "${BLUE}Removing wallpaper_tray_new.py...${NC}"
rm -f wallpaper_tray_new.py

echo -e "${BLUE}Removing wallpaper-tray-new.desktop...${NC}"
rm -f wallpaper-tray-new.desktop

echo -e "${BLUE}Removing install_tray_new.sh...${NC}"
rm -f install_tray_new.sh

echo -e "${BLUE}Removing uninstall_tray_new.sh...${NC}"
rm -f uninstall_tray_new.sh

# Make sure the script is executable
chmod +x wallpaper_tray.py

echo -e "${GREEN}Cleanup complete!${NC}"
echo -e "${BLUE}The redundant files have been removed.${NC}"
echo -e "${BLUE}The consolidated wallpaper_tray.py now contains all functionality.${NC}"