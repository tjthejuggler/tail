#!/usr/bin/env python3
"""
Wallpaper Color Manager

This script provides a command-line interface for:
- Analyzing images to determine their color composition
- Categorizing images into color categories using symlinks
- Resetting color categories
- Running the control panel

Usage:
    ./wallpaper_color_manager.py [options] [command]

Commands:
    analyze     Analyze images and categorize them
    reset       Reset all color categories
    panel       Run the control panel
    picker      Run the color picker
    help        Show this help message

Options:
    --config FILE       Use a specific configuration file
    --verbose           Enable verbose logging
    --help              Show this help message and exit
"""

import os
import sys
import argparse
import logging
import subprocess
from typing import Dict, List, Any, Optional

# Add the parent directory to the path so we can import the utils package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility modules
from utils import config_manager, color_analysis, file_operations

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_command(args: argparse.Namespace) -> int:
    """
    Analyze images and categorize them.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    # Load configuration
    config = config_manager.load_config(args.config)
    
    # Setup color directories
    logger.info("Setting up color directories...")
    results = file_operations.setup_color_directories(config)
    
    for path, success in results.items():
        if not success:
            logger.error(f"Failed to create directory: {path}")
            return 1
    
    # Reset categories if requested
    if args.reset:
        logger.info("Resetting categories...")
        stats = file_operations.reset_categories(config)
        logger.info(f"Reset complete: {stats['total_removed']} symlinks removed, {stats['errors']} errors")
    
    # Process new images
    logger.info("Processing new images...")
    new_stats = file_operations.process_new_images(
        config,
        lambda path, thresholds, *args: color_analysis.analyze_and_categorize(
            path, thresholds, tuple(config["resize_dimensions"]), config.get("color_detection_params"),
            config.get("color_selection_limits")
        )
    )
    
    logger.info(f"Processed {new_stats['processed']} new images, {new_stats['errors']} errors")
    
    # Print category counts
    logger.info("Category counts:")
    for category, count in new_stats["categories"].items():
        logger.info(f"  {category}: {count} images")
    
    return 0


def reset_command(args: argparse.Namespace) -> int:
    """
    Reset all color categories.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    # Load configuration
    config = config_manager.load_config(args.config)
    
    # Reset categories
    logger.info("Resetting categories...")
    stats = file_operations.reset_categories(config)
    
    logger.info(f"Reset complete: {stats['total_removed']} symlinks removed, {stats['errors']} errors")
    
    return 0


def panel_command(args: argparse.Namespace) -> int:
    """
    Run the control panel.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    # Import here to avoid circular imports
    try:
        from color_control_panel import main as panel_main
        
        # Run the control panel
        return panel_main()
        
    except ImportError:
        logger.error("Failed to import color_control_panel module")
        return 1


def picker_command(args: argparse.Namespace) -> int:
    """
    Run the color picker.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    # Import here to avoid circular imports
    try:
        from color_picker import main as picker_main
        
        # Run the color picker
        return picker_main()
        
    except ImportError:
        logger.error("Failed to import color_picker module")
        return 1


def help_command(args: argparse.Namespace) -> int:
    """
    Show help message.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    print(__doc__)
    return 0


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Wallpaper Color Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Global options
    parser.add_argument("--config", type=str,
                        help="Use a specific configuration file")
    
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")
    
    # Subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze images and categorize them")
    analyze_parser.add_argument("--reset", action="store_true",
                               help="Reset categories before analyzing")
    
    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset all color categories")
    
    # Panel command
    panel_parser = subparsers.add_parser("panel", help="Run the control panel")
    
    # Picker command
    picker_parser = subparsers.add_parser("picker", help="Run the color picker")
    
    # Help command
    help_parser = subparsers.add_parser("help", help="Show this help message")
    
    return parser.parse_args()


def main() -> int:
    """
    Main function.
    
    Returns:
        int: Exit code
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Run the appropriate command
    if args.command == "analyze":
        return analyze_command(args)
    elif args.command == "reset":
        return reset_command(args)
    elif args.command == "panel":
        return panel_command(args)
    elif args.command == "picker":
        return picker_command(args)
    elif args.command == "help" or args.command is None:
        return help_command(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())