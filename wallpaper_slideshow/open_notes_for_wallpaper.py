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
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and 'wallpaper_tray.py' in ' '.join(proc.info['cmdline']):
                    # Send SIGUSR1 signal to the process
                    # This will be caught by the tray app to open the notes tab
                    logger.info(f"Sending signal to tray app (PID {proc.info['pid']})")
                    os.kill(proc.info['pid'], signal.SIGUSR1)
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        logger.warning("Could not find tray app process to signal")
        return False
    except Exception as e:
        logger.error(f"Error opening notes tab: {e}")
        return False

def main():
    """Main function"""
    # Check if an image path was provided
    if len(sys.argv) < 2:
        print("Error: No image path provided")
        print(f"Usage: {sys.argv[0]} /path/to/image.jpg")
        return 1
    
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