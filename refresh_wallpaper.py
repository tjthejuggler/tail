#!/usr/bin/env python3

import os
import sys
import json
import shutil
import subprocess
import logging
import time
import glob
import random
from pathlib import Path
from datetime import datetime, timedelta
import importlib.util

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the color order (same as in the color control panel)
COLOR_ORDER = ["red", "orange", "green", "blue", "pink", "yellow", "white_gray_black"]

BASE_DIR = "/home/twain/Pictures"
TARGET_DIR = os.path.join(BASE_DIR, "llm_baby_monster")
CONFIG_PATH = "/home/twain/Projects/tail/wallpaper_color_manager_new/config.json"
CURRENT_COLOR_FILE = "/home/twain/Projects/tail/current_wallpaper_color.txt"
LBM_DIRS_PATH = "/home/twain/Pictures/lbm_dirs"

def load_favorites_module():
    """Dynamically load the wallpaper_favorites module."""
    try:
        # Get the path to the wallpaper_favorites.py script
        favorites_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "wallpaper_slideshow", "wallpaper_favorites.py")
        
        # Check if the script exists
        if not os.path.exists(favorites_path):
            logger.error(f"Wallpaper favorites script not found: {favorites_path}")
            return None
        
        # Load the module
        spec = importlib.util.spec_from_file_location("wallpaper_favorites", favorites_path)
        favorites_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(favorites_module)
        
        return favorites_module
    except Exception as e:
        logger.error(f"Error loading wallpaper favorites module: {e}")
        return None

def create_symlinks_from_favorites():
    """Create symlinks in the target directory for all favorite wallpapers."""
    logger.info("Creating symlinks from favorite wallpapers")
    try:
        # Load the favorites module
        favorites_module = load_favorites_module()
        if not favorites_module:
            return False
        
        # Create symlinks from favorites
        return favorites_module.create_symlinks_from_favorites(TARGET_DIR)
    except Exception as e:
        logger.error(f"Error creating symlinks from favorites: {e}")
        return False

def load_config():
    """Load configuration from file."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None

def get_weekly_habit_count():
    """Get the weekly habit count from the file."""
    try:
        with open("/home/twain/noteVault/habitCounters/week_average.txt", 'r') as f:
            return float(f.read().strip())
    except Exception as e:
        logger.error(f"Error reading weekly habit count: {e}")
        return 0

def get_color_from_count(count):
    """Determine color based on habit count."""
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
    else:
        return "white_gray_black"

def get_current_color():
    """Get the current wallpaper color from file."""
    try:
        if os.path.exists(CURRENT_COLOR_FILE):
            with open(CURRENT_COLOR_FILE, 'r') as f:
                return f.read().strip()
        return None
    except Exception as e:
        logger.error(f"Error reading current color: {e}")
        return None

def save_current_color(color):
    """Save the current wallpaper color to file."""
    try:
        with open(CURRENT_COLOR_FILE, 'w') as f:
            f.write(color)
        return True
    except Exception as e:
        logger.error(f"Error saving current color: {e}")
        return False

def clear_target_directory():
    """Clear all symlinks from the target directory."""
    logger.info(f"Clearing target directory: {TARGET_DIR}")
    try:
        # Ensure target directory exists
        os.makedirs(TARGET_DIR, exist_ok=True)
        
        # Remove all symlinks in the target directory
        count = 0
        for item in os.listdir(TARGET_DIR):
            item_path = os.path.join(TARGET_DIR, item)
            if os.path.islink(item_path):
                os.unlink(item_path)
                count += 1
        
        logger.info(f"Removed {count} symlinks from target directory")
        return True
    except Exception as e:
        logger.error(f"Error clearing target directory: {e}")
        return False

def create_symlinks_from_folder(source_folder):
    """Create symlinks in the target directory for all images in the source folder."""
    logger.info(f"refresh_wallpaper.py: create_symlinks_from_folder: Received source_folder: {source_folder}") # ADDED LOG
    try:
        # Ensure target directory exists
        os.makedirs(TARGET_DIR, exist_ok=True)
        
        # Get all image files in the source folder
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(source_folder, f"*{ext}")))
            image_files.extend(glob.glob(os.path.join(source_folder, f"*{ext.upper()}")))
        
        logger.info(f"refresh_wallpaper.py: create_symlinks_from_folder: Found {len(image_files)} images in {source_folder}") # ADDED LOG
        # Create symlinks for each image file
        count = 0
        for image_path in image_files:
            filename = os.path.basename(image_path)
            symlink_path = os.path.join(TARGET_DIR, filename)
            logger.info(f"refresh_wallpaper.py: create_symlinks_from_folder: Linking '{image_path}' to '{symlink_path}'") # ADDED LOG
            
            # Create symlink if it doesn't exist
            if not os.path.exists(symlink_path):
                os.symlink(image_path, symlink_path)
                count += 1
        
        logger.info(f"Created {count} symlinks in target directory")
        return count > 0
    except Exception as e:
        logger.error(f"Error creating symlinks: {e}")
        return False

def create_symlinks_from_color_folder(color):
    """Create symlinks in the target directory for all images in the color folder."""
    logger.info(f"Creating symlinks for color: {color}")
    try:
        config = load_config()
        if not config:
            return False
        
        # Get color directory path
        color_dir = os.path.join(BASE_DIR, config["paths"]["color_dirs"][color])
        
        # Create symlinks from the color directory
        return create_symlinks_from_folder(color_dir)
    except Exception as e:
        logger.error(f"Error creating symlinks for color {color}: {e}")
        return False

def create_symlinks_from_multiple_colors(colors):
    """Create symlinks in the target directory for all images in multiple color folders."""
    logger.info(f"Creating symlinks for multiple colors: {colors}")
    try:
        success = True
        total_count = 0
        
        for color in colors:
            logger.info(f"Processing color: {color}")
            config = load_config()
            if not config:
                return False
            
            # Get color directory path
            color_dir = os.path.join(BASE_DIR, config["paths"]["color_dirs"][color])
            
            # Get all image files in the color folder
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            image_files = []
            
            for ext in image_extensions:
                image_files.extend(glob.glob(os.path.join(color_dir, f"*{ext}")))
                image_files.extend(glob.glob(os.path.join(color_dir, f"*{ext.upper()}")))
            
            # Create symlinks for each image file
            count = 0
            for image_path in image_files:
                filename = os.path.basename(image_path)
                symlink_path = os.path.join(TARGET_DIR, filename)
                
                # Create symlink if it doesn't exist
                if not os.path.exists(symlink_path):
                    os.symlink(image_path, symlink_path)
                    count += 1
            
            logger.info(f"Created {count} symlinks from color {color}")
            total_count += count
            
            # If we couldn't create any symlinks for this color, log a warning
            if count == 0:
                logger.warning(f"No images found in color directory: {color_dir}")
        
        logger.info(f"Created a total of {total_count} symlinks from {len(colors)} colors")
        return total_count > 0
    except Exception as e:
        logger.error(f"Error creating symlinks for multiple colors: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def parse_folder_date(folder_name):
    """
    Parse a folder name in the format 'lbm-M-D-YY' to extract the date.
    Also handles other common date formats in folder names.
    """
    logger.info(f"Attempting to parse date from folder name: '{folder_name}'")
    try:
        # Split by '-' to handle variable-length month and day parts
        parts = folder_name.split('-')
        logger.info(f"Split parts: {parts}")
        
        # Check if we have the expected format (lbm-M-D-YY)
        if len(parts) >= 3:  # More flexible format checking
            # Try to extract date parts based on different patterns
            
            # Pattern: lbm-M-D-YY
            if len(parts) == 4 and parts[0] == 'lbm':
                logger.info(f"Matched pattern: lbm-M-D-YY")
                month_part, day_part, year_part = parts[1], parts[2], parts[3]
            # Pattern: M-D-YY (without prefix)
            elif len(parts) == 3 and all(p.isdigit() for p in parts):
                logger.info(f"Matched pattern: M-D-YY")
                month_part, day_part, year_part = parts[0], parts[1], parts[2]
            # Pattern: YYYY-MM-DD
            elif len(parts) == 3 and len(parts[0]) == 4 and parts[0].isdigit():
                logger.info(f"Matched pattern: YYYY-MM-DD")
                year_part, month_part, day_part = parts[0], parts[1], parts[2]
                # Convert 4-digit year to 2-digit for consistency
                year_part = year_part[2:]
            else:
                # Try to find any sequence of 3 numbers that could be a date
                digit_parts = [p for p in parts if p.isdigit()]
                logger.info(f"Looking for digit parts, found: {digit_parts}")
                if len(digit_parts) >= 3:
                    logger.info(f"Using digit parts as date components")
                    month_part, day_part, year_part = digit_parts[0], digit_parts[1], digit_parts[2]
                else:
                    logger.info(f"No recognizable date pattern in folder name: {folder_name}")
                    return None
            
            # Validate parts are numeric
            if not month_part.isdigit() or not day_part.isdigit() or not year_part.isdigit():
                logger.debug(f"Non-numeric date parts in folder name: {folder_name}")
                return None
                
            month = int(month_part)
            day = int(day_part)
            year = int(year_part)
            
            # Basic validation
            if month < 1 or month > 12:
                logger.debug(f"Invalid month ({month}) in folder name: {folder_name}")
                return None
                
            if day < 1 or day > 31:
                logger.debug(f"Invalid day ({day}) in folder name: {folder_name}")
                return None
            
            # Assume 2-digit year format (e.g., 25 -> 2025)
            if year < 100:
                year += 2000
            
            # Create date object with additional validation
            try:
                date_obj = datetime(year, month, day).date()
                logger.info(f"Successfully parsed date {date_obj} from folder {folder_name}")
                return date_obj
            except ValueError as e:
                # This catches invalid dates like February 30
                logger.debug(f"Invalid date combination in folder name: {folder_name}, error: {e}")
                return None
                
    except Exception as e:
        logger.debug(f"Error parsing date from folder name {folder_name}: {e}")
    
    return None

def get_recent_folders(days_back=7):
    """Get folders that have dates within the specified number of days from today."""
    logger.info(f"Getting folders from the last {days_back} days")
    try:
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=days_back)
        logger.info(f"Today's date: {today}, cutoff date: {cutoff_date}")
        logger.info(f"LBM_DIRS_PATH is set to: {LBM_DIRS_PATH}")
        
        # Get all subdirectories in the lbm_dirs path
        folders = []
        
        # Check if lbm_dirs path exists
        if not os.path.exists(LBM_DIRS_PATH):
            logger.error(f"LBM directories path does not exist: {LBM_DIRS_PATH}")
            # Try to find any directory with "lbm" in the name as a fallback
            base_pictures_dir = os.path.dirname(LBM_DIRS_PATH)
            logger.info(f"Base pictures directory: {base_pictures_dir}")
            if os.path.exists(base_pictures_dir):
                logger.info(f"Trying to find alternative directories in {base_pictures_dir}")
                for item in os.listdir(base_pictures_dir):
                    if "lbm" in item.lower() and os.path.isdir(os.path.join(base_pictures_dir, item)):
                        logger.info(f"Found alternative LBM directory: {item}")
                        return [os.path.join(base_pictures_dir, item)]
            return []
        
        # Get all items in the directory
        all_items = os.listdir(LBM_DIRS_PATH)
        logger.info(f"Found {len(all_items)} items in {LBM_DIRS_PATH}")
        
        # Log all folder names for debugging
        logger.info(f"All folder names: {', '.join(all_items)}")
        
        # First pass: Try to find folders with dates in their names
        for item in all_items:
            full_path = os.path.join(LBM_DIRS_PATH, item)
            
            # Check if it's a directory
            if os.path.isdir(full_path):
                logger.info(f"Processing directory: {item}")
                # Parse date from folder name
                folder_date = parse_folder_date(item)
                if folder_date:
                    logger.info(f"Folder {item} has date {folder_date}")
                    if folder_date >= cutoff_date:
                        logger.info(f"Folder {item} with date {folder_date} is within range (>= {cutoff_date})")
                        folders.append((full_path, folder_date))
                    else:
                        logger.info(f"Folder {item} with date {folder_date} is too old (< {cutoff_date})")
                else:
                    logger.info(f"Could not parse date from folder {item}")
        
        # If no folders with dates found, try to use folder modification times as a fallback
        if not folders:
            logger.info("No folders with date in name found, trying modification times")
            for item in all_items:
                full_path = os.path.join(LBM_DIRS_PATH, item)
                
                if os.path.isdir(full_path):
                    try:
                        # Get folder modification time
                        mod_time = os.path.getmtime(full_path)
                        mod_date = datetime.fromtimestamp(mod_time).date()
                        
                        logger.info(f"Folder {item} has modification date {mod_date}")
                        if mod_date >= cutoff_date:
                            logger.info(f"Folder {item} with mod date {mod_date} is within range (>= {cutoff_date})")
                            folders.append((full_path, mod_date))
                        else:
                            logger.info(f"Folder {item} with mod date {mod_date} is too old (< {cutoff_date})")
                    except Exception as e:
                        logger.error(f"Error getting modification time for {item}: {e}")
        
        # If still no folders found, just use all directories as a last resort
        if not folders and days_back > 365:  # Only for "all time" queries
            logger.info("No folders with dates found, using all directories")
            for item in all_items:
                full_path = os.path.join(LBM_DIRS_PATH, item)
                if os.path.isdir(full_path):
                    # Use current date as a placeholder
                    folders.append((full_path, today))
        
        # Sort by date (most recent first)
        folders.sort(key=lambda x: x[1], reverse=True)
        
        # Log the sorted folders
        if folders:
            logger.info("Sorted folders by date (most recent first):")
            for i, (path, date) in enumerate(folders):
                logger.info(f"  {i+1}. {os.path.basename(path)} - {date}")
        else:
            logger.warning("No folders with valid dates found within range")
        
        # Return just the paths
        return [folder[0] for folder in folders]
    except Exception as e:
        logger.error(f"Error getting recent folders: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def create_symlinks_from_recent_folders(days_back=7):
    """Create symlinks from folders with dates within the specified number of days."""
    logger.info(f"Creating symlinks from folders in the last {days_back} days")
    try:
        # Get recent folders
        recent_folders = get_recent_folders(days_back)
        
        if not recent_folders:
            logger.warning(f"No folders found within the last {days_back} days")
            return False
        
        logger.info(f"Found {len(recent_folders)} folders within the last {days_back} days")
        
        # Create symlinks from each folder
        total_count = 0
        for folder_idx, folder in enumerate(recent_folders):
            logger.info(f"Processing folder {folder_idx + 1}/{len(recent_folders)}: {os.path.basename(folder)}")
            
            # Get all image files in the folder
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            image_files = []
            
            for ext in image_extensions:
                image_files.extend(glob.glob(os.path.join(folder, f"*{ext}")))
                image_files.extend(glob.glob(os.path.join(folder, f"*{ext.upper()}")))
            
            logger.info(f"Found {len(image_files)} images in folder {os.path.basename(folder)}")
            
            # Create symlinks for each image file
            folder_count = 0
            for image_path in image_files:
                filename = os.path.basename(image_path)
                symlink_path = os.path.join(TARGET_DIR, filename)
                
                # Create symlink if it doesn't exist
                if not os.path.exists(symlink_path):
                    os.symlink(image_path, symlink_path)
                    total_count += 1
                    folder_count += 1
                else:
                    # If symlink already exists, check if it points to the same file
                    try:
                        existing_target = os.readlink(symlink_path)
                        if existing_target != image_path:
                            # Different target, create a unique name
                            base_name, ext = os.path.splitext(filename)
                            counter = 1
                            while True:
                                new_filename = f"{base_name}_{counter}{ext}"
                                new_symlink_path = os.path.join(TARGET_DIR, new_filename)
                                if not os.path.exists(new_symlink_path):
                                    os.symlink(image_path, new_symlink_path)
                                    total_count += 1
                                    folder_count += 1
                                    break
                                counter += 1
                    except OSError:
                        # Error reading symlink, skip this file
                        logger.warning(f"Could not read existing symlink: {symlink_path}")
            
            logger.info(f"Created {folder_count} symlinks from folder {os.path.basename(folder)}")
        
        logger.info(f"Created a total of {total_count} symlinks from {len(recent_folders)} folders")
        return total_count > 0
    except Exception as e:
        logger.error(f"Error creating symlinks from recent folders: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def update_wallpaper_folder(color=None, latest_folder=None, days_back=None, source_colors_str=None, use_favorites=False):
    """
    Update the wallpaper folder with images from the specified source.
    
    Args:
        color: Color category to use (single color)
        latest_folder: Path to the latest folder to use
        days_back: Number of days to look back for folders
        source_colors_str: Comma-separated string of color names to use as sources
        use_favorites: Whether to use favorite wallpapers
        
    Returns:
        tuple: (success, changed, previous_color)
    """
    logger.info(f"Updating wallpaper folder: color={color}, latest_folder={latest_folder}, days_back={days_back}, source_colors_str={source_colors_str}, use_favorites={use_favorites}")
    
    prev_color = get_current_color()
    config = load_config()
    current_selection_primary_color = None # Used to determine if color 'changed'

    if source_colors_str:
        selected_colors = [c.strip() for c in source_colors_str.split(',') if c.strip()]
        if not selected_colors:
            logger.error("No valid colors provided in --source-colors argument.")
            return False, False, prev_color
        
        logger.info(f"Using --source-colors: {selected_colors}")
        if not clear_target_directory():
            return False, False, prev_color
        success = create_symlinks_from_multiple_colors(selected_colors)
        if success and selected_colors:
            current_selection_primary_color = selected_colors[0] # Use first color for 'changed' status
            save_current_color(current_selection_primary_color)
        return success, current_selection_primary_color != prev_color, prev_color

    # If no specific source is provided via arguments, check the config
    if not color and latest_folder is None and days_back is None and not use_favorites and config:
        wallpaper_source = config.get("wallpaper_source")
        logger.info(f"Using wallpaper source from config: {wallpaper_source}")
        
        # Check if wallpaper_source is "slideshow_favorites"
        if wallpaper_source == "slideshow_favorites":
            logger.info("Using slideshow favorites from config")
            use_favorites = True
        
        if wallpaper_source == "direct_color_selection" and "direct_color_selection" in config:
            selected_colors_cfg = config.get("direct_color_selection", [])
            if selected_colors_cfg:
                logger.info(f"Using direct color selection from config with colors: {selected_colors_cfg}")
                if not clear_target_directory(): return False, False, prev_color
                success = create_symlinks_from_multiple_colors(selected_colors_cfg)
                if success:
                    current_selection_primary_color = selected_colors_cfg[0]
                    save_current_color(current_selection_primary_color)
                return success, current_selection_primary_color != prev_color, prev_color
            else:
                logger.warning("No colors selected in direct_color_selection (config)")
        elif wallpaper_source == "latest_by_date":
            days_setting = config.get("latest_by_date_settings", {}).get("days_back", 7)
            days_back = days_setting # This will be handled by the days_back logic below
            logger.info(f"Config: Using latest by date with days_back={days_back}")
        elif wallpaper_source == "latest":
            latest_folder = get_most_recent_folder() # This will be handled by latest_folder logic
            if latest_folder:
                logger.info(f"Config: Using most recent folder: {latest_folder}")
            else: # Fallback if no recent folder found
                logger.warning("Config: No recent folders found, falling back to weekly habits")
                weekly_count = get_weekly_habit_count()
                color = get_color_from_count(weekly_count)
                current_selection_primary_color = color
        elif wallpaper_source == "weekly_habits_inclusive":
            weekly_count = get_weekly_habit_count()
            habit_color = get_color_from_count(weekly_count)
            logger.info(f"Config: Using weekly habits inclusive with habit color: {habit_color}")
            if habit_color in COLOR_ORDER:
                index = COLOR_ORDER.index(habit_color)
                inclusive_colors = COLOR_ORDER[:index+1]
                logger.info(f"Config: Using inclusive colors: {inclusive_colors}")
                if not clear_target_directory(): return False, False, prev_color
                success = create_symlinks_from_multiple_colors(inclusive_colors)
                if success:
                    current_selection_primary_color = habit_color
                    save_current_color(current_selection_primary_color)
                return success, current_selection_primary_color != prev_color, prev_color
            else: # Fallback
                color = habit_color
                current_selection_primary_color = color
                logger.info(f"Config: Habit color not in order, using single color: {color}")
        elif wallpaper_source == "weekly_habits": # Default/fallback if other specific config options don't set color/latest_folder/days_back
            weekly_count = get_weekly_habit_count()
            color = get_color_from_count(weekly_count)
            current_selection_primary_color = color
            logger.info(f"Config: Using weekly habits with color: {color}")
        else: # True fallback if wallpaper_source is unrecognized
            weekly_count = get_weekly_habit_count()
            color = get_color_from_count(weekly_count)
            current_selection_primary_color = color
            logger.info(f"Config: Unrecognized source '{wallpaper_source}', falling back to weekly habits: {color}")

    # If color is still not set (e.g. only days_back or latest_folder was set from config, or no config path hit)
    if not color and not latest_folder and days_back is None and source_colors_str is None:
        weekly_count = get_weekly_habit_count()
        color = get_color_from_count(weekly_count)
        current_selection_primary_color = color
        logger.info(f"No specific source determined, falling back to weekly habits: {color}")
    elif color: # If color was set by an earlier fallback or directly
        current_selection_primary_color = color

    # Clear the target directory first (if not already cleared by multi-color paths)
    # Only check wallpaper_source if config was loaded and it exists in config
    if not source_colors_str and not (config and "wallpaper_source" in config and
                                     ((config["wallpaper_source"] == "direct_color_selection" and "direct_color_selection" in config and config["direct_color_selection"]) or
                                      (config["wallpaper_source"] == "weekly_habits_inclusive" and "habit_color" in locals() and habit_color in COLOR_ORDER))):
        if not clear_target_directory():
            return False, False, prev_color
    
    # Update based on the determined source
    if use_favorites:
        # Clear the target directory first
        if not clear_target_directory():
            return False, False, prev_color
        
        # Create symlinks from favorites
        success = create_symlinks_from_favorites()
        
        # Save "favorites" as the current color
        if success:
            save_current_color("favorites")
        
        return success, "favorites" != prev_color, prev_color
    elif latest_folder:
        success = create_symlinks_from_folder(latest_folder)
        # For latest_folder, we don't have a specific 'color' to save, so don't update current_color.txt
        # The 'changed' status will depend on whether TARGET_DIR content actually changed, which is hard to track here.
        # We'll assume it changed if successful.
        return success, True if success else False, prev_color
    elif days_back is not None:
        success = create_symlinks_from_recent_folders(days_back)
        # Similar to latest_folder, no specific color to save.
        return success, True if success else False, prev_color
    elif color: # This handles single color cases
        success = create_symlinks_from_color_folder(color)
        if success and current_selection_primary_color and current_selection_primary_color != prev_color:
            save_current_color(current_selection_primary_color)
        return success, current_selection_primary_color != prev_color if current_selection_primary_color else False, prev_color
    
    # Fallback if no specific action was taken (should ideally not be reached if logic is correct)
    logger.warning("No specific update action taken in update_wallpaper_folder.")
    return False, False, prev_color

def get_most_recent_folder():
    """Get the most recent folder based on date in folder name or modification time."""
    logger.info("Getting the most recent folder by date")
    try:
        # Get all folders with dates (using a large days_back value to include all)
        logger.info("Calling get_recent_folders with days_back=36500 (100 years)")
        folders = get_recent_folders(days_back=36500)  # ~100 years
        logger.info(f"get_recent_folders returned {len(folders)} folders")
        
        if not folders:
            logger.warning("No folders with valid dates found")
            
            # Fallback: Try to find any directory with images in the Pictures directory
            pictures_dir = os.path.expanduser("~/Pictures")
            if os.path.exists(pictures_dir):
                logger.info(f"Trying to find any directory with images in {pictures_dir}")
                
                # Get all subdirectories in Pictures
                potential_folders = []
                for item in os.listdir(pictures_dir):
                    full_path = os.path.join(pictures_dir, item)
                    if os.path.isdir(full_path):
                        # Check if directory contains images
                        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                        has_images = False
                        for ext in image_extensions:
                            if glob.glob(os.path.join(full_path, f"*{ext}")) or glob.glob(os.path.join(full_path, f"*{ext.upper()}")):
                                has_images = True
                                break
                        
                        if has_images:
                            # Get folder modification time
                            mod_time = os.path.getmtime(full_path)
                            potential_folders.append((full_path, mod_time))
                
                if potential_folders:
                    # Sort by modification time (most recent first)
                    potential_folders.sort(key=lambda x: x[1], reverse=True)
                    most_recent = potential_folders[0][0]
                    logger.info(f"Found directory with images: {most_recent}")
                    return most_recent
            
            # If still no folders found, try the TARGET_DIR itself
            if os.path.exists(TARGET_DIR) and os.path.isdir(TARGET_DIR):
                logger.info(f"Using TARGET_DIR as fallback: {TARGET_DIR}")
                return TARGET_DIR
                
            return None
        
        # The first folder is the most recent (already sorted in get_recent_folders)
        most_recent = folders[0]
        logger.info(f"Most recent folder: {most_recent}")
        return most_recent
    except Exception as e:
        logger.error(f"Error getting most recent folder: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Last resort fallback
        if os.path.exists(TARGET_DIR) and os.path.isdir(TARGET_DIR):
            logger.info(f"Using TARGET_DIR as emergency fallback after error: {TARGET_DIR}")
            return TARGET_DIR
            
        return None

def set_wallpaper_with_slideshow(image_path=None):
    """
    Set the wallpaper using the wallpaper_slideshow/set_specific_wallpaper.py script.
    If image_path is None, it will use a random image from the target directory.
    
    Args:
        image_path: Path to the image to set as wallpaper
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Setting wallpaper with slideshow script: {image_path}")
    try:
        # If no specific image is provided, choose a random one from the target directory
        if image_path is None:
            # Get all image files in the target directory
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            image_files = []
            
            for ext in image_extensions:
                image_files.extend(glob.glob(os.path.join(TARGET_DIR, f"*{ext}")))
                image_files.extend(glob.glob(os.path.join(TARGET_DIR, f"*{ext.upper()}")))
            
            if not image_files:
                logger.error("No image files found in target directory")
                return False
            
            # Choose a random image
            image_path = random.choice(image_files)
            logger.info(f"Randomly selected image: {image_path}")
        
        # Get the absolute path to the set_specific_wallpaper.py script
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "wallpaper_slideshow", "set_specific_wallpaper.py")
        
        # Check if the script exists
        if not os.path.exists(script_path):
            logger.error(f"Wallpaper script not found: {script_path}")
            return False
        
        # Run the script with the image path
        logger.info(f"Running: python3 {script_path} {image_path}")
        result = subprocess.run(
            ["python3", script_path, image_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            logger.error(f"Error setting wallpaper: {result.stderr}")
            return False
        
        logger.info("Wallpaper set successfully using slideshow script")
        return True
    except Exception as e:
        logger.error(f"Error setting wallpaper with slideshow script: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def start_wallpaper_slideshow():
    """
    Start the wallpaper slideshow using the custom_wallpaper.py script.
    This will automatically change wallpapers at the interval specified in config.ini.
    
    Returns:
        bool: True if slideshow started successfully, False otherwise
    """
    logger.info("Starting wallpaper slideshow")
    try:
        # First, check if a slideshow is already running by checking the PID file
        pid_file = os.path.expanduser("~/.config/custom_wallpaper_slideshow.pid")
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                # Check if process is still running
                try:
                    os.kill(pid, 0)  # Signal 0 is used to check if process exists
                    logger.info(f"Slideshow already running with PID {pid}")
                    return True
                except OSError:
                    # Process not running, remove stale PID file
                    logger.info(f"Removing stale PID file for non-existent process {pid}")
                    os.remove(pid_file)
            except (ValueError, IOError) as e:
                logger.error(f"Error checking existing slideshow: {e}")
                # Continue with starting a new slideshow
        
        # Get the absolute path to the custom_wallpaper.py script
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "wallpaper_slideshow", "custom_wallpaper.py")
        
        # Check if the script exists
        if not os.path.exists(script_path):
            logger.error(f"Slideshow script not found: {script_path}")
            return False
        
        # Update the config.ini file to use TARGET_DIR as the image directory
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "wallpaper_slideshow", "config.ini")
        
        # Create or update config.ini
        config = configparser.ConfigParser()
        if os.path.exists(config_path):
            config.read(config_path)
        
        # Ensure sections exist
        if 'General' not in config:
            config['General'] = {}
        
        # Set image directory to TARGET_DIR and interval to 15 seconds
        config['General']['image_directory'] = TARGET_DIR
        config['General']['interval'] = '15'  # 15 seconds
        config['General']['shuffle'] = 'true'
        
        # Save the config
        with open(config_path, 'w') as f:
            config.write(f)
        
        logger.info(f"Updated slideshow config to use directory: {TARGET_DIR}")
        
        # Start the slideshow in the background
        logger.info(f"Starting slideshow: python3 {script_path}")
        process = subprocess.Popen(
            ["python3", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # Detach from parent process
        )
        
        # Wait a moment to see if the process starts successfully
        time.sleep(1)
        if process.poll() is None:  # None means process is still running
            logger.info("Slideshow started successfully")
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Slideshow failed to start: {stderr.decode('utf-8')}")
            return False
    except Exception as e:
        logger.error(f"Error starting wallpaper slideshow: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def refresh_plasma_shell():
    """Refresh KDE Plasma shell without freezing the Python script."""
    logger.info("Refreshing KDE Plasma shell...")
    try:
        # First try starting the wallpaper slideshow
        if start_wallpaper_slideshow():
            logger.info("Wallpaper slideshow started successfully")
            return True
        
        # If slideshow fails, try setting a single wallpaper
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "wallpaper_slideshow", "set_specific_wallpaper.py")
        
        if os.path.exists(script_path):
            # Set a random wallpaper from the target directory
            if set_wallpaper_with_slideshow():
                logger.info("Plasma shell refreshed using wallpaper slideshow script")
                return True
        
        # Fallback to the old method if both approaches fail
        logger.warning("Falling back to plasmashell --replace method")
        subprocess.Popen(
            ['nohup', 'plasmashell', '--replace'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setpgrp
        )
        logger.info("Plasma shell refresh command executed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error refreshing plasma shell: {e}")
        return False


if __name__ == "__main__":
    args = sys.argv[1:]
    force_refresh = '--force-refresh' in args
    skip_refresh = '--no-refresh' in args
    most_recent_only = '--most-recent-only' in args
    use_favorites = '--use-favorites' in args
    source_colors_arg = None

    latest_folder = None
    color_arg = None
    days_back = None

    # New argument parsing for --source-colors
    if '--source-colors' in args:
        try:
            idx = args.index('--source-colors')
            if len(args) > idx + 1:
                source_colors_arg = args[idx + 1]
                logger.info(f"CLI arg --source-colors provided: {source_colors_arg}")
        except ValueError: # Should not happen if '--source-colors' is in args
            pass
            
    if '--latest-folder' in args:
        try:
            idx = args.index('--latest-folder')
            if len(args) > idx + 1:
                latest_folder = args[idx + 1]
        except ValueError:
            pass
    
    if '--days-back' in args:
        try:
            idx = args.index('--days-back')
            if len(args) > idx + 1:
                try:
                    days_back = int(args[idx + 1])
                except ValueError:
                    logger.error(f"Invalid days_back value: {args[idx + 1]}")
        except ValueError:
            pass
            
    if most_recent_only: # This implies --days-back should be ignored if latest_folder is found
        latest_folder_temp = get_most_recent_folder()
        if not latest_folder_temp:
            # Instead of failing, use a hardcoded fallback directory
            logger.warning("No folders with valid date format found for --most-recent-only, using fallback")
            
            # Try some common directories
            fallback_dirs = [
                os.path.join(BASE_DIR, "llm_baby_monster"),  # TARGET_DIR
                os.path.join(BASE_DIR, "Wallpapers"),
                os.path.expanduser("~/Pictures/Wallpapers"),
                os.path.expanduser("~/Pictures")
            ]
            
            for fallback_dir in fallback_dirs:
                if os.path.exists(fallback_dir) and os.path.isdir(fallback_dir):
                    # Check if directory contains images
                    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                    has_images = False
                    for ext in image_extensions:
                        if glob.glob(os.path.join(fallback_dir, f"*{ext}")) or glob.glob(os.path.join(fallback_dir, f"*{ext.upper()}")):
                            has_images = True
                            break
                    
                    if has_images:
                        latest_folder_temp = fallback_dir
                        logger.info(f"Using fallback directory with images: {fallback_dir}")
                        break
            
            if not latest_folder_temp:
                # Last resort: Use the TARGET_DIR itself if it exists and has images
                if os.path.exists(TARGET_DIR) and os.path.isdir(TARGET_DIR):
                    # Check if TARGET_DIR contains images
                    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                    has_images = False
                    for ext in image_extensions:
                        if glob.glob(os.path.join(TARGET_DIR, f"*{ext}")) or glob.glob(os.path.join(TARGET_DIR, f"*{ext.upper()}")):
                            has_images = True
                            break
                    
                    if has_images:
                        latest_folder_temp = TARGET_DIR
                        logger.info(f"Using TARGET_DIR as last resort: {TARGET_DIR}")
                
            if not latest_folder_temp:
                print("No suitable fallback directory found. Please check your image directories.")
                sys.exit(1)
                
        latest_folder = latest_folder_temp # Override if found
        days_back = None # Ensure days_back is not used if most_recent_only finds a folder
        logger.info(f"Using most recent folder (due to --most-recent-only): {latest_folder}")

    # Positional argument for single color (if not using other specific args)
    if not source_colors_arg and not latest_folder and days_back is None:
        for arg_idx, arg_val in enumerate(args):
            is_option_value = False
            if arg_idx > 0: # Check if it's a value for a preceding option
                if args[arg_idx-1] in ['--latest-folder', '--days-back', '--source-colors']:
                    is_option_value = True
            if not arg_val.startswith('--') and not is_option_value:
                color_arg = arg_val
                break
                
    success, changed, prev_color = update_wallpaper_folder(color_arg, latest_folder, days_back, source_colors_str=source_colors_arg, use_favorites=use_favorites)

    weekly_count = get_weekly_habit_count()
    current_color = get_color_from_count(weekly_count)

    if success and (changed or force_refresh) and not skip_refresh:
        refresh_plasma_shell()
    elif skip_refresh:
        logger.info("Plasma shell refresh skipped (--no-refresh).")

    if success:
        actual_color = color_arg or current_color
        if use_favorites:
            print(f"Wallpaper directory updated with favorite images")
        elif latest_folder:
            print(f"Wallpaper directory updated with images from: {os.path.basename(latest_folder)}")
        elif days_back is not None:
            print(f"Wallpaper directory updated with images from the last {days_back} days")
        elif prev_color != actual_color:
            print(f"Wallpaper color changed from {prev_color} to {actual_color}")
            print(f"Weekly habit average: {weekly_count:.1f}")
        else:
            print(f"Wallpaper directory updated with {actual_color} images")
            print(f"Weekly habit average: {weekly_count:.1f}")
    else:
        print("Failed to update wallpaper directory")
