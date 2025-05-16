#!/usr/bin/env python3
"""
Open Notes for Wallpaper

This script is used to open the wallpaper slideshow tray app's notes tab
for a specific image file. It's designed to be called from a KDE Dolphin
service menu when right-clicking on image files.

Usage:
    ./open_notes_for_wallpaper.py /path/to/image.jpg
"""

import os
import sys
import time
import subprocess
import signal
import psutil
from pathlib import Path
import logging
import importlib.util

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.expanduser('~/.wallpaper_notes_opener.log')
)
logger = logging.getLogger(__name__)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRAY_APP_SCRIPT = os.path.join(SCRIPT_DIR, "wallpaper_tray.py")
PID_FILE = os.path.expanduser("~/.config/custom_wallpaper_slideshow.pid")
NOTES_DIR = os.path.expanduser("~/.wallpaper_notes")
CUSTOM_WALLPAPER_SCRIPT = os.path.join(SCRIPT_DIR, "custom_wallpaper.py")
TRACK_CURRENT_WALLPAPER = os.path.join(SCRIPT_DIR, "track_current_wallpaper.py")
CURRENT_WALLPAPER_FILE = os.path.expanduser("~/.current_wallpaper")

def is_tray_app_running():
    """Check if the tray app is already running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if this is the wallpaper_tray.py process
            if proc.info['cmdline'] and 'wallpaper_tray.py' in ' '.join(proc.info['cmdline']):
                logger.info(f"Found tray app running with PID {proc.info['pid']}")
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def is_slideshow_running():
    """Check if the slideshow is running by checking the PID file"""
    if not os.path.exists(PID_FILE):
        return False
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process with this PID exists
        os.kill(pid, 0)  # This will raise an exception if the process doesn't exist
        return True
    except (ValueError, ProcessLookupError, FileNotFoundError, PermissionError):
        return False

def start_slideshow():
    """Start the wallpaper slideshow if it's not running"""
    if not is_slideshow_running():
        logger.info("Starting wallpaper slideshow...")
        try:
            subprocess.Popen(["python3", CUSTOM_WALLPAPER_SCRIPT])
            # Wait a moment for the slideshow to start
            time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Error starting slideshow: {e}")
            return False
    return True

def start_tray_app():
    """Start the tray app if it's not running"""
    if not is_tray_app_running():
        logger.info("Starting wallpaper tray app...")
        try:
            subprocess.Popen(["python3", TRAY_APP_SCRIPT])
            # Wait a moment for the tray app to start
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Error starting tray app: {e}")
            return False
    else:
        logger.info("Tray app is already running")
    return True

def open_notes_tab(image_path):
    """
    Open the main window to the notes tab and load the image
    
    This is done by sending a custom signal to the tray app process
    with the image path as an argument.
    """
    # Create a temporary file with the image path
    temp_file = os.path.join(NOTES_DIR, "open_image.tmp")
    os.makedirs(NOTES_DIR, exist_ok=True)
    
    try:
        with open(temp_file, 'w') as f:
            f.write(image_path)
        logger.info(f"Wrote image path to temporary file: {temp_file}")
        
        # Find the tray app process
        tray_app_found = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and 'wallpaper_tray.py' in ' '.join(proc.info['cmdline']):
                    # Send SIGUSR1 signal to the process
                    # This will be caught by the tray app to open the notes tab
                    logger.info(f"Sending signal to tray app (PID {proc.info['pid']})")
                    os.kill(proc.info['pid'], signal.SIGUSR1)
                    tray_app_found = True
                    
                    # Wait a moment to ensure the signal is processed
                    time.sleep(0.5)
                    
                    # Try to activate the window using xdotool if available (for X11)
                    try:
                        subprocess.run(["xdotool", "search", "--name", "Wallpaper Slideshow Manager", "windowactivate"],
                                      check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        logger.info("Attempted to activate window using xdotool")
                    except FileNotFoundError:
                        # xdotool not available, try using qdbus for KDE
                        try:
                            subprocess.run(["qdbus", "org.kde.KWin", "/KWin", "activateWindow", "Wallpaper Slideshow Manager"],
                                          check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            logger.info("Attempted to activate window using qdbus")
                        except FileNotFoundError:
                            logger.info("Neither xdotool nor qdbus available for window activation")
                    
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if not tray_app_found:
            logger.warning("Could not find tray app process to signal")
            return False
        
        return tray_app_found
    except Exception as e:
        logger.error(f"Error opening notes tab: {e}")
        return False

def get_current_wallpaper():
    """Get the current wallpaper path using the tracking system"""
    # First try to read from the tracking file
    if os.path.exists(CURRENT_WALLPAPER_FILE):
        try:
            with open(CURRENT_WALLPAPER_FILE, 'r') as f:
                wallpaper_path = f.read().strip()
            
            if wallpaper_path and os.path.exists(wallpaper_path):
                logger.info(f"Got current wallpaper from tracking file: {wallpaper_path}")
                return wallpaper_path
            else:
                logger.warning(f"Invalid wallpaper path in tracking file: {wallpaper_path}")
        except Exception as e:
            logger.error(f"Error reading current wallpaper file: {e}")
    
    # If that fails, try to use the tracking module
    try:
        if os.path.exists(TRACK_CURRENT_WALLPAPER):
            # Import the module dynamically
            spec = importlib.util.spec_from_file_location("track_current_wallpaper", TRACK_CURRENT_WALLPAPER)
            tracker = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tracker)
            
            # Get the current wallpaper
            wallpaper_path = tracker.get_current_wallpaper()
            if wallpaper_path:
                logger.info(f"Got current wallpaper from tracking module: {wallpaper_path}")
                return wallpaper_path
    except Exception as e:
        logger.error(f"Error using tracking module: {e}")
    
    logger.warning("Could not determine current wallpaper using tracking system")
    return None

def main():
    """Main function"""
    # Check if an image path was provided
    if len(sys.argv) < 2:
        # No image path provided, try to get the current wallpaper
        image_path = get_current_wallpaper()
        if not image_path:
            print("Error: Could not determine current wallpaper and no image path provided")
            print(f"Usage: {sys.argv[0]} [/path/to/image.jpg]")
            return 1
    else:
        image_path = sys.argv[1]
        
        # Check if the file exists and is an image
        if not os.path.isfile(image_path):
            print(f"Error: File not found: {image_path}")
            return 1
        
        # Get the absolute path
        image_path = os.path.abspath(image_path)
    
    logger.info(f"Opening notes for image: {image_path}")
    
    # Start the slideshow if it's not running
    if not start_slideshow():
        print("Error: Failed to start the wallpaper slideshow")
        return 1
    
    # Start the tray app if it's not running
    if not start_tray_app():
        print("Error: Failed to start the wallpaper tray app")
        return 1
    
    # Open the notes tab for the image
    if not open_notes_tab(image_path):
        print("Error: Failed to open the notes tab")
        return 1
    
    print(f"Opening notes for: {os.path.basename(image_path)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())