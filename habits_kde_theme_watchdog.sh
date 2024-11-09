#!/bin/bash

echo "Script started at $(date)" >> /home/lunkwill/logs/logfile.log

source /home/lunkwill/miniconda3/etc/profile.d/conda.sh  # Replace with the path to your conda.sh
conda activate base

file_to_watch="$HOME/noteVault/habitsdb.txt"
python_script="$HOME/projects/tail/habits_kde_theme.py"
py_widget="$HOME/projects/py_habits_widget/py_widget.py"
get_habits_daily_totals="$HOME/projects/py_habits_widget/get_habits_daily_totals.py"

# Start the initial instance of python_widget
python3 "$py_widget" &

#this just updates the phones list of daily habits totals in case it gets off
python3 "$get_habits_daily_totals" &

# Watch for file changes
while true; do
    inotifywait -e modify "$file_to_watch"
    
    # Kill the previous instance of python_widget
    pkill -f "py_widget.py"
    
    # Run python_script
    python3 "$python_script"
    
    # Start python_widget again
    python3 "$py_widget" &

    #this just updates the phones list of daily habits totals in case it gets off
    python3 "$get_habits_daily_totals" &
done
