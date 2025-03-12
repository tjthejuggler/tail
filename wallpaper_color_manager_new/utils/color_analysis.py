"""
Color analysis module for the Wallpaper Color Manager system.

This module provides functions for:
- Categorizing pixels into color categories
- Analyzing images to determine their color distribution
- Applying thresholds to determine which categories an image belongs to
"""

import os
import logging
from typing import Dict, List, Tuple, Optional, Any, Set
import numpy as np
from PIL import Image
import colorsys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color categories
COLOR_CATEGORIES = [
    "red",
    "orange",
    "green",
    "blue",
    "pink",
    "yellow",
    "white_gray_black"
]

# Default color detection parameters
DEFAULT_COLOR_DETECTION_PARAMS = {
    "red": {
        "hue_ranges": [[0, 30], [330, 360]],
        "saturation_range": [0.3, 1.0],
        "value_range": [0.2, 0.9]
    },
    "orange": {
        "hue_ranges": [[30, 60]],
        "saturation_range": [0.3, 1.0],
        "value_range": [0.2, 0.9]
    },
    "yellow": {
        "hue_ranges": [[60, 90]],
        "saturation_range": [0.3, 1.0],
        "value_range": [0.2, 0.9]
    },
    "green": {
        "hue_ranges": [[90, 150]],
        "saturation_range": [0.3, 1.0],
        "value_range": [0.2, 0.9]
    },
    "blue": {
        "hue_ranges": [[150, 210]],
        "saturation_range": [0.3, 1.0],
        "value_range": [0.2, 0.9]
    },
    "pink": {
        "hue_ranges": [[210, 330]],
        "saturation_range": [0.3, 1.0],
        "value_range": [0.2, 0.9]
    },
    "white_gray_black": {
        "saturation_threshold": 0.2,
        "low_value_threshold": 0.15,
        "high_value_threshold": 0.95
    }
}

# Cache for analyzed images
# Format: {image_path: {resize_dims: analysis_result}}
_analysis_cache = {}


def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """
    Convert RGB color values to HSV.
    
    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)
        
    Returns:
        tuple: (hue, saturation, value) where:
            - hue is in degrees (0-360)
            - saturation is 0-1
            - value is 0-1
    """
    # Normalize RGB values to 0-1
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0
    
    # Convert to HSV
    h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    
    # Convert hue to degrees
    h_degrees = h * 360
    
    return (h_degrees, s, v)


def categorize_pixel_multi(r: int, g: int, b: int, color_params: Dict[str, Any] = None) -> Set[str]:
    """
    Determine which color categories a pixel belongs to, allowing multiple categories.
    
    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)
        color_params: Color detection parameters
        
    Returns:
        set: Set of color category names
    """
    # Use default parameters if none provided
    if color_params is None:
        color_params = DEFAULT_COLOR_DETECTION_PARAMS
    
    # Convert RGB to HSV for better color discrimination
    h, s, v = rgb_to_hsv(r, g, b)
    
    # Check for white/gray/black first (low saturation or extreme value)
    wgb_params = color_params.get("white_gray_black", DEFAULT_COLOR_DETECTION_PARAMS["white_gray_black"])
    sat_threshold = wgb_params.get("saturation_threshold", 0.2)
    low_val_threshold = wgb_params.get("low_value_threshold", 0.15)
    high_val_threshold = wgb_params.get("high_value_threshold", 0.95)
    
    if s < sat_threshold or v < low_val_threshold or v > high_val_threshold:
        return {"white_gray_black"}
    
    # Check each color category
    matching_categories = set()
    
    for color in COLOR_CATEGORIES:
        if color == "white_gray_black":
            continue  # Already checked above
            
        color_param = color_params.get(color, DEFAULT_COLOR_DETECTION_PARAMS[color])
        hue_ranges = color_param.get("hue_ranges", DEFAULT_COLOR_DETECTION_PARAMS[color]["hue_ranges"])
        sat_range = color_param.get("saturation_range", DEFAULT_COLOR_DETECTION_PARAMS[color]["saturation_range"])
        val_range = color_param.get("value_range", DEFAULT_COLOR_DETECTION_PARAMS[color]["value_range"])
        
        # Check if saturation and value are in range
        if not (sat_range[0] <= s <= sat_range[1] and val_range[0] <= v <= val_range[1]):
            continue
            
        # Check if hue is in any of the ranges for this color
        for hue_range in hue_ranges:
            if hue_range[0] <= h < hue_range[1]:
                matching_categories.add(color)
                break
    
    # If no match found, return white_gray_black as fallback
    if not matching_categories:
        return {"white_gray_black"}
    
    return matching_categories


def categorize_pixel(r: int, g: int, b: int, color_params: Dict[str, Any] = None) -> str:
    """
    Determine which color category a pixel belongs to (single category).
    
    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)
        color_params: Color detection parameters
        
    Returns:
        str: Color category name
    """
    # Get all matching categories
    categories = categorize_pixel_multi(r, g, b, color_params)
    
    # Return the first category in the order of COLOR_CATEGORIES
    for color in COLOR_CATEGORIES:
        if color in categories:
            return color
    
    # Fallback
    return "white_gray_black"


def calculate_range_size(hue_ranges: List[List[float]]) -> float:
    """
    Calculate the total size of a set of hue ranges.
    
    Args:
        hue_ranges: List of [min, max] hue ranges
        
    Returns:
        float: Total size of the ranges (in degrees)
    """
    total_size = 0
    for hue_range in hue_ranges:
        # Handle ranges that wrap around 360 degrees
        if hue_range[0] > hue_range[1]:
            # This is a range like [330, 30] that wraps around 360
            size = (360 - hue_range[0]) + hue_range[1]
        else:
            size = hue_range[1] - hue_range[0]
        total_size += size
    return total_size


def analyze_image_multi(image_path: str,
                       resize_dimensions: Tuple[int, int] = (100, 100),
                       color_params: Dict[str, Any] = None) -> Dict[str, Dict[str, float]]:
    """
    Analyze an image to determine its color distribution with multi-category support.
    
    Args:
        image_path: Path to the image file
        resize_dimensions: Dimensions to resize image for analysis
        color_params: Color detection parameters
        
    Returns:
        dict: Contains color percentages and pixel map
    """
    # Check cache first
    cache_key = (image_path, resize_dimensions, str(color_params), "multi")
    if image_path in _analysis_cache and cache_key in _analysis_cache[image_path]:
        return _analysis_cache[image_path][cache_key]
    
    try:
        # Load and resize image
        img = Image.open(image_path)
        img = img.resize(resize_dimensions)
        img = img.convert('RGB')
        
        # Initialize counters
        color_counts = {color: 0 for color in COLOR_CATEGORIES}
        total_pixels = resize_dimensions[0] * resize_dimensions[1]
        
        # Create pixel map to store category assignments
        pixel_map = {}
        
        # Process each pixel
        for x in range(resize_dimensions[0]):
            for y in range(resize_dimensions[1]):
                r, g, b = img.getpixel((x, y))
                categories = categorize_pixel_multi(r, g, b, color_params)
                
                # Store in pixel map
                pixel_map[(x, y)] = list(categories)
                
                # Update counts
                for category in categories:
                    color_counts[category] += 1
        
        # Get range weights from parameters or calculate them
        range_sizes = {}
        range_weights = {}
        
        # Use default parameters if none provided
        if color_params is None:
            color_params = DEFAULT_COLOR_DETECTION_PARAMS
        
        # Get or calculate weights for each color (except white_gray_black)
        for color in COLOR_CATEGORIES:
            if color == "white_gray_black":
                continue
                
            color_param = color_params.get(color, DEFAULT_COLOR_DETECTION_PARAMS[color])
            hue_ranges = color_param.get("hue_ranges", DEFAULT_COLOR_DETECTION_PARAMS[color]["hue_ranges"])
            
            # Calculate total range size (for information only)
            range_size = calculate_range_size(hue_ranges)
            range_sizes[color] = range_size
            
            # Check if user-provided weights exist
            if "hue_weights" in color_param and len(color_param["hue_weights"]) > 0:
                # Use the average of user-provided weights
                user_weights = color_param["hue_weights"]
                # Apply a stronger effect by using the square of the weights
                # This makes higher weights have a much stronger impact
                squared_weights = [w * w for w in user_weights]
                range_weights[color] = sum(squared_weights) / len(squared_weights)
            else:
                # Calculate weight based on inverse of range size (legacy method)
                range_weights[color] = 360 / (range_size + 60)
        
        # Set weight for white_gray_black to 1.0 (no adjustment)
        range_weights["white_gray_black"] = 1.0
        
        # Calculate weighted counts
        weighted_counts = {}
        for color, count in color_counts.items():
            weighted_counts[color] = count * range_weights.get(color, 1.0)
        
        # Calculate total weighted count
        total_weighted_count = sum(weighted_counts.values())
        
        # Calculate weighted percentages
        if total_weighted_count > 0:
            color_percentages = {
                color: (weighted_count / total_weighted_count) * 100
                for color, weighted_count in weighted_counts.items()
            }
        else:
            # Fallback if total_weighted_count is 0
            color_percentages = {color: 0 for color in COLOR_CATEGORIES}
        
        # Prepare result
        result = {
            "color_percentages": color_percentages,
            "pixel_map": pixel_map,
            "range_sizes": range_sizes,
            "range_weights": range_weights
        }
        
        # Cache the result
        if image_path not in _analysis_cache:
            _analysis_cache[image_path] = {}
        _analysis_cache[image_path][cache_key] = result
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing image {image_path}: {e}")
        # Return default result on error
        return {
            "color_percentages": {color: 0 for color in COLOR_CATEGORIES},
            "pixel_map": {},
            "range_sizes": {},
            "range_weights": {}
        }


def analyze_image(image_path: str, 
                 resize_dimensions: Tuple[int, int] = (100, 100),
                 color_params: Dict[str, Any] = None) -> Dict[str, float]:
    """
    Analyze an image to determine its color distribution.
    
    Args:
        image_path: Path to the image file
        resize_dimensions: Dimensions to resize image for analysis
        color_params: Color detection parameters
        
    Returns:
        dict: Color percentages for each category
    """
    # Use multi-category analysis and extract just the percentages
    result = analyze_image_multi(image_path, resize_dimensions, color_params)
    return result["color_percentages"]


def apply_thresholds(color_percentages: Dict[str, float],
                     thresholds: Dict[str, float],
                     color_limits: Optional[Dict[str, Dict[str, int]]] = None) -> List[str]:
    """
    Determine which categories an image belongs to based on thresholds and color limits.
    
    Args:
        color_percentages: Percentage of each color in the image
        thresholds: Threshold percentage for each color
        color_limits: Min/max color limits for with/without white_gray_black
        
    Returns:
        list: Categories the image belongs to
    """
    # Default color limits if not provided
    if color_limits is None:
        color_limits = {
            "with_white_gray_black": {"min_colors": 1, "max_colors": 3},
            "without_white_gray_black": {"min_colors": 1, "max_colors": 3}
        }
    
    # First, find colors that meet their thresholds
    threshold_categories = []
    for color, percentage in color_percentages.items():
        if color in thresholds and percentage >= thresholds[color]:
            threshold_categories.append(color)
    
    # Check if white_gray_black is in the threshold categories
    has_wgb = "white_gray_black" in threshold_categories
    
    # Get the appropriate color limits
    limits = color_limits["with_white_gray_black"] if has_wgb else color_limits["without_white_gray_black"]
    min_colors = limits["min_colors"]
    max_colors = limits["max_colors"]
    
    # If white_gray_black is included, we need to count non-wgb colors separately
    non_wgb_threshold_categories = [c for c in threshold_categories if c != "white_gray_black"]
    
    # Calculate how many additional colors we need to meet the minimum
    additional_needed = max(0, min_colors - len(non_wgb_threshold_categories))
    
    # Final categories list
    categories = threshold_categories.copy()
    
    # If we need additional colors to meet the minimum
    if additional_needed > 0:
        # Get colors that didn't meet thresholds, excluding white_gray_black
        remaining_colors = [(color, percentage) for color, percentage in color_percentages.items()
                           if color not in threshold_categories and color != "white_gray_black" and percentage > 0]
        
        # Sort by percentage (highest first)
        remaining_colors.sort(key=lambda x: x[1], reverse=True)
        
        # Add colors until we reach the minimum or run out of colors
        for i in range(min(additional_needed, len(remaining_colors))):
            categories.append(remaining_colors[i][0])
    
    # If we have too many non-wgb colors, trim to the maximum
    if has_wgb:
        # Keep white_gray_black and limit other colors
        non_wgb_categories = [c for c in categories if c != "white_gray_black"]
        if len(non_wgb_categories) > max_colors:
            # Sort non-wgb categories by percentage
            sorted_categories = sorted(
                [(c, color_percentages[c]) for c in non_wgb_categories],
                key=lambda x: x[1],
                reverse=True
            )
            # Keep only the top max_colors
            kept_categories = [c[0] for c in sorted_categories[:max_colors]]
            # Rebuild categories with white_gray_black and kept categories
            categories = ["white_gray_black"] + kept_categories
    else:
        # No white_gray_black, just limit to max_colors
        if len(categories) > max_colors:
            # Sort categories by percentage
            sorted_categories = sorted(
                [(c, color_percentages[c]) for c in categories],
                key=lambda x: x[1],
                reverse=True
            )
            # Keep only the top max_colors
            categories = [c[0] for c in sorted_categories[:max_colors]]
    
    # Ensure at least one category is selected if all percentages are zero
    if not categories:
        # Find the color with the highest percentage
        max_color = max(color_percentages.items(), key=lambda x: x[1])[0]
        categories.append(max_color)
    
    return categories


def analyze_and_categorize(image_path: str,
                           thresholds: Dict[str, float],
                           resize_dimensions: Tuple[int, int] = (100, 100),
                           color_params: Dict[str, Any] = None,
                           color_limits: Optional[Dict[str, Dict[str, int]]] = None) -> Dict[str, Any]:
    """
    Analyze an image and determine which categories it belongs to.
    
    Args:
        image_path: Path to the image file
        thresholds: Threshold percentage for each color
        resize_dimensions: Dimensions to resize image for analysis
        color_params: Color detection parameters
        color_limits: Min/max color limits for with/without white_gray_black
        
    Returns:
        dict: Analysis result with color percentages and categories
    """
    # Analyze the image
    multi_result = analyze_image_multi(image_path, resize_dimensions, color_params)
    color_percentages = multi_result["color_percentages"]
    
    # Apply thresholds with color limits
    categories = apply_thresholds(color_percentages, thresholds, color_limits)
    
    # Return the result
    return {
        "filename": os.path.basename(image_path),
        "color_percentages": color_percentages,
        "categories": categories,
        "pixel_map": multi_result["pixel_map"]
    }


def get_pixel_color_info(image_path: str, x: int, y: int, 
                        resize_dimensions: Tuple[int, int] = (100, 100),
                        color_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get color information for a specific pixel in an image.
    
    Args:
        image_path: Path to the image file
        x: X coordinate
        y: Y coordinate
        resize_dimensions: Dimensions to resize image for analysis
        color_params: Color detection parameters
        
    Returns:
        dict: Color information for the pixel
    """
    try:
        # Load and resize image
        img = Image.open(image_path)
        img = img.resize(resize_dimensions)
        img = img.convert('RGB')
        
        # Get pixel color
        r, g, b = img.getpixel((x, y))
        
        # Convert to HSV
        h, s, v = rgb_to_hsv(r, g, b)
        
        # Get categories
        categories = categorize_pixel_multi(r, g, b, color_params)
        
        return {
            "rgb": (r, g, b),
            "hsv": (h, s, v),
            "categories": list(categories)
        }
        
    except Exception as e:
        logger.error(f"Error getting pixel color info: {e}")
        return {
            "rgb": (0, 0, 0),
            "hsv": (0, 0, 0),
            "categories": []
        }


def clear_cache() -> None:
    """
    Clear the analysis cache.
    """
    global _analysis_cache
    _analysis_cache = {}
    logger.info("Analysis cache cleared")


def analyze_region(image: Image.Image, color_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Analyze a region of an image to determine its color information.
    
    Args:
        image: PIL Image object of the region
        color_params: Color detection parameters
        
    Returns:
        dict: Color information for the region
    """
    try:
        # Convert to RGB if not already
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get image dimensions
        width, height = image.size
        total_pixels = width * height
        
        if total_pixels == 0:
            return {
                "average_rgb": (0, 0, 0),
                "average_hsv": (0, 0, 0),
                "dominant_category": "white_gray_black",
                "categories": []
            }
        
        # Initialize RGB and HSV accumulators
        r_total, g_total, b_total = 0, 0, 0
        h_total, s_total, v_total = 0, 0, 0
        
        # Initialize category counters
        color_counts = {color: 0 for color in COLOR_CATEGORIES}
        
        # Process each pixel
        for x in range(width):
            for y in range(height):
                r, g, b = image.getpixel((x, y))
                
                # Accumulate RGB values
                r_total += r
                g_total += g
                b_total += b
                
                # Convert to HSV and accumulate
                h, s, v = rgb_to_hsv(r, g, b)
                h_total += h
                s_total += s
                v_total += v
                
                # Categorize pixel
                categories = categorize_pixel_multi(r, g, b, color_params)
                
                # Update category counts
                for category in categories:
                    color_counts[category] += 1
        
        # Calculate averages
        avg_r = r_total / total_pixels
        avg_g = g_total / total_pixels
        avg_b = b_total / total_pixels
        
        avg_h = h_total / total_pixels
        avg_s = s_total / total_pixels
        avg_v = v_total / total_pixels
        
        # Get range weights from parameters or calculate them
        range_sizes = {}
        range_weights = {}
        
        # Use default parameters if none provided
        if color_params is None:
            color_params = DEFAULT_COLOR_DETECTION_PARAMS
        
        # Get or calculate weights for each color (except white_gray_black)
        for color in COLOR_CATEGORIES:
            if color == "white_gray_black":
                continue
                
            color_param = color_params.get(color, DEFAULT_COLOR_DETECTION_PARAMS[color])
            hue_ranges = color_param.get("hue_ranges", DEFAULT_COLOR_DETECTION_PARAMS[color]["hue_ranges"])
            
            # Calculate total range size (for information only)
            range_size = calculate_range_size(hue_ranges)
            range_sizes[color] = range_size
            
            # Check if user-provided weights exist
            if "hue_weights" in color_param and len(color_param["hue_weights"]) > 0:
                # Use the average of user-provided weights
                user_weights = color_param["hue_weights"]
                # Apply a stronger effect by using the square of the weights
                # This makes higher weights have a much stronger impact
                squared_weights = [w * w for w in user_weights]
                range_weights[color] = sum(squared_weights) / len(squared_weights)
            else:
                # Calculate weight based on inverse of range size (legacy method)
                range_weights[color] = 360 / (range_size + 60)
        
        # Set weight for white_gray_black to 1.0 (no adjustment)
        range_weights["white_gray_black"] = 1.0
        
        # Calculate weighted counts
        weighted_counts = {}
        for color, count in color_counts.items():
            weighted_counts[color] = count * range_weights.get(color, 1.0)
        
        # Calculate total weighted count
        total_weighted_count = sum(weighted_counts.values())
        
        # Calculate weighted percentages
        if total_weighted_count > 0:
            category_percentages = {
                color: (weighted_count / total_weighted_count) * 100
                for color, weighted_count in weighted_counts.items()
            }
        else:
            # Fallback if total_weighted_count is 0
            category_percentages = {color: 0 for color in COLOR_CATEGORIES}
        
        # Find dominant category based on weighted counts
        dominant_category = max(weighted_counts.items(), key=lambda x: x[1])[0] if weighted_counts else "white_gray_black"
        
        # Get categories above 10% threshold
        significant_categories = [
            color for color, percentage in category_percentages.items()
            if percentage >= 10
        ]
        
        return {
            "average_rgb": (avg_r, avg_g, avg_b),
            "average_hsv": (avg_h, avg_s, avg_v),
            "dominant_category": dominant_category,
            "categories": significant_categories,
            "category_percentages": category_percentages,
            "range_sizes": range_sizes,
            "range_weights": range_weights
        }
        
    except Exception as e:
        logger.error(f"Error analyzing region: {e}")
        return {
            "average_rgb": (0, 0, 0),
            "average_hsv": (0, 0, 0),
            "dominant_category": "white_gray_black",
            "categories": []
        }


def get_cache_stats() -> Dict[str, int]:
    """
    Get statistics about the analysis cache.
    
    Returns:
        dict: Cache statistics
    """
    total_images = len(_analysis_cache)
    total_analyses = sum(len(analyses) for analyses in _analysis_cache.values())
    
    return {
        "total_images": total_images,
        "total_analyses": total_analyses
    }


if __name__ == "__main__":
    # If run directly, test with a sample image
    import sys
    import json
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        if os.path.exists(image_path):
            print(f"Analyzing image: {image_path}")
            
            # Default thresholds
            thresholds = {color: 10 for color in COLOR_CATEGORIES}
            
            # Try to load color parameters from config.json
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
            color_params = None
            
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        color_params = config.get("color_detection_params")
                except Exception as e:
                    print(f"Error loading config: {e}")
            
            # Analyze and categorize
            result = analyze_and_categorize(image_path, thresholds, color_params=color_params)
            
            # Print results
            print("\nColor Percentages:")
            for color, percentage in result["color_percentages"].items():
                print(f"  {color}: {percentage:.2f}%")
            
            print("\nCategories:")
            for category in result["categories"]:
                print(f"  {category}")
        else:
            print(f"Image not found: {image_path}")
    else:
        print("Usage: python color_analysis.py <image_path>")