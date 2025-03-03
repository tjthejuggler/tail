# Configuration Design

This document outlines the configuration structure for the Wallpaper Color Manager system.

## Configuration File Structure

The system will use a JSON configuration file (`config.json`) with the following structure:

```json
{
  "color_thresholds": {
    "red": 10,
    "orange": 10,
    "green": 10,
    "blue": 10,
    "pink": 10,
    "yellow": 10,
    "white_gray_black": 10
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
  }
}
```

## Configuration Parameters

### Color Thresholds

The `color_thresholds` object defines the minimum percentage of pixels required for an image to be categorized in each color category:

- Each threshold is a percentage value (0-100)
- Default values are set to 10% for all colors
- These thresholds can be adjusted through the control panel

### Sample Images Directory

The `sample_images_dir` parameter specifies the directory where sample images are stored:

- This directory is used by the control panel for visualization
- Users can add their own images to this directory for testing
- Default value is "sample_images" (relative to the application directory)

### Resize Dimensions

The `resize_dimensions` parameter defines the size to which images are resized during analysis:

- Smaller dimensions result in faster analysis but potentially less accurate results
- Larger dimensions provide more accurate analysis but slower performance
- Default value is [100, 100] (width, height)

### Paths

The `paths` object defines all file system paths used by the application:

- `base_dir`: The base directory for all wallpaper operations
- `original_dir`: The directory containing the original wallpaper images
- `color_dirs`: An object mapping color categories to their respective directories

## Configuration Management

The system will include a configuration manager module that provides:

1. **Loading**: Load configuration from the JSON file
2. **Validation**: Ensure all required parameters are present and valid
3. **Defaults**: Provide default values for missing parameters
4. **Saving**: Save updated configuration back to the file
5. **Reset**: Reset configuration to default values

## User Interface for Configuration

The control panel will provide a user-friendly interface for adjusting configuration:

1. **Threshold Sliders**: Adjust color thresholds with immediate visual feedback
2. **Path Settings**: Configure file system paths
3. **Analysis Settings**: Adjust resize dimensions and other analysis parameters
4. **Save/Load**: Save current configuration or load saved configurations

## Configuration File Location

The configuration file will be stored in the application directory:

```
wallpaper_color_manager_new/config.json
```

This location ensures that the configuration is:
- Easy to find and backup
- Accessible to all application components
- Isolated from the original wallpaper manager system

## Configuration Versioning

The system will include version information in the configuration file to handle future updates:

```json
{
  "version": "1.0",
  "color_thresholds": {
    ...
  },
  ...
}
```

This allows the system to:
- Detect outdated configuration files
- Automatically upgrade configuration format when needed
- Maintain backward compatibility