#!/bin/bash

# Script to show the previous wallpaper even when slideshow is paused
# This script will temporarily unpause, go to previous image, then pause again

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Path to the PID file
PID_FILE="$HOME/.config/custom_wallpaper_slideshow.pid"

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

# Function to check if slideshow is paused
is_paused() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        # Check if the process is in T (stopped) state
        state=$(ps -o state= -p "$PID")
        if [ "$state" = "T" ]; then
            return 0  # True, is paused
        fi
    fi
    return 1  # False, not paused
}

# Function to show previous wallpaper
show_previous_wallpaper() {
    echo "Showing previous wallpaper..."
    "$PARENT_DIR/control_slideshow.sh" prev
    # Show notification
    notify-send "Wallpaper Slideshow" "Previous wallpaper" --icon=preferences-desktop-wallpaper
}

# Main logic
if is_slideshow_running; then
    was_paused=false
    
    # Check if slideshow is paused
    if is_paused; then
        was_paused=true
        # Temporarily unpause
        kill -CONT $(cat "$PID_FILE")
        sleep 0.2  # Small delay to ensure the process is ready
    fi
    
    # Show previous wallpaper
    show_previous_wallpaper
    
    # If it was paused, pause it again
    if [ "$was_paused" = true ]; then
        sleep 0.2  # Small delay to ensure the signal was processed
        kill -STOP $(cat "$PID_FILE")
    fi
else
    # Start slideshow if not running
    echo "Starting wallpaper slideshow..."
    "$PARENT_DIR/custom_wallpaper.py" &
    sleep 2  # Wait for slideshow to start
    
    # Then show previous wallpaper
    if is_slideshow_running; then
        show_previous_wallpaper
    fi
fi

exit 0