#!/usr/bin/env python3

import os
import sys
import json
import logging
import shutil
import time
from datetime import datetime
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

# Setup logging
logging.basicConfig(
    filename='/home/twain/logs/wallpaper_manager.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constants
BASE_DIR = "/home/twain/Pictures"
WEEK_AVERAGE_FILE = "/home/twain/noteVault/habitCounters/week_average.txt"
STATE_FILE = os.path.join(BASE_DIR, "llm_baby_monster_current", "state.json")
RETIRED_DIR = "/home/twain/Pictures/llm_baby_monster_retired"

# Color category directories
COLOR_DIRS = {
    "red": os.path.join(BASE_DIR, "llm_baby_monster_by_color", "red"),
    "orange": os.path.join(BASE_DIR, "llm_baby_monster_by_color", "orange"),
    "green": os.path.join(BASE_DIR, "llm_baby_monster_by_color", "green"),
    "blue": os.path.join(BASE_DIR, "llm_baby_monster_by_color", "blue"),
    "pink": os.path.join(BASE_DIR, "llm_baby_monster_by_color", "pink"),
    "yellow": os.path.join(BASE_DIR, "llm_baby_monster_by_color", "yellow"),
    "white_gray_black": os.path.join(BASE_DIR, "llm_baby_monster_by_color", "white_gray_black")
}

# Configuration
MULTI_COLOR_THRESHOLD = 0.15  # Colors with at least 15% presence will be included

# Define color ranges in RGB
COLOR_RANGES = {
    "red": [(150, 0, 0), (255, 100, 100)],
    "orange": [(150, 75, 0), (255, 200, 100)],
    "green": [(0, 150, 0), (100, 255, 100)],
    "blue": [(0, 0, 150), (100, 100, 255)],
    "pink": [(150, 0, 150), (255, 100, 255)],
    "yellow": [(150, 150, 0), (255, 255, 100)],
    "white_gray_black": [(0, 0, 0), (255, 255, 255)]  # This is a catch-all
}

def setup_directory_structure():
    """
    Create the necessary directory structure for the wallpaper color management system.
    """
    # Define all directories
    directories = [
        "llm_baby_monster_original",
        "llm_baby_monster_new",
        "llm_baby_monster_by_color",
        "llm_baby_monster_by_color/red",
        "llm_baby_monster_by_color/orange",
        "llm_baby_monster_by_color/green",
        "llm_baby_monster_by_color/blue",
        "llm_baby_monster_by_color/pink",
        "llm_baby_monster_by_color/yellow",
        "llm_baby_monster_by_color/white_gray_black",
        "llm_baby_monster_current"
    ]
    
    # Create directories if they don't exist
    for directory in directories:
        full_path = os.path.join(BASE_DIR, directory)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            logging.info(f"Created directory: {full_path}")
    
    # Create retired directory if it doesn't exist
    if not os.path.exists(RETIRED_DIR):
        os.makedirs(RETIRED_DIR)
        logging.info(f"Created retired directory: {RETIRED_DIR}")
    
    # Copy existing images to original directory if it's empty
    original_dir = os.path.join(BASE_DIR, "llm_baby_monster_original")
    source_dir = os.path.join(BASE_DIR, "llm_baby_monster")
    
    if os.path.exists(source_dir) and os.path.isdir(original_dir) and not os.listdir(original_dir):
        for filename in os.listdir(source_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                source_file = os.path.join(source_dir, filename)
                dest_file = os.path.join(original_dir, filename)
                if os.path.isfile(source_file):
                    shutil.copy2(source_file, dest_file)
        logging.info(f"Copied existing images to {original_dir}")

def analyze_image_color(image_path):
    """
    Analyze an image to determine its dominant color categories.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        List of strings representing the color categories
    """
    try:
        # Open image and resize for faster processing
        img = Image.open(image_path)
        img = img.resize((100, 100))
        img = img.convert('RGB')
        
        # Convert image to numpy array
        img_array = np.array(img)
        img_array = img_array.reshape((img_array.shape[0] * img_array.shape[1], 3))
        
        # Use k-means clustering to find dominant colors
        kmeans = KMeans(n_clusters=5)
        kmeans.fit(img_array)
        
        # Get the colors and their percentages
        colors = kmeans.cluster_centers_
        labels = kmeans.labels_
        label_counts = np.bincount(labels)
        percentages = label_counts / len(labels)
        
        # Combine colors and percentages
        color_percentages = list(zip(colors, percentages))
        
        # Sort by percentage (descending)
        color_percentages.sort(key=lambda x: x[1], reverse=True)
        
        # Get significant colors (those with percentage above threshold)
        significant_colors = [color for color, percentage in color_percentages
                             if percentage >= MULTI_COLOR_THRESHOLD]
        
        # If no significant colors (unlikely), just use the most dominant one
        if not significant_colors:
            significant_colors = [color_percentages[0][0]]
        
        # Map each RGB to color category and collect unique categories
        color_categories = []
        for color in significant_colors:
            category = map_rgb_to_category(color)
            if category not in color_categories:
                color_categories.append(category)
        
        # Always include white_gray_black if it's present in the image
        # This ensures grayscale elements are properly represented
        has_white_gray_black = False
        for color, percentage in color_percentages:
            if (is_grayscale(color) and percentage >= MULTI_COLOR_THRESHOLD * 0.5 and
                "white_gray_black" not in color_categories):
                color_categories.append("white_gray_black")
                break
        
        return color_categories
        
    except Exception as e:
        logging.error(f"Error analyzing image {image_path}: {e}")
        return ["white_gray_black"]  # Default to this category on error

def is_grayscale(rgb):
    """
    Check if a color is grayscale (R, G, B values are close to each other).
    
    Args:
        rgb: Numpy array of RGB values
        
    Returns:
        Boolean indicating if the color is grayscale
    """
    # Calculate the maximum difference between any two RGB channels
    max_diff = max(abs(rgb[0] - rgb[1]), abs(rgb[0] - rgb[2]), abs(rgb[1] - rgb[2]))
    
    # If the difference is small, consider it grayscale
    return max_diff < 30

def map_rgb_to_category(rgb):
    """
    Map an RGB color to one of our predefined categories.
    
    Args:
        rgb: Numpy array of RGB values
        
    Returns:
        String representing the color category
    """
    # Calculate distance to each color range
    min_distances = {}
    
    for category, ranges in COLOR_RANGES.items():
        min_range, max_range = ranges
        
        # Check if color is within range
        if all(min_range[i] <= rgb[i] <= max_range[i] for i in range(3)):
            return category
        
        # Calculate minimum distance to range
        min_dist = 0
        for i in range(3):
            if rgb[i] < min_range[i]:
                min_dist += (min_range[i] - rgb[i]) ** 2
            elif rgb[i] > max_range[i]:
                min_dist += (rgb[i] - max_range[i]) ** 2
        
        min_distances[category] = min_dist
    
    # Return category with minimum distance
    return min(min_distances.items(), key=lambda x: x[1])[0]

def process_new_images(new_dir, original_dir, color_dirs):
    """
    Process new images, analyze their colors, and organize them.
    
    Args:
        new_dir: Directory containing new images
        original_dir: Directory to store original copies
        color_dirs: Dictionary mapping color categories to directories
    
    Returns:
        Number of images processed
    """
    processed_count = 0
    
    for filename in os.listdir(new_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            image_path = os.path.join(new_dir, filename)
            
            # Skip if not a file
            if not os.path.isfile(image_path):
                continue
                
            # Analyze colors - now returns a list of color categories
            color_categories = analyze_image_color(image_path)
            
            # Copy to original directory
            original_path = os.path.join(original_dir, filename)
            shutil.copy2(image_path, original_path)
            
            # Create symlinks in all appropriate color directories
            for color_category in color_categories:
                color_dir = color_dirs[color_category]
                symlink_path = os.path.join(color_dir, filename)
                
                # Remove existing symlink if it exists
                if os.path.exists(symlink_path):
                    os.remove(symlink_path)
                    
                # Create new symlink
                os.symlink(original_path, symlink_path)
            
            # Remove from new directory
            os.remove(image_path)
            
            processed_count += 1
            logging.info(f"Processed image {filename} as {', '.join(color_categories)}")
            
    return processed_count

def get_color_from_count(count):
    """
    Determine color category based on habit count.
    """
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

def get_weekly_average():
    """
    Read the weekly average from the file.
    """
    try:
        with open(WEEK_AVERAGE_FILE, 'r') as f:
            return float(f.read().strip())
    except Exception as e:
        logging.error(f"Error reading weekly average: {e}")
        return 0

def get_current_state():
    """
    Read the current state from the state file.
    """
    if not os.path.exists(STATE_FILE):
        return {"last_color": None, "last_update": None}
    
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading state file: {e}")
        return {"last_color": None, "last_update": None}

def save_current_state(color):
    """
    Save the current state to the state file.
    """
    state = {
        "last_color": color,
        "last_update": datetime.now().isoformat()
    }
    
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving state file: {e}")

def update_wallpaper_directory(color):
    """
    Update the KDE wallpaper directory to point to the appropriate color directory.
    """
    wallpaper_dir = os.path.join(BASE_DIR, "llm_baby_monster")
    color_dir = COLOR_DIRS[color]
    
    try:
        # Check if there are images in the color directory
        if not os.path.exists(color_dir) or not os.listdir(color_dir):
            logging.warning(f"No images in {color} directory. Using white_gray_black instead.")
            color = "white_gray_black"
            color_dir = COLOR_DIRS[color]
            
            # If still no images, log error and return
            if not os.path.exists(color_dir) or not os.listdir(color_dir):
                logging.error("No images in any color directory. Cannot update wallpaper.")
                return False
        
        # Clear existing wallpaper directory
        for item in os.listdir(wallpaper_dir):
            item_path = os.path.join(wallpaper_dir, item)
            if os.path.islink(item_path) or os.path.isfile(item_path):
                os.remove(item_path)
        
        # Create symlinks to all images in the color directory
        for filename in os.listdir(color_dir):
            source = os.path.join(color_dir, filename)
            target = os.path.join(wallpaper_dir, filename)
            
            # Only create symlinks for files, not directories
            if os.path.isfile(source):
                os.symlink(source, target)
        
        logging.info(f"Updated wallpaper directory to {color} category")
        return True
    except Exception as e:
        logging.error(f"Error updating wallpaper directory: {e}")
        return False

def categorize_existing_images():
    """
    Categorize all existing images in the original directory.
    """
    original_dir = os.path.join(BASE_DIR, "llm_baby_monster_original")
    retired_dir = RETIRED_DIR
    
    if not os.path.exists(original_dir):
        logging.error(f"Original directory {original_dir} does not exist")
        return 0
    
    categorized_count = 0
    
    for filename in os.listdir(original_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            image_path = os.path.join(original_dir, filename)
            
            # Skip if not a file
            if not os.path.isfile(image_path):
                continue
                
            # Skip if image is retired
            if os.path.exists(os.path.join(retired_dir, filename)):
                continue
                
            # Analyze colors - now returns a list of color categories
            color_categories = analyze_image_color(image_path)
            
            # Track if this image was newly categorized in any category
            newly_categorized = False
            
            # Create symlinks in all appropriate color directories
            for color_category in color_categories:
                color_dir = COLOR_DIRS[color_category]
                symlink_path = os.path.join(color_dir, filename)
                
                # Skip if symlink already exists
                if os.path.exists(symlink_path):
                    continue
                    
                # Create new symlink
                os.symlink(image_path, symlink_path)
                newly_categorized = True
            
            if newly_categorized:
                categorized_count += 1
            
    if categorized_count > 0:
        logging.info(f"Categorized {categorized_count} existing images")
    
    return categorized_count

def is_image_retired(filename):
    """
    Check if an image is in the retired directory.
    
    Args:
        filename: The filename to check
        
    Returns:
        Boolean indicating if the image is retired
    """
    retired_path = os.path.join(RETIRED_DIR, filename)
    return os.path.exists(retired_path)

def retire_image(filename):
    """
    Retire an image by moving it to the retired directory and removing all symlinks.
    
    Args:
        filename: The filename to retire
        
    Returns:
        Boolean indicating success
    """
    try:
        # Check if already retired
        if is_image_retired(filename):
            logging.info(f"Image {filename} is already retired")
            return True
            
        # Get paths
        original_path = os.path.join(BASE_DIR, "llm_baby_monster_original", filename)
        retired_path = os.path.join(RETIRED_DIR, filename)
        
        # Check if original exists
        if not os.path.exists(original_path):
            logging.error(f"Cannot retire {filename}: original file not found")
            return False
            
        # Move the file to retired directory
        shutil.move(original_path, retired_path)
        
        # Remove all symlinks from color directories
        for color, color_dir in COLOR_DIRS.items():
            symlink_path = os.path.join(color_dir, filename)
            if os.path.exists(symlink_path):
                os.remove(symlink_path)
                
        logging.info(f"Retired image {filename}")
        return True
        
    except Exception as e:
        logging.error(f"Error retiring image {filename}: {e}")
        return False

def main():
    try:
        # Ensure logs directory exists
        os.makedirs('/home/twain/logs', exist_ok=True)
        
        # Ensure directory structure exists
        setup_directory_structure()
        
        # Categorize existing images if needed
        categorize_existing_images()
        
        # Process any new images
        new_dir = os.path.join(BASE_DIR, "llm_baby_monster_new")
        original_dir = os.path.join(BASE_DIR, "llm_baby_monster_original")
        processed_count = process_new_images(new_dir, original_dir, COLOR_DIRS)
        
        if processed_count > 0:
            logging.info(f"Processed {processed_count} new images")
        
        # Get weekly average and determine color
        weekly_average = get_weekly_average()
        current_color = get_color_from_count(weekly_average)
        
        # Get current state
        state = get_current_state()
        
        # Update wallpaper directory if color has changed
        if current_color != state["last_color"]:
            if update_wallpaper_directory(current_color):
                save_current_state(current_color)
                logging.info(f"Changed wallpaper color to {current_color} (weekly average: {weekly_average})")
        
    except Exception as e:
        logging.error(f"Unexpected error in main function: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())