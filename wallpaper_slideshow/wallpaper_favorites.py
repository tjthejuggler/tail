#!/usr/bin/env python3
"""
Wallpaper Favorites Manager

This script manages favorite wallpapers for the slideshow application.
It can add the current wallpaper to favorites, list favorites, and remove favorites.

Usage:
    ./wallpaper_favorites.py --add-current    Add current wallpaper to favorites
    ./wallpaper_favorites.py --list           List all favorite wallpapers
    ./wallpaper_favorites.py --remove PATH    Remove a wallpaper from favorites
    ./wallpaper_favorites.py --gui            Open the favorites management GUI
"""

import os
import sys
import json
import argparse
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import subprocess
import configparser

# Constants
FAVORITES_DIR = os.path.expanduser("~/.wallpaper_favorites")
FAVORITES_FILE = os.path.join(FAVORITES_DIR, "favorites.json")
CURRENT_WALLPAPER_FILE = os.path.expanduser("~/Projects/tail/current-wallpaper")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")

def ensure_favorites_dir():
    """Ensure the favorites directory exists."""
    if not os.path.exists(FAVORITES_DIR):
        os.makedirs(FAVORITES_DIR)

def load_favorites():
    """Load favorites from the JSON file."""
    ensure_favorites_dir()
    if not os.path.exists(FAVORITES_FILE):
        return {"favorites": []}
    
    try:
        with open(FAVORITES_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {FAVORITES_FILE}")
        return {"favorites": []}
    except Exception as e:
        print(f"Error loading favorites: {e}")
        return {"favorites": []}

def save_favorites(data):
    """Save favorites to the JSON file."""
    ensure_favorites_dir()
    try:
        with open(FAVORITES_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving favorites: {e}")
        return False

def get_current_wallpaper():
    """Get the path of the current wallpaper."""
    if not os.path.exists(CURRENT_WALLPAPER_FILE):
        print(f"Error: Current wallpaper file not found at {CURRENT_WALLPAPER_FILE}")
        return None
    
    try:
        with open(CURRENT_WALLPAPER_FILE, 'r') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading current wallpaper: {e}")
        return None

def add_to_favorites(path=None):
    """Add a wallpaper to favorites."""
    if path is None:
        path = get_current_wallpaper()
        if path is None:
            return False
    
    # Ensure the path is absolute
    path = os.path.abspath(path)
    
    # Check if the file exists
    if not os.path.exists(path):
        print(f"Error: File not found at {path}")
        return False
    
    # Load favorites
    data = load_favorites()
    
    # Check if already in favorites
    if path in data["favorites"]:
        print(f"Wallpaper already in favorites: {path}")
        return True
    
    # Add to favorites
    data["favorites"].append(path)
    
    # Save favorites
    if save_favorites(data):
        print(f"Added to favorites: {path}")
        return True
    return False

def remove_from_favorites(path):
    """Remove a wallpaper from favorites."""
    # Ensure the path is absolute
    path = os.path.abspath(path)
    
    # Load favorites
    data = load_favorites()
    
    # Check if in favorites
    if path not in data["favorites"]:
        print(f"Wallpaper not in favorites: {path}")
        return False
    
    # Remove from favorites
    data["favorites"].remove(path)
    
    # Save favorites
    if save_favorites(data):
        print(f"Removed from favorites: {path}")
        return True
    return False

def list_favorites():
    """List all favorite wallpapers."""
    data = load_favorites()
    if not data["favorites"]:
        print("No favorite wallpapers.")
        return []
    
    for i, path in enumerate(data["favorites"]):
        print(f"{i+1}. {path}")
    
    return data["favorites"]

def update_slideshow_config(use_favorites_only=True):
    """Update the slideshow config to use favorites only."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Config file not found at {CONFIG_FILE}")
        return False
    
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        
        if 'General' not in config:
            config['General'] = {}
        
        config['General']['use_favorites_only'] = 'true' if use_favorites_only else 'false'
        
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)
        
        print(f"Updated slideshow config: use_favorites_only = {use_favorites_only}")
        return True
    except Exception as e:
        print(f"Error updating slideshow config: {e}")
        return False

def restart_slideshow():
    """Restart the slideshow to apply changes."""
    restart_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "restart_slideshow.sh")
    if not os.path.exists(restart_script):
        print(f"Error: Restart script not found at {restart_script}")
        return False
    
    try:
        subprocess.run(["bash", restart_script], check=True)
        print("Slideshow restarted successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error restarting slideshow: {e}")
        return False

class FavoritesGUI:
    """GUI for managing favorite wallpapers."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Wallpaper Favorites Manager")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        self.favorites = []
        self.current_image_path = None
        self.current_image_tk = None
        
        self.create_ui()
        self.load_favorites()
    
    def create_ui(self):
        """Create the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Wallpaper Favorites Manager",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)
        
        # Split into left and right panes
        panes = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        panes.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left pane - Favorites list
        left_frame = ttk.Frame(panes)
        panes.add(left_frame, weight=1)
        
        # Favorites list label
        list_label = ttk.Label(
            left_frame,
            text="Favorite Wallpapers",
            font=("Arial", 12, "bold")
        )
        list_label.pack(pady=5)
        
        # Favorites list with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.favorites_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            font=("Arial", 10)
        )
        self.favorites_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.favorites_listbox.yview)
        
        # Bind selection event
        self.favorites_listbox.bind("<<ListboxSelect>>", self.on_favorite_selected)
        
        # Buttons frame
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        # Add button
        add_button = ttk.Button(
            buttons_frame,
            text="Add Current",
            command=self.add_current_wallpaper
        )
        add_button.pack(side=tk.LEFT, padx=5)
        
        # Add from file button
        add_file_button = ttk.Button(
            buttons_frame,
            text="Add from File",
            command=self.add_from_file
        )
        add_file_button.pack(side=tk.LEFT, padx=5)
        
        # Remove button
        remove_button = ttk.Button(
            buttons_frame,
            text="Remove Selected",
            command=self.remove_selected
        )
        remove_button.pack(side=tk.RIGHT, padx=5)
        
        # Right pane - Preview
        right_frame = ttk.Frame(panes)
        panes.add(right_frame, weight=2)
        
        # Preview label
        preview_label = ttk.Label(
            right_frame,
            text="Preview",
            font=("Arial", 12, "bold")
        )
        preview_label.pack(pady=5)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(right_frame, text="Image Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Path label
        self.path_label = ttk.Label(
            right_frame,
            text="",
            wraplength=400
        )
        self.path_label.pack(fill=tk.X, pady=5)
        
        # Set as wallpaper button
        set_button = ttk.Button(
            right_frame,
            text="Set as Wallpaper",
            command=self.set_as_wallpaper
        )
        set_button.pack(pady=5)
        
        # Bottom frame for slideshow controls
        bottom_frame = ttk.LabelFrame(main_frame, text="Slideshow Controls")
        bottom_frame.pack(fill=tk.X, pady=10)
        
        # Use favorites only checkbox
        self.use_favorites_var = tk.BooleanVar(value=False)
        use_favorites_check = ttk.Checkbutton(
            bottom_frame,
            text="Use only favorite wallpapers in slideshow",
            variable=self.use_favorites_var,
            command=self.on_use_favorites_changed
        )
        use_favorites_check.pack(padx=10, pady=5, anchor=tk.W)
        
        # Apply and restart button
        apply_button = ttk.Button(
            bottom_frame,
            text="Apply and Restart Slideshow",
            command=self.apply_and_restart
        )
        apply_button.pack(padx=10, pady=5, anchor=tk.E)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=5)
        
        # Load the current use_favorites_only setting
        self.load_use_favorites_setting()
    
    def load_favorites(self):
        """Load favorites from the JSON file and update the listbox."""
        data = load_favorites()
        self.favorites = data["favorites"]
        
        # Clear listbox
        self.favorites_listbox.delete(0, tk.END)
        
        # Add favorites to listbox
        for path in self.favorites:
            filename = os.path.basename(path)
            self.favorites_listbox.insert(tk.END, filename)
        
        # Update status
        self.status_var.set(f"Loaded {len(self.favorites)} favorite wallpapers")
    
    def load_use_favorites_setting(self):
        """Load the use_favorites_only setting from the config file."""
        if not os.path.exists(CONFIG_FILE):
            return
        
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            
            if 'General' in config and 'use_favorites_only' in config['General']:
                use_favorites = config['General']['use_favorites_only'].lower() == 'true'
                self.use_favorites_var.set(use_favorites)
        except Exception as e:
            print(f"Error loading use_favorites_only setting: {e}")
    
    def on_favorite_selected(self, event):
        """Handle selection of a favorite wallpaper."""
        selection = self.favorites_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < 0 or index >= len(self.favorites):
            return
        
        path = self.favorites[index]
        self.show_preview(path)
    
    def show_preview(self, path):
        """Show a preview of the selected wallpaper."""
        if not os.path.exists(path):
            self.status_var.set(f"Error: File not found at {path}")
            return
        
        try:
            # Load and display image
            img = Image.open(path)
            
            # Resize to fit the label while maintaining aspect ratio
            img_width, img_height = img.size
            
            # Get label dimensions
            label_width = self.preview_label.winfo_width()
            label_height = self.preview_label.winfo_height()
            
            # If the label hasn't been fully initialized yet, use default dimensions
            if label_width < 10 or label_height < 10:
                label_width = 400
                label_height = 300
            
            # Calculate scale factor
            scale = min(label_width / img_width, label_height / img_height)
            
            # Calculate new dimensions
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to PhotoImage
            self.current_image_path = path
            self.current_image_tk = ImageTk.PhotoImage(img)
            
            # Update label
            self.preview_label.config(image=self.current_image_tk)
            
            # Update path label
            self.path_label.config(text=path)
            
            self.status_var.set(f"Showing preview: {os.path.basename(path)}")
            
        except Exception as e:
            self.status_var.set(f"Error showing preview: {e}")
    
    def add_current_wallpaper(self):
        """Add the current wallpaper to favorites."""
        if add_to_favorites():
            self.load_favorites()
            self.status_var.set("Added current wallpaper to favorites")
        else:
            self.status_var.set("Error adding current wallpaper to favorites")
    
    def add_from_file(self):
        """Add a wallpaper from file to favorites."""
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.gif"),
            ("All files", "*.*")
        ]
        
        path = filedialog.askopenfilename(
            title="Select Wallpaper Image",
            filetypes=filetypes
        )
        
        if not path:
            return
        
        if add_to_favorites(path):
            self.load_favorites()
            self.status_var.set(f"Added to favorites: {os.path.basename(path)}")
        else:
            self.status_var.set(f"Error adding to favorites: {os.path.basename(path)}")
    
    def remove_selected(self):
        """Remove the selected wallpaper from favorites."""
        selection = self.favorites_listbox.curselection()
        if not selection:
            self.status_var.set("No wallpaper selected")
            return
        
        index = selection[0]
        if index < 0 or index >= len(self.favorites):
            return
        
        path = self.favorites[index]
        
        # Confirm with user
        result = messagebox.askyesno(
            "Confirm Remove",
            f"Are you sure you want to remove this wallpaper from favorites?\n\n{os.path.basename(path)}"
        )
        
        if not result:
            return
        
        if remove_from_favorites(path):
            self.load_favorites()
            self.status_var.set(f"Removed from favorites: {os.path.basename(path)}")
        else:
            self.status_var.set(f"Error removing from favorites: {os.path.basename(path)}")
    
    def set_as_wallpaper(self):
        """Set the selected wallpaper as the current wallpaper."""
        if not self.current_image_path:
            self.status_var.set("No wallpaper selected")
            return
        
        try:
            # Use the set_wallpaper.sh script
            set_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "set_wallpaper.sh")
            if not os.path.exists(set_script):
                self.status_var.set(f"Error: Set wallpaper script not found at {set_script}")
                return
            
            subprocess.run(["bash", set_script, self.current_image_path], check=True)
            self.status_var.set(f"Set as wallpaper: {os.path.basename(self.current_image_path)}")
        except Exception as e:
            self.status_var.set(f"Error setting wallpaper: {e}")
    
    def on_use_favorites_changed(self):
        """Handle change of the use_favorites_only checkbox."""
        use_favorites = self.use_favorites_var.get()
        self.status_var.set(f"Use favorites only: {use_favorites}")
    
    def apply_and_restart(self):
        """Apply the use_favorites_only setting and restart the slideshow."""
        use_favorites = self.use_favorites_var.get()
        
        # Confirm with user
        result = messagebox.askyesno(
            "Confirm Restart",
            f"Are you sure you want to {'use only favorite wallpapers' if use_favorites else 'use all wallpapers'} and restart the slideshow?"
        )
        
        if not result:
            return
        
        if update_slideshow_config(use_favorites):
            if restart_slideshow():
                self.status_var.set("Applied settings and restarted slideshow")
            else:
                self.status_var.set("Applied settings but failed to restart slideshow")
        else:
            self.status_var.set("Error applying settings")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Wallpaper Favorites Manager")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--add-current", action="store_true", help="Add current wallpaper to favorites")
    group.add_argument("--list", action="store_true", help="List all favorite wallpapers")
    group.add_argument("--remove", metavar="PATH", help="Remove a wallpaper from favorites")
    group.add_argument("--gui", action="store_true", help="Open the favorites management GUI")
    
    args = parser.parse_args()
    
    if args.add_current:
        add_to_favorites()
    elif args.list:
        list_favorites()
    elif args.remove:
        remove_from_favorites(args.remove)
    elif args.gui:
        root = tk.Tk()
        app = FavoritesGUI(root)
        root.mainloop()
    else:
        # Default to GUI
        root = tk.Tk()
        app = FavoritesGUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()