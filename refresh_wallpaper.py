#!/usr/bin/env python3

import os
import sys
import json
import shutil
import subprocess
import logging
import time
import glob
from pathlib import Path
from datetime import datetime, timedelta

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
    """Parse a folder name in the format 'lbm-M-D-YY' to extract the date."""
    try:
        # Split by '-' to handle variable-length month and day parts
        parts = folder_name.split('-')
        
        # Check if we have the expected format (lbm-M-D-YY)
        if len(parts) == 4 and parts[0] == 'lbm':
            # Validate each part is a number
            if not parts[1].isdigit() or not parts[2].isdigit() or not parts[3].isdigit():
                logger.warning(f"Non-numeric date parts in folder name: {folder_name}")
                return None
                
            month = int(parts[1])
            day = int(parts[2])
            year = int(parts[3])
            
            # Basic validation
            if month < 1 or month > 12:
                logger.warning(f"Invalid month ({month}) in folder name: {folder_name}")
                return None
                
            if day < 1 or day > 31:
                logger.warning(f"Invalid day ({day}) in folder name: {folder_name}")
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
                logger.warning(f"Invalid date combination in folder name: {folder_name}, error: {e}")
                return None
                
    except Exception as e:
        logger.error(f"Error parsing date from folder name {folder_name}: {e}")
    
    return None

def get_recent_folders(days_back=7):
    """Get folders that have dates within the specified number of days from today."""
    logger.info(f"Getting folders from the last {days_back} days")
    try:
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=days_back)
        logger.info(f"Today's date: {today}, cutoff date: {cutoff_date}")
        
        # Get all subdirectories in the lbm_dirs path
        folders = []
        
        # Check if lbm_dirs path exists
        if not os.path.exists(LBM_DIRS_PATH):
            logger.error(f"LBM directories path does not exist: {LBM_DIRS_PATH}")
            return []
        
        # Get all items in the directory
        all_items = os.listdir(LBM_DIRS_PATH)
        logger.info(f"Found {len(all_items)} items in {LBM_DIRS_PATH}")
        
        # Log all folder names for debugging
        logger.info(f"All folder names: {', '.join(all_items)}")
        
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
        
        # Create symlinks from each folder
        total_count = 0
        for folder in recent_folders:
            # Get all image files in the folder
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            image_files = []
            
            for ext in image_extensions:
                image_files.extend(glob.glob(os.path.join(folder, f"*{ext}")))
                image_files.extend(glob.glob(os.path.join(folder, f"*{ext.upper()}")))
            
            # Create symlinks for each image file
            for image_path in image_files:
                filename = os.path.basename(image_path)
                symlink_path = os.path.join(TARGET_DIR, filename)
                
                # Create symlink if it doesn't exist
                if not os.path.exists(symlink_path):
                    os.symlink(image_path, symlink_path)
                    total_count += 1
        
        logger.info(f"Created {total_count} symlinks from {len(recent_folders)} folders")
        return total_count > 0
    except Exception as e:
        logger.error(f"Error creating symlinks from recent folders: {e}")
        return False

def update_wallpaper_folder(color=None, latest_folder=None, days_back=None, source_colors_str=None):
    """
    Update the wallpaper folder with images from the specified source.
    
    Args:
        color: Color category to use (single color)
        latest_folder: Path to the latest folder to use
        days_back: Number of days to look back for folders
        source_colors_str: Comma-separated string of color names to use as sources
        
    Returns:
        tuple: (success, changed, previous_color)
    """
    logger.info(f"Updating wallpaper folder: color={color}, latest_folder={latest_folder}, days_back={days_back}, source_colors_str={source_colors_str}")
    
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
    if not color and latest_folder is None and days_back is None and config:
        wallpaper_source = config.get("wallpaper_source")
        logger.info(f"Using wallpaper source from config: {wallpaper_source}")
        
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
    if not source_colors_str and not (wallpaper_source == "direct_color_selection" and selected_colors_cfg) and not (wallpaper_source == "weekly_habits_inclusive" and habit_color in COLOR_ORDER) :
        if not clear_target_directory():
            return False, False, prev_color
    
    # Update based on the determined source
    if latest_folder:
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
    """Get the most recent folder based on date in folder name."""
    logger.info("Getting the most recent folder by date")
    try:
        # Get all folders with dates (using a large days_back value to include all)
        folders = get_recent_folders(days_back=36500)  # ~100 years
        
        if not folders:
            logger.warning("No folders with valid dates found")
            return None
        
        # The first folder is the most recent (already sorted in get_recent_folders)
        most_recent = folders[0]
        logger.info(f"Most recent folder: {most_recent}")
        return most_recent
    except Exception as e:
        logger.error(f"Error getting most recent folder: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def refresh_plasma_shell():
    """Refresh KDE Plasma shell without freezing the Python script."""
    logger.info("Refreshing KDE Plasma shell...")
    try:
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
            print("No folders with valid date format found for --most-recent-only")
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
                
    success, changed, prev_color = update_wallpaper_folder(color_arg, latest_folder, days_back, source_colors_str=source_colors_arg)

    weekly_count = get_weekly_habit_count()
    current_color = get_color_from_count(weekly_count)

    if success and (changed or force_refresh) and not skip_refresh:
        refresh_plasma_shell()
    elif skip_refresh:
        logger.info("Plasma shell refresh skipped (--no-refresh).")

    if success:
        actual_color = color_arg or current_color
        if latest_folder:
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
