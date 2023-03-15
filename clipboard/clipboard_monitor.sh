#!/bin/bash

#this script watches my clipboard and saves anything i copy that is more than 1 word to a file with the date as the filename

# Initialize variable to store the current clipboard contents
current_contents=""

while true; do
    # Check the current clipboard contents
    new_contents="$(xclip -selection clipboard -o)"

    # Count the number of words in the clipboard contents
    word_count=$(echo "$new_contents" | wc -w)

    # If the clipboard contents have changed and the word count is greater than 1, append the new contents to the file
    if [ "$new_contents" != "$current_contents" ] && [ $word_count -gt 1 ] && [ $word_count -lt 250 ]; then
        # Read the current status from the status file
        if [ -f ~/clipboard_monitoring_status.txt ]; then
            status=$(cat ~/clipboard_monitoring_status.txt)
        else
            status="off"
        fi

        # If the status is off, exit the script
        if [ "$status" != "off" ]; then
            # Get the current date in the format yyyyMMdd
            current_date=$(date +"%Y%m%d")

            # Set the file path
            file_path=~/Documents/obsidian_note_vault/noteVault/clipboard/comp/$current_date.md

            # Create the file if it doesn't exist
            touch "$file_path"

            # Save the clipboard contents to the file
            echo -e "$new_contents\n" | cat - "$file_path" > temp && mv temp "$file_path"

            current_contents="$new_contents"
        fi

    fi
    # Sleep for a short period of time before checking again
    sleep 0.5
done
