#!/bin/bash

# Script to toggle pause/resume of the wallpaper slideshow
# Designed to be bound to a KDE mouse shortcut

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Path to the PID file
PID_FILE="$HOME/.config/custom_wallpaper_slideshow.pid"
CUSTOM_WALLPAPER_SCRIPT="$PARENT_DIR/custom_wallpaper.py"

# Function to check if slideshow is running
is_slideshow_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null; then
            return 0  # Running
        fi
    fi
    return 1  # Not running
}

# Function to start the slideshow
start_slideshow() {
    echo "Starting wallpaper slideshow..."
    "$CUSTOM_WALLPAPER_SCRIPT" &
    sleep 2  # Wait for slideshow to start
}

# Function to check if slideshow is paused
is_slideshow_paused() {
    # Check if there's a pause indicator file
    if [ -f "$HOME/.config/custom_wallpaper_slideshow.paused" ]; then
        return 0  # Paused
    else
        return 1  # Not paused
    fi
}

# Function to toggle pause/resume
toggle_pause() {
    if is_slideshow_paused; then
        echo "Resuming slideshow..."
        "$PARENT_DIR/control_slideshow.sh" pause
        rm -f "$HOME/.config/custom_wallpaper_slideshow.paused"
        notify-send "Wallpaper Slideshow" "Slideshow resumed" --icon=preferences-desktop-wallpaper
    else
        echo "Pausing slideshow..."
        "$PARENT_DIR/control_slideshow.sh" pause
        touch "$HOME/.config/custom_wallpaper_slideshow.paused"
        notify-send "Wallpaper Slideshow" "Slideshow paused" --icon=preferences-desktop-wallpaper
    fi
}

# Main logic
if is_slideshow_running; then
    toggle_pause
else
    # Start slideshow if not running
    start_slideshow
    # No need to toggle pause immediately after starting
fi

exit 0