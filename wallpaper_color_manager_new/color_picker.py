#!/usr/bin/env python3
"""
Color Picker

This script provides a standalone color picker tool for:
- Selecting regions of images
- Analyzing color information
- Adding color ranges to color categories

Usage:
    ./color_picker.py [options]

Options:
    --config FILE       Use a specific configuration file
    --image FILE        Open a specific image file
    --verbose           Enable verbose logging
    --help              Show this help message and exit
"""

import os
import sys
import argparse
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image, ImageTk, ImageDraw

# Add the parent directory to the path so we can import the utils package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility modules
from utils import config_manager, color_analysis

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ColorPicker:
    """
    Color Picker GUI.
    """
    
    def __init__(self, root, config_path=None, image_path=None):
        """
        Initialize the Color Picker.
        
        Args:
            root: Tkinter root window
            config_path: Path to the configuration file
            image_path: Path to the image file to open
        """
        self.root = root
        self.root.title("Wallpaper Color Manager - Color Picker")
        # Set window size
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Load configuration
        self.config_path = config_path
        self.config = config_manager.load_config(config_path)
        
        # Initialize variables
        self.image_path = image_path
        self.image = None
        self.image_tk = None
        self.selection_active = False
        self.start_pos = None
        self.current_pos = None
        self.selection_rect = None
        
        # Create UI
        self.create_ui()
        
        # Load image if provided
        if image_path:
            self.load_image(image_path)
    
    def create_ui(self):
        """
        Create the user interface.
        """
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Color Picker",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)
        
        # Description
        desc_label = ttk.Label(
            main_frame,
            text="Click and drag on the image to select a region. The color information for the selected region\n"
                 "will be displayed below. You can add the selected color range to a color category.",
            wraplength=800
        )
        desc_label.pack(pady=5)
        
        # Image frame
        image_frame = ttk.LabelFrame(main_frame, text="Image")
        image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create a canvas for the image
        self.canvas = tk.Canvas(
            image_frame,
            width=600,
            height=400,
            bg="lightgray"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Open image button
        open_button = ttk.Button(
            button_frame,
            text="Open Image",
            command=self.open_image
        )
        open_button.pack(side=tk.LEFT, padx=5)
        
        # Color information frame
        info_frame = ttk.LabelFrame(main_frame, text="Color Information")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create a frame for the color information
        color_info_frame = ttk.Frame(info_frame)
        color_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # RGB values
        rgb_frame = ttk.Frame(color_info_frame)
        rgb_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(rgb_frame, text="RGB:", width=10).pack(side=tk.LEFT, padx=5)
        self.rgb_label = ttk.Label(rgb_frame, text="")
        self.rgb_label.pack(side=tk.LEFT, padx=5)
        
        # HSV values
        hsv_frame = ttk.Frame(color_info_frame)
        hsv_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(hsv_frame, text="HSV:", width=10).pack(side=tk.LEFT, padx=5)
        self.hsv_label = ttk.Label(hsv_frame, text="")
        self.hsv_label.pack(side=tk.LEFT, padx=5)
        
        # Color sample
        sample_frame = ttk.Frame(color_info_frame)
        sample_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(sample_frame, text="Sample:", width=10).pack(side=tk.LEFT, padx=5)
        self.color_sample_canvas = tk.Canvas(
            sample_frame,
            width=100,
            height=20,
            bg="lightgray"
        )
        self.color_sample_canvas.pack(side=tk.LEFT, padx=5)
        
        # Add to category frame
        add_category_frame = ttk.LabelFrame(main_frame, text="Add to Category")
        add_category_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create a frame for the category buttons
        category_buttons_frame = ttk.Frame(add_category_frame)
        category_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create a button for each color category
        for i, color in enumerate(color_analysis.COLOR_CATEGORIES):
            if color == "white_gray_black":
                continue  # Skip white/gray/black
                
            button = ttk.Button(
                category_buttons_frame,
                text=color.capitalize(),
                command=lambda c=color: self.add_to_category(c)
            )
            button.grid(row=i//4, column=i%4, padx=5, pady=2, sticky="ew")
        
        # Configure grid columns to be equal width
        for i in range(4):
            category_buttons_frame.columnconfigure(i, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=5)
    
    def open_image(self):
        """
        Open an image file.
        """
        # Open file dialog
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.gif"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Open Image",
            filetypes=filetypes
        )
        
        if not filename:
            return
        
        # Load image
        self.load_image(filename)
    
    def load_image(self, image_path):
        """
        Load an image file.
        
        Args:
            image_path: Path to the image file
        """
        try:
            # Store image path
            self.image_path = image_path
            
            # Load image
            self.image = Image.open(image_path)
            
            # Resize to fit the canvas while maintaining aspect ratio
            img_width, img_height = self.image.size
            
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # If the canvas hasn't been fully initialized yet, use default dimensions
            if canvas_width < 10 or canvas_height < 10:
                canvas_width = 600
                canvas_height = 400
            
            # Calculate scale factor
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            # Calculate new dimensions
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image
            resized_image = self.image.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to PhotoImage
            self.image_tk = ImageTk.PhotoImage(resized_image)
            
            # Clear canvas
            self.canvas.delete("all")
            
            # Create image on canvas
            self.canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self.image_tk,
                anchor=tk.CENTER
            )
            
            self.status_var.set(f"Loaded image: {os.path.basename(image_path)}")
            
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            self.status_var.set(f"Error loading image: {e}")
            messagebox.showerror(
                "Error",
                f"An error occurred while loading the image:\n\n{e}"
            )
    
    def on_mouse_down(self, event):
        """
        Handle mouse button press.
        
        Args:
            event: Mouse event
        """
        if not self.image_path:
            return
        
        # Start selection
        self.selection_active = True
        self.start_pos = (event.x, event.y)
        self.current_pos = (event.x, event.y)
        
        # Create selection rectangle
        self.selection_rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="red",
            width=2
        )
    
    def on_mouse_drag(self, event):
        """
        Handle mouse drag.
        
        Args:
            event: Mouse event
        """
        if not self.selection_active:
            return
        
        # Update current position
        self.current_pos = (event.x, event.y)
        
        # Update selection rectangle
        x1, y1 = self.start_pos
        x2, y2 = self.current_pos
        
        self.canvas.coords(
            self.selection_rect,
            x1, y1, x2, y2
        )
    
    def on_mouse_up(self, event):
        """
        Handle mouse button release.
        
        Args:
            event: Mouse event
        """
        if not self.selection_active:
            return
        
        # End selection
        self.selection_active = False
        
        # Get selection coordinates
        x1, y1 = self.start_pos
        x2, y2 = self.current_pos
        
        # Ensure x1 <= x2 and y1 <= y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # Analyze selected region
        self.analyze_selected_region(x1, y1, x2, y2)
    
    def analyze_selected_region(self, x1, y1, x2, y2):
        """
        Analyze the selected region of the image.
        
        Args:
            x1: Left coordinate
            y1: Top coordinate
            x2: Right coordinate
            y2: Bottom coordinate
        """
        if not self.image_path or not self.image:
            return
        
        try:
            # Use the resized image that's actually displayed on the canvas
            # This ensures we're getting the exact pixels the user sees
            img = self.image
            
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Calculate image position on canvas (centered)
            img_width, img_height = img.size
            img_x_offset = (canvas_width - img_width) // 2
            img_y_offset = (canvas_height - img_height) // 2
            
            # Adjust coordinates to account for image position
            x1 = x1 - img_x_offset
            y1 = y1 - img_y_offset
            x2 = x2 - img_x_offset
            y2 = y2 - img_y_offset
            
            # Ensure coordinates are within image bounds
            x1 = max(0, min(x1, img_width - 1))
            y1 = max(0, min(y1, img_height - 1))
            x2 = max(0, min(x2, img_width - 1))
            y2 = max(0, min(y2, img_height - 1))
            
            # Ensure x1 <= x2 and y1 <= y2
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            
            # Crop image to selected region
            region = img.crop((x1, y1, x2, y2))
            
            # Log the selection details for debugging
            logger.debug(f"Selected region: ({x1}, {y1}) to ({x2}, {y2})")
            logger.debug(f"Region size: {region.size}")
            
            # Analyze region
            result = color_analysis.analyze_region(region)
            
            # Update color information
            self.update_color_information(result)
            
        except Exception as e:
            logger.error(f"Error analyzing selected region: {e}")
            self.status_var.set(f"Error analyzing selected region: {e}")
    
    def update_color_information(self, result):
        """
        Update the color information display.
        
        Args:
            result: Analysis result
        """
        if not result:
            return
        
        # Update RGB label
        rgb = result.get("average_rgb", (0, 0, 0))
        self.rgb_label.config(text=f"R: {rgb[0]:.0f}, G: {rgb[1]:.0f}, B: {rgb[2]:.0f}")
        
        # Update HSV label
        hsv = result.get("average_hsv", (0, 0, 0))
        self.hsv_label.config(text=f"H: {hsv[0]:.0f}°, S: {hsv[1]:.2f}, V: {hsv[2]:.2f}")
        
        # Update color sample
        rgb_hex = f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"
        self.color_sample_canvas.config(bg=rgb_hex)
        
        # Update status
        categories = result.get("categories", [])
        if categories:
            self.status_var.set(f"Selected region is primarily: {', '.join(categories)}")
        else:
            self.status_var.set("Selected region analyzed")
    
    def add_to_category(self, category):
        """
        Add the selected color range to a category.
        
        Args:
            category: Color category
        """
        if not self.image_path:
            return
        
        try:
            # Get HSV value from label
            hsv_text = self.hsv_label.cget("text")
            
            if not hsv_text:
                messagebox.showwarning(
                    "No Selection",
                    "Please select a region of the image first."
                )
                return
            
            # Parse HSV values
            hsv_parts = hsv_text.split(", ")
            h = float(hsv_parts[0].split(": ")[1].rstrip("°"))
            s = float(hsv_parts[1].split(": ")[1])
            v = float(hsv_parts[2].split(": ")[1])
            
            # Create a new hue range
            if category == "white_gray_black":
                # Special case for white/gray/black
                messagebox.showinfo(
                    "White/Gray/Black",
                    "The white/gray/black category is based on saturation and value thresholds, "
                    "not hue ranges. Please adjust these thresholds in the Color Detection Settings tab."
                )
                return
            
            # Get current color parameters
            if "color_detection_params" not in self.config:
                self.config["color_detection_params"] = {}
            
            if category not in self.config["color_detection_params"]:
                self.config["color_detection_params"][category] = color_analysis.DEFAULT_COLOR_DETECTION_PARAMS[category].copy()
            
            # Get current hue ranges
            hue_ranges = self.config["color_detection_params"][category].get("hue_ranges", [])
            
            # Create a new hue range with +/- 15 degrees
            new_range = [max(0, h - 15), min(360, h + 15)]
            
            # Add the new range
            hue_ranges.append(new_range)
            
            # Update configuration
            self.config["color_detection_params"][category]["hue_ranges"] = hue_ranges
            
            # Save configuration
            config_manager.save_config(self.config, self.config_path)
            
            # Show success message
            messagebox.showinfo(
                "Range Added",
                f"Added hue range {new_range[0]:.0f}° - {new_range[1]:.0f}° to {category.capitalize()} category."
            )
            
        except Exception as e:
            logger.error(f"Error adding to category: {e}")
            self.status_var.set(f"Error adding to category: {e}")
            messagebox.showerror(
                "Error",
                f"An error occurred while adding to category:\n\n{e}"
            )


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Color Picker")
    
    parser.add_argument("--config", type=str,
                        help="Use a specific configuration file")
    
    parser.add_argument("--image", type=str,
                        help="Open a specific image file")
    
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")
    
    return parser.parse_args()


def main():
    """
    Main function.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    try:
        # Create Tkinter root
        root = tk.Tk()
        
        # Create color picker
        app = ColorPicker(root, args.config, args.image)
        
        # Start main loop
        root.mainloop()
        
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())