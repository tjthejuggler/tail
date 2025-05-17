#!/bin/bash
# Script to run the color control panel

# Change to the directory containing this script
cd "$(dirname "$0")"

# Make sure the color_control_panel.py is executable
chmod +x color_control_panel.py

# Run the color control panel
./color_control_panel.py "$@"