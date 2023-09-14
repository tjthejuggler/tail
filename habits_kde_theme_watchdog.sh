#!/bin/bash

echo "Script started at $(date)" >> /home/lunkwill/logs/logfile.log

file_to_watch="$HOME/Documents/obsidyen/habitsdb.txt"
python_script="$HOME/projects/tail/habits_kde_theme.py"
py_widget="$HOME/projects/py_habits_widget/py_widget.py"

# Start the initial instance of python_widget
python3 "$py_widget" &

# Watch for file changes
while true; do
    inotifywait -e modify "$file_to_watch"
    
    # Kill the previous instance of python_widget
    pkill -f "py_widget.py"
    
    # Run python_script
    python3 "$python_script"
    
    # Start python_widget again
    python3 "$py_widget" &
done
