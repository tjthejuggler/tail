#!/usr/bin/env python3
"""
Simple Wallpaper Switch

This script directly updates the KDE wallpaper slideshow directory using the approach
suggested by the user. It converts the folder path to a file URL and updates the
plasmashellrc file directly.

Usage:
    python3 simple_wallpaper_switch.py <color>

Where <color> is one of: red, orange, green, blue, pink, yellow, white_gray_black
"""

import os
import sys
import subprocess
import logging

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
    if not os.path.exists(color_folder) or not os.path.isdir(color_folder):
        logger.error(f"Color folder does not exist: {color_folder}")
        return False
    
    logger.info(f"Switching wallpaper folder to: {color_folder}")
    
    # Convert the path to a file URL
    image_folder_url = f'file://{os.path.abspath(color_folder)}'
    logger.info(f"File URL: {image_folder_url}")
    
    try:
        # Update the wallpaper slideshow directory using kwriteconfig5
        subprocess.run([
            'kwriteconfig5',
            '--file', 'plasmashellrc',
            '--group', 'Wallpaper',
            '--group', 'org.kde.slideshow',
            '--key', 'SlidePaths',
            image_folder_url
        ], check=True)
        logger.info("Updated plasmashellrc with new slideshow path")
        
        # Also update the plasma-org.kde.plasma.desktop-appletsrc file for all containments
        plasma_config = os.path.join(os.path.expanduser("~"), ".config", "plasma-org.kde.plasma.desktop-appletsrc")
        if os.path.exists(plasma_config):
            # Try to find all containment numbers
            try:
                output = subprocess.check_output(["grep", "-n", "\\[Containments\\]", plasma_config]).decode().strip()
                containments = []
                for line in output.split('\n'):
                    parts = line.split('[')
                    if len(parts) > 2:
                        containment = parts[2].split(']')[0]
                        if containment.isdigit():
                            containments.append(containment)
                
                if containments:
                    logger.info(f"Found containments: {containments}")
                    for containment in containments:
                        # Update for slideshow plugin
                        subprocess.run([
                            "kwriteconfig5",
                            "--file", "plasma-org.kde.plasma.desktop-appletsrc",
                            "--group", f"Containments",
                            "--group", containment,
                            "--group", "Wallpaper",
                            "--group", "org.kde.slideshow",
                            "--group", "General",
                            "--key", "SlidePaths",
                            image_folder_url
                        ], check=False)
                        
                        # Update for image plugin
                        subprocess.run([
                            "kwriteconfig5",
                            "--file", "plasma-org.kde.plasma.desktop-appletsrc",
                            "--group", f"Containments",
                            "--group", containment,
                            "--group", "Wallpaper",
                            "--group", "org.kde.image",
                            "--group", "General",
                            "--key", "Image",
                            image_folder_url
                        ], check=False)
                    
                    logger.info("Updated all containments in plasma-org.kde.plasma.desktop-appletsrc")
                else:
                    logger.warning("No containments found, using default containment 1")
                    # Update default containment 1
                    subprocess.run([
                        "kwriteconfig5",
                        "--file", "plasma-org.kde.plasma.desktop-appletsrc",
                        "--group", "Containments",
                        "--group", "1",
                        "--group", "Wallpaper",
                        "--group", "org.kde.slideshow",
                        "--group", "General",
                        "--key", "SlidePaths",
                        image_folder_url
                    ], check=False)
            except Exception as e:
                logger.warning(f"Error finding containments: {e}")
                # Update default containment 1
                subprocess.run([
                    "kwriteconfig5",
                    "--file", "plasma-org.kde.plasma.desktop-appletsrc",
                    "--group", "Containments",
                    "--group", "1",
                    "--group", "Wallpaper",
                    "--group", "org.kde.slideshow",
                    "--group", "General",
                    "--key", "SlidePaths",
                    image_folder_url
                ], check=False)
        
        # Reload the Plasma shell to apply the changes
        subprocess.run(['plasmashell', 'reload'], check=True)
        logger.info("Reloaded Plasma shell")
        
        return True
    except Exception as e:
        logger.error(f"Error updating wallpaper folder: {e}")
        return False

if __name__ == "__main__":
    # Check if a color was provided
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <color>")
        print(f"Valid colors: {', '.join(COLOR_FOLDERS.keys())}")
        sys.exit(1)
    
    # Get the color from the command line
    color = sys.argv[1]
    
    # Enable debug logging if requested
    if "--debug" in sys.argv:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Switch the wallpaper folder
    if switch_wallpaper_folder(color):
        print(f"Successfully switched wallpaper folder to: {color}")
    else:
        print(f"Failed to switch wallpaper folder to: {color}")
        sys.exit(1)