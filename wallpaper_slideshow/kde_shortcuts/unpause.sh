#!/bin/bash

# Get the PID of the slideshow process
PID_FILE=~/.config/custom_wallpaper_slideshow.pid

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    
    # Check if the process exists
    if ps -p $PID > /dev/null; then
        # Send SIGCONT signal to resume the slideshow
        kill -CONT $PID
        echo "Slideshow resumed."
    else
        echo "Slideshow process not running."
    fi
else
    echo "PID file not found. Slideshow may not be running."
fi