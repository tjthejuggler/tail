#!/usr/bin/env python3

"""
Script to set a specific wallpaper using the KDE Plasma D-Bus interface.
This demonstrates the core functionality of the wallpaper slideshow program.
Also tracks the current wallpaper for instant access by other scripts.
"""

import os
import subprocess
import sys
from pathlib import Path
import importlib.util

def set_kde_wallpaper(image_path):
    """Set the KDE Plasma wallpaper to the specified image."""
    if not image_path or not os.path.exists(image_path):
        print(f"Error: Image path is invalid or file does not exist: {image_path}")
        return False

    # Ensure absolute path and correct file:// prefix
    abs_image_path = str(Path(image_path).resolve())
    file_uri = f"file://{abs_image_path}"

    script = f"""
    var allDesktops = desktops();
    if (allDesktops.length === 0) {{
        print("No desktops found by Plasma scripting engine.");
    }}
    for (var i = 0; i < allDesktops.length; i++) {{
        var d = allDesktops[i];
        d.wallpaperPlugin = "org.kde.image";
        d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
        d.writeConfig("Image", "{file_uri}");
    }}
    """
    try:
        print(f"Setting wallpaper to: {file_uri}")
        # Use subprocess to call qdbus with full path
        qdbus_executable = "/usr/lib/qt6/bin/qdbus"
        result = subprocess.run([
            qdbus_executable, "org.kde.plasmashell", "/PlasmaShell",
            "org.kde.PlasmaShell.evaluateScript", script
        ], capture_output=True, text=True, check=False)

        if result.returncode != 0:
            print(f"Error setting wallpaper via qdbus. Return code: {result.returncode}")
            print(f"Stdout: {result.stdout.strip()}")
            print(f"Stderr: {result.stderr.strip()}")
            return False
        elif result.stdout.strip():  # Sometimes Plasma script engine prints its own errors here
            if "Error:" in result.stdout or "failed" in result.stdout:
                print(f"Plasma script engine reported an error: {result.stdout.strip()}")
                return False
            else:
                print("Wallpaper set successfully (qdbus returned 0, got output).")
                return True
        else:
            print("Wallpaper set successfully (qdbus returned 0, no output).")
            return True

    except FileNotFoundError:
        print("Error: qdbus command not found. Is it installed and in your PATH?")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while setting wallpaper: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <image_path>")
        print("Example:")
        print(f"  {sys.argv[0]} /path/to/wallpaper.jpg")
        return 1

    image_path = sys.argv[1]
    success = set_kde_wallpaper(image_path)
    
    # Track the current wallpaper
    if success:
        try:
            # Try to import the track_current_wallpaper module
            script_dir = os.path.dirname(os.path.abspath(__file__))
            tracker_path = os.path.join(script_dir, "track_current_wallpaper.py")
            
            if os.path.exists(tracker_path):
                # Import the module dynamically
                spec = importlib.util.spec_from_file_location("track_current_wallpaper", tracker_path)
                tracker = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(tracker)
                
                # Save the current wallpaper
                tracker.save_current_wallpaper(image_path)
                print(f"Tracked current wallpaper: {image_path}")
            else:
                print(f"Warning: track_current_wallpaper.py not found at {tracker_path}")
        except Exception as e:
            print(f"Warning: Failed to track current wallpaper: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())