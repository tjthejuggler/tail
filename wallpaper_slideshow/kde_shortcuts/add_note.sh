#!/bin/bash

# Script to add a note to the current wallpaper
# Designed to be bound to a KDE mouse shortcut

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Path to the PID file and scripts
PID_FILE="$HOME/.config/custom_wallpaper_slideshow.pid"
CUSTOM_WALLPAPER_SCRIPT="$PARENT_DIR/custom_wallpaper.py"
TRAY_APP_SCRIPT="$PARENT_DIR/wallpaper_tray.py"
TRACK_CURRENT_WALLPAPER="$PARENT_DIR/track_current_wallpaper.py"
NOTES_DIR="$HOME/.wallpaper_notes"

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

# Function to check if tray app is running
is_tray_app_running() {
    if pgrep -f "python3.*wallpaper_tray.py" > /dev/null; then
        return 0  # Running
    fi
    return 1  # Not running
}

# Function to start the slideshow
start_slideshow() {
    echo "Starting wallpaper slideshow..."
    "$CUSTOM_WALLPAPER_SCRIPT" &
    sleep 2  # Wait for slideshow to start
}

# Function to start the tray app
start_tray_app() {
    echo "Starting wallpaper tray app..."
    "$TRAY_APP_SCRIPT" &
    sleep 2  # Wait for tray app to start
}

# Function to get current wallpaper and open notes
open_notes_for_current_wallpaper() {
    # Get the current wallpaper path from the tracking file
    if [ -f "$HOME/.current_wallpaper" ]; then
        WALLPAPER_PATH=$(cat "$HOME/.current_wallpaper")
        
        if [ -z "$WALLPAPER_PATH" ]; then
            echo "Error: Current wallpaper file is empty"
            notify-send "Wallpaper Slideshow" "Error: Current wallpaper file is empty" --icon=dialog-error
            return 1
        fi
        
        if [ ! -f "$WALLPAPER_PATH" ]; then
            echo "Error: Wallpaper file not found: $WALLPAPER_PATH"
            notify-send "Wallpaper Slideshow" "Error: Wallpaper file not found" --icon=dialog-error
            return 1
        fi
    else
        # Fallback to using the Python script if the tracking file doesn't exist
        echo "Current wallpaper tracking file not found, using Python script as fallback"
        WALLPAPER_PATH=$(python3 "$TRACK_CURRENT_WALLPAPER")
        
        if [ -z "$WALLPAPER_PATH" ] || [ ! -f "$WALLPAPER_PATH" ]; then
            echo "Error: Could not determine current wallpaper"
            notify-send "Wallpaper Slideshow" "Error: Could not determine current wallpaper" --icon=dialog-error
            return 1
        fi
    fi
    
    echo "Current wallpaper: $WALLPAPER_PATH"
    
    # Create notes directory if it doesn't exist
    mkdir -p "$NOTES_DIR"
    
    # Write wallpaper path to temporary file for the tray app to read
    mkdir -p "$NOTES_DIR"
    echo "$WALLPAPER_PATH" > "$NOTES_DIR/open_image.tmp"
    chmod 644 "$NOTES_DIR/open_image.tmp"
    
    # Create a temporary file to store the wallpaper path
    mkdir -p "$NOTES_DIR"
    echo "$WALLPAPER_PATH" > "$NOTES_DIR/open_image.tmp"
    chmod 644 "$NOTES_DIR/open_image.tmp"
    
    # Check if tray app is running
    if is_tray_app_running; then
        echo "Tray app is running, sending signal to open notes"
        
        # Send SIGUSR1 signal to the tray app to open notes
        pkill -USR1 -f "python3.*wallpaper_tray.py"
        
        # Wait a moment to see if the tray app responds
        sleep 1
        
        # Check if the tray app is still running
        if ! is_tray_app_running; then
            echo "Tray app crashed after sending signal, restarting it"
            python3 "$TRAY_APP_SCRIPT" --open-notes "$WALLPAPER_PATH" &
            sleep 1
        fi
    else
        # Start the tray app with the --open-notes flag and the wallpaper path
        echo "Tray app not running, starting it with --open-notes flag"
        python3 "$TRAY_APP_SCRIPT" --open-notes "$WALLPAPER_PATH" &
        sleep 1
    fi
    
    # Verify the tray app is running
    if ! is_tray_app_running; then
        echo "Failed to start tray app, showing notification"
        notify-send "Wallpaper Slideshow" "Failed to start tray app for notes" --icon=dialog-error
        return 1
    fi
    
    # Show notification
    notify-send "Wallpaper Slideshow" "Opening notes for current wallpaper" --icon=preferences-desktop-wallpaper
    
    return 0
}

# Main logic
# First, ensure slideshow is running
if ! is_slideshow_running; then
    start_slideshow
fi

# Then, ensure tray app is running
if ! is_tray_app_running; then
    start_tray_app
fi

# Finally, open notes for current wallpaper
open_notes_for_current_wallpaper

exit 0