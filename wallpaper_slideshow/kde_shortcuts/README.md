# KDE Mouse Shortcuts for Wallpaper Slideshow

This directory contains scripts that can be bound to KDE mouse shortcuts to control the wallpaper slideshow.

## Available Scripts

1. **previous_slide.sh** - Show the previous wallpaper in the slideshow
2. **next_slide.sh** - Show the next wallpaper in the slideshow
3. **toggle_pause.sh** - Pause or resume the slideshow
4. **add_note.sh** - Add a note to the current wallpaper (now with instant tracking for immediate access)

## Setup Instructions

1. First, make all scripts executable by running:
   ```bash
   ./make_executable.sh
   ```

2. To set up KDE mouse shortcuts:
   - Open System Settings
   - Go to Shortcuts > Custom Shortcuts
   - Click "Edit > New > Global Shortcut > Command/URL"
   - Give it a name like "Next Wallpaper"
   - In the "Trigger" tab, click "None" next to "Shortcut" and then press the mouse button combination you want to use (e.g., Meta+Mouse Button 4)
   - In the "Action" tab, enter the full path to the script (e.g., `/home/username/Projects/tail/wallpaper_slideshow/kde_shortcuts/next_slide.sh`)
   - Click "Apply"
   - Repeat for each script

## Script Behavior

- If the slideshow is not running, the scripts will automatically start it before performing their action
- The add_note.sh script will also start the tray application if it's not already running
- The add_note.sh script now uses a new wallpaper tracking system that provides instant access to the current wallpaper, making note-adding much faster and more reliable

## Recommended Mouse Button Assignments

Here are some suggested mouse button assignments:

- **Mouse Button 4 (Back)** - Previous wallpaper
- **Mouse Button 5 (Forward)** - Next wallpaper
- **Shift+Mouse Button 4** - Toggle pause/resume
- **Shift+Mouse Button 5** - Add note to current wallpaper

You can customize these assignments based on your preferences and available mouse buttons.