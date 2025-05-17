#!/bin/bash
# Script to run the wallpaper tray application

# Change to the directory containing this script
cd "$(dirname "$0")"

# Make sure the wallpaper_tray.py is executable
chmod +x wallpaper_tray.py

# Run the wallpaper tray application
./wallpaper_tray.py "$@"