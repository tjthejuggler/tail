#!/usr/bin/env python3

import os
import sys
import json
import numpy as np
from PIL import Image
import re

def analyze_labeled_images():
    """
    Analyze labeled images to improve color ranges.
    """
    # Paths
    base_dir = "/home/twain/Pictures"
    labels_file = os.path.join(base_dir, "image_color_labels.json")
    original_dir = os.path.join(base_dir, "llm_baby_monster_original")
    
    # Check if labels file exists
    if not os.path.exists(labels_file):
        print("No labeled data found. Please run image_color_labeler.py first.")
        return
    
    # Load labeled data
    with open(labels_file, 'r') as f:
        labeled_images = json.load(f)
    
    print(f"Found {len(labeled_images)} labeled images.")
    
    # Group images by color category
    color_groups = {}
    total_labels = 0
    
    for filename, colors in labeled_images.items():
        # Handle both old format (string) and new format (list)
        if isinstance(colors, str):
            colors = [colors]  # Convert to list for consistency
            
        for color in colors:
            if color not in color_groups:
                color_groups[color] = []
            color_groups[color].append(filename)
            total_labels += 1
    
    # Print summary
    print("\nLabeled images by color category:")
    for color, images in color_groups.items():
        print(f"{color}: {len(images)} images")
    
    print(f"\nTotal images: {len(labeled_images)}, Total labels: {total_labels}")
    print(f"Average labels per image: {total_labels / len(labeled_images):.2f}")
    
    # Analyze color distributions for each category
    color_ranges = {}
    
    for color, filenames in color_groups.items():
        if not filenames:
            continue
        
        print(f"\nAnalyzing {len(filenames)} images for {color} category...")
        
        # Collect dominant colors from each image
        dominant_colors = []
        
        for filename in filenames:
            image_path = os.path.join(original_dir, filename)
            if not os.path.exists(image_path):
                print(f"Warning: Image {filename} not found in {original_dir}")
                continue
            
            try:
                # Open image and resize for faster processing
                img = Image.open(image_path)
                img = img.resize((100, 100))
                img = img.convert('RGB')
                
                # Convert image to numpy array
                img_array = np.array(img)
                img_array = img_array.reshape((img_array.shape[0] * img_array.shape[1], 3))
                
                # Calculate average color
                avg_color = np.mean(img_array, axis=0)
                dominant_colors.append(avg_color)
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
        
        if not dominant_colors:
            continue
        
        # Convert to numpy array for easier calculations
        dominant_colors = np.array(dominant_colors)
        
        # Calculate min and max values for each RGB channel
        # Use percentiles to avoid outliers
        min_values = np.percentile(dominant_colors, 10, axis=0)
        max_values = np.percentile(dominant_colors, 90, axis=0)
        
        # Add some margin
        margin = 20
        min_values = np.maximum(min_values - margin, 0)
        max_values = np.minimum(max_values + margin, 255)
        
        # Store the range
        color_ranges[color] = [
            min_values.astype(int).tolist(),
            max_values.astype(int).tolist()
        ]
    
    # Print the new color ranges
    print("\nNew color ranges:")
    for color, ranges in color_ranges.items():
        print(f"{color}: {ranges}")
    
    # Update the wallpaper_color_manager.py script
    update_color_manager_script(color_ranges)

def update_color_manager_script(new_color_ranges):
    """
    Update the COLOR_RANGES in the wallpaper_color_manager.py script.
    """
    script_path = "/home/twain/Projects/tail/wallpaper_color_manager.py"
    
    # Read the script
    with open(script_path, 'r') as f:
        script_content = f.read()
    
    # Find the COLOR_RANGES definition
    color_ranges_pattern = r'COLOR_RANGES\s*=\s*\{[^}]*\}'
    color_ranges_match = re.search(color_ranges_pattern, script_content, re.DOTALL)
    
    if not color_ranges_match:
        print("Could not find COLOR_RANGES in the script.")
        return
    
    # Format the new color ranges
    new_ranges_str = "COLOR_RANGES = {\n"
    for color, ranges in new_color_ranges.items():
        new_ranges_str += f'    "{color}": [{ranges[0]}, {ranges[1]}],\n'
    
    # Add white_gray_black as a catch-all if not present
    if "white_gray_black" not in new_color_ranges:
        new_ranges_str += '    "white_gray_black": [(0, 0, 0), (255, 255, 255)],  # This is a catch-all\n'
    
    new_ranges_str += "}"
    
    # Replace the old color ranges with the new ones
    updated_script = re.sub(color_ranges_pattern, new_ranges_str, script_content)
    
    # Create a backup of the original script
    backup_path = script_path + ".bak"
    with open(backup_path, 'w') as f:
        f.write(script_content)
    
    # Write the updated script
    with open(script_path, 'w') as f:
        f.write(updated_script)
    
    print(f"\nUpdated {script_path} with new color ranges.")
    print(f"Original script backed up to {backup_path}")
    
    # Suggest next steps
    print("\nNext steps:")
    print("1. Run the wallpaper_color_manager.py script to recategorize the images")
    print("2. Check if the categorization has improved")
    print("3. If needed, run image_color_labeler.py again to label more images")

if __name__ == "__main__":
    analyze_labeled_images()