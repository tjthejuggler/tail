#!/usr/bin/env python3
"""
Direct Wallpaper Switch

This script directly modifies the KDE configuration to change the wallpaper folder.
It takes a more focused approach to ensure the changes are applied correctly.

Usage:
    python3 direct_wallpaper_switch.py <color>

Where <color> is one of: red, orange, green, blue, pink, yellow, white_gray_black
"""

import os
import sys
import subprocess
import logging
import time
import glob
import re

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

def find_kde_config_files():
    """Find all relevant KDE configuration files"""
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, ".config")
    
    # Look for all potential configuration files
    config_files = []
    
    # Common KDE config files
    common_files = [
        "plasma-org.kde.plasma.desktop-appletsrc",
        "plasmashellrc",
        "plasmarc",
        "kscreenlockerrc"
    ]
    
    for filename in common_files:
        path = os.path.join(config_dir, filename)
        if os.path.exists(path):
            config_files.append(path)
    
    # Look for any other files that might contain wallpaper settings
    for root, dirs, files in os.walk(config_dir):
        for file in files:
            if file.endswith("rc") and "plasma" in file.lower() and os.path.join(root, file) not in config_files:
                config_files.append(os.path.join(root, file))
    
    return config_files

def find_wallpaper_settings(config_files):
    """Find all wallpaper settings in the configuration files"""
    settings = []
    
    for config_file in config_files:
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                
                # Look for wallpaper settings
                if "wallpaper" in content.lower() or "slideshow" in content.lower():
                    logger.info(f"Found potential wallpaper settings in: {config_file}")
                    settings.append(config_file)
                    
                    # Print the relevant sections for debugging
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "wallpaper" in line.lower() or "slideshow" in line.lower() or "image=" in line.lower():
                            start = max(0, i - 5)
                            end = min(len(lines), i + 5)
                            context = lines[start:end]
                            logger.debug(f"Context in {config_file}:\n" + "\n".join(context))
        except Exception as e:
            logger.error(f"Error reading {config_file}: {e}")
    
    return settings

def modify_kde_config_directly(color_folder):
    """Modify the KDE configuration directly to change the wallpaper folder"""
    home_dir = os.path.expanduser("~")
    
    # The main plasma config file
    plasma_config = os.path.join(home_dir, ".config", "plasma-org.kde.plasma.desktop-appletsrc")
    
    if not os.path.exists(plasma_config):
        logger.error(f"Plasma config file not found: {plasma_config}")
        return False
    
    # Backup the config file
    backup_file = plasma_config + ".bak." + str(int(time.time()))
    try:
        with open(plasma_config, 'r') as src, open(backup_file, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Created backup: {backup_file}")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False
    
    # Read the config file
    try:
        with open(plasma_config, 'r') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read config file: {e}")
        return False
    
    # Modify the content
    modified = False
    
    # Replace Image= lines
    image_pattern = re.compile(r'(Image=).*', re.MULTILINE)
    if image_pattern.search(content):
        content = image_pattern.sub(r'\1' + color_folder, content)
        modified = True
        logger.info("Modified Image= setting")
    
    # Replace SlidePaths= lines
    slidepaths_pattern = re.compile(r'(SlidePaths=).*', re.MULTILINE)
    if slidepaths_pattern.search(content):
        content = slidepaths_pattern.sub(r'\1' + color_folder, content)
        modified = True
        logger.info("Modified SlidePaths= setting")
    
    # Write the modified content back to the file
    if modified:
        try:
            with open(plasma_config, 'w') as f:
                f.write(content)
            logger.info(f"Updated config file: {plasma_config}")
        except Exception as e:
            logger.error(f"Failed to write config file: {e}")
            return False
    else:
        logger.warning("No wallpaper settings found to modify")
    
    # Also use kwriteconfig5 to update all possible containments
    try:
        # Find all containment sections
        containment_pattern = re.compile(r'\[Containments\]\[(\d+)\]')
        containments = containment_pattern.findall(content)
        
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
                    color_folder
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
                    color_folder
                ], check=False)
            
            logger.info("Updated all containments using kwriteconfig5")
        else:
            # If no containments found, try with default containment 1
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
            
            logger.info("Updated default containment using kwriteconfig5")
    except Exception as e:
        logger.error(f"Error updating containments: {e}")
    
    # Also try to update the plasmashellrc file
    plasmashellrc = os.path.join(home_dir, ".config", "plasmashellrc")
    if os.path.exists(plasmashellrc):
        try:
            subprocess.run([
                "kwriteconfig5",
                "--file", "plasmashellrc",
                "--group", "Wallpaper",
                "--group", "org.kde.image",
                "--group", "General",
                "--key", "Image",
                color_folder
            ], check=False)
            
            logger.info("Updated plasmashellrc")
        except Exception as e:
            logger.error(f"Error updating plasmashellrc: {e}")
    
    # Try to force KDE to reload the configuration
    try:
        # Method 1: Use qdbus to reload the configuration
        subprocess.run([
            "qdbus",
            "org.kde.plasmashell",
            "/PlasmaShell",
            "org.kde.PlasmaShell.evaluateScript",
            f"""
            var allDesktops = desktops();
            for (i=0; i<allDesktops.length; i++) {{
                d = allDesktops[i];
                d.wallpaperPlugin = "org.kde.image";
                d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
                d.writeConfig("Image", "{color_folder}");
                d.reloadConfig();
            }}
            """
        ], check=False)
        
        # Method 2: Use plasmashell reload
        subprocess.run(["plasmashell", "reload"], check=False)
        
        # Method 3: Restart plasmashell
        subprocess.run(["plasmashell", "--replace", "&"], shell=True, check=False)
        
        logger.info("Forced KDE to reload configuration")
    except Exception as e:
        logger.error(f"Error forcing KDE to reload: {e}")
    
    return True

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
    
    # Find all KDE configuration files
    config_files = find_kde_config_files()
    logger.info(f"Found {len(config_files)} KDE configuration files")
    
    # Find all wallpaper settings
    wallpaper_settings = find_wallpaper_settings(config_files)
    logger.info(f"Found {len(wallpaper_settings)} files with wallpaper settings")
    
    # Modify the KDE configuration directly
    success = modify_kde_config_directly(color_folder)
    
    return success

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