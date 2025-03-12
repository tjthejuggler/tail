#!/bin/bash

# Set up logging
logfile="$HOME/logs/watchdog_phone.log"
mkdir -p "$(dirname "$logfile")" # Ensure log directory exists
echo "Script started at $(date)" >> "$logfile"

# Set up heartbeat file to monitor script health
heartbeat_file="/tmp/habits_kde_theme_watchdog_phone_heartbeat"
touch "$heartbeat_file"

# Load pyenv properly
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

# Source virtual environment
source /home/twain/Projects/py_habits_widget/py_habits_widget/bin/activate

# Define script paths
file_to_watch="$HOME/noteVault/habitsdb_phone.txt"
python_script="$HOME/Projects/tail/habits_kde_theme.py"
py_widget="$HOME/Projects/py_habits_widget/py_widget.py"
get_habits_daily_totals="$HOME/Projects/py_habits_widget/get_habits_daily_totals.py"
update_habitsdb_from_phone="$HOME/Projects/py_habits_widget/update_habitsdb_from_habitsdb_phone.py"

# Add script paths
wallpaper_manager="$HOME/Projects/tail/wallpaper_color_manager_new/wallpaper_color_manager.py"
wallpaper_venv="$HOME/Projects/tail/wallpaper_venv/bin/python3"
refresh_wallpaper="$HOME/Projects/tail/refresh_wallpaper.py"

# Function to update the heartbeat file
update_heartbeat() {
    date +%s > "$heartbeat_file"
    echo "Heartbeat updated at $(date)" >> "$logfile"
}

# Function to run the wallpaper manager
run_wallpaper_manager() {
    echo "Running wallpaper manager at $(date)" >> "$logfile"
    "$wallpaper_venv" "$wallpaper_manager" analyze >> "$logfile" 2>&1
    echo "Wallpaper manager completed at $(date)" >> "$logfile"
}

# Function to update the wallpaper folder based on weekly habit average
update_wallpaper_directory() {
    echo "Updating wallpaper directory based on weekly habit average at $(date)" >> "$logfile"
    
    # Use the refresh_wallpaper.py script to update the wallpaper directory and refresh the Plasma shell
    python3 "$refresh_wallpaper" --force-refresh >> "$logfile" 2>&1
    
    echo "Wallpaper directory update completed at $(date)" >> "$logfile"
}

# Start the initial instance of python_widget
python3 "$py_widget" &
echo "Started py_widget.py" >> "$logfile"

# This updates the phone's list of daily habits totals in case it gets off
python3 "$get_habits_daily_totals" &
echo "Ran get_habits_daily_totals.py" >> "$logfile"

# Run the wallpaper manager and update wallpaper directory initially
run_wallpaper_manager
update_wallpaper_directory

# Set up a self-recovery mechanism in a separate process
(
    while true; do
        sleep 300  # Check every 5 minutes
        
        # Check if heartbeat file exists and has been updated in the last 10 minutes
        if [ -f "$heartbeat_file" ]; then
            last_heartbeat=$(cat "$heartbeat_file")
            current_time=$(date +%s)
            time_diff=$((current_time - last_heartbeat))
            
            # If heartbeat is older than 10 minutes (600 seconds), restart the script
            if [ $time_diff -gt 600 ]; then
                echo "WARNING: Watchdog appears stuck (last heartbeat $time_diff seconds ago). Restarting at $(date)" >> "$logfile"
                
                # Kill the current watchdog process and start a new one
                pkill -f "habits_kde_theme_watchdog_phone.sh"
                nohup "$0" > /dev/null 2>&1 &
                
                # Exit this instance
                exit 0
            fi
        fi
    done
) &

# Main loop
while true; do
    # Update heartbeat at the start of each loop
    update_heartbeat
    
    # Wait for file changes
    inotifywait -e modify "$file_to_watch"
    
    echo "File change detected at $(date)" >> "$logfile"
    sleep 7  # Ensure file is fully written
    
    # Update heartbeat after file change detected
    update_heartbeat
    
    # Kill the previous instance of python_widget
    pkill -f "py_widget.py"
    echo "Killed py_widget.py" >> "$logfile"
    
    # Run scripts in the background to avoid blocking
    (python3 "$python_script" >> "$logfile" 2>&1) &
    (python3 "$update_habitsdb_from_phone" >> "$logfile" 2>&1) &
    
    sleep 1  # Give scripts time to start
    
    # Start python_widget again
    python3 "$py_widget" &
    echo "Restarted py_widget.py" >> "$logfile"
    
    # Update daily totals
    python3 "$get_habits_daily_totals" &
    echo "Ran get_habits_daily_totals.py" >> "$logfile"
    
    # Run the wallpaper manager
    run_wallpaper_manager
    
    # Update wallpaper directory based on weekly habit average
    update_wallpaper_directory
    
    # Update heartbeat at the end of each loop
    update_heartbeat
done
        