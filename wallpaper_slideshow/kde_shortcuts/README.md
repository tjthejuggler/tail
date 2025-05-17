# KDE Shortcuts for Wallpaper Slideshow

This directory contains scripts that can be used to create KDE keyboard shortcuts for controlling the wallpaper slideshow.

## Available Scripts

- `next_slide.sh` - Show the next wallpaper in the slideshow
- `previous_slide.sh` - Show the previous wallpaper in the slideshow
- `previous_when_paused.sh` - Show the previous wallpaper even when slideshow is paused
- `toggle_pause.sh` - Toggle pause/resume of the slideshow
- `pause.sh` - Pause the slideshow
- `unpause.sh` - Unpause the slideshow
- `add_to_favorites.sh` - Add the current wallpaper to favorites
- `add_note.sh` - Open the notes editor for the current wallpaper
- `custom_mode_upper_left.sh` - Custom script for mouse button that goes back to previous image even when paused

## Setting Up Keyboard Shortcuts in KDE

1. Open System Settings
2. Go to Shortcuts > Custom Shortcuts
3. Click "Edit" > "New" > "Global Shortcut" > "Command/URL"
4. Give your shortcut a name (e.g., "Next Wallpaper")
5. Click on the "Trigger" tab and set your desired keyboard shortcut
6. Click on the "Action" tab and enter the full path to the script (e.g., `/home/username/Projects/tail/wallpaper_slideshow/kde_shortcuts/next_slide.sh`)
7. Click "Apply"

## Favorites Feature

The `add_to_favorites.sh` script allows you to add the current wallpaper to your favorites list. You can then configure the slideshow to only show your favorite wallpapers by:

1. Opening the Wallpaper Manager (click on the tray icon)
2. Going to the "Favorites" tab
3. Checking the "Use only favorites in slideshow" option
4. Clicking "Apply and Restart Slideshow"

You can also manage your favorites through the Favorites tab in the Wallpaper Manager:
- Add new wallpapers to favorites
- Remove wallpapers from favorites
- Set a favorite wallpaper as the current wallpaper

## Making Scripts Executable

If you encounter permission issues when running the scripts, make sure they are executable:

```bash
chmod +x /path/to/wallpaper_slideshow/kde_shortcuts/*.sh
```

## Custom Mouse Button Scripts

The `custom_mode_upper_left.sh` script is designed to be used with custom mouse button mappings. It allows you to:

1. Go back to the previous wallpaper
2. Continue going back through wallpapers even when the slideshow is paused

This is achieved by using the `previous_when_paused.sh` script which:
- Temporarily unpauses the slideshow if it's paused
- Goes to the previous image
- Pauses the slideshow again if it was paused before

### Setting Up Mouse Button Shortcuts

To use these scripts with mouse buttons:
1. Configure your mouse button software to execute the script path
2. For example: `/home/username/Projects/tail/wallpaper_slideshow/kde_shortcuts/custom_mode_upper_left.sh`