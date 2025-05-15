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
./set_specific_wallpaper_kwrite.py /path/to/your/image.jpg
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

### Checking Logs

If running in the background with the suggested command, check the log file:
```bash
cat ~/.custom_wallpaper.log
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

You will be asked for confirmation before anything is removed.