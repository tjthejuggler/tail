# KDE Plasma Wallpaper Slideshow

A custom wallpaper slideshow program for KDE Plasma that gives you full control over your desktop background changes.

![KDE Plasma Wallpaper](https://kde.org/images/plasma5.png)

## Overview

This program provides a flexible and customizable wallpaper slideshow solution for KDE Plasma desktop environments. Unlike the built-in slideshow functionality, this custom solution gives you complete control over:

- When and how wallpapers change
- The ability to go to next/previous images
- Pausing and resuming the slideshow
- Reloading the image list without restarting
- Detailed logging for troubleshooting
- Taking notes on wallpapers via the system tray application
- Configuring slideshow settings through a user-friendly interface

It's particularly useful for users who want to use images from removable drives or network locations, as it provides better control over the slideshow process.

## Key Features

- **Configurable Intervals**: Set your own timing for wallpaper changes
- **Multiple Control Methods**: Use signals, a control script, desktop shortcuts, or the system tray icon
- **Format Support**: Works with JPG, PNG, BMP, GIF, WebP images
- **Shuffle Mode**: Option to display images in random order
- **Detailed Logging**: Track what's happening with the slideshow
- **Easy Installation**: Simple setup with an installation script
- **Desktop Integration**: Includes desktop entry for application menus and autostart
- **Direct Wallpaper Setting**: Set a specific wallpaper image without using the slideshow
- **System Tray Integration**: Control the slideshow from the system tray and take notes on wallpapers
- **Wallpaper Notes**: Associate notes with wallpapers for easy reference
- **Wallpaper History**: View and restore previously shown wallpapers
- **File Browser**: Browse and select image files directly within the notes interface
- **Tabbed Interface**: Access history, notes, and settings in a single window
- **Dolphin Integration**: Right-click on image files in Dolphin to add notes directly

## Getting Started

1. Navigate to the `wallpaper_slideshow` directory
2. Run the installation script:
   ```bash
   ./install.sh
   ```
3. Edit the configuration file at `~/.config/wallpaper_slideshow/config.ini` to set your image directory and preferences
4. Start the slideshow:
   ```bash
   ./custom_wallpaper.py
   ```

   Or set a specific wallpaper directly:
   ```bash
   ./set_wallpaper.sh /path/to/your/image.jpg
   ```

## System Tray Application

The system tray application provides a convenient way to control the wallpaper slideshow and take notes on wallpapers.

### Installation

1. Navigate to the `wallpaper_slideshow` directory
2. Run the installation script:
   ```bash
   ./install_tray.sh
   ```

   Or for the new tabbed interface:
   ```bash
   ./install_tray_new.sh
   ```

### Features

#### Classic Interface
- **Left-click**: Open the notes window for the current wallpaper
- **Right-click menu**:
  - Open Notes: View and edit notes for the current wallpaper
  - Wallpaper History: View and restore previously shown wallpapers
  - Next/Previous Wallpaper: Navigate through the slideshow
  - Pause/Resume: Toggle the slideshow
  - Color Control Panel: Open the color control panel
  - Restart Slideshow: Restart the slideshow
  - Quit: Exit the system tray application

#### New Tabbed Interface
- **Left-click**: Open the main window with tabs for history, notes, and settings
- **Right-click menu**:
  - Open Wallpaper Manager: Open the main window with tabs
  - Next/Previous Wallpaper: Navigate through the slideshow
  - Pause/Resume: Toggle the slideshow
  - Color Control Panel: Open the color control panel
  - Restart Slideshow: Restart the slideshow
  - Quit: Exit the system tray application
|
### Dolphin File Manager Integration
|
The KDE Dolphin integration allows you to:
- Right-click on any image file in Dolphin
- Select "Add a note to this wallpaper" from the context menu
- The tray app will open to the notes tab with the selected image loaded
|
To install the Dolphin integration:
```bash
./install_dolphin_integration.sh
```
|
This integration is also offered during the tray app installation.

### Main Window (Tabbed Interface)

The new tabbed interface combines multiple features in a single window:

#### History Tab
- View recently shown wallpapers
- Set a specific wallpaper as the current wallpaper
- Clear the wallpaper history

#### Notes Tab
- View and edit notes for the current wallpaper
- Browse all wallpapers with notes
- Browse and select image files with the integrated file browser
- View thumbnails for image files in the file browser
- Navigate through directories with back, forward, up, and home buttons
- Filter for image files based on supported extensions
- Set any image as the current wallpaper by double-clicking
- Export and import notes
- Refresh the current wallpaper

#### Settings Tab
- Configure slideshow settings:
  - Image directory
  - Change interval
  - Shuffle mode
  - Supported file extensions
  - Log and PID file locations
- Apply settings without restarting the application
- Reset to default settings

### Notes Window (Classic Interface)

The notes window allows you to:
- View and edit notes for the current wallpaper
- Browse all wallpapers with notes
- Browse and select image files with the integrated file browser
- View thumbnails for image files in the file browser
- Navigate through directories with back, forward, up, and home buttons
- Filter for image files based on supported extensions
- Set any image as the current wallpaper by double-clicking
- Export and import notes
- Refresh the current wallpaper

### Wallpaper History (Classic Interface)

The wallpaper history window allows you to:
- View recently shown wallpapers
- Set a specific wallpaper as the current wallpaper
- Clear the wallpaper history

## Examples

The `examples` directory contains sample scripts demonstrating how to integrate with and control the wallpaper slideshow from your own scripts and applications:

- **Bash Script Integration**: `examples/change_wallpaper_example.sh` shows how to control the slideshow from a Bash script
- **Python Integration**: `examples/python_integration.py` shows how to control the slideshow from a Python application

These examples demonstrate checking if the slideshow is running, starting and stopping the slideshow, showing next/previous wallpapers, toggling pause/resume, and more.

See the [Examples README](examples/README.md) for more details.

## Documentation

For detailed instructions on installation, configuration, and usage, please see the [full documentation](DOCUMENTATION.md).

## Troubleshooting

### Known Issues and Fixes

#### Dolphin Integration Service Menu Not Appearing

**Issue**: The "Add a note to this wallpaper" option may not appear in the Dolphin right-click menu on newer KDE versions.

**Fix**: This issue has been resolved by updating the installation script to use the correct service menu location for modern KDE versions:
- The script now checks for both old (`~/.local/share/kservices5/ServiceMenus/`) and new (`~/.local/share/kio/servicemenus/`) KDE service menu locations
- It automatically selects the appropriate location based on your KDE version
- The service menu file is now made executable during installation
- The uninstall script has also been updated to check both locations

If you previously installed the Dolphin integration and don't see the menu option, or if you get a "You are not authorized to execute this file" error, simply run the installation script again:
```bash
./install_dolphin_integration.sh
```

If you still get the "not authorized" error after reinstalling, you can manually make the desktop file executable:
```bash
chmod +x ~/.local/share/kio/servicemenus/wallpaper-notes.desktop
kbuildsycoca5  # Refresh KDE service cache
```

#### Main Window Not Opening or Coming to Front

**Issue**: When using the "Add a note to this wallpaper" option from Dolphin, the main window might not open if the tray app is not running, or it might not come to the front if it's minimized.

**Fix**: This issue has been resolved by:
- Improving the window activation code to ensure the window is properly shown and brought to the front
- Adding additional window activation methods using xdotool and qdbus when available
- Ensuring the window is not left in a minimized state
- Adding proper event processing to ensure window activation takes effect immediately
- Improving the tray app detection and startup process

If you experience any issues with the window not appearing, try restarting the tray app:
```bash
killall -9 python3 wallpaper_tray.py
python3 wallpaper_slideshow/wallpaper_tray.py &
```

#### Refresh Current Wallpaper in Notes Tab

**Issue**: Prior to version 1.2.3, clicking "Refresh Current Wallpaper" while in the notes tab could cause the application to crash.

**Fix**: This issue has been resolved by:
- Adding robust error handling in the refresh_current_wallpaper() method
- Improving the screenshot comparison logic in get_current_wallpaper.py
- Adding fallback mechanisms when wallpaper detection fails
- Implementing better thread safety for background operations

If you experience any crashes, please update to the latest version.

### Debugging

If you encounter issues:
1. Check the log files:
   - Main application: `~/.custom_wallpaper.log`
   - Tray application: `~/.wallpaper_tray.log`
   - Main window: `~/.wallpaper_main_window.log`
2. Enable debug mode for the wallpaper detection:
   ```bash
   python3 get_current_wallpaper.py --debug
   ```
   This will save debug screenshots to your home directory.

## Requirements

- KDE Plasma desktop environment
- Python 3
- `qdbus` command (part of Qt tools)
- PyQt5 (for the system tray application)
- psutil (for the Dolphin integration)
- OpenCV and scikit-image (for wallpaper detection)

## License

This project is open source and available under the MIT License.