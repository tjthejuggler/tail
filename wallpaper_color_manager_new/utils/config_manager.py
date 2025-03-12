"""
Configuration Manager Module

This module provides functions for:
- Loading configuration from a file
- Saving configuration to a file
- Creating default configuration
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "version": "1.0",
    "color_thresholds": {
        "red": 10,
        "orange": 10,
        "green": 10,
        "blue": 10,
        "pink": 10,
        "yellow": 10,
        "white_gray_black": 10
    },
    "color_selection_limits": {
        "with_white_gray_black": {
            "min_colors": 1,
            "max_colors": 3
        },
        "without_white_gray_black": {
            "min_colors": 1,
            "max_colors": 3
        }
    },
    "color_detection_params": {
        "red": {
            "hue_ranges": [[0, 30], [330, 360]],
            "hue_weights": [1.0, 1.0],
            "saturation_range": [0.3, 1.0],
            "value_range": [0.2, 0.9]
        },
        "orange": {
            "hue_ranges": [[30, 60]],
            "hue_weights": [1.0],
            "saturation_range": [0.3, 1.0],
            "value_range": [0.2, 0.9]
        },
        "yellow": {
            "hue_ranges": [[60, 90]],
            "hue_weights": [1.0],
            "saturation_range": [0.3, 1.0],
            "value_range": [0.2, 0.9]
        },
        "green": {
            "hue_ranges": [[90, 150]],
            "hue_weights": [1.0],
            "saturation_range": [0.3, 1.0],
            "value_range": [0.2, 0.9]
        },
        "blue": {
            "hue_ranges": [[150, 210]],
            "hue_weights": [1.0],
            "saturation_range": [0.3, 1.0],
            "value_range": [0.2, 0.9]
        },
        "pink": {
            "hue_ranges": [[210, 330]],
            "hue_weights": [1.0],
            "saturation_range": [0.3, 1.0],
            "value_range": [0.2, 0.9]
        },
        "white_gray_black": {
            "saturation_threshold": 0.2,
            "low_value_threshold": 0.15,
            "high_value_threshold": 0.95
        }
    },
    "sample_images_dir": "sample_images",
    "resize_dimensions": [100, 100],
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
    },
    "last_analysis_dir": "",
    "last_analysis_settings": {},
    "processed_files": {}
}

# Default configuration file path
DEFAULT_CONFIG_PATH = "config.json"


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    # Use default path if none provided
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    # Create absolute path if not already absolute
    if not os.path.isabs(config_path):
        # Assume relative to the application directory
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(app_dir, config_path)
    
    # Check if file exists
    if os.path.exists(config_path):
        try:
            # Load configuration from file
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Loaded configuration from {config_path}")
            
            # Merge with default configuration to ensure all keys exist
            merged_config = DEFAULT_CONFIG.copy()
            deep_update(merged_config, config)
            
            return merged_config
            
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            logger.info("Using default configuration")
            return DEFAULT_CONFIG.copy()
    else:
        logger.warning(f"Configuration file not found: {config_path}")
        logger.info("Creating default configuration")
        
        # Create default configuration
        config = DEFAULT_CONFIG.copy()
        
        # Save default configuration
        save_config(config, config_path)
        
        return config


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    Save configuration to a file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to the configuration file
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Use default path if none provided
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    # Create absolute path if not already absolute
    if not os.path.isabs(config_path):
        # Assume relative to the application directory
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(app_dir, config_path)
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
        
        # Save configuration to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved configuration to {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving configuration to {config_path}: {e}")
        return False


def deep_update(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    Deep update a dictionary with another dictionary.
    
    Args:
        target: Target dictionary to update
        source: Source dictionary with new values
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_update(target[key], value)
        else:
            target[key] = value


def get_config_path() -> str:
    """
    Get the default configuration path.
    
    Returns:
        str: Default configuration path
    """
    # Get application directory
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create absolute path
    config_path = os.path.join(app_dir, DEFAULT_CONFIG_PATH)
    
    return config_path


if __name__ == "__main__":
    # If run directly, create or load the default configuration
    config_path = get_config_path()
    
    print(f"Default configuration path: {config_path}")
    
    # Load configuration
    config = load_config(config_path)
    
    # Print configuration
    print("\nConfiguration:")
    print(json.dumps(config, indent=2))