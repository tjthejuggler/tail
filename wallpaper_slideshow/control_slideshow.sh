#!/bin/bash

# Control script for the custom wallpaper slideshow

PID_FILE="$HOME/.config/custom_wallpaper_slideshow.pid"

# Check if the PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo "Error: PID file not found at $PID_FILE"
    echo "Is the slideshow running? Start it with ./custom_wallpaper.py"
    exit 1
fi

# Read the PID from the file
PID=$(cat "$PID_FILE")

# Check if the process is running
if ! ps -p "$PID" > /dev/null; then
    echo "Error: Process with PID $PID is not running."
    echo "The PID file may be stale. Remove it with: rm $PID_FILE"
    echo "Then restart the slideshow with: ./custom_wallpaper.py"
    exit 1
fi

# Function to display usage
show_usage() {
    echo "Usage: $0 [command]"
    echo "Commands:"
    echo "  next        - Show next wallpaper"
    echo "  prev        - Show previous wallpaper"
    echo "  pause       - Toggle pause/resume the slideshow"
    echo "  pause_only  - Pause the slideshow (only if running)"
    echo "  unpause     - Resume the slideshow (only if paused)"
    echo "  reload      - Reload the image list"
    echo "  stop        - Stop the slideshow"
    echo "  status      - Check if the slideshow is running"
}

# Process command line arguments
if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

# Function to check if slideshow is paused
is_paused() {
    # Check if the process is in T (stopped) state
    state=$(ps -o state= -p "$PID")
    if [ "$state" = "T" ]; then
        return 0  # True, is paused
    else
        return 1  # False, not paused
    fi
}

case "$1" in
    next)
        echo "Showing next wallpaper..."
        kill -USR1 "$PID"
        ;;
    prev)
        echo "Showing previous wallpaper..."
        kill -USR2 "$PID"
        ;;
    pause)
        echo "Toggling pause/resume..."
        kill -TSTP "$PID"
        ;;
    pause_only)
        if is_paused; then
            echo "Slideshow is already paused."
        else
            echo "Pausing slideshow..."
            kill -TSTP "$PID"
        fi
        ;;
    unpause)
        if is_paused; then
            echo "Resuming slideshow..."
            kill -TSTP "$PID"
        else
            echo "Slideshow is already running."
        fi
        ;;
    reload)
        echo "Reloading image list..."
        kill -HUP "$PID"
        ;;
    stop)
        echo "Stopping slideshow..."
        kill -TERM "$PID"
        ;;
    status)
        if is_paused; then
            echo "Slideshow is paused with PID $PID"
        else
            echo "Slideshow is running with PID $PID"
        fi
        ;;
    *)
        echo "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac

exit 0