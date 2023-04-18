#!/bin/bash

echo "Script started at $(date)" >> /home/lunkwill/logs/logfile.log

sleep 10

file_to_watch="$HOME/Documents/obsidyen/habitsdb.txt"
python_script="$HOME/projects/tail/habits_kde_theme.py"

while true; do
  inotifywait -e modify,attrib,move,close_write,create,delete,delete_self --timeout 10 "$file_to_watch"
  if [ $? -eq 0 ]; then
    python3 "$python_script"
  fi
done
