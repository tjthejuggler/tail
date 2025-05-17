#!/bin/bash

# Custom mode script for upper left mouse button
# This script goes back to the previous image even when slideshow is paused

notify-send "Custom Mode" "Upper Left Button Pressed" -t 2000

# Use the new script that handles going back even when paused
/home/twain/Projects/tail/wallpaper_slideshow/kde_shortcuts/previous_when_paused.sh

# No need to call pause.sh separately as the previous_when_paused.sh
# will maintain the paused state if it was already paused