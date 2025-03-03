#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """
    Restart the analysis process:
    1. Run the improve_color_analyzer.py to update color ranges
    2. Clear all color directories
    3. Recategorize all images using the new color ranges
    """
    try:
        # Paths
        base_dir = "/home/twain/Pictures"
        color_dirs = [
            os.path.join(base_dir, "llm_baby_monster_by_color", "red"),
            os.path.join(base_dir, "llm_baby_monster_by_color", "orange"),
            os.path.join(base_dir, "llm_baby_monster_by_color", "green"),
            os.path.join(base_dir, "llm_baby_monster_by_color", "blue"),
            os.path.join(base_dir, "llm_baby_monster_by_color", "pink"),
            os.path.join(base_dir, "llm_baby_monster_by_color", "yellow"),
            os.path.join(base_dir, "llm_baby_monster_by_color", "white_gray_black")
        ]
        
        # Step 1: Run the improve_color_analyzer.py
        logging.info("Running improve_color_analyzer.py to update color ranges...")
        result = subprocess.run(["python3", "improve_color_analyzer.py"], 
                               capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"Error running improve_color_analyzer.py: {result.stderr}")
            return 1
        
        logging.info(result.stdout)
        
        # Step 2: Clear all color directories
        logging.info("Clearing all color directories...")
        for color_dir in color_dirs:
            if os.path.exists(color_dir):
                # Remove all symlinks in the directory
                for filename in os.listdir(color_dir):
                    file_path = os.path.join(color_dir, filename)
                    if os.path.islink(file_path) or os.path.isfile(file_path):
                        os.remove(file_path)
                logging.info(f"Cleared {color_dir}")
        
        # Step 3: Run wallpaper_color_manager.py to recategorize all images
        logging.info("Running wallpaper_color_manager.py to recategorize all images...")
        result = subprocess.run(["python3", "wallpaper_color_manager.py"], 
                               capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"Error running wallpaper_color_manager.py: {result.stderr}")
            return 1
        
        logging.info("Analysis process restarted successfully!")
        logging.info("All images have been recategorized using the updated color ranges.")
        
        return 0
    
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())