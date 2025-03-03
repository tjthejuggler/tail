# Wallpaper Color Manager

This system manages your wallpaper images based on your weekly habit average. It categorizes images by their dominant colors and updates your KDE wallpaper slideshow directory to display images that match a color corresponding to your current weekly habit count.

## Files and Their Purpose

### 1. `wallpaper_color_manager.py`

**Purpose:** The main script that categorizes images and updates the wallpaper directory based on your weekly habit average.

**How to Run:**
```bash
cd /home/twain/Projects/tail/wallpaper_color_manager
./wallpaper_color_manager.py
```

**What it Does:**
- Reads your weekly average from `/home/twain/noteVault/habitCounters/week_average.txt`
- Determines the corresponding color category
- Analyzes images to determine their dominant colors
- Categorizes images into multiple color-specific directories based on their colors
- Updates the KDE wallpaper slideshow directory to point to the appropriate color directory

### 2. `image_color_labeler.py`

**Purpose:** A GUI tool to manually label images with their correct color categories.

**How to Run:**
```bash
cd /home/twain/Projects/tail/wallpaper_color_manager
./image_color_labeler.py
```

**What it Does:**
- Displays images from the original directory one by one
- Allows you to select multiple color categories for each image using checkboxes
- Provides buttons for:
  - **Confirm Selection**: Save the selected colors and move to the next image
  - **Retire Image**: Move the image to the retired directory and remove it from all color folders
  - **Skip Image**: Move to the next image without saving any selections
- Saves your labels to `/home/twain/Pictures/image_color_labels.json`

### 3. `improve_color_analyzer.py`

**Purpose:** Uses your manual labels to improve the color analysis algorithm.

**How to Run:**
```bash
cd /home/twain/Projects/tail/wallpaper_color_manager
./improve_color_analyzer.py
```

**What it Does:**
- Reads your manual labels from `/home/twain/Pictures/image_color_labels.json`
- Handles images with multiple color labels
- Analyzes the color distribution of each labeled image
- Updates the color ranges in `wallpaper_color_manager.py` to improve categorization
- Creates a backup of the original script before making changes

### 4. `wallpaper_color_manager_implementation.md`

**Purpose:** Detailed implementation plan and technical documentation.

**How to Use:**
- Read this file to understand the technical details of the implementation
- Useful for developers who want to modify or extend the system

### 5. `wallpaper_color_manager_README.md`

**Purpose:** General documentation and user guide.

**How to Use:**
- Read this file for an overview of the system and general usage instructions

## Workflow for Improving Color Categorization

1. **Run the Image Labeler:**
   ```bash
   cd /home/twain/Projects/tail/wallpaper_color_manager
   ./image_color_labeler.py
   ```
   Label at least 20-30 images for each color category.

2. **Improve the Color Analysis Algorithm:**
   ```bash
   cd /home/twain/Projects/tail/wallpaper_color_manager
   ./improve_color_analyzer.py
   ```

3. **Recategorize All Images:**
   ```bash
   cd /home/twain/Projects/tail/wallpaper_color_manager
   ./wallpaper_color_manager.py
   ```

4. Repeat steps 1-3 as needed until you're satisfied with the categorization.

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
├── llm_baby_monster_current/         # Current active color directory
└── llm_baby_monster_retired/         # Retired images no longer used as wallpapers
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

## Troubleshooting

- **Check the log file**: `/home/twain/logs/wallpaper_manager.log`
- **Reset categorization**: Delete the contents of the color directories (but not the directories themselves) and run the wallpaper_color_manager.py script again.
- **Backup**: The original images are always preserved in the `llm_baby_monster_original` directory.