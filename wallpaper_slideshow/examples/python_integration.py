#!/usr/bin/env python3

"""
Example Python script demonstrating how to integrate with the wallpaper slideshow program.
This script shows how to control the slideshow from a Python application.
"""

import os
import time
import signal
import subprocess
import argparse
from pathlib import Path

# Path to the PID file
PID_FILE = os.path.expanduser("~/.config/custom_wallpaper_slideshow.pid")

# Path to the slideshow script (assuming this example is in the examples directory)
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "custom_wallpaper.py")


def is_slideshow_running():
    """Check if the slideshow is running."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            
            # Check if process with this PID exists
            try:
                os.kill(pid, 0)  # Signal 0 doesn't kill the process, just checks if it exists
                return pid
            except OSError:
                return None
        except (ValueError, IOError):
            return None
    return None


def start_slideshow():
    """Start the wallpaper slideshow."""
    print("Starting wallpaper slideshow...")
    
    # Check if slideshow is already running
    if is_slideshow_running():
        print("Slideshow is already running.")
        return
    
    # Make sure the script is executable
    if not os.access(SCRIPT_PATH, os.X_OK):
        os.chmod(SCRIPT_PATH, 0o755)
    
    # Start the slideshow as a background process
    subprocess.Popen([SCRIPT_PATH], 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL, 
                     start_new_session=True)
    
    # Wait for the slideshow to start
    time.sleep(2)
    
    if is_slideshow_running():
        print("Slideshow started successfully.")
    else:
        print("Failed to start slideshow.")


def stop_slideshow():
    """Stop the wallpaper slideshow."""
    pid = is_slideshow_running()
    if pid:
        print(f"Stopping slideshow (PID: {pid})...")
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            if not is_slideshow_running():
                print("Slideshow stopped successfully.")
            else:
                print("Failed to stop slideshow gracefully, forcing termination...")
                os.kill(pid, signal.SIGKILL)
        except OSError as e:
            print(f"Error stopping slideshow: {e}")
    else:
        print("Slideshow is not running.")


def send_signal(sig):
    """Send a signal to the slideshow process."""
    pid = is_slideshow_running()
    if pid:
        try:
            os.kill(pid, sig)
            return True
        except OSError as e:
            print(f"Error sending signal: {e}")
            return False
    else:
        print("Slideshow is not running.")
        return False


def show_next_wallpaper():
    """Show the next wallpaper."""
    print("Showing next wallpaper...")
    if send_signal(signal.SIGUSR1):
        print("Signal sent successfully.")


def show_previous_wallpaper():
    """Show the previous wallpaper."""
    print("Showing previous wallpaper...")
    if send_signal(signal.SIGUSR2):
        print("Signal sent successfully.")


def toggle_pause():
    """Toggle pause/resume of the slideshow."""
    print("Toggling pause/resume...")
    if send_signal(signal.SIGTSTP):
        print("Signal sent successfully.")


def reload_images():
    """Reload the image list."""
    print("Reloading image list...")
    if send_signal(signal.SIGHUP):
        print("Signal sent successfully.")


def run_demo():
    """Run a demo sequence."""
    print("Running demo sequence...")
    
    # Start slideshow if not running
    if not is_slideshow_running():
        start_slideshow()
        time.sleep(2)
    
    # Show a few wallpapers
    show_next_wallpaper()
    time.sleep(2)
    show_next_wallpaper()
    time.sleep(2)
    show_previous_wallpaper()
    time.sleep(2)
    
    # Toggle pause/resume
    print("Pausing slideshow...")
    toggle_pause()
    time.sleep(3)
    print("Resuming slideshow...")
    toggle_pause()
    time.sleep(2)
    
    # Show one more wallpaper
    show_next_wallpaper()
    
    print("Demo sequence completed.")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Control the wallpaper slideshow from Python.")
    parser.add_argument("action", choices=["start", "stop", "next", "prev", "pause", "reload", "status", "demo"],
                        help="Action to perform")
    
    args = parser.parse_args()
    
    if args.action == "start":
        start_slideshow()
    elif args.action == "stop":
        stop_slideshow()
    elif args.action == "next":
        show_next_wallpaper()
    elif args.action == "prev":
        show_previous_wallpaper()
    elif args.action == "pause":
        toggle_pause()
    elif args.action == "reload":
        reload_images()
    elif args.action == "status":
        pid = is_slideshow_running()
        if pid:
            print(f"Slideshow is running with PID: {pid}")
        else:
            print("Slideshow is not running.")
    elif args.action == "demo":
        run_demo()


if __name__ == "__main__":
    main()