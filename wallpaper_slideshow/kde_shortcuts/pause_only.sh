#!/bin/bash
# Script to pause the wallpaper slideshow

# Get the PID of the slideshow process
SLIDESHOW_PID=$(pgrep -f "python.*wallpaper_slideshow/wallpaper_main_window.py")

if [ -n "$SLIDESHOW_PID" ]; then
    # Send the pause signal to the slideshow
    kill -USR1 $SLIDESHOW_PID
    echo "Slideshow paused"
else
    echo "Slideshow process not found"
fi