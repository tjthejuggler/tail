#!/bin/bash

file_to_watch="$HOME/Documents/obsidian_note_vault/noteVault/habitCounters/totalHabitCount.txt"
python_script="$HOME/projects/tail/habits_kde_theme.py"

while true; do
  inotifywait -e modify,attrib,move,close_write,create,delete,delete_self "$file_to_watch"
  python3 "$python_script"
done
