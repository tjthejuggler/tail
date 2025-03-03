#!/usr/bin/env python3
"""
Switch Wallpaper Folder

This script updates the KDE wallpaper configuration to point to a different folder
based on the specified color.

Usage:
    python3 switch_wallpaper_folder.py <color>

Where <color> is one of: red, orange, green, blue, pink, yellow, white_gray_black
"""

import os
import sys
import subprocess
import logging
import shutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define color folders
BASE_DIR = "/home/twain/Pictures"
COLOR_FOLDERS = {
    "red": os.path.join(BASE_DIR, "llm_baby_monster_by_color/red"),
    "orange": os.path.join(BASE_DIR, "llm_baby_monster_by_color/orange"),
    "green": os.path.join(BASE_DIR, "llm_baby_monster_by_color/green"),
    "blue": os.path.join(BASE_DIR, "llm_baby_monster_by_color/blue"),
    "pink": os.path.join(BASE_DIR, "llm_baby_monster_by_color/pink"),
    "yellow": os.path.join(BASE_DIR, "llm_baby_monster_by_color/yellow"),
    "white_gray_black": os.path.join(BASE_DIR, "llm_baby_monster_by_color/white_gray_black")
}

def switch_wallpaper_folder(color):
    """
    Switch the KDE wallpaper folder to the specified color folder.
    
    Args:
        color: The color folder to switch to
    """
    if color not in COLOR_FOLDERS:
        logger.error(f"Invalid color: {color}")
        logger.info(f"Valid colors: {', '.join(COLOR_FOLDERS.keys())}")
        return False
    
    # Get the path to the color folder
    color_folder = COLOR_FOLDERS[color]
    
    # Check if the folder exists
    if not os.path.exists(color_folder):
        logger.error(f"Color folder does not exist: {color_folder}")
        return False
    
    logger.info(f"Switching wallpaper folder to: {color_folder}")
    
    # Path to the Plasma wallpaper configuration files
    home_dir = os.path.expanduser("~")
    config_files = [
        os.path.join(home_dir, ".config", "plasmashellrc"),
        os.path.join(home_dir, ".config", "plasma-org.kde.plasma.desktop-appletsrc")
    ]
    
    success = False
    
    # Try to update each configuration file
    for config_file in config_files:
        if os.path.exists(config_file):
            logger.info(f"Updating configuration file: {config_file}")
            
            # Backup the original configuration file
            backup_file = config_file + ".bak"
            try:
                shutil.copy2(config_file, backup_file)
                logger.info(f"Created backup: {backup_file}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
            
            try:
                # Read the existing configuration file
                with open(config_file, 'r') as f:
                    lines = f.readlines()
                
                # Modify the configuration lines
                modified = False
                for i, line in enumerate(lines):
                    # Look for Image= lines
                    if line.strip().startswith('Image='):
                        lines[i] = f'Image={color_folder}\n'
                        modified = True
                    # Look for SlidePaths= lines
                    elif line.strip().startswith('SlidePaths='):
                        lines[i] = f'SlidePaths={color_folder}\n'
                        modified = True
                
                if modified:
                    # Write the updated configuration back to the file
                    with open(config_file, 'w') as f:
                        f.writelines(lines)
                    logger.info(f"Updated configuration file: {config_file}")
                    success = True
                else:
                    logger.warning(f"No wallpaper paths found in: {config_file}")
            except Exception as e:
                logger.error(f"Error updating configuration file: {e}")
    
    # Also use kwriteconfig5 to update the configuration
    try:
        # Update the wallpaper path for the slideshow plugin
        subprocess.run([
            "kwriteconfig5",
            "--file", "plasma-org.kde.plasma.desktop-appletsrc",
            "--group", "Containments",
            "--group", "1",
            "--group", "Wallpaper",
            "--group", "org.kde.slideshow",
            "--group", "General",
            "--key", "SlidePaths",
            color_folder
        ], check=False)
        
        # Update the wallpaper path for the image plugin
        subprocess.run([
            "kwriteconfig5",
            "--file", "plasma-org.kde.plasma.desktop-appletsrc",
            "--group", "Containments",
            "--group", "1",
            "--group", "Wallpaper",
            "--group", "org.kde.image",
            "--group", "General",
            "--key", "Image",
            color_folder
        ], check=False)
        
        logger.info("Updated configuration using kwriteconfig5")
        success = True
    except Exception as e:
        logger.warning(f"Failed to update configuration using kwriteconfig5: {e}")
    
    # Reload the Plasma shell to apply the changes
    try:
        subprocess.run(['plasmashell', 'reload'], check=False)
        logger.info("Reloaded Plasma shell")
    except Exception as e:
        logger.warning(f"Failed to reload Plasma shell: {e}")
        
        # Try alternative method to restart Plasma
        try:
            subprocess.run(["plasmashell", "--replace", "&"], shell=True, check=False)
            logger.info("Restarted Plasma shell")
        except Exception as e:
            logger.error(f"Failed to restart Plasma shell: {e}")
    
    return success

if __name__ == "__main__":
    # Check if a color was provided
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <color>")
        print(f"Valid colors: {', '.join(COLOR_FOLDERS.keys())}")
        sys.exit(1)
    
    # Get the color from the command line
    color = sys.argv[1]
    
    # Switch the wallpaper folder
    if switch_wallpaper_folder(color):
        print(f"Successfully switched wallpaper folder to: {color}")
    else:
        print(f"Failed to switch wallpaper folder to: {color}")
        sys.exit(1)