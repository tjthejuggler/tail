#!/bin/bash
# Script to restart the wallpaper slideshow

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Stopping slideshow..."
./control_slideshow.sh stop

# Wait for slideshow to stop
sleep 2

# Check if PID file exists and process is still running
PID_FILE=~/.config/custom_wallpaper_slideshow.pid
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null; then
        echo "Killing old process ($OLD_PID)..."
        kill -TERM "$OLD_PID"
        sleep 1
    fi
fi

# Start the slideshow again
echo "Starting slideshow..."
python3 "$SCRIPT_DIR/custom_wallpaper.py" &

# Wait for slideshow to start
sleep 1

# Force a wallpaper change to verify it's working
echo "Forcing wallpaper change..."
./control_slideshow.sh next

echo "Slideshow restarted successfully"