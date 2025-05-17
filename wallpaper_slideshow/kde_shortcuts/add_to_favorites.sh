#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Path to the tracking script
TRACK_CURRENT_WALLPAPER="$PARENT_DIR/track_current_wallpaper.py"

# Get the current wallpaper path from the tracking file
CURRENT_WALLPAPER_FILE="$HOME/.current_wallpaper"

# Function to get current wallpaper
get_current_wallpaper() {
    # First try to read from the tracking file
    if [ -f "$CURRENT_WALLPAPER_FILE" ]; then
        WALLPAPER_PATH=$(cat "$CURRENT_WALLPAPER_FILE")
        
        if [ -z "$WALLPAPER_PATH" ]; then
            echo "Error: Current wallpaper file is empty"
            notify-send "Wallpaper Favorites" "Error: Current wallpaper file is empty" --icon=dialog-error
            return 1
        fi
        
        if [ ! -f "$WALLPAPER_PATH" ]; then
            echo "Error: Wallpaper file not found: $WALLPAPER_PATH"
            notify-send "Wallpaper Favorites" "Error: Wallpaper file not found" --icon=dialog-error
            return 1
        fi
    else
        # Fallback to using the Python script if the tracking file doesn't exist
        echo "Current wallpaper tracking file not found, using Python script as fallback"
        WALLPAPER_PATH=$(python3 "$TRACK_CURRENT_WALLPAPER")
        
        if [ -z "$WALLPAPER_PATH" ] || [ ! -f "$WALLPAPER_PATH" ]; then
            echo "Error: Could not determine current wallpaper"
            notify-send "Wallpaper Favorites" "Error: Could not determine current wallpaper" --icon=dialog-error
            return 1
        fi
    fi
    
    echo "$WALLPAPER_PATH"
    return 0
}

# Get the current wallpaper
CURRENT_WALLPAPER=$(get_current_wallpaper)
RESULT=$?

if [ $RESULT -eq 0 ] && [ -n "$CURRENT_WALLPAPER" ]; then
    # Set the favorites directory and file
    FAVORITES_DIR="$HOME/.wallpaper_favorites"
    FAVORITES_FILE="$FAVORITES_DIR/favorites.json"
    
    # Create favorites directory if it doesn't exist
    mkdir -p "$FAVORITES_DIR"
    
    # Check if the wallpaper is already in favorites
    if [ -f "$FAVORITES_FILE" ] && grep -q "\"favorites\".*\"$CURRENT_WALLPAPER\"" "$FAVORITES_FILE"; then
        echo "Wallpaper is already in favorites."
        notify-send "Wallpaper Favorites" "This wallpaper is already in your favorites."
        exit 0
    fi
    
    # Add the wallpaper to favorites
    # We'll use Python to properly update the JSON file
    python3 -c "
import json
import os

favorites_file = '$FAVORITES_FILE'
wallpaper = '$CURRENT_WALLPAPER'

# Initialize or load favorites data
if os.path.exists(favorites_file) and os.path.getsize(favorites_file) > 0:
    try:
        with open(favorites_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        data = {'favorites': []}
else:
    data = {'favorites': []}

# Add the wallpaper to favorites if not already there
if 'favorites' not in data:
    data['favorites'] = []

if wallpaper not in data['favorites']:
    data['favorites'].append(wallpaper)
    
    # Save the updated favorites
    with open(favorites_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f'Added {os.path.basename(wallpaper)} to favorites.')
else:
    print('Wallpaper is already in favorites.')
"
    
    # Show a notification
    notify-send "Wallpaper Favorites" "Current wallpaper added to favorites."
    
    # Create a refresh trigger file with a timestamp to ensure it's always new
    REFRESH_FILE="$HOME/.wallpaper_favorites/refresh_favorites_$(date +%s)"
    echo "Refresh triggered at $(date)" > "$REFRESH_FILE"
    
    # Try to directly trigger a refresh using qdbus if available
    if command -v qdbus &> /dev/null; then
        # Try to find the wallpaper tray application
        TRAY_SERVICES=$(qdbus | grep -i wallpaper)
        if [ -n "$TRAY_SERVICES" ]; then
            for SERVICE in $TRAY_SERVICES; do
                # Try to call a refresh method if it exists
                qdbus $SERVICE /MainWindow refreshFavorites 2>/dev/null || true
            done
        fi
    fi
    
    # Also try the signal approach as a fallback
    TRAY_PID=$(pgrep -f "python3.*wallpaper_tray.py")
    if [ -n "$TRAY_PID" ]; then
        # Send SIGUSR1 to the tray application
        kill -SIGUSR1 $TRAY_PID
        # Also send SIGUSR2 as an alternative signal
        kill -SIGUSR2 $TRAY_PID 2>/dev/null || true
        echo "Signaled tray application to refresh favorites"
    else
        echo "Tray application not running, favorites will be refreshed on next launch"
    fi
else
    # Error message is already displayed by the get_current_wallpaper function
    exit 1
fi