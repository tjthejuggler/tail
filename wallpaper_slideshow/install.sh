#!/bin/bash

# Installation script for the KDE Plasma Wallpaper Slideshow

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== KDE Plasma Wallpaper Slideshow Installer ==="
echo

# Make scripts executable
echo "Making scripts executable..."
chmod +x custom_wallpaper.py
chmod +x control_slideshow.sh
echo "Done."
echo

# Create config directory if it doesn't exist
CONFIG_DIR="$HOME/.config/wallpaper_slideshow"
echo "Creating configuration directory at $CONFIG_DIR..."
mkdir -p "$CONFIG_DIR"
echo "Done."
echo

# Copy config file if it doesn't exist
CONFIG_FILE="$CONFIG_DIR/config.ini"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Copying default configuration file to $CONFIG_FILE..."
    cp config.ini "$CONFIG_FILE"
    echo "Done."
else
    echo "Configuration file already exists at $CONFIG_FILE."
    echo "Skipping to preserve your settings."
fi
echo

# Ask if user wants to install desktop entry
echo "Would you like to install the desktop entry? (y/n)"
read -r install_desktop

if [[ "$install_desktop" =~ ^[Yy]$ ]]; then
    # Create applications directory if it doesn't exist
    APPS_DIR="$HOME/.local/share/applications"
    mkdir -p "$APPS_DIR"
    
    # Copy desktop entry
    echo "Installing desktop entry to $APPS_DIR/wallpaper-slideshow.desktop..."
    cp wallpaper-slideshow.desktop "$APPS_DIR/"
    
    # Update the Exec path in the desktop entry
    sed -i "s|Exec=.*|Exec=$SCRIPT_DIR/custom_wallpaper.py|" "$APPS_DIR/wallpaper-slideshow.desktop"
    echo "Done."
    echo
    
    # Ask if user wants to add to autostart
    echo "Would you like to add the slideshow to autostart? (y/n)"
    read -r add_autostart
    
    if [[ "$add_autostart" =~ ^[Yy]$ ]]; then
        # Create autostart directory if it doesn't exist
        AUTOSTART_DIR="$HOME/.config/autostart"
        mkdir -p "$AUTOSTART_DIR"
        
        # Copy desktop entry to autostart
        echo "Adding to autostart at $AUTOSTART_DIR/wallpaper-slideshow.desktop..."
        cp wallpaper-slideshow.desktop "$AUTOSTART_DIR/"
        
        # Update the Exec path in the desktop entry
        sed -i "s|Exec=.*|Exec=$SCRIPT_DIR/custom_wallpaper.py|" "$AUTOSTART_DIR/wallpaper-slideshow.desktop"
        echo "Done."
    fi
fi
echo

# Create symbolic link to control script
BIN_DIR="$HOME/.local/bin"
if [ ! -d "$BIN_DIR" ]; then
    echo "Creating $BIN_DIR directory..."
    mkdir -p "$BIN_DIR"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo "Adding $BIN_DIR to your PATH in .bashrc..."
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        echo "Please restart your terminal or run 'source ~/.bashrc' for this to take effect."
    fi
fi

echo "Creating symbolic link to control script..."
ln -sf "$SCRIPT_DIR/control_slideshow.sh" "$BIN_DIR/wallpaper-slideshow"
echo "Done. You can now use 'wallpaper-slideshow' command from anywhere."
echo

echo "=== Installation Complete ==="
echo
echo "To start the slideshow now, run:"
echo "  $SCRIPT_DIR/custom_wallpaper.py"
echo
echo "To control the slideshow, use:"
echo "  wallpaper-slideshow next     # Show next wallpaper"
echo "  wallpaper-slideshow prev     # Show previous wallpaper"
echo "  wallpaper-slideshow pause    # Toggle pause/resume"
echo "  wallpaper-slideshow reload   # Reload image list"
echo "  wallpaper-slideshow stop     # Stop the slideshow"
echo
echo "Configuration file is located at:"
echo "  $CONFIG_FILE"
echo
echo "Edit this file to change the image directory, interval, and other settings."
echo