#!/usr/bin/env python3
"""
Update Wallpaper Folder

This script updates the /home/twain/Pictures/llm_baby_monster directory
with images from the appropriate color category based on the current
week's habit average.

Usage:
    python3 update_wallpaper_folder.py [color]

If color is not provided, it will be determined from the current weekly habit count.
"""

import os
import sys
import json
import shutil
import random
import logging
import subprocess
import time
from pathlib import Path

# Ensure log directory exists
log_dir = '/home/twain/logs'
os.makedirs(log_dir, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, 'update_wallpaper_folder.log'))
    ]
)
logger = logging.getLogger(__name__)

# Enable debug logging for troubleshooting
if '--debug' in sys.argv:
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled")

# Define paths
BASE_DIR = "/home/twain/Pictures"
TARGET_DIR = os.path.join(BASE_DIR, "llm_baby_monster")
COLOR_BASE_DIR = os.path.join(BASE_DIR, "llm_baby_monster_by_color")
CONFIG_PATH = "/home/twain/Projects/tail/wallpaper_color_manager_new/config.json"
CURRENT_COLOR_FILE = "/home/twain/Projects/tail/current_wallpaper_color.txt"

# Define color thresholds (same as in habits_kde_theme.py)
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
        return "white_gray_black"  # Using white_gray_black instead of transparent
    else:
        return "white_gray_black"  # Using white_gray_black instead of transparent

def send_notification(title, message):
    """Send a desktop notification"""
    try:
        subprocess.run(["notify-send", title, message])
        logger.info(f"Notification sent: {title} - {message}")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")

def refresh_kde_wallpaper():
    """
    Refresh the KDE wallpaper slideshow to recognize new images
    """
    try:
        logger.info("Refreshing KDE wallpaper slideshow...")
        
        # Find all relevant KDE configuration files
        home_dir = os.path.expanduser("~")
        config_files = [
            os.path.join(home_dir, ".config", "plasma-org.kde.plasma.desktop-appletsrc"),
            os.path.join(home_dir, ".config", "plasmarc"),
            os.path.join(home_dir, ".config", "kscreenlockerrc"),
            os.path.join(home_dir, ".config", "kwinrc")
        ]
        
        # Method 1: Create a new slideshow configuration file
        try:
            # Create a directory for our custom slideshow
            slideshow_dir = os.path.join(home_dir, ".local", "share", "plasma", "wallpapers", "customslideshow")
            os.makedirs(slideshow_dir, exist_ok=True)
            
            # Create a new slideshow configuration file
            slideshow_path = os.path.join(slideshow_dir, "customslideshow.slideshow")
            with open(slideshow_path, 'w') as f:
                f.write(f"[Slideshow]\n")
                f.write(f"SlidePaths={TARGET_DIR}\n")
                f.write(f"SlideInterval=10\n")
                f.write(f"RandomizeOrder=true\n")
                f.write(f"LastChange={int(time.time())}\n")
            
            logger.info(f"Created custom slideshow config: {slideshow_path}")
            
            # Also touch all config files to force reload
            for config_file in config_files:
                if os.path.exists(config_file):
                    # Backup the file
                    backup_path = config_file + ".bak"
                    shutil.copy2(config_file, backup_path)
                    
                    # Update the modification time
                    os.utime(config_file, None)
                    logger.info(f"Touched config file: {config_file}")
                    
            # Instead of directly modifying the file, use kwriteconfig5 to safely update it
            try:
                # Find all desktop containments
                containments_output = subprocess.check_output(
                    ["grep", "-n", "\\[Containments\\]", os.path.join(home_dir, ".config", "plasma-org.kde.plasma.desktop-appletsrc")]
                ).decode().strip()
                
                if containments_output:
                    logger.info("Found containments in plasma config")
                    
                    # Use a more targeted approach with kwriteconfig5
                    for i in range(1, 10):  # Try a few containment numbers
                        # Update the slideshow paths for each possible containment
                        subprocess.run([
                            "kwriteconfig5",
                            "--file", "plasma-org.kde.plasma.desktop-appletsrc",
                            "--group", f"Containments",
                            "--group", f"{i}",
                            "--group", "Wallpaper",
                            "--group", "org.kde.slideshow",
                            "--group", "General",
                            "--key", "SlidePaths",
                            TARGET_DIR
                        ], check=False)
                        
                        # Update the timestamp
                        subprocess.run([
                            "kwriteconfig5",
                            "--file", "plasma-org.kde.plasma.desktop-appletsrc",
                            "--group", f"Containments",
                            "--group", f"{i}",
                            "--group", "Wallpaper",
                            "--group", "org.kde.slideshow",
                            "--group", "General",
                            "--key", "LastChange",
                            str(int(time.time()))
                        ], check=False)
                    
                    logger.info("Updated plasma config using kwriteconfig5")
            except Exception as e:
                logger.warning(f"Failed to update plasma config: {e}")
        except Exception as e:
            logger.warning(f"Failed to create custom slideshow config: {e}")
        
        # Method 2: Use kwriteconfig5 to force wallpaper settings update
        try:
            # Force update wallpaper settings
            subprocess.run([
                "kwriteconfig5",
                "--file", "plasma-org.kde.plasma.desktop-appletsrc",
                "--group", "Containments",
                "--group", "1",
                "--group", "Wallpaper",
                "--group", "org.kde.slideshow",
                "--group", "General",
                "--key", "SlidePaths",
                TARGET_DIR
            ], check=False)
            
            # Also update the timestamp to force refresh
            subprocess.run([
                "kwriteconfig5",
                "--file", "plasma-org.kde.plasma.desktop-appletsrc",
                "--group", "Containments",
                "--group", "1",
                "--group", "Wallpaper",
                "--group", "org.kde.slideshow",
                "--group", "General",
                "--key", "LastChange",
                str(int(time.time()))
            ], check=False)
            
            logger.info("Updated wallpaper settings via kwriteconfig5")
        except Exception as e:
            logger.warning(f"Failed to update settings via kwriteconfig5: {e}")
        
        # Method 3: Try to use DBus to refresh the wallpaper (using org.kde.image plugin)
        try:
            # Use qdbus to refresh the wallpaper using the approach suggested by the user
            subprocess.run([
                "qdbus",
                "org.kde.plasmashell",
                "/PlasmaShell",
                "org.kde.PlasmaShell.evaluateScript",
                f"""
                var allDesktops = desktops();
                for (i=0; i<allDesktops.length; i++) {{
                    allDesktops[i].wallpaperPlugin = 'org.kde.image';
                    allDesktops[i].currentConfigGroup = ['Wallpaper', 'org.kde.image'];
                    allDesktops[i].writeConfig('Image', '{TARGET_DIR}');
                    allDesktops[i].reloadConfig();
                }}
                """
            ], check=False)
            logger.info("KDE wallpaper refreshed via DBus (org.kde.image plugin)")
        except Exception as e:
            logger.warning(f"Failed to refresh wallpaper via DBus (org.kde.image): {e}")
            
        # Method 3b: Try to use DBus to refresh the wallpaper (using org.kde.slideshow plugin)
        try:
            # Use qdbus to refresh the wallpaper
            subprocess.run([
                "qdbus",
                "org.kde.plasmashell",
                "/PlasmaShell",
                "org.kde.PlasmaShell.evaluateScript",
                f"""
                var allDesktops = desktops();
                for (i=0; i<allDesktops.length; i++) {{
                    d = allDesktops[i];
                    d.wallpaperPlugin = "org.kde.slideshow";
                    d.currentConfigGroup = Array("Wallpaper", "org.kde.slideshow", "General");
                    d.writeConfig("SlidePaths", "{TARGET_DIR}");
                    d.writeConfig("LastChange", Date.now());
                    d.reloadConfig();
                }}
                """
            ], check=False)
            logger.info("KDE wallpaper refreshed via DBus (org.kde.slideshow plugin)")
        except Exception as e:
            logger.warning(f"Failed to refresh wallpaper via DBus (org.kde.slideshow): {e}")
        
        # Method 4: Create a direct symlink to our directory in the KDE wallpaper folder
        try:
            # Create a symlink in the KDE wallpaper folder
            kde_wallpaper_dir = os.path.join(home_dir, ".local", "share", "wallpapers")
            os.makedirs(kde_wallpaper_dir, exist_ok=True)
            
            # Create a symlink to our target directory
            symlink_path = os.path.join(kde_wallpaper_dir, "llm_baby_monster")
            
            # Remove existing symlink if it exists
            if os.path.exists(symlink_path):
                if os.path.islink(symlink_path):
                    os.unlink(symlink_path)
                elif os.path.isdir(symlink_path):
                    shutil.rmtree(symlink_path)
            
            # Create the symlink
            os.symlink(TARGET_DIR, symlink_path)
            logger.info(f"Created symlink to target directory in KDE wallpaper folder: {symlink_path}")
            
            # Also create a metadata.desktop file to make it a valid KDE wallpaper
            metadata_dir = os.path.join(kde_wallpaper_dir, "llm_baby_monster")
            os.makedirs(metadata_dir, exist_ok=True)
            metadata_path = os.path.join(metadata_dir, "metadata.desktop")
            with open(metadata_path, 'w') as f:
                f.write("[Desktop Entry]\n")
                f.write("Name=LLM Baby Monster\n")
                f.write("X-KDE-PluginInfo-Name=llm_baby_monster\n")
                f.write("X-KDE-PluginInfo-Author=Wallpaper Color Manager\n")
                f.write("X-KDE-PluginInfo-License=CC-BY-SA\n")
                f.write("X-KDE-PluginInfo-Website=https://kde.org\n")
                f.write("\n")
                f.write("[Wallpaper]\n")
                f.write("defaultWallpaperTheme=llm_baby_monster\n")
                f.write("defaultFileSuffix=.jpg\n")
                f.write("defaultWidth=1920\n")
                f.write("defaultHeight=1080\n")
            
            logger.info(f"Created metadata.desktop file for KDE wallpaper")
        except Exception as e:
            logger.warning(f"Failed to create KDE wallpaper symlink: {e}")
        
        # Method 5: Reload Plasma settings using plasmashell reload (as suggested by user)
        try:
            # Use plasmashell reload as suggested by the user
            subprocess.run(["plasmashell", "reload"], check=False)
            logger.info("Reloaded plasma settings using 'plasmashell reload'")
        except Exception as e:
            logger.warning(f"Failed to reload plasma settings: {e}")
            
            # If that fails, try a gentle restart
            try:
                subprocess.run(["plasmashell", "--replace", "&"], shell=True, check=False)
                logger.info("Restarted plasma shell")
            except Exception as e:
                logger.warning(f"Failed to restart plasmashell gently: {e}")
                
                # If that fails, try a more forceful restart
                try:
                    subprocess.run(["killall", "plasmashell"], check=False)
                    time.sleep(2)
                    subprocess.run(["kstart5", "plasmashell"], check=False)
                    logger.info("Forcefully restarted plasmashell")
                except Exception as e:
                    logger.error(f"Failed to forcefully restart plasmashell: {e}")
            
    except Exception as e:
        logger.error(f"Error refreshing KDE wallpaper: {e}")

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
    
    # Refresh KDE wallpaper if directory changed or force refresh is enabled
    if success and (changed or force_refresh):
        # Get current color for notification
        weekly_count = get_weekly_habit_count()
        current_color = get_color_from_count(weekly_count)
        
        # Refresh KDE wallpaper
        refresh_kde_wallpaper()
        
        # Send notification
        if prev_color and prev_color != current_color:
            title = f"Wallpaper Color Changed: {prev_color} → {current_color}"
            message = f"Weekly habit average: {weekly_count:.1f}\nWallpaper directory updated with {current_color} images."
        else:
            title = f"Wallpaper Directory Updated: {current_color}"
            message = f"Weekly habit average: {weekly_count:.1f}\nWallpaper directory populated with {current_color} images."
        
        send_notification(title, message)