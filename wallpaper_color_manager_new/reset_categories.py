#!/usr/bin/env python3
"""
Reset Categories

This script resets all color categories by removing symlinks.

Usage:
    ./reset_categories.py [options]

Options:
    --config FILE       Use a specific configuration file
    --verbose           Enable verbose logging
    --help              Show this help message and exit
"""

import os
import sys
import argparse
import logging

# Add the parent directory to the path so we can import the utils package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility modules
from utils import config_manager, file_operations

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Reset Categories")
    
    parser.add_argument("--config", type=str,
                        help="Use a specific configuration file")
    
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")
    
    return parser.parse_args()


def main():
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
    
    try:
        # Load configuration
        config = config_manager.load_config(args.config)
        
        # Reset categories
        logger.info("Resetting categories...")
        stats = file_operations.reset_categories(config)
        
        logger.info(f"Reset complete: {stats['total_removed']} symlinks removed, {stats['errors']} errors")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())