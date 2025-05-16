#!/bin/bash

# Script to show the next wallpaper in the slideshow
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

# Function to show next wallpaper
show_next_wallpaper() {
    echo "Showing next wallpaper..."
    "$PARENT_DIR/control_slideshow.sh" next
    # Show notification
    notify-send "Wallpaper Slideshow" "Next wallpaper" --icon=preferences-desktop-wallpaper
}

# Main logic
if is_slideshow_running; then
    show_next_wallpaper
else
    # Start slideshow if not running
    start_slideshow
    # Then show next wallpaper
    if is_slideshow_running; then
        show_next_wallpaper
    fi
fi

exit 0