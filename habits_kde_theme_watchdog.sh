#!/bin/bash

echo "Script started at $(date)" >> /home/twain/logs/logfile.log

source /home/twain/miniconda3/etc/profile.d/conda.sh  # Replace with the path to your conda.sh
conda activate base

file_to_watch="$HOME/noteVault/habitsdb.txt"
python_script="$HOME/projects/tail/habits_kde_theme.py"
py_widget="$HOME/projects/py_habits_widget/py_widget.py"
get_habits_daily_totals="$HOME/projects/py_habits_widget/get_habits_daily_totals.py"
wallpaper_manager="$HOME/Projects/tail/wallpaper_color_manager/wallpaper_color_manager.py"  # Add wallpaper manager script
wallpaper_venv="$HOME/Projects/tail/wallpaper_venv/bin/python3"  # Python from virtual environment
# Start the initial instance of python_widget
python3 "$py_widget" &

#this just updates the phones list of daily habits totals in case it gets off
python3 "$get_habits_daily_totals" &

# Run the wallpaper manager initially
"$wallpaper_venv" "$wallpaper_manager" &
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
    
    # Run the wallpaper manager
    "$wallpaper_venv" "$wallpaper_manager" &
done
