#!/bin/bash

# Script to make all KDE shortcut scripts executable

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Make all scripts executable
chmod +x "$SCRIPT_DIR/previous_slide.sh"
chmod +x "$SCRIPT_DIR/next_slide.sh"
chmod +x "$SCRIPT_DIR/toggle_pause.sh"
chmod +x "$SCRIPT_DIR/add_note.sh"
chmod +x "$SCRIPT_DIR/pause_only.sh"
chmod +x "$SCRIPT_DIR/unpause.sh"
chmod +x "$SCRIPT_DIR/add_to_favorites.sh"

echo "All KDE shortcut scripts are now executable."
echo "You can now bind these scripts to KDE mouse shortcuts:"
echo "  - $SCRIPT_DIR/previous_slide.sh"
echo "  - $SCRIPT_DIR/next_slide.sh"
echo "  - $SCRIPT_DIR/toggle_pause.sh"
echo "  - $SCRIPT_DIR/pause_only.sh"
echo "  - $SCRIPT_DIR/unpause.sh"
echo "  - $SCRIPT_DIR/add_note.sh"
echo "  - $SCRIPT_DIR/add_to_favorites.sh"

exit 0