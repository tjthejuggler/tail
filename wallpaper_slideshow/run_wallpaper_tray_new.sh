#!/bin/bash
# Script to run the new wallpaper tray application

# Change to the directory containing this script
cd "$(dirname "$0")"

# Make sure the wallpaper_tray_new.py is executable
chmod +x wallpaper_tray_new.py

# Run the new wallpaper tray application
./wallpaper_tray_new.py "$@"