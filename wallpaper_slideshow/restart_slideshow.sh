#!/bin/bash

# Script to restart the wallpaper slideshow with the updated configuration
# This ensures the slideshow uses the directory updated by the color control panel

echo "Restarting wallpaper slideshow and tray icon..."

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Kill the tray icon application if it's running
echo "Stopping tray icon application..."
pkill -f "python3 $SCRIPT_DIR/wallpaper_tray.py" || true

# Stop the current slideshow if it's running
echo "Stopping current slideshow..."
"$SCRIPT_DIR/control_slideshow.sh" stop

# Wait a moment for everything to stop
sleep 2

# Make sure the config.ini is using the target directory
TARGET_DIR="/home/twain/Pictures/llm_baby_monster"
CONFIG_FILE="$SCRIPT_DIR/config.ini"

# Check if the config file exists
if [ -f "$CONFIG_FILE" ]; then
    # Check if the image_directory is already set to the target directory
    if grep -q "image_directory = $TARGET_DIR" "$CONFIG_FILE"; then
        echo "Config already using target directory: $TARGET_DIR"
    else
        # Update the image_directory setting
        sed -i "s|image_directory = .*|image_directory = $TARGET_DIR|" "$CONFIG_FILE"
        echo "Updated config.ini to use target directory: $TARGET_DIR"
    fi
else
    echo "Config file not found: $CONFIG_FILE"
    exit 1
fi

# Start the slideshow
echo "Starting slideshow daemon..."
python3 "$SCRIPT_DIR/custom_wallpaper.py" &

# Wait a moment for the slideshow to start
sleep 2

# Start the tray icon application
echo "Starting tray icon application..."
python3 "$SCRIPT_DIR/wallpaper_tray.py" &

# Wait a moment for the tray icon to start
sleep 2

echo "Slideshow and tray icon restarted successfully!"
echo "The slideshow is now using the directory updated by the color control panel."
echo "Try changing the wallpaper source in the color control panel and see if the slideshow updates."