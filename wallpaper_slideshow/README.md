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

### Features

- **Left-click**: Open the notes window for the current wallpaper
- **Right-click menu**:
  - Open Notes: View and edit notes for the current wallpaper
  - Wallpaper History: View and restore previously shown wallpapers
  - Next/Previous Wallpaper: Navigate through the slideshow
  - Pause/Resume: Toggle the slideshow
  - Color Control Panel: Open the color control panel
  - Restart Slideshow: Restart the slideshow
  - Quit: Exit the system tray application

### Notes Window

The notes window allows you to:
- View and edit notes for the current wallpaper
- Browse all wallpapers with notes
- Export and import notes
- Refresh the current wallpaper

### Wallpaper History

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

## Requirements

- KDE Plasma desktop environment
- Python 3
- `qdbus` command (part of Qt tools)
- PyQt5 (for the system tray application)

## License

This project is open source and available under the MIT License.