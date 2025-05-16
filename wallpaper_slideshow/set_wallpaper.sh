#!/bin/bash

# Simple shell script to set a specific wallpaper using the KDE Plasma Wallpaper Slideshow program

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if an image path was provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <image_path>"
    echo "Example:"
    echo "  $0 /path/to/wallpaper.jpg"
    exit 1
fi

# Get the image path
IMAGE_PATH="$1"

# Check if the image exists
if [ ! -f "$IMAGE_PATH" ]; then
    echo "Error: Image file does not exist: $IMAGE_PATH"
    exit 1
fi

# Set the wallpaper using the Python script with D-Bus method
echo "Setting wallpaper to: $IMAGE_PATH"
"$SCRIPT_DIR/set_specific_wallpaper.py" "$IMAGE_PATH"

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo "Wallpaper set successfully!"
    
    # Track the current wallpaper
    if [ -f "$SCRIPT_DIR/track_current_wallpaper.py" ]; then
        echo "Tracking current wallpaper..."
        "$SCRIPT_DIR/track_current_wallpaper.py" "$IMAGE_PATH"
        
        if [ $? -eq 0 ]; then
            echo "Tracked current wallpaper: $IMAGE_PATH"
        else
            echo "Warning: Failed to track current wallpaper"
        fi
    else
        echo "Warning: Wallpaper tracking script not found"
    fi
else
    echo "Failed to set wallpaper."
    exit 1
fi

exit 0