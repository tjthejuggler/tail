#!/bin/bash

# List of files and directories to backup
SOURCE="/home/lunkwill/Documents/obsidian_note_vault/noteVault/tail /home/lunkwill/Documents/obsidian_note_vault/noteVault/backups /home/lunkwill/Documents/obsidian_note_vault/noteVault/habitsdb_auto_backup"

# Local temporary directory for the archive
TEMP_DIR="/home/lunkwill/Documents/temp"

# Destination on Google Drive
DEST="gdrive:/comp_backups"

# Get the current date
DATE=$(date +"%Y-%m-%d")

# Create the archive with the date in the filename
ARCHIVE_NAME="backup_${DATE}.tar.gz"
tar -czf "${TEMP_DIR}/${ARCHIVE_NAME}" $SOURCE

# Upload the archive to Google Drive
rclone copy "${TEMP_DIR}/${ARCHIVE_NAME}" $DEST --update --verbose --transfers 30 --checkers 8 --contimeout 60s --timeout 300s --retries 3 --low-level-retries 10 --stats 1s

# Remove the local archive
rm "${TEMP_DIR}/${ARCHIVE_NAME}"
