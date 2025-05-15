#!/bin/bash

# Example script demonstrating how to use the wallpaper slideshow program
# This script shows how to control the slideshow from another script

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

# Function to start the slideshow
start_slideshow() {
    echo "Starting wallpaper slideshow..."
    "$PARENT_DIR/custom_wallpaper.py" &
    sleep 2  # Wait for slideshow to start
    echo "Slideshow started."
}

# Function to show next wallpaper
show_next_wallpaper() {
    if is_slideshow_running; then
        PID=$(cat "$PID_FILE")
        echo "Showing next wallpaper..."
        kill -USR1 "$PID"
    else
        echo "Slideshow is not running."
    fi
}

# Function to show previous wallpaper
show_previous_wallpaper() {
    if is_slideshow_running; then
        PID=$(cat "$PID_FILE")
        echo "Showing previous wallpaper..."
        kill -USR2 "$PID"
    else
        echo "Slideshow is not running."
    fi
}

# Function to toggle pause/resume
toggle_pause() {
    if is_slideshow_running; then
        PID=$(cat "$PID_FILE")
        echo "Toggling pause/resume..."
        kill -TSTP "$PID"
    else
        echo "Slideshow is not running."
    fi
}

# Function to reload image list
reload_images() {
    if is_slideshow_running; then
        PID=$(cat "$PID_FILE")
        echo "Reloading image list..."
        kill -HUP "$PID"
    else
        echo "Slideshow is not running."
    fi
}

# Function to stop slideshow
stop_slideshow() {
    if is_slideshow_running; then
        PID=$(cat "$PID_FILE")
        echo "Stopping slideshow..."
        kill -TERM "$PID"
        sleep 1
        if ! is_slideshow_running; then
            echo "Slideshow stopped."
        else
            echo "Failed to stop slideshow."
        fi
    else
        echo "Slideshow is not running."
    fi
}

# Example usage
case "$1" in
    start)
        start_slideshow
        ;;
    next)
        show_next_wallpaper
        ;;
    prev)
        show_previous_wallpaper
        ;;
    pause)
        toggle_pause
        ;;
    reload)
        reload_images
        ;;
    stop)
        stop_slideshow
        ;;
    demo)
        # Run a demo sequence
        echo "Running demo sequence..."
        
        # Start slideshow if not running
        if ! is_slideshow_running; then
            start_slideshow
        fi
        
        # Show a few wallpapers
        sleep 2
        show_next_wallpaper
        sleep 2
        show_next_wallpaper
        sleep 2
        show_previous_wallpaper
        sleep 2
        
        # Toggle pause/resume
        echo "Pausing slideshow..."
        toggle_pause
        sleep 3
        echo "Resuming slideshow..."
        toggle_pause
        sleep 2
        
        # Show one more wallpaper
        show_next_wallpaper
        
        echo "Demo sequence completed."
        ;;
    *)
        echo "Usage: $0 {start|next|prev|pause|reload|stop|demo}"
        echo
        echo "Commands:"
        echo "  start  - Start the wallpaper slideshow"
        echo "  next   - Show next wallpaper"
        echo "  prev   - Show previous wallpaper"
        echo "  pause  - Toggle pause/resume"
        echo "  reload - Reload image list"
        echo "  stop   - Stop the slideshow"
        echo "  demo   - Run a demo sequence"
        exit 1
        ;;
esac

exit 0