# KDE Plasma Wallpaper Slideshow - Documentation

This document provides detailed instructions for installing, configuring, and using the KDE Plasma Wallpaper Slideshow program.

## Table of Contents

- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Easy Installation](#easy-installation)
  - [Manual Installation](#manual-installation)
- [Configuration](#configuration)
  - [Configuration Options](#configuration-options)
  - [Example Configuration](#example-configuration)
- [Usage](#usage)
  - [Running the Program](#running-the-program)
  - [Testing the Slideshow](#testing-the-slideshow)
  - [Controlling the Slideshow](#controlling-the-slideshow)
  - [Autostart on Login](#autostart-on-login)
- [Wallpaper Tracking System](#wallpaper-tracking-system)
  - [How It Works](#how-it-works)
  - [Benefits](#benefits)
  - [Manual Usage](#manual-usage)
- [System Tray Application](#system-tray-application)
  - [Installation](#system-tray-installation)
  - [Features](#system-tray-features)
  - [Notes Window (Classic Interface)](#notes-window)
  - [Wallpaper History (Classic Interface)](#wallpaper-history)
  - [Tabbed Interface](#tabbed-interface)
    - [History Tab](#history-tab)
    - [Notes Tab](#notes-tab)
    - [Settings Tab](#settings-tab)
  - [Autostart](#system-tray-autostart)
- [Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)
  - [Checking Logs](#checking-logs)
- [Uninstallation](#uninstallation)

## Installation

### Prerequisites

1. Ensure you have Python 3 installed on your system
2. Make sure `qdbus` is installed (part of Qt tools)
   - On Kubuntu/Debian: `sudo apt install qttools5-dev-tools`
   - On Fedora: `sudo dnf install qt5-qttools-devel`
   - On Arch/Manjaro: `sudo pacman -S qt5-tools`
3. For the system tray application, you'll need PyQt5:
   - On Kubuntu/Debian: `sudo apt install python3-pyqt5`
   - On Fedora: `sudo dnf install python3-pyqt5`
   - On Arch/Manjaro: `sudo pacman -S python-pyqt5`
   - Or using pip: `pip install --user PyQt5`

### Easy Installation

The easiest way to install is using the provided installation script:

```bash
./install.sh
```

This script will:
- Make all scripts executable
- Create necessary configuration directories
- Install the desktop entry (optional)
- Add the slideshow to autostart (optional)
- Create a command-line shortcut for controlling the slideshow

### Manual Installation

If you prefer to install manually:

1. Clone or download this repository
2. Make the script executable:
   ```bash
   chmod +x custom_wallpaper.py
   chmod +x control_slideshow.sh
   ```
3. Copy the configuration file (optional):
   ```bash
   mkdir -p ~/.config/wallpaper_slideshow
   cp config.ini ~/.config/wallpaper_slideshow/
   ```

## Configuration

The slideshow can be configured using the `config.ini` file. You don't need to edit the Python script directly.

### Configuration Options

#### General Settings

- `image_directory`: Path to the directory containing your wallpaper images
  - Default: `~/Pictures/Wallpapers`
  - For removable drives, use the full path (e.g., `/run/media/username/drive-name/Wallpapers`)
- `interval`: Time in seconds between wallpaper changes (default: 300 seconds / 5 minutes)
- `shuffle`: Whether to shuffle images randomly (true/false)

#### Advanced Settings

- `supported_extensions`: List of supported image file extensions
- `pid_file`: Path to store the PID file
- `log_file`: Path to the log file (leave empty to log to console only)

### Example Configuration

```ini
[General]
image_directory = ~/Pictures/Wallpapers
interval = 300
shuffle = false

[Advanced]
supported_extensions = .jpg, .jpeg, .png, .bmp, .gif, .webp
pid_file = ~/.config/custom_wallpaper_slideshow.pid
log_file = ~/.custom_wallpaper.log
```

## Usage

### Running the Program

**For testing (in a terminal):**
```bash
./custom_wallpaper.py
```
You'll see log messages in the terminal. Press Ctrl+C to stop.

**To run in the background:**
```bash
nohup ./custom_wallpaper.py > ~/.custom_wallpaper.log 2>&1 &
```
This detaches it from your terminal and redirects output to a log file.

### Testing the Slideshow

A test script is included to verify that the slideshow is working correctly:

```bash
./test_slideshow.sh
```

This script will:
- Check if all required dependencies are installed
- Verify that the configuration file exists
- Check if the image directory exists and contains images
- Optionally run a quick test of the slideshow functionality

### Setting a Specific Wallpaper

In addition to the slideshow functionality, you can also set a specific wallpaper image using the provided scripts:

```bash
# Using the shell script wrapper
./set_wallpaper.sh /path/to/your/image.jpg

# Or using the Python script directly
./set_specific_wallpaper.py /path/to/your/image.jpg
```

These scripts use the KDE configuration system to set the wallpaper directly, without needing to start the slideshow.

### Controlling the Slideshow

The script prints its Process ID (PID) when it starts and saves it to `~/.config/custom_wallpaper_slideshow.pid`.

You can get the PID by:
```bash
cat ~/.config/custom_wallpaper_slideshow.pid
```

Assuming the PID is `12345`, you can control the slideshow with these commands:

#### Using the Control Script

For easier control, use the included `control_slideshow.sh` script:

```bash
# Make the control script executable
chmod +x control_slideshow.sh

# Control commands
./control_slideshow.sh next     # Show next wallpaper
./control_slideshow.sh prev     # Show previous wallpaper
./control_slideshow.sh pause    # Toggle pause/resume
./control_slideshow.sh reload   # Reload image list
./control_slideshow.sh stop     # Stop the slideshow
./control_slideshow.sh status   # Check if slideshow is running
```

#### Using Direct Signals

If you prefer to use signals directly:

- **Next Image:** `kill -USR1 12345`
- **Previous Image:** `kill -USR2 12345`
- **Pause/Resume Slideshow:** `kill -TSTP 12345`
- **Reload Image List:** `kill -HUP 12345` (useful after adding new images)
- **Stop the Script:** `kill -TERM 12345` or `kill $(cat ~/.config/custom_wallpaper_slideshow.pid)`

### Autostart on Login

#### Method 1: Using System Settings

1. Go to System Settings -> Startup and Shutdown -> Autostart
2. Click "Add Script..."
3. Browse to and select your `custom_wallpaper.py` script
4. Make sure it's marked as "Executable"

#### Method 2: Using the Desktop Entry

A desktop entry file (`wallpaper-slideshow.desktop`) is included for easy integration with your desktop environment:

1. Copy the desktop entry to the autostart directory:
   ```bash
   cp wallpaper-slideshow.desktop ~/.config/autostart/
   ```

2. Make sure the path in the desktop entry is correct:
   - Open `~/.config/autostart/wallpaper-slideshow.desktop` in a text editor
   - Update the `Exec` line if needed to point to the correct location of your script

You can also add the slideshow to your application menu:
```bash
cp wallpaper-slideshow.desktop ~/.local/share/applications/
```

## Wallpaper Tracking System

The wallpaper tracking system is a new feature that provides instant access to the current wallpaper path, making operations like adding notes much faster and more reliable.

### How It Works

1. Whenever a wallpaper is set (either by the slideshow or manually), its path is saved to a tracking file at `~/.current_wallpaper`
2. When you want to add a note to the current wallpaper, the system reads this file to instantly get the wallpaper path
3. This eliminates the need for slow and potentially unreliable methods like parsing log files or taking screenshots

The tracking system is implemented in the following components:

- `track_current_wallpaper.py`: A standalone script that provides functions for saving and retrieving the current wallpaper path
- `set_specific_wallpaper.py`: Updated to track the wallpaper whenever it's set manually
- `custom_wallpaper.py`: Updated to track the wallpaper whenever it changes during the slideshow
- `add_note.sh`: Updated to use the tracking system for instant access to the current wallpaper
- `open_notes_for_wallpaper.py`: Updated to use the tracking system when no specific wallpaper is provided
- `wallpaper_tray.py`: Updated to use the tracking system for faster and more reliable wallpaper detection

### Benefits

- **Speed**: Adding notes to the current wallpaper is now instantaneous
- **Reliability**: No more issues with log file parsing or screenshot comparison
- **Simplicity**: The system uses a simple text file that can be easily read by any script or program
- **Fallbacks**: If the tracking file is unavailable, the system falls back to the previous methods

### Manual Usage

You can manually use the tracking system with the following commands:

```bash
# Get the current wallpaper path
python3 track_current_wallpaper.py

# Set the current wallpaper path
python3 track_current_wallpaper.py /path/to/wallpaper.jpg
```

## System Tray Application

The system tray application provides a convenient way to control the wallpaper slideshow and take notes on wallpapers. There are two versions available: the classic interface and the new tabbed interface.

### System Tray Installation

To install the classic system tray application:

```bash
./install_tray.sh
```

To install the new tabbed interface:

```bash
./install_tray_new.sh
```

These scripts will:
- Make the necessary scripts executable
- Create the tray icon
- Install the desktop entry for the system tray application
- Set up autostart for the system tray application
- Create the notes directory

### System Tray Features

#### Classic Interface

The classic system tray application provides the following features:

- **Left-click**: Open the notes window for the current wallpaper
- **Right-click menu**:
  - **Open Notes**: View and edit notes for the current wallpaper
  - **Wallpaper History**: View and restore previously shown wallpapers
  - **Next/Previous Wallpaper**: Navigate through the slideshow
  - **Pause/Resume**: Toggle the slideshow
  - **Color Control Panel**: Open the color control panel
  - **Restart Slideshow**: Restart the slideshow
  - **Quit**: Exit the system tray application

#### New Tabbed Interface

The new tabbed interface provides the following features:

- **Left-click**: Open the main window with tabs for history, notes, and settings
- **Right-click menu**:
  - **Open Wallpaper Manager**: Open the main window with tabs
  - **Next/Previous Wallpaper**: Navigate through the slideshow
  - **Pause/Resume**: Toggle the slideshow
  - **Color Control Panel**: Open the color control panel
  - **Restart Slideshow**: Restart the slideshow
  - **Quit**: Exit the system tray application

### Notes Window

The notes window allows you to:

- View and edit notes for the current wallpaper
- Browse all wallpapers with notes
- Export and import notes
- Refresh the current wallpaper

Notes are stored in the `~/.wallpaper_notes` directory in a JSON file. Each note is associated with a specific wallpaper file path.

The notes window now uses the new wallpaper tracking system for instant access to the current wallpaper, making it much faster and more reliable when adding notes to the current wallpaper.

### Wallpaper History

The wallpaper history window allows you to:

- View recently shown wallpapers
- Set a specific wallpaper as the current wallpaper
- Clear the wallpaper history

The history is stored in the `~/.wallpaper_notes/wallpaper_history.json` file and keeps track of the last 50 wallpapers shown.

### Tabbed Interface

The new tabbed interface combines multiple features in a single window, making it easier to manage your wallpaper slideshow.

#### History Tab

The History tab provides the same functionality as the standalone Wallpaper History window:

- View recently shown wallpapers with thumbnails
- Set a specific wallpaper as the current wallpaper by double-clicking or using the "Set as Current Wallpaper" button
- Clear the wallpaper history
- Refresh the history list

#### Notes Tab

The Notes tab provides the same functionality as the standalone Notes window:

- View and edit notes for the current wallpaper
- Browse all wallpapers with notes
- Export and import notes
- Refresh the current wallpaper

#### Settings Tab

The Settings tab provides a user-friendly interface for configuring the slideshow:

- **General Settings**:
  - Image directory: Set the directory containing your wallpaper images
  - Change interval: Set the time between wallpaper changes (in seconds)
  - Shuffle images: Enable or disable random shuffling of wallpapers

- **Advanced Settings**:
  - Supported extensions: Configure which file extensions are recognized as wallpapers
  - PID file: Set the location of the PID file
  - Log file: Set the location of the log file

- **Actions**:
  - Save Settings: Save the settings without applying them
  - Apply Settings: Save the settings and restart the slideshow to apply them
  - Reset to Defaults: Reset all settings to their default values

### System Tray Autostart

The system tray application is automatically configured to start when you log in. If you want to disable this:

1. Go to System Settings -> Startup and Shutdown -> Autostart
2. Find "Wallpaper Slideshow Tray" in the list
3. Uncheck the box next to it or remove it

## Troubleshooting

### Common Issues

1. **No images found**: Check that `IMAGE_DIR` points to a directory containing supported image files.

2. **Error setting wallpaper via qdbus**: Ensure `qdbus` is installed and in your PATH.

3. **Cannot unmount drive**: If your images are on a removable drive and you can't unmount it:
   - Stop the slideshow script first: `kill $(cat ~/.config/custom_wallpaper_slideshow.pid)`
   - KDE Plasma itself might be keeping the current wallpaper file open

4. **Script not running after login**: If using autostart:
   - Add a delay by inserting `time.sleep(10)` at the beginning of the main block
   - Check the log file for errors

5. **System tray icon not appearing**: Make sure PyQt5 is installed correctly:
   - Check if the tray application is running: `ps aux | grep wallpaper_tray.py`
   - Check the log file: `cat ~/.wallpaper_tray.log`

6. **Tracking file issues**: If the wallpaper tracking system isn't working:
   - Check if the tracking file exists: `cat ~/.current_wallpaper`
   - Ensure the file has the correct permissions: `chmod 644 ~/.current_wallpaper`
   - Try manually updating it: `python3 track_current_wallpaper.py /path/to/wallpaper.jpg`
   - Check if the scripts have been updated to use the tracking system

### Checking Logs

If running in the background with the suggested command, check the log file:
```bash
cat ~/.custom_wallpaper.log
```

For the system tray application, check its log file:
```bash
cat ~/.wallpaper_tray.log
```

## Uninstallation

If you want to remove the wallpaper slideshow program, you can use the provided uninstall script:

```bash
./uninstall.sh
```

This script will:
- Stop any running instances of the slideshow
- Remove desktop entries from applications menu and autostart
- Remove the command-line shortcut
- Remove configuration and log files

To uninstall the classic system tray application:

```bash
./uninstall_tray.sh
```

To uninstall the new tabbed interface:

```bash
./uninstall_tray_new.sh
```

These scripts will:
- Remove desktop entries for the system tray application
- Remove autostart entry for the system tray application
- Optionally remove all wallpaper notes
- Optionally restore the other version if you're switching between versions

You will be asked for confirmation before anything is removed.