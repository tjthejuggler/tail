#!/bin/bash
# Script to pause the wallpaper slideshow

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTROL_SCRIPT="$SCRIPT_DIR/../control_slideshow.sh"

# Check if control script exists
if [ ! -f "$CONTROL_SCRIPT" ]; then
    echo "Error: Control script not found at $CONTROL_SCRIPT"
    exit 1
fi

# Pause the slideshow
"$CONTROL_SCRIPT" pause_only