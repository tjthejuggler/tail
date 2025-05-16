#!/usr/bin/env python3
"""
Wallpaper Tracking System

This script provides functions to save and retrieve the current wallpaper path.
It maintains a simple text file with the path of the current wallpaper,
allowing for instant access when adding notes or performing other operations.

Usage:
    # Get the current wallpaper path
    python3 track_current_wallpaper.py
    
    # Set the current wallpaper path
    python3 track_current_wallpaper.py /path/to/wallpaper.jpg
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CURRENT_WALLPAPER_FILE = os.path.expanduser("~/.current_wallpaper")

def save_current_wallpaper(wallpaper_path):
    """
    Save the path of the current wallpaper to a file.
    
    Args:
        wallpaper_path (str): Path to the current wallpaper
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate input
        if not wallpaper_path:
            logger.error("Empty wallpaper path provided")
            return False
            
        # Ensure the path is absolute
        abs_path = str(Path(wallpaper_path).resolve())
        
        # Check if the file exists
        if not os.path.exists(abs_path):
            logger.error(f"Wallpaper file does not exist: {abs_path}")
            return False
            
        # Check if the file is an image
        _, ext = os.path.splitext(abs_path.lower())
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            logger.error(f"File is not a supported image type: {abs_path}")
            return False
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(CURRENT_WALLPAPER_FILE), exist_ok=True)
        
        # Save the path to the file
        with open(CURRENT_WALLPAPER_FILE, 'w') as f:
            f.write(abs_path)
        
        # Set appropriate permissions
        try:
            os.chmod(CURRENT_WALLPAPER_FILE, 0o644)  # rw-r--r--
        except Exception as e:
            logger.warning(f"Could not set permissions on tracking file: {e}")
        
        logger.info(f"Saved current wallpaper path: {abs_path}")
        print(f"Current wallpaper set to: {abs_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving current wallpaper path: {e}")
        return False

def get_current_wallpaper():
    """
    Get the path of the current wallpaper from the file.
    
    Returns:
        str: Path to the current wallpaper, or None if not found
    """
    try:
        if not os.path.exists(CURRENT_WALLPAPER_FILE):
            logger.warning(f"Current wallpaper file not found: {CURRENT_WALLPAPER_FILE}")
            return None
        
        # Check if the file is readable
        if not os.access(CURRENT_WALLPAPER_FILE, os.R_OK):
            logger.warning(f"Current wallpaper file is not readable: {CURRENT_WALLPAPER_FILE}")
            return None
            
        with open(CURRENT_WALLPAPER_FILE, 'r') as f:
            wallpaper_path = f.read().strip()
        
        # Validate the path
        if not wallpaper_path:
            logger.warning("Current wallpaper file is empty")
            return None
            
        # Check if the file exists
        if not os.path.exists(wallpaper_path):
            logger.warning(f"Wallpaper file does not exist: {wallpaper_path}")
            return None
            
        # Check if the file is an image
        _, ext = os.path.splitext(wallpaper_path.lower())
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            logger.warning(f"File is not a supported image type: {wallpaper_path}")
            return None
        
        logger.info(f"Retrieved current wallpaper path: {wallpaper_path}")
        return wallpaper_path
    except Exception as e:
        logger.error(f"Error getting current wallpaper path: {e}")
        return None

def main():
    """Main function"""
    # If an argument is provided, save it as the current wallpaper
    if len(sys.argv) > 1:
        wallpaper_path = sys.argv[1]
        save_current_wallpaper(wallpaper_path)
    # Otherwise, get and print the current wallpaper
    else:
        wallpaper_path = get_current_wallpaper()
        if wallpaper_path:
            print(wallpaper_path)
        else:
            print("No current wallpaper found")
            sys.exit(1)

if __name__ == "__main__":
    main()