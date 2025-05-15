#!/bin/bash

# Test script for the KDE Plasma Wallpaper Slideshow

echo "=== KDE Plasma Wallpaper Slideshow Test ==="
echo

# Check if Python 3 is installed
echo "Checking for Python 3..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Python 3 is installed: $PYTHON_VERSION"
else
    echo "✗ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi
echo

# Check if qdbus is installed
echo "Checking for qdbus..."
if command -v qdbus &> /dev/null; then
    echo "✓ qdbus is installed"
else
    echo "✗ qdbus is not installed. Please install qdbus and try again."
    echo "  - On Kubuntu/Debian: sudo apt install qttools5-dev-tools"
    echo "  - On Fedora: sudo dnf install qt5-qttools-devel"
    echo "  - On Arch/Manjaro: sudo pacman -S qt5-tools"
    exit 1
fi
echo

# Check if the script exists and is executable
SCRIPT_PATH="./custom_wallpaper.py"
echo "Checking for custom_wallpaper.py..."
if [ -f "$SCRIPT_PATH" ]; then
    echo "✓ custom_wallpaper.py exists"
    
    if [ -x "$SCRIPT_PATH" ]; then
        echo "✓ custom_wallpaper.py is executable"
    else
        echo "✗ custom_wallpaper.py is not executable"
        echo "  Running: chmod +x $SCRIPT_PATH"
        chmod +x "$SCRIPT_PATH"
        echo "✓ Made custom_wallpaper.py executable"
    fi
else
    echo "✗ custom_wallpaper.py not found in the current directory"
    exit 1
fi
echo

# Check if config.ini exists
CONFIG_PATH="./config.ini"
echo "Checking for config.ini..."
if [ -f "$CONFIG_PATH" ]; then
    echo "✓ config.ini exists"
else
    echo "✗ config.ini not found in the current directory"
    exit 1
fi
echo

# Check if the image directory exists
IMAGE_DIR=$(grep "image_directory" "$CONFIG_PATH" | cut -d "=" -f 2 | tr -d " ")
# Expand ~ to $HOME
IMAGE_DIR="${IMAGE_DIR/#\~/$HOME}"
echo "Checking image directory: $IMAGE_DIR..."
if [ -d "$IMAGE_DIR" ]; then
    echo "✓ Image directory exists"
    
    # Check if there are images in the directory
    IMAGE_COUNT=$(find "$IMAGE_DIR" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.bmp" -o -name "*.gif" -o -name "*.webp" \) | wc -l)
    if [ "$IMAGE_COUNT" -gt 0 ]; then
        echo "✓ Found $IMAGE_COUNT images in the directory"
    else
        echo "✗ No supported images found in the directory"
        echo "  Please add some images to $IMAGE_DIR"
    fi
else
    echo "✗ Image directory does not exist: $IMAGE_DIR"
    echo "  Please create the directory or update the config.ini file"
fi
echo

# Ask if user wants to run a quick test
echo "Would you like to run a quick test of the slideshow? (y/n)"
read -r run_test

if [[ "$run_test" =~ ^[Yy]$ ]]; then
    echo
    echo "Running a quick test of the slideshow..."
    echo "This will start the slideshow, show a few images, and then stop."
    echo "Press Ctrl+C at any time to stop the test."
    echo
    
    # Start the slideshow
    echo "Starting slideshow..."
    python3 "$SCRIPT_PATH" &
    SLIDESHOW_PID=$!
    
    # Wait for the slideshow to start
    sleep 2
    
    # Check if the slideshow is running
    if ps -p "$SLIDESHOW_PID" > /dev/null; then
        echo "✓ Slideshow started successfully with PID $SLIDESHOW_PID"
        
        # Wait a moment for the first image to be displayed
        echo "Waiting for the first image to be displayed..."
        sleep 3
        
        # Show next image
        echo "Showing next image..."
        kill -USR1 "$SLIDESHOW_PID"
        sleep 3
        
        # Show previous image
        echo "Showing previous image..."
        kill -USR2 "$SLIDESHOW_PID"
        sleep 3
        
        # Pause slideshow
        echo "Pausing slideshow..."
        kill -TSTP "$SLIDESHOW_PID"
        sleep 2
        
        # Resume slideshow
        echo "Resuming slideshow..."
        kill -TSTP "$SLIDESHOW_PID"
        sleep 2
        
        # Stop slideshow
        echo "Stopping slideshow..."
        kill -TERM "$SLIDESHOW_PID"
        sleep 1
        
        # Check if the slideshow was stopped
        if ! ps -p "$SLIDESHOW_PID" > /dev/null; then
            echo "✓ Slideshow stopped successfully"
        else
            echo "✗ Failed to stop slideshow"
            echo "  Killing process..."
            kill -9 "$SLIDESHOW_PID"
        fi
    else
        echo "✗ Failed to start slideshow"
    fi
fi
echo

echo "=== Test Complete ==="
echo
echo "If all checks passed, the wallpaper slideshow should work correctly."
echo "If any checks failed, please fix the issues and try again."
echo