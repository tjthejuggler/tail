#!/usr/bin/env python3
"""
Refresh Wallpaper

This script updates the symlinks in the /home/twain/Pictures/llm_baby_monster directory
based on the weekly habit count, and then refreshes the Plasma shell to make it
update its view of what's in the directory.

Usage:
    python3 refresh_wallpaper.py [color]

If color is not provided, it will be determined from the current weekly habit count.
"""

import os
import sys
import json
import shutil
import subprocess
import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths
BASE_DIR = "/home/twain/Pictures"
TARGET_DIR = os.path.join(BASE_DIR, "llm_baby_monster")
COLOR_BASE_DIR = os.path.join(BASE_DIR, "llm_baby_monster_by_color")
CONFIG_PATH = "/home/twain/Projects/tail/wallpaper_color_manager_new/config.json"
CURRENT_COLOR_FILE = "/home/twain/Projects/tail/current_wallpaper_color.txt"

# Define color thresholds
def get_color_from_count(count):
    if count < 13:
        return "red"
    elif 13 < count <= 20:
        return "orange"
    elif 20 < count <= 30:
        return "green"
    elif 30 < count <= 41:
        return "blue"
    elif 41 < count <= 48:
        return "pink"
    elif 48 < count <= 55:
        return "yellow"
    elif 55 < count <= 62:
        return "white_gray_black"
    else:
        return "white_gray_black"

def get_weekly_habit_count():
    """Get the current weekly habit count from the totals file"""
    totals_file = '/home/twain/noteVault/habitCounters/total_habits.txt2'
    
    # Check if file exists
    if not os.path.exists(totals_file):
        logger.error(f"Totals file not found: {totals_file}")
        # Fallback to a default value
        return 25  # Middle of the green range as a safe default
    
    try:
        # Read the totals file
        with open(totals_file, 'r') as f:
            totals_str = f.read().strip()
            logger.debug(f"Raw totals string: {totals_str}")
            
            if not totals_str:
                logger.error("Totals file is empty")
                return 25  # Default to middle of green range
            
            totals = [int(x) for x in totals_str.split(',')]
            logger.debug(f"Parsed totals: {totals}")
            
            # Calculate week average from the totals file
            if not totals:
                logger.error("No totals found after parsing")
                return 25  # Default to middle of green range
                
            week_totals = totals[:7]  # First 7 values are the most recent
            if not week_totals:
                logger.error("No weekly totals found")
                return 25  # Default to middle of green range
                
            weekly_average = sum(week_totals) / len(week_totals)
            
            logger.info(f"Weekly habit average: {weekly_average}")
            return weekly_average
        
    except Exception as e:
        logger.error(f"Error getting weekly habit count: {e}")
        # Fallback to a default value
        return 25  # Middle of the green range as a safe default

def load_config():
    """Load the wallpaper color manager configuration"""
    # Check if config file exists
    if not os.path.exists(CONFIG_PATH):
        logger.error(f"Config file not found: {CONFIG_PATH}")
        # Create a default config
        return create_default_config()
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            logger.info(f"Config loaded from {CONFIG_PATH}")
            return config
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {e}")
        return create_default_config()
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return create_default_config()

def create_default_config():
    """Create a default configuration if the config file is missing or invalid"""
    logger.warning("Creating default configuration")
    
    default_config = {
        "paths": {
            "base_dir": "/home/twain/Pictures",
            "original_dir": "llm_baby_monster_original",
            "color_dirs": {
                "red": "llm_baby_monster_by_color/red",
                "orange": "llm_baby_monster_by_color/orange",
                "green": "llm_baby_monster_by_color/green",
                "blue": "llm_baby_monster_by_color/blue",
                "pink": "llm_baby_monster_by_color/pink",
                "yellow": "llm_baby_monster_by_color/yellow",
                "white_gray_black": "llm_baby_monster_by_color/white_gray_black"
            }
        }
    }
    
    # Try to save the default config
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(default_config, f, indent=2)
        logger.info(f"Default config saved to {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Error saving default config: {e}")
    
    return default_config

def update_wallpaper_folder(color=None):
    """
    Update the wallpaper folder with images from the specified color category.
    
    Args:
        color: The color category to use. If None, it will be determined from the weekly habit count.
        
    Returns:
        tuple: (success, color_changed, previous_color)
    """
    # Check if we have a previous color
    previous_color = None
    color_changed = False
    try:
        if os.path.exists(CURRENT_COLOR_FILE):
            with open(CURRENT_COLOR_FILE, 'r') as f:
                previous_color = f.read().strip()
    except Exception as e:
        logger.error(f"Error reading previous color: {e}")
    
    # Determine color if not provided
    if color is None:
        weekly_count = get_weekly_habit_count()
        color = get_color_from_count(weekly_count)
    
    logger.info(f"Using color category: {color}")
    
    # Check if color has changed
    if previous_color and previous_color != color:
        color_changed = True
        logger.info(f"Color changed from {previous_color} to {color}")
    
    # Save the current color to a file for reference
    try:
        with open(CURRENT_COLOR_FILE, 'w') as f:
            f.write(color)
    except Exception as e:
        logger.error(f"Error saving current color: {e}")
    
    # Load config to get the correct paths
    config = load_config()
    if not config:
        logger.error("Failed to load configuration")
        return False, color_changed, previous_color
    
    # Get the source directory for the selected color
    color_dir = config["paths"]["color_dirs"].get(color)
    if not color_dir:
        logger.error(f"Color directory not found for {color}")
        return False, color_changed, previous_color
    
    source_dir = os.path.join(BASE_DIR, color_dir)
    
    # Ensure source directory exists
    if not os.path.exists(source_dir) or not os.path.isdir(source_dir):
        logger.error(f"Source directory does not exist: {source_dir}")
        return False, color_changed, previous_color
    
    # Ensure target directory exists
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    # Get current files in target directory before clearing
    old_files = set()
    for item in os.listdir(TARGET_DIR):
        if item.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            old_files.add(item)
    
    # Clear the target directory
    for item in os.listdir(TARGET_DIR):
        item_path = os.path.join(TARGET_DIR, item)
        try:
            if os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isfile(item_path):
                os.remove(item_path)
        except Exception as e:
            logger.error(f"Error removing {item_path}: {e}")
    
    # Get all image files from the source directory
    image_files = []
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            # For symlinks, get the actual file they point to
            file_path = os.path.join(source_dir, filename)
            if os.path.islink(file_path):
                real_path = os.path.realpath(file_path)
                if os.path.exists(real_path) and os.path.isfile(real_path):
                    image_files.append((filename, real_path))
            else:
                image_files.append((filename, file_path))
    
    # If no images found in the color category, try using white_gray_black as fallback
    if not image_files and color != "white_gray_black":
        logger.warning(f"No images found in {color} category, trying white_gray_black as fallback")
        fallback_color = "white_gray_black"
        fallback_dir = os.path.join(BASE_DIR, config["paths"]["color_dirs"].get(fallback_color, ""))
        
        if os.path.exists(fallback_dir) and os.path.isdir(fallback_dir):
            for filename in os.listdir(fallback_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    file_path = os.path.join(fallback_dir, filename)
                    if os.path.islink(file_path):
                        real_path = os.path.realpath(file_path)
                        if os.path.exists(real_path) and os.path.isfile(real_path):
                            image_files.append((filename, real_path))
                    else:
                        image_files.append((filename, file_path))
    
    # If still no images, log error and return
    if not image_files:
        logger.error(f"No images found in {color} category or fallback")
        return False, color_changed, previous_color
    
    # Create symlinks in the target directory
    count = 0
    new_files = set()
    for filename, source_path in image_files:
        try:
            target_path = os.path.join(TARGET_DIR, filename)
            os.symlink(source_path, target_path)
            new_files.add(filename)
            count += 1
        except Exception as e:
            logger.error(f"Error creating symlink for {filename}: {e}")
    
    logger.info(f"Created {count} symlinks in {TARGET_DIR}")
    
    # Check if files have changed
    files_changed = old_files != new_files
    if files_changed:
        logger.info("Wallpaper directory contents have changed")
    
    # Return success and whether color or files changed
    return True, (color_changed or files_changed), previous_color

def refresh_plasma_shell():
    """Refresh the Plasma shell to make it update its view of what's in the directory"""
    logger.info("Attempting to refresh KDE Plasma shell...")
    
    # Method 1: Run the command directly as a shell command
    try:
        logger.info("Trying method 1: plasmashell --replace &")
        # Use shell=True and pass the entire command as a string to properly handle the &
        subprocess.run("plasmashell --replace &", shell=True, check=False)
        logger.info("Plasma shell replace command executed")
        return True
    except Exception as e:
        logger.error(f"Error with method 1: {e}")
    
    # Method 2: Try without the &
    try:
        logger.info("Trying method 2: plasmashell --replace")
        subprocess.run(["plasmashell", "--replace"], shell=False, check=False)
        logger.info("Plasma shell replace command executed (without &)")
        return True
    except Exception as e:
        logger.error(f"Error with method 2: {e}")
    
    # Method 3: Try the old method as a fallback
    try:
        logger.info("Trying method 3: plasmashell reload")
        subprocess.run(["plasmashell", "reload"], check=False)
        logger.info("Plasma shell reload command executed")
        return True
    except Exception as e:
        logger.error(f"Error with method 3: {e}")
    
    # Method 4: Last resort - use os.system
    try:
        logger.info("Trying method 4: os.system")
        os.system("plasmashell --replace &")
        logger.info("Plasma shell replace command executed via os.system")
        return True
    except Exception as e:
        logger.error(f"Error with method 4: {e}")
        return False

if __name__ == "__main__":
    # Parse arguments
    args = sys.argv[1:]
    force_refresh = False
    color_arg = None
    
    # Process arguments
    for arg in args:
        if arg == '--force-refresh':
            force_refresh = True
            logger.info("Force refresh enabled")
        elif not arg.startswith('--'):
            color_arg = arg
    
    # Update wallpaper folder
    if color_arg:
        success, changed, prev_color = update_wallpaper_folder(color_arg)
    else:
        # Otherwise determine color from weekly habit count
        success, changed, prev_color = update_wallpaper_folder()
    
    # Refresh Plasma shell if directory changed or force refresh is enabled
    if success and (changed or force_refresh):
        # Get current color for notification
        weekly_count = get_weekly_habit_count()
        current_color = get_color_from_count(weekly_count)
        
        # Refresh Plasma shell
        refresh_plasma_shell()
        
        # Print success message
        # Use color_arg if provided, otherwise use the color determined by weekly habit count
        actual_color = color_arg if color_arg else get_color_from_count(weekly_count)
        
        if prev_color and prev_color != actual_color:
            print(f"Wallpaper color changed from {prev_color} to {actual_color}")
            print(f"Weekly habit average: {weekly_count:.1f}")
        else:
            print(f"Wallpaper directory updated with {actual_color} images")
            print(f"Weekly habit average: {weekly_count:.1f}")