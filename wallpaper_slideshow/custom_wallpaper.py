#!/usr/bin/env python3

import os
import time
import random
import subprocess
import signal
import glob
import configparser
from pathlib import Path

# --- Configuration ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")

# Default configuration values
DEFAULT_CONFIG = {
    "image_directory": os.path.expanduser("~/Pictures/Wallpapers"),
    "interval": 300,
    "shuffle": False,
    "supported_extensions": ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'],
    "pid_file": os.path.expanduser("~/.config/custom_wallpaper_slideshow.pid"),
    "log_file": ""
}

def load_config():
    """Load configuration from config.ini file"""
    config = DEFAULT_CONFIG.copy()
    
    if os.path.exists(CONFIG_FILE):
        parser = configparser.ConfigParser()
        try:
            parser.read(CONFIG_FILE)
            
            if 'General' in parser:
                if 'image_directory' in parser['General']:
                    config['image_directory'] = os.path.expanduser(parser['General']['image_directory'])
                
                if 'interval' in parser['General']:
                    config['interval'] = parser.getint('General', 'interval')
                
                if 'shuffle' in parser['General']:
                    config['shuffle'] = parser.getboolean('General', 'shuffle')
            
            if 'Advanced' in parser:
                if 'supported_extensions' in parser['Advanced']:
                    extensions = parser['Advanced']['supported_extensions'].split(',')
                    config['supported_extensions'] = [ext.strip() for ext in extensions]
                
                if 'pid_file' in parser['Advanced']:
                    config['pid_file'] = os.path.expanduser(parser['Advanced']['pid_file'])
                
                if 'log_file' in parser['Advanced']:
                    config['log_file'] = os.path.expanduser(parser['Advanced']['log_file'])
        
        except Exception as e:
            print(f"Error loading config file: {e}")
            print("Using default configuration.")
    else:
        print(f"Config file not found at {CONFIG_FILE}")
        print("Using default configuration.")
    
    return config

# Load configuration
config = load_config()
IMAGE_DIR = config['image_directory']
SLIDESHOW_INTERVAL = config['interval']
SUPPORTED_EXTENSIONS = config['supported_extensions']
PID_FILE = Path(config['pid_file'])
LOG_FILE = config['log_file']
SHUFFLE_IMAGES = config['shuffle']

# --- Global State ---
image_files = []
current_index = -1
paused = False
last_change_time = 0
program_pid = os.getpid()

# --- Helper Functions ---
def log(message):
    log_entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(log_entry)
    
    # If log file is specified, write to it
    if LOG_FILE:
        try:
            # Ensure log file directory exists
            log_dir = os.path.dirname(LOG_FILE)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            with open(LOG_FILE, "a") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")

def get_image_files():
    global image_files, current_index
    log(f"Scanning for images in: {IMAGE_DIR}")
    found_files = []
    if not os.path.isdir(IMAGE_DIR):
        log(f"Error: Image directory '{IMAGE_DIR}' not found or not a directory.")
        image_files = []
        current_index = -1
        return

    for ext in SUPPORTED_EXTENSIONS:
        found_files.extend(glob.glob(os.path.join(IMAGE_DIR, f"*{ext}"), recursive=False))  # Set recursive=True if you have subfolders
        found_files.extend(glob.glob(os.path.join(IMAGE_DIR, f"*{ext.upper()}"), recursive=False))

    if not found_files:
        log("No image files found.")
    else:
        # Deduplicate in case of case-insensitive filesystem and mixed case extensions
        image_files = sorted(list(set(str(Path(f).resolve()) for f in found_files)))
        log(f"Found {len(image_files)} images.")
        
        # Shuffle images if configured to do so
        if SHUFFLE_IMAGES:
            random.shuffle(image_files)
            log("Images shuffled randomly.")
    current_index = -1  # Reset index

def set_kde_wallpaper(image_path):
    if not image_path or not os.path.exists(image_path):
        log(f"Error: Image path is invalid or file does not exist: {image_path}")
        return

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
        log(f"Setting wallpaper to: {file_uri}")
        # Use subprocess to call qdbus with full path
        qdbus_executable = "/usr/lib/qt6/bin/qdbus"
        result = subprocess.run([
            qdbus_executable, "org.kde.plasmashell", "/PlasmaShell",
            "org.kde.PlasmaShell.evaluateScript", script
        ], capture_output=True, text=True, check=False)  # check=False to inspect output

        if result.returncode != 0:
            log(f"Error setting wallpaper via qdbus. Return code: {result.returncode}")
            log(f"Stdout: {result.stdout.strip()}")
            log(f"Stderr: {result.stderr.strip()}")
        elif result.stdout.strip():  # Sometimes Plasma script engine prints its own errors here
            if "Error:" in result.stdout or "failed" in result.stdout:
                log(f"Plasma script engine reported an error: {result.stdout.strip()}")
            else:
                log("Wallpaper set successfully (qdbus returned 0, got output).")
        else:
            log("Wallpaper set successfully (qdbus returned 0, no output).")

    except FileNotFoundError:
        log("Error: qdbus command not found. Is it installed and in your PATH?")
    except Exception as e:
        log(f"An unexpected error occurred while setting wallpaper: {e}")


def change_wallpaper_and_update_state(new_index):
    global current_index, last_change_time
    if not image_files:
        log("No images available to display.")
        return

    current_index = new_index % len(image_files)  # Wrap around
    set_kde_wallpaper(image_files[current_index])
    last_change_time = time.time()
    log(f"Current wallpaper index: {current_index}, Image: {os.path.basename(image_files[current_index])}")

def show_next_image(force_change=False):
    global paused
    if paused and not force_change:
        log("Slideshow is paused. Not changing image.")
        return
    if not image_files:
        log("No images, cannot go to next.")
        return
    log("Showing next image.")
    change_wallpaper_and_update_state(current_index + 1)

def show_previous_image():
    if not image_files:
        log("No images, cannot go to previous.")
        return
    log("Showing previous image.")
    # Calculate previous index, ensuring wrap-around
    prev_idx = (current_index - 1 + len(image_files)) % len(image_files)
    change_wallpaper_and_update_state(prev_idx)


# --- Signal Handlers ---
def handle_sigusr1(signum, frame):  # Next image
    log("SIGUSR1 received: Next image.")
    show_next_image(force_change=True)  # Force change even if paused by interval

def handle_sigusr2(signum, frame):  # Previous image
    log("SIGUSR2 received: Previous image.")
    show_previous_image()

def handle_sighup(signum, frame):  # Reload images from disk
    log("SIGHUP received: Reloading image list.")
    get_image_files()
    if image_files and current_index == -1:  # If list was empty or just reloaded
        show_next_image(force_change=True)

def handle_sigterm(signum, frame):  # Graceful shutdown
    log("SIGTERM received: Shutting down.")
    cleanup_and_exit()

def handle_sigint(signum, frame):  # Ctrl+C
    log("SIGINT received (Ctrl+C): Shutting down.")
    cleanup_and_exit()

def handle_sigtstp(signum, frame):  # Pause/Resume (Ctrl+Z usually sends this, or use kill -TSTP)
    global paused
    paused = not paused
    if paused:
        log("SIGTSTP received: Pausing slideshow.")
    else:
        log("SIGTSTP received: Resuming slideshow.")
        # Optionally, change wallpaper immediately on resume if interval passed
        # if image_files and (time.time() - last_change_time >= SLIDESHOW_INTERVAL):
        #    show_next_image()

def cleanup_and_exit(exit_code=0):
    log("Cleaning up...")
    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
            log(f"Removed PID file: {PID_FILE}")
        except OSError as e:
            log(f"Error removing PID file: {e}")
    log("Exiting.")
    exit(exit_code)

# --- Main Logic ---
if __name__ == "__main__":
    log(f"Custom Wallpaper Slideshow started. PID: {program_pid}")
    log(f"Configuration loaded from: {CONFIG_FILE if os.path.exists(CONFIG_FILE) else 'default values'}")
    log(f"Image directory: {IMAGE_DIR}")
    log(f"Interval: {SLIDESHOW_INTERVAL} seconds")
    log(f"Shuffle mode: {'Enabled' if SHUFFLE_IMAGES else 'Disabled'}")
    log(f"To control: ")
    log(f"  Next:     kill -USR1 {program_pid}")
    log(f"  Previous: kill -USR2 {program_pid}")
    log(f"  Pause/Resume: kill -TSTP {program_pid}")
    log(f"  Reload list: kill -HUP {program_pid}")
    log(f"  Stop:     kill -TERM {program_pid}  (or Ctrl+C if run in foreground)")

    # Write PID to file
    try:
        os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)  # Ensure directory exists
        with open(PID_FILE, "w") as f:
            f.write(str(program_pid))
        log(f"PID file created: {PID_FILE}")
    except IOError as e:
        log(f"Could not write PID file {PID_FILE}: {e}")
        log("Controls requiring PID file might not work as easily.")

    # Register signal handlers
    signal.signal(signal.SIGUSR1, handle_sigusr1)
    signal.signal(signal.SIGUSR2, handle_sigusr2)
    signal.signal(signal.SIGHUP, handle_sighup)
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTSTP, handle_sigtstp)  # For pause/resume

    get_image_files()
    if image_files:
        show_next_image(force_change=True)  # Show first image immediately
    else:
        log("No images found on startup. Waiting for SIGHUP or restart with images.")

    try:
        while True:
            if not paused and image_files and (time.time() - last_change_time >= SLIDESHOW_INTERVAL):
                show_next_image()
            time.sleep(1)  # Check every second
    except Exception as e:
        log(f"Unhandled exception in main loop: {e}")
    finally:
        cleanup_and_exit(1)