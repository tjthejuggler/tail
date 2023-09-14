#!/bin/bash

echo "Script started at $(date)" >> /home/lunkwill/logs/logfile.log

file_to_watch="$HOME/Documents/obsidyen/submitted_dreams.txt"
python_script="$HOME/projects/tail/create_dream_images.py"

# Start the initial instance of python_widget
python3 "$py_widget" &

# Watch for file changes
while true; do
    inotifywait -e modify "$file_to_watch"
    
    # Run python_script
    python3 "$python_script"

done
