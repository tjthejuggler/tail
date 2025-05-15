# KDE Wallpaper Identifier

A tool to identify the current wallpaper image being displayed on KDE Plasma, especially useful for slideshow wallpapers that change every 15 seconds.

## Features

- Shows the filename of the currently displayed wallpaper
- **Automatically detects KDE wallpaper configuration** to find the correct wallpaper directory
- **Prioritizes the specific slideshow directory** for faster and more accurate matching
- Uses advanced image comparison techniques (SSIM or MSE) with **histogram analysis** for more accurate identification
- Can crop screenshots to remove desktop elements for better accuracy
- Can display the full path to the wallpaper image
- Can list all images in the slideshow rotation
- Works with KDE Plasma's slideshow wallpaper feature
- Performance optimization options for faster results
- Debug mode for troubleshooting identification issues

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install numpy pillow opencv-python scikit-image
   ```
3. Make the script executable:
   ```bash
   chmod +x get_current_wallpaper.py
   ```
4. Make the wrapper script executable:
   ```bash
   chmod +x current-wallpaper
   ```

## Usage

### Basic Usage

```bash
# Basic usage - shows current wallpaper filename
./current-wallpaper

# Show more details including full path
./current-wallpaper --verbose

# Output only the filename without any additional text (useful for scripts)
./current-wallpaper --name-only

# Fast mode - quicker results with slightly lower accuracy
./current-wallpaper --fast

# Use KDE configuration only (fastest, no screenshot comparison)
./current-wallpaper --kde-config-only

# Get just the name of the current wallpaper (useful for scripts)
./current-wallpaper --name-only
```

### Advanced Options

```bash
# Use SSIM comparison method (more accurate, higher is better)
./current-wallpaper --method ssim

# Use MSE comparison method (lower is better)
./current-wallpaper --method mse

# Crop screenshot to remove desktop elements (improves accuracy)
./current-wallpaper --crop

# Customize crop margins
./current-wallpaper --crop --crop-top 80 --crop-bottom 40 --crop-left 20 --crop-right 20

# Set custom resolution for comparison (lower = faster, higher = more accurate)
./current-wallpaper --resolution 1280x720

# List all images in the slideshow
./current-wallpaper --all-screens

# Get just the filenames of all images in the slideshow
./current-wallpaper --all-screens --name-only

# Manually specify a directory to scan for wallpapers
./current-wallpaper --scan-dir ~/Pictures/Wallpapers

# Enable debug mode (saves debug screenshots for troubleshooting)
./current-wallpaper --debug
```

### Performance Optimization

```bash
# Use fast mode (lower resolution, early stopping)
./current-wallpaper --fast

# Set confidence threshold for early stopping (0.0-1.0)
./current-wallpaper --confidence 0.7

# Limit the number of images to compare
./current-wallpaper --max-images 20

# Combine options for best performance
./current-wallpaper --name-only --fast
```

### Using in Scripts

The `--name-only` option is particularly useful for scripts:

```bash
# Get the current wallpaper filename for use in a script
CURRENT_WALLPAPER=$(./current-wallpaper --name-only --fast)
echo "Current wallpaper is: $CURRENT_WALLPAPER"

# Example: Copy the current wallpaper to another location
cp "/path/to/wallpapers/$CURRENT_WALLPAPER" ~/Pictures/favorites/
```

### Full Help

```bash
python3 get_current_wallpaper.py --help
```

## How It Works

The script uses multiple approaches to identify the current wallpaper:

1. **First tries to get the wallpaper directly from KDE configuration** (fastest method)
2. If that fails, it uses a screenshot-based approach:
   - **Detects KDE wallpaper configuration** to find the correct wallpaper directory
   - Takes a screenshot of the desktop
   - Optionally crops the screenshot to remove desktop elements (panels, icons, etc.)
   - Compares the screenshot with wallpaper images from the detected slideshow directory
   - Uses a combination of Structural Similarity Index (SSIM), Mean Squared Error (MSE), and **histogram analysis** for more robust comparison
   - Identifies the wallpaper with the highest similarity score

### Performance Optimizations

The script includes several optimizations to improve performance:

- **KDE config only mode**: Fastest method that avoids screenshot comparison entirely
- **Slideshow directory detection**: Prioritizes the current slideshow directory for faster matching
- **Resolution**: Lower resolution comparisons are faster but less accurate
- **Early stopping**: Stops comparing once a match with high confidence is reached
- **Image limiting**: Option to limit the number of images to compare (default: 100)
- **Fast mode**: Combines multiple optimizations for the fastest results

### Troubleshooting with Debug Mode

If you're having trouble with the tool identifying the wrong wallpaper, you can use debug mode:

```bash
./current-wallpaper --debug
```

This will:
- Save a copy of the screenshot to `~/wallpaper_debug_screenshot.png`
- Save a copy of the matched wallpaper to `~/wallpaper_debug_match.png`
- Show detailed matching scores and information

You can also manually specify a directory to scan for wallpapers:

```bash
./current-wallpaper --scan-dir ~/Pictures/Wallpapers
```

## Troubleshooting

If you encounter the error `qdbus: could not find a Qt installation of ''`, you may need to install the `qt5-tools` package:

```bash
# For Ubuntu/Debian
sudo apt install qt5-tools

# For Fedora
sudo dnf install qt5-tools
```

## License

This project is open source and available under the MIT License.