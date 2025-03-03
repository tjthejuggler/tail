# Wallpaper Color Manager

This system manages your wallpaper images based on your weekly habit average. It categorizes images by their dominant color and updates your KDE wallpaper slideshow directory to display images that match a color corresponding to your current weekly habit count.

## Components

1. **wallpaper_color_manager.py**: The main script that categorizes images and updates the wallpaper directory.
2. **image_color_labeler.py**: A tool to manually label images with their correct color category.
3. **improve_color_analyzer.py**: A script that uses the labeled data to improve the color analysis algorithm.

## Directory Structure

```
/home/twain/Pictures/
├── llm_baby_monster/                 # Original directory (KDE looks here)
├── llm_baby_monster_original/        # Master copy of all images
├── llm_baby_monster_new/             # Directory for new images awaiting analysis
├── llm_baby_monster_by_color/        # Color-categorized directories
│   ├── red/
│   ├── orange/
│   ├── green/
│   ├── blue/
│   ├── pink/
│   ├── yellow/
│   └── white_gray_black/
└── llm_baby_monster_current/         # Current active color directory
```

## Color Categories

Images are categorized based on the following weekly average habit count ranges:

- **Red**: count < 13
- **Orange**: 13 < count <= 20
- **Green**: 20 < count <= 30
- **Blue**: 30 < count <= 41
- **Pink**: 41 < count <= 48
- **Yellow**: 48 < count <= 55
- **White/Gray/Black/Colorless**: count > 55 or doesn't fit other categories

## Usage

### Initial Setup

The system is already set up and integrated with your habit tracking system. The `wallpaper_color_manager.py` script is called by the `habits_kde_theme_watchdog.sh` script whenever your habit count changes.

### Adding New Images

1. Place new images in the `/home/twain/Pictures/llm_baby_monster_new/` directory.
2. The next time your habit count changes, the new images will be automatically analyzed, categorized, and added to the appropriate color directory.

### Improving Color Categorization

If you notice that images are not being categorized correctly (e.g., too many images in the white_gray_black category), you can use the following workflow to improve the color analysis:

1. **Label Images**:
   ```bash
   python3 /home/twain/Projects/tail/image_color_labeler.py
   ```
   This will show you images from the white_gray_black directory one by one. Press the corresponding key to indicate the correct color category:
   - `r`: red
   - `o`: orange
   - `g`: green
   - `b`: blue
   - `p`: pink
   - `y`: yellow
   - `w`: white_gray_black
   - `s`: skip this image

2. **Improve Color Analysis**:
   ```bash
   python3 /home/twain/Projects/tail/improve_color_analyzer.py
   ```
   This will analyze the labeled images and update the color ranges in the `wallpaper_color_manager.py` script.

3. **Recategorize Images**:
   ```bash
   python3 /home/twain/Projects/tail/wallpaper_color_manager.py
   ```
   This will recategorize all images using the improved color analysis algorithm.

4. Repeat steps 1-3 as needed until you're satisfied with the categorization.

## Troubleshooting

- **Check the log file**: `/home/twain/logs/wallpaper_manager.log`
- **Reset categorization**: Delete the contents of the color directories (but not the directories themselves) and run the wallpaper_color_manager.py script again.
- **Backup**: The original images are always preserved in the `llm_baby_monster_original` directory.

## Files

- **wallpaper_color_manager.py**: Main script for categorizing images and updating the wallpaper directory.
- **image_color_labeler.py**: Tool for manually labeling images with their correct color category.
- **improve_color_analyzer.py**: Script for improving the color analysis algorithm based on labeled data.
- **wallpaper_color_manager_implementation.md**: Detailed implementation plan and documentation.