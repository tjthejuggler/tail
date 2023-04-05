#!/bin/bash

# This script watches clipboard_monitor and restarts it if it is frozen

# To make this script executable, run the following command:
# chmod +x clipboard_monitor_watchdog.sh

# Path to the main script
main_script=/home/lunkwill/projects/tail/clipboard/clipboard_monitor.sh

# Function to get the PID of the main script
get_pid() {
    pgrep -f "$main_script"
}

# Function to get the CPU usage of the main script
get_cpu_usage() {
    local pid=$1
    ps -p "$pid" -o %cpu --no-headers
}

# Function to get the start time of the main script
get_start_time() {
    local pid=$1
    ps -p "$pid" -o lstart= | tr -s ' '
}

# Main loop
while true; do
    pid=$(get_pid)

    if [ -z "$pid" ]; then
        # Start the main script if it's not running
        bash "$main_script" &
    else
        # Get the start time of the main script
        script_start_time=$(get_start_time "$pid")
        script_start_timestamp=$(date -d "$script_start_time" +%s)
        
        # Get the current time
        current_time=$(date +%s)

        # Calculate the elapsed time since the script started
        elapsed_time=$((current_time - script_start_timestamp))

        # Restart the script if it's frozen
        if [ "$(get_cpu_usage "$pid")" == "0.0" ] &&
           sleep 5 &&
           [ "$(get_cpu_usage "$pid")" == "0.0" ] &&
           sleep 5 &&
           [ "$(get_cpu_usage "$pid")" == "0.0" ]; then
            kill "$pid"
            bash "$main_script" &
        # Restart the script if it's been running for more than 30 minutes
        elif [ "$elapsed_time" -gt 1800 ]; then
            kill "$pid"
            bash "$main_script" &
        fi
    fi

    # Sleep for a short period of time before checking again
    sleep 5
done
