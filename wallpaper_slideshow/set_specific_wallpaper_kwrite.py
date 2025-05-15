#!/usr/bin/env python3

"""
Script to set a specific wallpaper using the KDE Plasma D-Bus interface.
This script was previously using kwriteconfig5, but now uses the more reliable D-Bus method.
The name is kept for backward compatibility.
"""

import os
import subprocess
import sys
from pathlib import Path

def set_kde_wallpaper_kwrite(image_path):
    """Set the KDE Plasma wallpaper to the specified image using D-Bus."""
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
    success = set_kde_wallpaper_kwrite(image_path)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())