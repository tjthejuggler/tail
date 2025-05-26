# Wallpaper Color Manager

A system for organizing wallpapers by color using symlinks, allowing a single image to be categorized into multiple color categories.

## Overview

The Wallpaper Color Manager analyzes images to determine their color composition and organizes them into color categories using symlinks. This allows a single image to appear in multiple color categories without duplicating the file.

Key features:
- Analyze images to determine color composition
- Categorize images into color categories using symlinks
- Configurable color thresholds and detection parameters
- Interactive control panel for adjusting settings and previewing results
- Color picker for selecting color ranges directly from images
- Range weighting system that gives more importance to smaller, more specific color ranges

## System Architecture

The system consists of several components:

1. **Color Analysis Module**: Analyzes images to determine their color composition
2. **File Operations Module**: Manages file operations like creating symlinks and directories
3. **Configuration Manager**: Handles loading and saving configuration
4. **Control Panel**: Provides a graphical user interface for adjusting settings and previewing results
5. **Color Picker**: Allows selecting color ranges directly from images

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install pillow numpy matplotlib
   ```
3. Run the control panel:
   ```
   python color_control_panel.py
   ```

## Usage

### Control Panel

The control panel provides a graphical user interface for adjusting settings and previewing results. It has three tabs:

1. **Main**: Shows sample images, color distribution, and allows adjusting thresholds
2. **Color Detection Settings**: Allows configuring color detection parameters
3. **Color Picker**: Allows selecting color ranges directly from images

#### Main Tab

The main tab shows a sample image and its color distribution. You can:
- Navigate through sample images using the Previous/Next buttons
- Add new sample images using the Add Sample Image button
- Adjust color thresholds using the sliders
- Reset categories using the Reset Categories button
- Run the analysis using the Run Analysis button

#### Color Detection Settings Tab

The color detection settings tab allows configuring color detection parameters for each color category. You can:
- Adjust hue ranges for each color
- Add or remove hue ranges
- Adjust saturation and value ranges
- Reset to defaults using the Reset to Defaults button
- Apply changes using the Apply Changes button

#### Color Picker Tab

The color picker tab allows selecting color ranges directly from images. You can:
- Click and drag on the image to select a region
- View the color information for the selected region
- Add the selected color range to a color category
- Visualize color categories in the image

### Configuration

The system uses a configuration file (`config.json`) to store settings. The configuration includes:

- Color thresholds: Percentage thresholds for each color category
- Color detection parameters: HSV ranges for each color category
- Paths: Paths to the original and color category directories
- Sample images directory: Path to the directory containing sample images
- Resize dimensions: Dimensions to resize images for analysis

### Color Categories

The system supports the following color categories:
- Red
- Orange
- Green
- Blue
- Pink
- Yellow
- White/Gray/Black

Each color category has configurable HSV ranges that determine which pixels are classified as that color.

### How It Works

1. The system analyzes each image to determine its color composition
2. For each color category, if the percentage of pixels in that category exceeds the threshold, the image is categorized into that category
3. The system creates symlinks in the color category directories pointing to the original image
4. This allows a single image to appear in multiple color categories without duplicating the file

### Range Weighting System

The range weighting system gives more importance to smaller, more specific color ranges:

1. For each color category, the system calculates the total size of its hue ranges (in degrees)
2. A weight is assigned to each color based on the inverse of its range size
3. Smaller ranges get higher weights, making them more influential in the color distribution
4. This ensures that colors with very specific, narrow ranges are properly recognized even if they have fewer pixels

For example:
- A color with a narrow range (e.g., 10°) will get a higher weight than a color with a wide range (e.g., 60°)
- This means that even if a small number of pixels fall into a narrow range, they can still significantly contribute to that color's percentage
- The weight formula is: `weight = 360 / (range_size + 60)`, which ensures reasonable weights without extreme values

The range sizes and weights are displayed in the color distribution chart and color picker, allowing you to see how they affect the color analysis.

## Design Decisions

### Why Symlinks?

Using symlinks allows a single image to appear in multiple color categories without duplicating the file. This saves disk space and ensures that changes to the original file are reflected in all categories.

### Why HSV Color Space?

The HSV (Hue, Saturation, Value) color space is more intuitive for color categorization than RGB. Hue represents the color, saturation represents the intensity, and value represents the brightness. This makes it easier to define color categories.

Using HSV also enables our range weighting system, which gives more importance to smaller, more specific hue ranges. This allows for more precise color categorization, especially for colors with narrow hue ranges that might otherwise be overwhelmed by colors with wider ranges.

### Why Configurable Color Detection Parameters?

Different users may have different preferences for what constitutes a "red" or "blue" image. Configurable color detection parameters allow users to customize the system to their preferences.

### Why a Control Panel?

A graphical user interface makes it easier to adjust settings and preview results. The control panel provides a user-friendly way to interact with the system.

### Why a Color Picker?

The color picker allows users to select color ranges directly from images. This makes it easier to fine-tune color detection parameters for specific images or colors.

## File Structure

```
wallpaper_color_manager_new/
├── color_control_panel.py   # Main control panel script
├── color_picker.py          # Color picker module
├── config.json              # Configuration file
├── README.md                # This file
├── sample_images/           # Sample images for the control panel
└── utils/                   # Utility modules
    ├── __init__.py          # Package initialization
    ├── color_analysis.py    # Color analysis module
    ├── config_manager.py    # Configuration manager
    └── file_operations.py   # File operations module
```

## Troubleshooting

### Images Not Categorized Correctly

If images are not being categorized correctly, try:
1. Adjusting the color thresholds
2. Adjusting the color detection parameters
3. Using the color picker to select color ranges directly from the image

### Symlinks Not Created

If symlinks are not being created, check:
1. That the color category directories exist
2. That you have permission to create symlinks
3. That the original directory exists and contains images

### Control Panel Not Working

If the control panel is not working, check:
1. That you have installed all dependencies
2. That the configuration file exists and is valid
3. That the sample images directory exists and contains images

## Recent Bug Fixes

### Version 1.1 (Latest)

**Fixed Issues:**
1. **"Last X days" wallpaper source bug**: Previously, when selecting "Use images from folders in /home/twain/Pictures/lbm_dirs with format (lbm-M-D-YY) within the last X days", the system was only using the most recent folder instead of all folders from the specified time period. This has been fixed to properly include all folders within the specified number of days.

2. **Log file buildup**: Removed automatic file logging that was creating and filling up log files unnecessarily. The application now only logs to the console, preventing disk space issues from accumulated log files.

**Technical Details:**
- Modified `create_symlinks_from_recent_folders()` in `refresh_wallpaper.py` to process all folders within the specified date range, not just the most recent one
- Enhanced logging to show progress when processing multiple folders
- Added handling for duplicate filenames when creating symlinks from multiple folders
- Disabled file logging in `color_control_panel.py` to prevent log file accumulation
- Updated UI messages to accurately reflect when multiple folders are being used

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.