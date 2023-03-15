#!/bin/bash

# this script watches clipboard_monitor and restarts it if it is frozen

# to make this scrpt executable run the following command:
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

# Main loop
while true; do
    pid=$(get_pid)

    if [ -z "$pid" ]; then
        # Start the main script if it's not running
        bash "$main_script" &
    else
        # Check if the main script's CPU usage is 0 for 3 consecutive checks (15 seconds)
        if [ "$(get_cpu_usage "$pid")" == "0.0" ] &&
           sleep 5 &&
           [ "$(get_cpu_usage "$pid")" == "0.0" ] &&
           sleep 5 &&
           [ "$(get_cpu_usage "$pid")" == "0.0" ]; then
            # Kill the frozen main script and restart it
            kill "$pid"
            bash "$main_script" &
        fi
    fi

    # Sleep for a short period of time before checking again
    sleep 5
done
