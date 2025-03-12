"""
File Operations Module

This module provides functions for:
- Creating and managing color category directories
- Creating symlinks for categorized images
- Resetting color categories
- Processing new images
- Categorizing existing images
"""

import os
import shutil
import logging
from typing import Dict, List, Any, Callable, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ensure_directory(path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        bool: True if directory exists or was created, False otherwise
    """
    if os.path.exists(path):
        if os.path.isdir(path):
            return True
        else:
            logger.error(f"Path exists but is not a directory: {path}")
            return False
    
    try:
        os.makedirs(path, exist_ok=True)
        logger.info(f"Created directory: {path}")
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False


def setup_color_directories(config: Dict[str, Any]) -> Dict[str, bool]:
    """
    Set up color category directories.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        dict: Status of each directory creation
    """
    results = {}
    
    # Get base directory
    base_dir = config["paths"]["base_dir"]
    
    # Ensure base directory exists
    if not ensure_directory(base_dir):
        return {"base_dir": False}
    
    results["base_dir"] = True
    
    # Ensure original directory exists
    original_dir = os.path.join(base_dir, config["paths"]["original_dir"])
    results["original_dir"] = ensure_directory(original_dir)
    
    # Ensure color directories exist
    for color, color_dir in config["paths"]["color_dirs"].items():
        # Create absolute path
        abs_color_dir = os.path.join(base_dir, color_dir)
        
        # Ensure directory exists
        results[color] = ensure_directory(abs_color_dir)
    
    return results


def setup_sample_images(config: Dict[str, Any], max_samples: int = 5) -> List[str]:
    """
    Set up sample images for the control panel.
    
    Args:
        config: Configuration dictionary
        max_samples: Maximum number of sample images to copy
        
    Returns:
        list: Paths to sample images
    """
    # Get sample images directory
    sample_dir = config.get("sample_images_dir", "sample_images")
    
    # Create absolute path
    if not os.path.isabs(sample_dir):
        # Assume relative to the application directory
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sample_dir = os.path.join(app_dir, sample_dir)
    
    # Ensure directory exists
    if not ensure_directory(sample_dir):
        return []
    
    # Get original directory
    base_dir = config["paths"]["base_dir"]
    original_dir = os.path.join(base_dir, config["paths"]["original_dir"])
    
    # Check if original directory exists
    if not os.path.exists(original_dir) or not os.path.isdir(original_dir):
        logger.warning(f"Original directory does not exist: {original_dir}")
        return []
    
    # Get list of image files in original directory
    image_files = []
    for filename in os.listdir(original_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            image_files.append(os.path.join(original_dir, filename))
    
    # Limit number of samples
    if len(image_files) > max_samples:
        # Take evenly spaced samples
        step = len(image_files) // max_samples
        image_files = image_files[::step][:max_samples]
    
    # Copy sample images
    sample_paths = []
    for src in image_files:
        try:
            # Get filename
            filename = os.path.basename(src)
            
            # Create destination path
            dst = os.path.join(sample_dir, filename)
            
            # Copy file if it doesn't exist
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
                logger.info(f"Copied sample image: {filename}")
            
            # Add to sample paths
            sample_paths.append(dst)
            
        except Exception as e:
            logger.error(f"Error copying sample image {src}: {e}")
    
    return sample_paths


def reset_categories(config: Dict[str, Any]) -> Dict[str, int]:
    """
    Reset all color categories by removing symlinks.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        dict: Statistics about the reset operation
    """
    stats = {
        "total_removed": 0,
        "errors": 0
    }
    
    # Get base directory
    base_dir = config["paths"]["base_dir"]
    
    # Process each color directory
    for color, color_dir in config["paths"]["color_dirs"].items():
        # Create absolute path
        abs_color_dir = os.path.join(base_dir, color_dir)
        
        # Skip if directory doesn't exist
        if not os.path.exists(abs_color_dir) or not os.path.isdir(abs_color_dir):
            logger.warning(f"Color directory does not exist: {abs_color_dir}")
            continue
        
        # Remove all symlinks in the directory
        for filename in os.listdir(abs_color_dir):
            file_path = os.path.join(abs_color_dir, filename)
            
            try:
                # Check if it's a symlink
                if os.path.islink(file_path):
                    # Remove symlink
                    os.unlink(file_path)
                    stats["total_removed"] += 1
                    logger.debug(f"Removed symlink: {file_path}")
            except Exception as e:
                logger.error(f"Error removing symlink {file_path}: {e}")
                stats["errors"] += 1
    
    logger.info(f"Reset complete: {stats['total_removed']} symlinks removed, {stats['errors']} errors")
    return stats


def restart_sorting(config: Dict[str, Any]) -> Dict[str, int]:
    """
    Restart sorting by removing all symlinks from color folders and the main folder.
    This provides a fresh start for sorting with new settings.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        dict: Statistics about the restart operation
    """
    stats = {
        "total_removed": 0,
        "errors": 0
    }
    
    # First, reset all color categories
    reset_stats = reset_categories(config)
    stats["total_removed"] += reset_stats["total_removed"]
    stats["errors"] += reset_stats["errors"]
    
    # Get base directory
    base_dir = config["paths"]["base_dir"]
    
    # Check for the main little_baby_monster folder
    # This is assumed to be in the base directory
    main_folder = os.path.join(base_dir, "little_baby_monster")
    
    if os.path.exists(main_folder) and os.path.isdir(main_folder):
        # Remove all symlinks in the main folder
        for filename in os.listdir(main_folder):
            file_path = os.path.join(main_folder, filename)
            
            try:
                # Check if it's a symlink
                if os.path.islink(file_path):
                    # Remove symlink
                    os.unlink(file_path)
                    stats["total_removed"] += 1
                    logger.debug(f"Removed symlink from main folder: {file_path}")
            except Exception as e:
                logger.error(f"Error removing symlink from main folder {file_path}: {e}")
                stats["errors"] += 1
    else:
        logger.warning(f"Main folder does not exist: {main_folder}")
    
    logger.info(f"Restart complete: {stats['total_removed']} symlinks removed, {stats['errors']} errors")
    return stats


def get_image_files_recursive(directory: str) -> List[str]:
    """
    Get all image files in a directory and its subdirectories.
    
    Args:
        directory: Directory path to scan
        
    Returns:
        list: Absolute paths to image files
    """
    image_files = []
    
    try:
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    # Create absolute path
                    image_path = os.path.join(root, filename)
                    image_files.append(image_path)
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {e}")
    
    return image_files

def process_new_images(
    config: Dict[str, Any],
    analyze_func: Callable[[str, Dict[str, float], Any, Any, Any], Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Process new images in the original directory.
    
    Args:
        config: Configuration dictionary
        analyze_func: Function to analyze and categorize images
        
    Returns:
        dict: Statistics about the processing
    """
    stats = {
        "processed": 0,
        "errors": 0,
        "categories": {}
    }
    
    # Get directories
    base_dir = config["paths"]["base_dir"]
    original_dir = os.path.join(base_dir, config["paths"]["original_dir"])
    
    # Check if original directory exists
    if not os.path.exists(original_dir) or not os.path.isdir(original_dir):
        logger.warning(f"Original directory does not exist: {original_dir}")
        return stats
    
    # Get thresholds and color limits
    thresholds = config["color_thresholds"]
    color_limits = config.get("color_selection_limits")
    
    # Get all image files recursively
    image_files = get_image_files_recursive(original_dir)
    
    # Process each image
    for image_path in image_files:
        try:
            # Get filename for symlink creation
            filename = os.path.basename(image_path)
            
            # Analyze and categorize image
            result = analyze_func(image_path, thresholds, None, None, color_limits)
            
            # Create symlinks for each category
            for category in result["categories"]:
                # Get color directory
                color_dir = os.path.join(base_dir, config["paths"]["color_dirs"][category])
                
                # Create symlink
                symlink_path = os.path.join(color_dir, filename)
                
                # Check if symlink already exists
                if os.path.exists(symlink_path):
                    # Skip if already exists
                    continue
                
                # Create symlink
                os.symlink(image_path, symlink_path)
                
                # Update stats
                stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            # Update stats
            stats["processed"] += 1
            
            # Log progress
            if stats["processed"] % 100 == 0:
                logger.info(f"Processed {stats['processed']} images")
        
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            stats["errors"] += 1
    
    logger.info(f"Processing complete: {stats['processed']} images processed, {stats['errors']} errors")
    return stats


def categorize_existing_images(
    config: Dict[str, Any],
    analyze_func: Callable[[str, Dict[str, float], Any, Any, Any], Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Categorize existing images that are already in the original directory.
    
    Args:
        config: Configuration dictionary
        analyze_func: Function to analyze and categorize images
        
    Returns:
        dict: Statistics about the categorization
    """
    # This is essentially the same as process_new_images
    # since we're just creating symlinks for existing images
    return process_new_images(config, analyze_func)


def get_image_categories(config: Dict[str, Any], image_path: str) -> List[str]:
    """
    Get the categories an image belongs to based on existing symlinks.
    
    Args:
        config: Configuration dictionary
        image_path: Path to the image file
        
    Returns:
        list: Categories the image belongs to
    """
    categories = []
    
    # Get base directory
    base_dir = config["paths"]["base_dir"]
    
    # Get image filename
    filename = os.path.basename(image_path)
    
    # Check each color directory
    for color, color_dir in config["paths"]["color_dirs"].items():
        # Create absolute path
        abs_color_dir = os.path.join(base_dir, color_dir)
        
        # Skip if directory doesn't exist
        if not os.path.exists(abs_color_dir) or not os.path.isdir(abs_color_dir):
            continue
        
        # Check if image exists in this category
        symlink_path = os.path.join(abs_color_dir, filename)
        
        if os.path.exists(symlink_path) and os.path.islink(symlink_path):
            categories.append(color)
    
    return categories


def get_category_counts(config: Dict[str, Any]) -> Dict[str, int]:
    """
    Get the number of images in each category.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        dict: Number of images in each category
    """
    counts = {}
    
    # Get base directory
    base_dir = config["paths"]["base_dir"]
    
    # Count images in each color directory
    for color, color_dir in config["paths"]["color_dirs"].items():
        # Create absolute path
        abs_color_dir = os.path.join(base_dir, color_dir)
        
        # Skip if directory doesn't exist
        if not os.path.exists(abs_color_dir) or not os.path.isdir(abs_color_dir):
            counts[color] = 0
            continue
        
        # Count symlinks in the directory
        count = 0
        for filename in os.listdir(abs_color_dir):
            file_path = os.path.join(abs_color_dir, filename)
            
            if os.path.islink(file_path):
                count += 1
        
        counts[color] = count
    
    return counts


def get_uncategorized_images(config: Dict[str, Any]) -> List[str]:
    """
    Get images that are not categorized in any color category.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        list: Paths to uncategorized images
    """
    uncategorized = []
    
    # Get directories
    base_dir = config["paths"]["base_dir"]
    original_dir = os.path.join(base_dir, config["paths"]["original_dir"])
    
    # Check if original directory exists
    if not os.path.exists(original_dir) or not os.path.isdir(original_dir):
        logger.warning(f"Original directory does not exist: {original_dir}")
        return uncategorized
    
    # Check each image in the original directory
    for filename in os.listdir(original_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            # Create absolute path
            image_path = os.path.join(original_dir, filename)
            
            # Check if image is categorized
            categories = get_image_categories(config, image_path)
            
            if not categories:
                uncategorized.append(image_path)
    
    return uncategorized


if __name__ == "__main__":
    # If run directly, test with a sample configuration
    import sys
    import json
    
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        if os.path.exists(config_path):
            print(f"Loading configuration: {config_path}")
            
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Setup color directories
                print("\nSetting up color directories...")
                results = setup_color_directories(config)
                
                for path, success in results.items():
                    print(f"  {path}: {'Success' if success else 'Failed'}")
                
                # Get category counts
                print("\nCategory counts:")
                counts = get_category_counts(config)
                
                for category, count in counts.items():
                    print(f"  {category}: {count} images")
                
                # Get uncategorized images
                print("\nUncategorized images:")
                uncategorized = get_uncategorized_images(config)
                
                print(f"  {len(uncategorized)} uncategorized images")
                
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"Configuration file not found: {config_path}")
    else:
        print("Usage: python file_operations.py <config_path>")