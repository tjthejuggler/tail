#!/bin/bash

# Uninstallation script for the KDE Plasma Wallpaper Slideshow

echo "=== KDE Plasma Wallpaper Slideshow Uninstaller ==="
echo

# Ask for confirmation
echo "This will remove the wallpaper slideshow program and all its components."
echo "Your configuration and log files will also be removed."
echo
echo "Are you sure you want to continue? (y/n)"
read -r confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo

# Stop any running instances
PID_FILE="$HOME/.config/custom_wallpaper_slideshow.pid"
if [ -f "$PID_FILE" ]; then
    echo "Stopping running slideshow instance..."
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null; then
        kill -TERM "$PID"
        echo "Slideshow stopped."
    else
        echo "No running slideshow found, but PID file exists."
    fi
    rm -f "$PID_FILE"
    echo "PID file removed."
else
    echo "No PID file found. Slideshow may not be running."
fi
echo

# Remove desktop entries
APPS_ENTRY="$HOME/.local/share/applications/wallpaper-slideshow.desktop"
AUTOSTART_ENTRY="$HOME/.config/autostart/wallpaper-slideshow.desktop"

if [ -f "$APPS_ENTRY" ]; then
    echo "Removing desktop entry from applications menu..."
    rm -f "$APPS_ENTRY"
    echo "Done."
fi

if [ -f "$AUTOSTART_ENTRY" ]; then
    echo "Removing desktop entry from autostart..."
    rm -f "$AUTOSTART_ENTRY"
    echo "Done."
fi
echo

# Remove symbolic link
BIN_LINK="$HOME/.local/bin/wallpaper-slideshow"
if [ -L "$BIN_LINK" ]; then
    echo "Removing command-line shortcut..."
    rm -f "$BIN_LINK"
    echo "Done."
fi
echo

# Remove configuration directory
CONFIG_DIR="$HOME/.config/wallpaper_slideshow"
if [ -d "$CONFIG_DIR" ]; then
    echo "Removing configuration directory..."
    rm -rf "$CONFIG_DIR"
    echo "Done."
fi
echo

# Remove log file
LOG_FILE="$HOME/.custom_wallpaper.log"
if [ -f "$LOG_FILE" ]; then
    echo "Removing log file..."
    rm -f "$LOG_FILE"
    echo "Done."
fi
echo

echo "=== Uninstallation Complete ==="
echo
echo "The wallpaper slideshow program has been removed from your system."
echo "If you want to completely remove the program files, you can delete"
echo "the wallpaper_slideshow directory manually."
echo