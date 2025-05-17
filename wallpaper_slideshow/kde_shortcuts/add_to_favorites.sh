#!/bin/bash

# Get the current wallpaper path from the tracking file
CURRENT_WALLPAPER_FILE=~/Projects/tail/current-wallpaper

if [ -f "$CURRENT_WALLPAPER_FILE" ]; then
    CURRENT_WALLPAPER=$(cat "$CURRENT_WALLPAPER_FILE")
    
    if [ -f "$CURRENT_WALLPAPER" ]; then
        # Load the config file to get the favorites list
        CONFIG_FILE=~/Projects/tail/wallpaper_color_manager_new/config.json
        
        # Check if the wallpaper is already in favorites
        if grep -q "\"favorites\".*\"$CURRENT_WALLPAPER\"" "$CONFIG_FILE"; then
            echo "Wallpaper is already in favorites."
            notify-send "Wallpaper Favorites" "This wallpaper is already in your favorites."
            exit 0
        fi
        
        # Add the wallpaper to favorites
        # We'll use Python to properly update the JSON file
        python3 -c "
import json
import os

config_file = '$CONFIG_FILE'
wallpaper = '$CURRENT_WALLPAPER'

# Load the config
with open(config_file, 'r') as f:
    config = json.load(f)

# Initialize favorites list if it doesn't exist
if 'favorites' not in config:
    config['favorites'] = []

# Add the wallpaper to favorites if not already there
if wallpaper not in config['favorites']:
    config['favorites'].append(wallpaper)
    
    # Save the updated config
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f'Added {os.path.basename(wallpaper)} to favorites.')
else:
    print('Wallpaper is already in favorites.')
"
        
        # Show a notification
        notify-send "Wallpaper Favorites" "Current wallpaper added to favorites."
    else
        echo "Current wallpaper file not found: $CURRENT_WALLPAPER"
        notify-send "Wallpaper Favorites" "Error: Current wallpaper file not found."
    fi
else
    echo "Current wallpaper tracking file not found: $CURRENT_WALLPAPER_FILE"
    notify-send "Wallpaper Favorites" "Error: Current wallpaper tracking file not found."
fi