# Wallpaper Slideshow Examples

This directory contains example scripts demonstrating how to integrate with and control the KDE Plasma Wallpaper Slideshow program from your own scripts and applications.

## Available Examples

### 1. Bash Script Integration (`change_wallpaper_example.sh`)

This example shows how to control the wallpaper slideshow from a Bash script. It demonstrates:

- Checking if the slideshow is running
- Starting and stopping the slideshow
- Showing next/previous wallpapers
- Toggling pause/resume
- Reloading the image list
- Running a demo sequence

**Usage:**
```bash
./change_wallpaper_example.sh {start|next|prev|pause|reload|stop|demo}
```

### 2. Python Integration (`python_integration.py`)

This example shows how to control the wallpaper slideshow from a Python application. It demonstrates:

- Checking if the slideshow is running
- Starting and stopping the slideshow
- Showing next/previous wallpapers
- Toggling pause/resume
- Reloading the image list
- Running a demo sequence

**Usage:**
```bash
./python_integration.py {start|stop|next|prev|pause|reload|status|demo}
```

## Integration Guide

### Key Concepts

1. **PID File**: The slideshow stores its Process ID (PID) in `~/.config/custom_wallpaper_slideshow.pid`. You can use this to check if the slideshow is running and to send signals to control it.

2. **Control Signals**: The slideshow responds to various signals:
   - `SIGUSR1`: Show next wallpaper
   - `SIGUSR2`: Show previous wallpaper
   - `SIGTSTP`: Toggle pause/resume
   - `SIGHUP`: Reload image list
   - `SIGTERM`: Stop the slideshow

### Integration Steps

1. **Check if the slideshow is running**:
   - Read the PID from the PID file
   - Verify the process with that PID exists

2. **Start the slideshow**:
   - Execute the `custom_wallpaper.py` script
   - Wait for it to initialize

3. **Control the slideshow**:
   - Send the appropriate signals to the slideshow process

4. **Stop the slideshow**:
   - Send the SIGTERM signal to the slideshow process

## Creating Your Own Integration

You can use these examples as a starting point for your own integration. The key points to remember are:

1. Always check if the slideshow is running before sending signals
2. Handle errors gracefully if the slideshow is not running or if signals fail
3. Provide clear feedback to the user about what's happening

For more advanced integration, you could:
- Create a GUI application to control the slideshow
- Integrate with system events (e.g., change wallpaper when a USB drive is connected)
- Schedule wallpaper changes based on time of day or other conditions