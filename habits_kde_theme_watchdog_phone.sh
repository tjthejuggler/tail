#!/bin/bash

echo "Script started at $(date)" >> /home/twain/logs/logfile.log

# Initialize pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

# Activate the desired pyenv environment
source /home/twain/Projects/py_habits_widget/py_habits_widget/bin/activate

file_to_watch="$HOME/noteVault/habitsdb_phone.txt"
python_script="$HOME/Projects/tail/habits_kde_theme.py"
py_widget="$HOME/Projects/py_habits_widget/py_widget.py"
get_habits_daily_totals="$HOME/Projects/py_habits_widget/get_habits_daily_totals.py"
update_habitsdb_from_phone="$HOME/Projects/py_habits_widget/update_habitsdb_from_habitsdb_phone.py"

# Start the initial instance of python_widget
python3 "$py_widget" &

# This just updates the phone's list of daily habits totals in case it gets off
python3 "$get_habits_daily_totals" &

# Watch for file changes
while true; do
    inotifywait -e modify "$file_to_watch"

    # Wait for 7 seconds to make sure the file is written
    sleep 7

    # Kill the previous instance of python_widget
    pkill -f "py_widget.py"
    
    # Run python_script
    python3 "$python_script"
    
    # Run update_habitsdb_from_phone script
    python3 "$update_habitsdb_from_phone"
    
    # Start python_widget again
    python3 "$py_widget" &

    # This just updates the phone's list of daily habits totals in case it gets off
    python3 "$get_habits_daily_totals" &
done