#!/usr/bin/env python3
"""
Color Control Panel

This script provides a graphical user interface for:
- Adjusting color threshold settings
- Viewing sample images and their color distributions
- Previewing categorization results
- Resetting color categories
- Running the analysis process

Usage:
    ./color_control_panel.py [options]

Options:
    --config FILE       Use a specific configuration file
    --verbose           Enable verbose logging
    --help              Show this help message and exit
"""

import os
import sys
import argparse
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import shutil
import colorsys
from typing import Dict, List, Any, Optional, Tuple, Set
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk, ImageDraw

# Add the parent directory to the path so we can import the utils package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility modules
from utils import config_manager, color_analysis, file_operations

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ColorControlPanel:
    """
    Color Control Panel GUI.
    """
    
    def __init__(self, root, config_path=None):
        """
        Initialize the Color Control Panel.
        
        Args:
            root: Tkinter root window
            config_path: Path to the configuration file
        """
        self.root = root
        self.root.title("Wallpaper Color Manager - Control Panel")
        # Increase default window size
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Load configuration
        self.config_path = config_path
        self.config = config_manager.load_config(config_path)
        
        # Initialize variables
        self.threshold_vars = {}
        self.color_param_vars = {}
        self.sample_images = []
        self.current_image_index = 0
        self.current_image_path = None
        self.current_image_tk = None
        self.current_analysis = None
        self.current_overlay_image = None
        self.current_overlay_tk = None
        
        # Color picker variables
        self.color_picker_active = False
        self.color_picker_start_pos = None
        self.color_picker_current_pos = None
        self.color_picker_selection = None
        
        # Track processed files
        self.processed_files = self.config.get("processed_files", {})
        
        # Initialize wallpaper source selection
        if "wallpaper_source" not in self.config:
            self.config["wallpaper_source"] = "weekly_habits"
        
        # Create UI
        self.create_ui()
        
        # Load sample images
        self.load_sample_images()
        
        # Show first image
        if self.sample_images:
            self.show_image(0)
    
    def create_ui(self):
        """
        Create the user interface.
        """
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.main_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.limits_tab = ttk.Frame(self.notebook)
        self.color_picker_tab = ttk.Frame(self.notebook)
        self.wallpaper_source_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_tab, text="Main")
        self.notebook.add(self.settings_tab, text="Color Detection Settings")
        self.notebook.add(self.limits_tab, text="Color Selection Limits")
        self.notebook.add(self.color_picker_tab, text="Color Picker")
        self.notebook.add(self.wallpaper_source_tab, text="Wallpaper Source")
        
        # Create main tab UI
        self.create_main_tab_ui()
        
        # Create settings tab UI
        self.create_settings_tab_ui()
        
        # Create color selection limits tab UI
        self.create_limits_tab_ui()
        
        # Create color picker tab UI
        self.create_color_picker_tab_ui()
        
        # Create wallpaper source tab UI
        self.create_wallpaper_source_tab_ui()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=5)
    
    def create_main_tab_ui(self):
        """
        Create the UI for the main tab.
        """
        # Top frame for image and distribution
        top_frame = ttk.Frame(self.main_tab)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Image frame
        image_frame = ttk.LabelFrame(top_frame, text="Sample Image")
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.image_label = ttk.Label(image_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Distribution frame
        dist_frame = ttk.LabelFrame(top_frame, text="Color Distribution")
        dist_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create matplotlib figure for color distribution
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.plot = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, dist_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Categories frame
        categories_frame = ttk.LabelFrame(self.main_tab, text="Categories")
        categories_frame.pack(fill=tk.X, pady=5)
        
        self.category_labels = {}
        category_frame = ttk.Frame(categories_frame)
        category_frame.pack(fill=tk.X, padx=5, pady=5)
        
        for i, color in enumerate(color_analysis.COLOR_CATEGORIES):
            label = ttk.Label(
                category_frame, 
                text=color.capitalize(),
                background="lightgray",
                relief="raised",
                padding=5,
                width=10
            )
            label.grid(row=0, column=i, padx=5, pady=5)
            self.category_labels[color] = label
        
        # Thresholds frame
        thresholds_frame = ttk.LabelFrame(self.main_tab, text="Color Thresholds")
        thresholds_frame.pack(fill=tk.X, pady=5)
        
        # Create sliders for each color
        for i, color in enumerate(color_analysis.COLOR_CATEGORIES):
            frame = ttk.Frame(thresholds_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Color label
            label = ttk.Label(frame, text=f"{color.capitalize()}:", width=15)
            label.pack(side=tk.LEFT, padx=5)
            
            # Threshold variable
            var = tk.DoubleVar(value=self.config["color_thresholds"].get(color, 10))
            self.threshold_vars[color] = var
            
            # Slider
            slider = ttk.Scale(
                frame,
                from_=0,
                to=100,
                orient=tk.HORIZONTAL,
                variable=var,
                command=lambda v, c=color: self.on_threshold_change(c)
            )
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # Value label
            value_label = ttk.Label(frame, text=f"{var.get():.0f}%", width=5)
            value_label.pack(side=tk.LEFT, padx=5)
            
            # Update value label when slider changes
            var.trace_add("write", lambda *args, vl=value_label, v=var: 
                         vl.config(text=f"{v.get():.0f}%"))
        
        # Navigation frame
        nav_frame = ttk.Frame(self.main_tab)
        nav_frame.pack(fill=tk.X, pady=5)
        
        # Previous button
        prev_button = ttk.Button(
            nav_frame,
            text="< Previous Image",
            command=self.prev_image
        )
        prev_button.pack(side=tk.LEFT, padx=5)
        
        # Image counter label
        self.counter_label = ttk.Label(nav_frame, text="0/0")
        self.counter_label.pack(side=tk.LEFT, padx=5)
        
        # Next button
        next_button = ttk.Button(
            nav_frame,
            text="Next Image >",
            command=self.next_image
        )
        next_button.pack(side=tk.LEFT, padx=5)
        
        # Add sample button
        add_button = ttk.Button(
            nav_frame,
            text="Add Sample Image",
            command=self.add_sample_image
        )
        add_button.pack(side=tk.RIGHT, padx=5)
        
        # New images directory frame
        new_images_frame = ttk.LabelFrame(self.main_tab, text="New Images Directory")
        new_images_frame.pack(fill=tk.X, pady=5)
        
        # Directory selection
        dir_frame = ttk.Frame(new_images_frame)
        dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Directory label
        ttk.Label(dir_frame, text="Directory:").pack(side=tk.LEFT, padx=5)
        
        # Directory entry - load from config if available
        last_dir = self.config.get("last_analysis_dir", "")
        self.new_images_dir_var = tk.StringVar(value=last_dir)
        dir_entry = ttk.Entry(dir_frame, textvariable=self.new_images_dir_var, width=40)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Browse button
        browse_button = ttk.Button(
            dir_frame,
            text="Browse...",
            command=self.browse_new_images_dir
        )
        browse_button.pack(side=tk.LEFT, padx=5)
        
        # Help text
        help_text = ttk.Label(
            new_images_frame,
            text="Leave empty to process all images in the original directory (will reset existing categories).\n"
                 "Specify a directory to only process new images from that location (will add to existing categories).",
            wraplength=800
        )
        help_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Action frame
        action_frame = ttk.Frame(self.main_tab)
        action_frame.pack(fill=tk.X, pady=5)
        
        # Button frame for reset options
        reset_frame = ttk.Frame(action_frame)
        reset_frame.pack(side=tk.LEFT)
        
        # Reset Categories button
        reset_button = ttk.Button(
            reset_frame,
            text="Reset Categories",
            command=self.reset_categories
        )
        reset_button.pack(side=tk.LEFT, padx=5)
        
        # Restart Sorting button
        restart_button = ttk.Button(
            reset_frame,
            text="Restart Sorting",
            command=self.restart_sorting
        )
        restart_button.pack(side=tk.LEFT, padx=5)
        
        # Run button
        run_button = ttk.Button(
            action_frame,
            text="Run Analysis",
            command=self.run_analysis
        )
        run_button.pack(side=tk.RIGHT, padx=5)
    
    def create_settings_tab_ui(self):
        """
        Create the UI for the settings tab.
        """
        # Main settings frame
        settings_frame = ttk.Frame(self.settings_tab, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            settings_frame,
            text="Color Detection Settings",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)
        
        # Description
        desc_label = ttk.Label(
            settings_frame,
            text="Adjust the HSV (Hue, Saturation, Value) ranges for each color category.\n"
                 "These settings control how pixels are classified into color categories.",
            wraplength=800
        )
        desc_label.pack(pady=5)
        
        # Create a notebook for color settings
        color_notebook = ttk.Notebook(settings_frame)
        color_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create a tab for each color
        self.color_param_vars = {}
        
        for color in color_analysis.COLOR_CATEGORIES:
            # Skip white_gray_black for now, it has different parameters
            if color == "white_gray_black":
                continue
                
            # Create tab for this color
            color_tab = ttk.Frame(color_notebook)
            color_notebook.add(color_tab, text=color.capitalize())
            
            # Get color parameters
            color_params = self.config.get("color_detection_params", {}).get(
                color, color_analysis.DEFAULT_COLOR_DETECTION_PARAMS[color]
            )
            
            # Initialize variables for this color
            self.color_param_vars[color] = {}
            
            # Add a color spectrum visualization
            spectrum_frame = ttk.LabelFrame(color_tab, text="Hue Spectrum (0-360°)")
            spectrum_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Create a canvas for the spectrum
            spectrum_canvas = tk.Canvas(
                spectrum_frame,
                width=600,
                height=30,
                bg="white"
            )
            spectrum_canvas.pack(fill=tk.X, padx=5, pady=5)
            
            # Store the canvas reference
            self.color_param_vars[color]["spectrum_canvas"] = spectrum_canvas
            
            # Draw the spectrum
            self.draw_hue_spectrum(spectrum_canvas)
            
            # Create UI for hue ranges
            hue_frame = ttk.LabelFrame(color_tab, text="Hue Ranges (0-360°)")
            hue_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Add weight explanation
            weight_info = ttk.Label(
                hue_frame,
                text="Note: Weights have an enhanced effect (squared internally for stronger impact)",
                font=("Arial", 8, "italic"),
                foreground="blue"
            )
            weight_info.pack(fill=tk.X, padx=5, pady=2)
            
            hue_ranges = color_params.get("hue_ranges",
                                         color_analysis.DEFAULT_COLOR_DETECTION_PARAMS[color]["hue_ranges"])
            
            self.color_param_vars[color]["hue_ranges"] = []
            
            for i, hue_range in enumerate(hue_ranges):
                range_frame = ttk.Frame(hue_frame)
                range_frame.pack(fill=tk.X, padx=5, pady=5)
                
                # Range label
                range_label = ttk.Label(range_frame, text=f"Range {i+1}:")
                range_label.pack(side=tk.LEFT, padx=5)
                
                # Min value
                min_var = tk.DoubleVar(value=hue_range[0])
                min_label = ttk.Label(range_frame, text="Min:")
                min_label.pack(side=tk.LEFT, padx=5)
                min_entry = ttk.Spinbox(
                    range_frame,
                    from_=0,
                    to=360,
                    increment=1,
                    width=5,
                    textvariable=min_var,
                    command=lambda c=color: self.update_hue_spectrum(c)
                )
                min_entry.pack(side=tk.LEFT, padx=5)
                
                # Add trace to update spectrum when value changes
                min_var.trace_add("write", lambda *args, c=color: self.update_hue_spectrum(c))
                
                # Max value
                max_var = tk.DoubleVar(value=hue_range[1])
                max_label = ttk.Label(range_frame, text="Max:")
                max_label.pack(side=tk.LEFT, padx=5)
                max_entry = ttk.Spinbox(
                    range_frame,
                    from_=0,
                    to=360,
                    increment=1,
                    width=5,
                    textvariable=max_var,
                    command=lambda c=color: self.update_hue_spectrum(c)
                )
                max_entry.pack(side=tk.LEFT, padx=5)
                
                # Add trace to update spectrum when value changes
                max_var.trace_add("write", lambda *args, c=color: self.update_hue_spectrum(c))
                
                # Store variables
                self.color_param_vars[color]["hue_ranges"].append((min_var, max_var))
                
                # Weight slider
                weight_label = ttk.Label(range_frame, text="Weight:")
                weight_label.pack(side=tk.LEFT, padx=5)
                
                # Get weight from config if available, otherwise default to 1.0
                weight_value = 1.0
                if "hue_weights" in color_params and i < len(color_params["hue_weights"]):
                    weight_value = color_params["hue_weights"][i]
                
                weight_var = tk.DoubleVar(value=weight_value)
                weight_spinbox = ttk.Spinbox(
                    range_frame,
                    from_=0.1,
                    to=20.0,  # Increased maximum to allow for stronger weights
                    increment=0.5,  # Larger increment for easier adjustment
                    width=5,
                    textvariable=weight_var,
                    command=lambda c=color: self.on_color_param_change(c)
                )
                weight_spinbox.pack(side=tk.LEFT, padx=5)
                
                # Store weight variable
                if "weights" not in self.color_param_vars[color]:
                    self.color_param_vars[color]["weights"] = []
                self.color_param_vars[color]["weights"].append(weight_var)

                # Add/remove buttons
                if i == 0:
                    # Add button for first range
                    add_button = ttk.Button(
                        range_frame,
                        text="Add Range",
                        command=lambda c=color: self.add_hue_range(c)
                    )
                    add_button.pack(side=tk.LEFT, padx=5)
                else:
                    # Remove button for additional ranges
                    current_idx = i  # Create a local variable that won't change
                    remove_button = ttk.Button(
                        range_frame,
                        text="Remove",
                        command=lambda c=color, idx=current_idx: self.remove_hue_range(c, idx)
                    )
                    remove_button.pack(side=tk.LEFT, padx=5)
            
            # Create UI for saturation range
            sat_frame = ttk.LabelFrame(color_tab, text="Saturation Range (0-1)")
            sat_frame.pack(fill=tk.X, padx=10, pady=5)
            
            sat_range = color_params.get("saturation_range", 
                                        color_analysis.DEFAULT_COLOR_DETECTION_PARAMS[color]["saturation_range"])
            
            # Min saturation
            sat_min_var = tk.DoubleVar(value=sat_range[0])
            self.color_param_vars[color]["saturation_min"] = sat_min_var
            
            sat_min_frame = ttk.Frame(sat_frame)
            sat_min_frame.pack(fill=tk.X, padx=5, pady=5)
            
            sat_min_label = ttk.Label(sat_min_frame, text="Min Saturation:")
            sat_min_label.pack(side=tk.LEFT, padx=5)
            
            sat_min_slider = ttk.Scale(
                sat_min_frame,
                from_=0,
                to=1,
                orient=tk.HORIZONTAL,
                variable=sat_min_var,
                command=lambda v, c=color: self.on_color_param_change(c)
            )
            sat_min_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            sat_min_value = ttk.Label(sat_min_frame, text=f"{sat_min_var.get():.2f}")
            sat_min_value.pack(side=tk.LEFT, padx=5)
            
            sat_min_var.trace_add("write", lambda *args, vl=sat_min_value, v=sat_min_var: 
                                 vl.config(text=f"{v.get():.2f}"))
            
            # Max saturation
            sat_max_var = tk.DoubleVar(value=sat_range[1])
            self.color_param_vars[color]["saturation_max"] = sat_max_var
            
            sat_max_frame = ttk.Frame(sat_frame)
            sat_max_frame.pack(fill=tk.X, padx=5, pady=5)
            
            sat_max_label = ttk.Label(sat_max_frame, text="Max Saturation:")
            sat_max_label.pack(side=tk.LEFT, padx=5)
            
            sat_max_slider = ttk.Scale(
                sat_max_frame,
                from_=0,
                to=1,
                orient=tk.HORIZONTAL,
                variable=sat_max_var,
                command=lambda v, c=color: self.on_color_param_change(c)
            )
            sat_max_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            sat_max_value = ttk.Label(sat_max_frame, text=f"{sat_max_var.get():.2f}")
            sat_max_value.pack(side=tk.LEFT, padx=5)
            
            sat_max_var.trace_add("write", lambda *args, vl=sat_max_value, v=sat_max_var: 
                                 vl.config(text=f"{v.get():.2f}"))
            
            # Create UI for value range
            val_frame = ttk.LabelFrame(color_tab, text="Value Range (0-1)")
            val_frame.pack(fill=tk.X, padx=10, pady=5)
            
            val_range = color_params.get("value_range", 
                                        color_analysis.DEFAULT_COLOR_DETECTION_PARAMS[color]["value_range"])
            
            # Min value
            val_min_var = tk.DoubleVar(value=val_range[0])
            self.color_param_vars[color]["value_min"] = val_min_var
            
            val_min_frame = ttk.Frame(val_frame)
            val_min_frame.pack(fill=tk.X, padx=5, pady=5)
            
            val_min_label = ttk.Label(val_min_frame, text="Min Value:")
            val_min_label.pack(side=tk.LEFT, padx=5)
            
            val_min_slider = ttk.Scale(
                val_min_frame,
                from_=0,
                to=1,
                orient=tk.HORIZONTAL,
                variable=val_min_var,
                command=lambda v, c=color: self.on_color_param_change(c)
            )
            val_min_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            val_min_value = ttk.Label(val_min_frame, text=f"{val_min_var.get():.2f}")
            val_min_value.pack(side=tk.LEFT, padx=5)
            
            val_min_var.trace_add("write", lambda *args, vl=val_min_value, v=val_min_var: 
                                 vl.config(text=f"{v.get():.2f}"))
            
            # Max value
            val_max_var = tk.DoubleVar(value=val_range[1])
            self.color_param_vars[color]["value_max"] = val_max_var
            
            val_max_frame = ttk.Frame(val_frame)
            val_max_frame.pack(fill=tk.X, padx=5, pady=5)
            
            val_max_label = ttk.Label(val_max_frame, text="Max Value:")
            val_max_label.pack(side=tk.LEFT, padx=5)
            
            val_max_slider = ttk.Scale(
                val_max_frame,
                from_=0,
                to=1,
                orient=tk.HORIZONTAL,
                variable=val_max_var,
                command=lambda v, c=color: self.on_color_param_change(c)
            )
            val_max_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            val_max_value = ttk.Label(val_max_frame, text=f"{val_max_var.get():.2f}")
            val_max_value.pack(side=tk.LEFT, padx=5)
            
            val_max_var.trace_add("write", lambda *args, vl=val_max_value, v=val_max_var: 
                                 vl.config(text=f"{v.get():.2f}"))
        
        # Create tab for white/gray/black
        wgb_tab = ttk.Frame(color_notebook)
        color_notebook.add(wgb_tab, text="White/Gray/Black")
        
        # Get white/gray/black parameters
        wgb_params = self.config.get("color_detection_params", {}).get(
            "white_gray_black", color_analysis.DEFAULT_COLOR_DETECTION_PARAMS["white_gray_black"]
        )
        
        # Initialize variables
        self.color_param_vars["white_gray_black"] = {}
        
        # Create UI for saturation threshold
        sat_frame = ttk.LabelFrame(wgb_tab, text="Saturation Threshold")
        sat_frame.pack(fill=tk.X, padx=10, pady=5)
        
        sat_threshold = wgb_params.get("saturation_threshold", 
                                      color_analysis.DEFAULT_COLOR_DETECTION_PARAMS["white_gray_black"]["saturation_threshold"])
        
        sat_var = tk.DoubleVar(value=sat_threshold)
        self.color_param_vars["white_gray_black"]["saturation_threshold"] = sat_var
        
        sat_frame_inner = ttk.Frame(sat_frame)
        sat_frame_inner.pack(fill=tk.X, padx=5, pady=5)
        
        sat_label = ttk.Label(sat_frame_inner, text="Saturation Threshold:")
        sat_label.pack(side=tk.LEFT, padx=5)
        
        sat_slider = ttk.Scale(
            sat_frame_inner,
            from_=0,
            to=1,
            orient=tk.HORIZONTAL,
            variable=sat_var,
            command=lambda v: self.on_color_param_change("white_gray_black")
        )
        sat_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        sat_value = ttk.Label(sat_frame_inner, text=f"{sat_var.get():.2f}")
        sat_value.pack(side=tk.LEFT, padx=5)
        
        sat_var.trace_add("write", lambda *args, vl=sat_value, v=sat_var: 
                         vl.config(text=f"{v.get():.2f}"))
        
        # Create UI for low value threshold
        low_val_frame = ttk.LabelFrame(wgb_tab, text="Low Value Threshold (for black)")
        low_val_frame.pack(fill=tk.X, padx=10, pady=5)
        
        low_val_threshold = wgb_params.get("low_value_threshold", 
                                          color_analysis.DEFAULT_COLOR_DETECTION_PARAMS["white_gray_black"]["low_value_threshold"])
        
        low_val_var = tk.DoubleVar(value=low_val_threshold)
        self.color_param_vars["white_gray_black"]["low_value_threshold"] = low_val_var
        
        low_val_frame_inner = ttk.Frame(low_val_frame)
        low_val_frame_inner.pack(fill=tk.X, padx=5, pady=5)
        
        low_val_label = ttk.Label(low_val_frame_inner, text="Low Value Threshold:")
        low_val_label.pack(side=tk.LEFT, padx=5)
        
        low_val_slider = ttk.Scale(
            low_val_frame_inner,
            from_=0,
            to=1,
            orient=tk.HORIZONTAL,
            variable=low_val_var,
            command=lambda v: self.on_color_param_change("white_gray_black")
        )
        low_val_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        low_val_value = ttk.Label(low_val_frame_inner, text=f"{low_val_var.get():.2f}")
        low_val_value.pack(side=tk.LEFT, padx=5)
        
        low_val_var.trace_add("write", lambda *args, vl=low_val_value, v=low_val_var: 
                             vl.config(text=f"{v.get():.2f}"))
        
        # Create UI for high value threshold
        high_val_frame = ttk.LabelFrame(wgb_tab, text="High Value Threshold (for white)")
        high_val_frame.pack(fill=tk.X, padx=10, pady=5)
        
        high_val_threshold = wgb_params.get("high_value_threshold", 
                                           color_analysis.DEFAULT_COLOR_DETECTION_PARAMS["white_gray_black"]["high_value_threshold"])
        
        high_val_var = tk.DoubleVar(value=high_val_threshold)
        self.color_param_vars["white_gray_black"]["high_value_threshold"] = high_val_var
        
        high_val_frame_inner = ttk.Frame(high_val_frame)
        high_val_frame_inner.pack(fill=tk.X, padx=5, pady=5)
        
        high_val_label = ttk.Label(high_val_frame_inner, text="High Value Threshold:")
        high_val_label.pack(side=tk.LEFT, padx=5)
        
        high_val_slider = ttk.Scale(
            high_val_frame_inner,
            from_=0,
            to=1,
            orient=tk.HORIZONTAL,
            variable=high_val_var,
            command=lambda v: self.on_color_param_change("white_gray_black")
        )
        high_val_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        high_val_value = ttk.Label(high_val_frame_inner, text=f"{high_val_var.get():.2f}")
        high_val_value.pack(side=tk.LEFT, padx=5)
        
        high_val_var.trace_add("write", lambda *args, vl=high_val_value, v=high_val_var: 
                              vl.config(text=f"{v.get():.2f}"))
        
        # Add buttons for settings management
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Reset to defaults button
        reset_defaults_button = ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_color_params_to_defaults
        )
        reset_defaults_button.pack(side=tk.LEFT, padx=5)
        
        # Apply button
        apply_button = ttk.Button(
            button_frame,
            text="Apply Changes",
            command=self.apply_color_params
        )
        apply_button.pack(side=tk.RIGHT, padx=5)
    
    def load_sample_images(self):
        """
        Load sample images from the sample images directory.
        """
        self.status_var.set("Loading sample images...")
        
        # Get sample images directory
        sample_dir = self.config.get("sample_images_dir", "sample_images")
        
        # Create absolute path
        if not os.path.isabs(sample_dir):
            # Assume relative to the application directory
            app_dir = os.path.dirname(os.path.abspath(__file__))
            sample_dir = os.path.join(app_dir, sample_dir)
        
        # Ensure directory exists
        if not os.path.exists(sample_dir):
            try:
                os.makedirs(sample_dir)
                logger.info(f"Created sample images directory: {sample_dir}")
            except Exception as e:
                logger.error(f"Error creating sample images directory: {e}")
                self.status_var.set("Error loading sample images")
                return
        
        # Get list of sample images
        self.sample_images = []
        for filename in os.listdir(sample_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                self.sample_images.append(os.path.join(sample_dir, filename))
        
        # If no sample images, try to copy some from the original directory
        if not self.sample_images:
            self.status_var.set("No sample images found. Copying from original directory...")
            self.sample_images = file_operations.setup_sample_images(self.config)
        
        # Update counter label
        self.update_counter_label()
        
        self.status_var.set(f"Loaded {len(self.sample_images)} sample images")
    
    def update_counter_label(self):
        """
        Update the image counter label.
        """
        if self.sample_images:
            self.counter_label.config(
                text=f"{self.current_image_index + 1}/{len(self.sample_images)}"
            )
        else:
            self.counter_label.config(text="0/0")
    
    def show_image(self, index):
        """
        Show the image at the specified index.
        
        Args:
            index: Index of the image to show
        """
        if not self.sample_images:
            self.status_var.set("No sample images available")
            return
        
        if index < 0 or index >= len(self.sample_images):
            return
        
        self.current_image_index = index
        self.current_image_path = self.sample_images[index]
        
        try:
            # Load and display image
            img = Image.open(self.current_image_path)
            
            # Resize to fit the label while maintaining aspect ratio
            img_width, img_height = img.size
            
            # Get label dimensions
            label_width = self.image_label.winfo_width()
            label_height = self.image_label.winfo_height()
            
            # If the label hasn't been fully initialized yet, use default dimensions
            if label_width < 10 or label_height < 10:
                label_width = 400
                label_height = 300
            
            # Ensure we don't divide by zero
            if img_width == 0 or img_height == 0:
                logger.error(f"Invalid image dimensions: {img_width}x{img_height}")
                self.status_var.set("Error: Invalid image dimensions")
                return
                
            # Calculate scale factor
            scale = min(label_width / img_width, label_height / img_height)
            
            # Calculate new dimensions
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to PhotoImage
            self.current_image_tk = ImageTk.PhotoImage(img)
            
            # Update label
            self.image_label.config(image=self.current_image_tk)
            
            # Update counter label
            self.update_counter_label()
            
            # Analyze image
            self.analyze_current_image()
            
            # Update color picker image if on that tab
            if self.notebook.index(self.notebook.select()) == 2:  # Color Picker tab
                self.show_color_picker_image(index)
            
            self.status_var.set(f"Showing image: {os.path.basename(self.current_image_path)}")
            
        except Exception as e:
            logger.error(f"Error showing image: {e}")
            self.status_var.set(f"Error showing image: {e}")
    
    def analyze_current_image(self):
        """
        Analyze the current image and update the UI.
        """
        if not self.current_image_path:
            return
        
        try:
            # Get thresholds from UI
            thresholds = {
                color: var.get()
                for color, var in self.threshold_vars.items()
            }
            
            # Get color parameters
            color_params = self.get_color_params()
            
            # Analyze image
            self.current_analysis = color_analysis.analyze_and_categorize(
                self.current_image_path,
                thresholds,
                tuple(self.config["resize_dimensions"]),
                color_params,
                self.config.get("color_selection_limits")
            )
            
            # Update color distribution chart
            self.update_distribution_chart()
            
            # Update category indicators
            self.update_category_indicators()
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            self.status_var.set(f"Error analyzing image: {e}")
    
    def update_distribution_chart(self):
        """
        Update the color distribution chart.
        """
        if not self.current_analysis:
            return
        
        try:
            # Clear the plot
            self.plot.clear()
            
            # Get color percentages
            percentages = self.current_analysis["color_percentages"]
            
            # Get range sizes and weights if available
            range_sizes = self.current_analysis.get("range_sizes", {})
            range_weights = self.current_analysis.get("range_weights", {})
            
            # Get thresholds
            thresholds = {
                color: var.get()
                for color, var in self.threshold_vars.items()
            }
            
            # Create bar chart
            colors = list(percentages.keys())
            values = [percentages[color] for color in colors]
            
            # Create bars
            bars = self.plot.barh(colors, values)
            
            # Color the bars
            for i, bar in enumerate(bars):
                color = colors[i]
                if color == "red":
                    bar.set_color("red")
                elif color == "orange":
                    bar.set_color("orange")
                elif color == "green":
                    bar.set_color("green")
                elif color == "blue":
                    bar.set_color("blue")
                elif color == "pink":
                    bar.set_color("pink")
                elif color == "yellow":
                    bar.set_color("yellow")
                elif color == "white_gray_black":
                    bar.set_color("gray")
            
            # Add threshold markers
            for i, color in enumerate(colors):
                threshold = thresholds.get(color, 10)
                self.plot.axvline(x=threshold, ymin=i/len(colors), ymax=(i+1)/len(colors),
                                 color='black', linestyle='--', linewidth=1)
            
            # Add percentage labels with range size and weight info
            for i, color in enumerate(colors):
                v = values[i]
                label_text = f"{v:.1f}%"
                
                # Add range size and weight info for non-white_gray_black colors
                if color != "white_gray_black" and color in range_sizes and color in range_weights:
                    size = range_sizes[color]
                    weight = range_weights[color]
                    # Show the effective weight (squared) to help user understand the impact
                    label_text += f" (Size: {size:.0f}°, Weight: {weight:.1f}x)"
                
                self.plot.text(v + 1, i, label_text, va='center')
            
            # Set labels and title
            self.plot.set_xlabel("Percentage (with Enhanced Weighting)")
            self.plot.set_title("Color Distribution with Enhanced Weight Effect")
            
            # Set x-axis limits
            self.plot.set_xlim(0, 100)
            
            # Update canvas
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Error updating distribution chart: {e}")
            self.status_var.set(f"Error updating distribution chart: {e}")
    
    def update_category_indicators(self):
        """
        Update the category indicators.
        """
        if not self.current_analysis:
            return
        
        try:
            # Get categories
            categories = self.current_analysis["categories"]
            
            # Update labels
            for color, label in self.category_labels.items():
                if color in categories:
                    label.config(background="lightgreen", relief="raised")
                else:
                    label.config(background="lightgray", relief="flat")
            
        except Exception as e:
            logger.error(f"Error updating category indicators: {e}")
            self.status_var.set(f"Error updating category indicators: {e}")
    
    def on_threshold_change(self, color):
        """
        Handle threshold change event.
        
        Args:
            color: Color category that changed
        """
        # Update configuration
        self.config["color_thresholds"][color] = self.threshold_vars[color].get()
        
        # Save configuration
        config_manager.save_config(self.config, self.config_path)
        
        # Re-analyze current image
        self.analyze_current_image()
    
    def prev_image(self):
        """
        Show the previous image.
        """
        if self.sample_images:
            index = (self.current_image_index - 1) % len(self.sample_images)
            self.show_image(index)
    
    def next_image(self):
        """
        Show the next image.
        """
        if self.sample_images:
            index = (self.current_image_index + 1) % len(self.sample_images)
            self.show_image(index)
    
    def add_sample_image(self):
        """
        Add a new sample image.
        """
        # Get sample images directory
        sample_dir = self.config.get("sample_images_dir", "sample_images")
        
        # Create absolute path
        if not os.path.isabs(sample_dir):
            # Assume relative to the application directory
            app_dir = os.path.dirname(os.path.abspath(__file__))
            sample_dir = os.path.join(app_dir, sample_dir)
        
        # Open file dialog
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.gif"),
            ("All files", "*.*")
        ]
        
        filenames = filedialog.askopenfilenames(
            title="Select Sample Images",
            filetypes=filetypes
        )
        
        if not filenames:
            return
        
        # Copy selected files to sample directory
        for src in filenames:
            try:
                # Get filename
                filename = os.path.basename(src)
                
                # Create destination path
                dst = os.path.join(sample_dir, filename)
                
                # Copy file
                shutil.copy2(src, dst)
                
                # Add to sample images list
                self.sample_images.append(dst)
                
                self.status_var.set(f"Added sample image: {filename}")
                
            except Exception as e:
                logger.error(f"Error adding sample image: {e}")
                self.status_var.set(f"Error adding sample image: {e}")
        
        # Update counter label
        self.update_counter_label()
        
        # Show the first added image
        if self.sample_images:
            self.show_image(len(self.sample_images) - len(filenames))
    
    def reset_categories(self):
        """
        Reset all color categories.
        """
        # Confirm with user
        result = messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset all color categories?\n\n"
            "This will remove all symlinks and clear all categorizations."
        )
        
        if not result:
            return
        
        # Disable UI during reset
        self.disable_ui()
        self.status_var.set("Resetting categories...")
        
        # Run reset in a separate thread
        thread = threading.Thread(target=self._reset_categories_thread)
        thread.daemon = True
        thread.start()
    
    def _reset_categories_thread(self):
        """
        Reset categories in a separate thread.
        """
        try:
            # Reset categories
            stats = file_operations.reset_categories(self.config)
            
            # Update UI
            self.root.after(0, lambda: self.status_var.set(
                f"Reset complete: {stats['total_removed']} symlinks removed, "
                f"{stats['errors']} errors"
            ))
            
            # Show result
            if stats["errors"] > 0:
                self.root.after(0, lambda: messagebox.showwarning(
                    "Reset Complete",
                    f"Reset completed with {stats['errors']} errors.\n\n"
                    f"See log for details."
                ))
            else:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Reset Complete",
                    f"Reset completed successfully.\n\n"
                    f"{stats['total_removed']} symlinks removed."
                ))
            
        except Exception as e:
            logger.error(f"Error resetting categories: {e}")
            self.root.after(0, lambda: self.status_var.set(f"Error resetting categories: {e}"))
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"An error occurred while resetting categories:\n\n{e}"
            ))
        
        finally:
            # Re-enable UI
            self.root.after(0, self.enable_ui)
    
    def browse_new_images_dir(self):
        """
        Open a directory selection dialog for new images.
        """
        # Open directory dialog
        directory = filedialog.askdirectory(
            title="Select New Images Directory"
        )
        
        if directory:
            self.new_images_dir_var.set(directory)
            # Save to configuration
            self.config["last_analysis_dir"] = directory
            config_manager.save_config(self.config, self.config_path)
            self.status_var.set(f"Selected new images directory: {directory}")
    
    def run_analysis(self):
        """
        Run the analysis process.
        """
        # Check if a custom directory is specified
        custom_dir = self.new_images_dir_var.get().strip()
        
        # Prepare confirmation message
        if custom_dir:
            message = (f"Are you sure you want to run the analysis process?\n\n"
                      f"This will process images from the custom directory:\n"
                      f"{custom_dir}\n\n"
                      f"and categorize them based on current thresholds and color detection settings.")
        else:
            message = ("Are you sure you want to run the analysis process?\n\n"
                      "This will categorize all images in the original directory based on current "
                      "thresholds and color detection settings.")
        
        # Confirm with user
        result = messagebox.askyesno(
            "Confirm Analysis",
            message
        )
        
        if not result:
            return
        
        # Disable UI during analysis
        self.disable_ui()
        self.status_var.set("Running analysis...")
        
        # Run analysis in a separate thread
        thread = threading.Thread(target=self._run_analysis_thread)
        thread.daemon = True
        thread.start()
    
    def _run_analysis_thread(self):
        """
        Run analysis in a separate thread.
        """
        try:
            # Get color parameters
            color_params = self.get_color_params()
            
            # Check if a custom directory is specified
            custom_dir = self.new_images_dir_var.get().strip()
            
            # Save current analysis settings
            current_settings = {
                "color_thresholds": self.config["color_thresholds"].copy(),
                "color_detection_params": self.config["color_detection_params"].copy(),
                "color_selection_limits": self.config["color_selection_limits"].copy(),
                "timestamp": time.time()
            }
            
            # Create a settings hash for tracking processed files
            settings_hash = str(hash(str(current_settings)))
            self.config["last_analysis_settings"] = current_settings
            
            # Initialize processed files tracking for this settings hash if needed
            if settings_hash not in self.processed_files:
                self.processed_files[settings_hash] = []
            
            if custom_dir:
                # When using a custom directory, we don't reset categories
                # We just add the new images to the existing categories
                reset_stats = {"total_removed": 0, "errors": 0}
                
                # Create a copy of the config with the custom directory
                custom_config = self.config.copy()
                custom_config["paths"] = self.config["paths"].copy()
                custom_config["paths"]["original_dir"] = custom_dir
                
                # Process images from the custom directory
                self.root.after(0, lambda: self.status_var.set(
                    f"Processing images from custom directory: {custom_dir}..."
                ))
                
                # Process new images from custom directory with file tracking
                new_stats = self.process_new_images_with_tracking(
                    custom_config,
                    color_params,
                    settings_hash
                )
                
                # Skip categorizing existing images since we're only processing the custom directory
                existing_stats = {"processed": 0, "errors": 0, "categories": {}}
            else:
                # For the original directory, first reset categories
                reset_stats = file_operations.reset_categories(self.config)
                
                # Update UI
                self.root.after(0, lambda: self.status_var.set(
                    f"Reset complete. Analyzing images..."
                ))
                
                # Process new images from the original directory in config with file tracking
                new_stats = self.process_new_images_with_tracking(
                    self.config,
                    color_params,
                    settings_hash
                )
                
                # Update UI
                self.root.after(0, lambda: self.status_var.set(
                    f"Processed new images. Categorizing existing images..."
                ))
                
                # Categorize existing images with file tracking
                existing_stats = self.process_new_images_with_tracking(
                    self.config,
                    color_params,
                    settings_hash
                )
            
            # Save processed files to config
            self.config["processed_files"] = self.processed_files
            config_manager.save_config(self.config, self.config_path)
            
            # Update UI
            self.root.after(0, lambda: self.status_var.set(
                f"Analysis complete"
            ))
            
            # Prepare result message
            message = "Analysis completed.\n\n"
            
            # Add information about the directory used
            custom_dir = self.new_images_dir_var.get().strip()
            if custom_dir:
                message += f"Processed images from custom directory:\n{custom_dir}\n\n"
            
            if new_stats["processed"] > 0:
                message += f"Processed {new_stats['processed']} new images.\n"
            
            if existing_stats["processed"] > 0:
                message += f"Categorized {existing_stats['processed']} existing images.\n"
            
            message += "\nCategory counts:\n"
            
            # Combine category counts
            category_counts = {}
            for category in self.config["color_thresholds"]:
                count = (new_stats["categories"].get(category, 0) +
                        existing_stats["categories"].get(category, 0))
                category_counts[category] = count
                message += f"  {category}: {count} images\n"
            
            # Show result
            total_errors = (reset_stats["errors"] + new_stats["errors"] +
                           existing_stats["errors"])
            
            if total_errors > 0:
                message += f"\nCompleted with {total_errors} errors. See log for details."
                self.root.after(0, lambda: messagebox.showwarning(
                    "Analysis Complete",
                    message
                ))
            else:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Analysis Complete",
                    message
                ))
                
            # Clear the custom directory field after processing
            if custom_dir:
                self.root.after(0, lambda: self.new_images_dir_var.set(""))
            
        except Exception as e:
            logger.error(f"Error running analysis: {e}")
            self.root.after(0, lambda: self.status_var.set(f"Error running analysis: {e}"))
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"An error occurred while running analysis:\n\n{e}"
            ))
        
        finally:
            # Re-enable UI
            self.root.after(0, self.enable_ui)
    
    def add_hue_range(self, color):
        """
        Add a new hue range for a color.
        
        Args:
            color: Color category
        """
        # Create a new frame for the range
        color_tab = self.notebook.nametowidget(self.notebook.select())
        hue_frame = None
        
        # Find the hue frame
        for child in color_tab.winfo_children():
            if isinstance(child, ttk.LabelFrame) and child.cget("text") == "Hue Ranges (0-360°)":
                hue_frame = child
                break
        
        if not hue_frame:
            return
        
        # Create a new range frame
        range_frame = ttk.Frame(hue_frame)
        range_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Range label
        i = len(self.color_param_vars[color]["hue_ranges"])
        range_label = ttk.Label(range_frame, text=f"Range {i+1}:")
        range_label.pack(side=tk.LEFT, padx=5)
        
        # Min value
        min_var = tk.DoubleVar(value=0)
        min_label = ttk.Label(range_frame, text="Min:")
        min_label.pack(side=tk.LEFT, padx=5)
        min_entry = ttk.Spinbox(
            range_frame,
            from_=0,
            to=360,
            increment=1,
            width=5,
            textvariable=min_var
        )
        min_entry.pack(side=tk.LEFT, padx=5)
        
        # Max value
        max_var = tk.DoubleVar(value=30)
        max_label = ttk.Label(range_frame, text="Max:")
        max_label.pack(side=tk.LEFT, padx=5)
        max_entry = ttk.Spinbox(
            range_frame,
            from_=0,
            to=360,
            increment=1,
            width=5,
            textvariable=max_var
        )
        max_entry.pack(side=tk.LEFT, padx=5)
        
        # Remove button
        remove_button = ttk.Button(
            range_frame,
            text="Remove",
            command=lambda c=color, idx=i: self.remove_hue_range(c, idx)
        )
        remove_button.pack(side=tk.LEFT, padx=5)
        
        # Store variables
        self.color_param_vars[color]["hue_ranges"].append((min_var, max_var))
        
        # Update the analysis
        self.on_color_param_change(color)
    
    def remove_hue_range(self, color, index):
        """
        Remove a hue range for a color.
        
        Args:
            color: Color category
            index: Index of the range to remove
        """
        try:
            # Log for debugging
            logger.debug(f"Removing hue range {index} for {color}")
            logger.debug(f"Current hue ranges: {len(self.color_param_vars[color]['hue_ranges'])}")
            
            # Remove the variables directly from the color parameters
            if index < len(self.color_param_vars[color]["hue_ranges"]):
                # Remove hue range
                del self.color_param_vars[color]["hue_ranges"][index]
                # Remove corresponding weight if it exists
                if "weights" in self.color_param_vars[color] and index < len(self.color_param_vars[color]["weights"]):
                    del self.color_param_vars[color]["weights"][index]
                
                # Update the configuration immediately
                if "color_detection_params" not in self.config:
                    self.config["color_detection_params"] = {}
                
                # Get current color parameters
                color_params = self.get_color_params()
                self.config["color_detection_params"][color] = color_params[color]
                
                # Save configuration
                config_manager.save_config(self.config, self.config_path)
                
                # Clear cache
                color_analysis.clear_cache()
                
                # Rebuild the UI for this color tab
                self.notebook.forget(1)  # Remove settings tab
                self.settings_tab = ttk.Frame(self.notebook)
                self.notebook.insert(1, self.settings_tab, text="Color Detection Settings")
                self.create_settings_tab_ui()
                self.notebook.select(1)  # Select settings tab
                
                # Re-analyze current image
                self.analyze_current_image()
                
                # Show success message
                self.status_var.set(f"Removed hue range {index+1} for {color}")
            else:
                logger.warning(f"Invalid index {index} for color {color} with {len(self.color_param_vars[color]['hue_ranges'])} ranges")
                self.status_var.set(f"Error: Invalid range index")
            
        except Exception as e:
            logger.error(f"Error removing hue range: {e}")
            messagebox.showerror(
                "Error",
                f"An error occurred while removing the hue range:\n\n{e}"
            )
    
    def get_color_params(self):
        """
        Get the current color parameters from the UI.
        
        Returns:
            dict: Color detection parameters
        """
        color_params = {}
        
        # Get parameters for each color
        for color in color_analysis.COLOR_CATEGORIES:
            if color == "white_gray_black":
                # Special case for white/gray/black
                color_params[color] = {
                    "saturation_threshold": self.color_param_vars[color]["saturation_threshold"].get(),
                    "low_value_threshold": self.color_param_vars[color]["low_value_threshold"].get(),
                    "high_value_threshold": self.color_param_vars[color]["high_value_threshold"].get()
                }
            else:
                # Regular colors
                hue_ranges = []
                hue_weights = []
                
                # Get hue ranges and weights
                for i, (min_var, max_var) in enumerate(self.color_param_vars[color]["hue_ranges"]):
                    hue_ranges.append([min_var.get(), max_var.get()])
                    # Get weight if available, default to 1.0
                    weight = 1.0
                    if "weights" in self.color_param_vars[color] and i < len(self.color_param_vars[color]["weights"]):
                        weight = self.color_param_vars[color]["weights"][i].get()
                    hue_weights.append(weight)
                
                color_params[color] = {
                    "hue_ranges": hue_ranges,
                    "hue_weights": hue_weights,
                    "saturation_range": [
                        self.color_param_vars[color]["saturation_min"].get(),
                        self.color_param_vars[color]["saturation_max"].get()
                    ],
                    "value_range": [
                        self.color_param_vars[color]["value_min"].get(),
                        self.color_param_vars[color]["value_max"].get()
                    ]
                }
        
        return color_params
    
    def on_color_param_change(self, color):
        """
        Handle color parameter change event.
        
        Args:
            color: Color category that changed
        """
        # Get current color parameters
        color_params = self.get_color_params()
        
        # Update configuration
        if "color_detection_params" not in self.config:
            self.config["color_detection_params"] = {}
        
        self.config["color_detection_params"][color] = color_params[color]
        
        # Save configuration
        config_manager.save_config(self.config, self.config_path)
        
        # Clear cache to ensure re-analysis
        color_analysis.clear_cache()
        
        # Update the hue spectrum visualization
        if color != "white_gray_black":
            self.update_hue_spectrum(color)
        
        # Re-analyze current image
        self.analyze_current_image()
    
    def reset_color_params_to_defaults(self):
        """
        Reset color parameters to defaults.
        """
        # Confirm with user
        result = messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset all color detection parameters to defaults?"
        )
        
        if not result:
            return
        
        # Reset configuration
        self.config["color_detection_params"] = color_analysis.DEFAULT_COLOR_DETECTION_PARAMS
        
        # Save configuration
        config_manager.save_config(self.config, self.config_path)
        
        # Clear cache
        color_analysis.clear_cache()
        
        # Reload UI
        self.notebook.forget(1)  # Remove settings tab
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Color Detection Settings")
        self.create_settings_tab_ui()
        
        # Re-analyze current image
        self.analyze_current_image()
        
        # Show success message
        messagebox.showinfo(
            "Reset Complete",
            "Color detection parameters have been reset to defaults."
        )
    
    def create_color_picker_tab_ui(self):
        """
        Create the UI for the color picker tab.
        """
        # Main frame
        main_frame = ttk.Frame(self.color_picker_tab, padding="10")
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
        self.color_picker_canvas = tk.Canvas(
            image_frame,
            width=600,
            height=400,
            bg="lightgray"
        )
        self.color_picker_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bind mouse events
        self.color_picker_canvas.bind("<ButtonPress-1>", self.on_color_picker_start)
        self.color_picker_canvas.bind("<B1-Motion>", self.on_color_picker_drag)
        self.color_picker_canvas.bind("<ButtonRelease-1>", self.on_color_picker_end)
        
        # Navigation frame
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, pady=5)
        
        # Previous button
        prev_button = ttk.Button(
            nav_frame,
            text="< Previous Image",
            command=self.prev_color_picker_image
        )
        prev_button.pack(side=tk.LEFT, padx=5)
        
        # Image counter label
        self.color_picker_counter_label = ttk.Label(nav_frame, text="0/0")
        self.color_picker_counter_label.pack(side=tk.LEFT, padx=5)
        
        # Next button
        next_button = ttk.Button(
            nav_frame,
            text="Next Image >",
            command=self.next_color_picker_image
        )
        next_button.pack(side=tk.LEFT, padx=5)
        
        # Add sample button
        add_button = ttk.Button(
            nav_frame,
            text="Add Sample Image",
            command=self.add_sample_image
        )
        add_button.pack(side=tk.RIGHT, padx=5)
        
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
            button = ttk.Button(
                category_buttons_frame,
                text=color.capitalize(),
                command=lambda c=color: self.add_to_category(c)
            )
            button.grid(row=i//4, column=i%4, padx=5, pady=2, sticky="ew")
        
        # Configure grid columns to be equal width
        for i in range(4):
            category_buttons_frame.columnconfigure(i, weight=1)
    
    def on_color_picker_start(self, event):
        """
        Handle mouse button press in the color picker.
        
        Args:
            event: Mouse event
        """
        if not self.current_image_path:
            return
        
        # Start selection
        self.color_picker_active = True
        self.color_picker_start_pos = (event.x, event.y)
        self.color_picker_current_pos = (event.x, event.y)
        
        # Create selection rectangle
        self.color_picker_selection = self.color_picker_canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="red",
            width=2
        )
    
    def on_color_picker_drag(self, event):
        """
        Handle mouse drag in the color picker.
        
        Args:
            event: Mouse event
        """
        if not self.color_picker_active:
            return
        
        # Update current position
        self.color_picker_current_pos = (event.x, event.y)
        
        # Update selection rectangle
        x1, y1 = self.color_picker_start_pos
        x2, y2 = self.color_picker_current_pos
        
        self.color_picker_canvas.coords(
            self.color_picker_selection,
            x1, y1, x2, y2
        )
    
    def on_color_picker_end(self, event):
        """
        Handle mouse button release in the color picker.
        
        Args:
            event: Mouse event
        """
        if not self.color_picker_active:
            return
        
        # End selection
        self.color_picker_active = False
        
        # Get selection coordinates
        x1, y1 = self.color_picker_start_pos
        x2, y2 = self.color_picker_current_pos
        
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
        if not self.current_image_path or not self.current_overlay_image:
            return
        
        try:
            # Use the resized image that's actually displayed on the canvas
            # This ensures we're getting the exact pixels the user sees
            img = self.current_overlay_image
            
            # Get canvas dimensions
            canvas_width = self.color_picker_canvas.winfo_width()
            canvas_height = self.color_picker_canvas.winfo_height()
            
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
            
            # Get color parameters
            color_params = self.get_color_params()
            
            # Analyze region with color parameters
            result = color_analysis.analyze_region(region, color_params)
            
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
        
        # Create or update range size and weight information frame
        if hasattr(self, 'range_info_frame'):
            # Clear existing frame
            for widget in self.range_info_frame.winfo_children():
                widget.destroy()
        else:
            # Create frame if it doesn't exist
            info_frame = self.color_picker_tab.nametowidget(self.notebook.select())
            for child in info_frame.winfo_children():
                if isinstance(child, ttk.LabelFrame) and child.cget("text") == "Color Information":
                    info_frame = child
                    break
            
            self.range_info_frame = ttk.Frame(info_frame)
            self.range_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add range size and weight information
        range_sizes = result.get("range_sizes", {})
        range_weights = result.get("range_weights", {})
        
        if range_sizes and range_weights:
            # Add header
            ttk.Label(
                self.range_info_frame,
                text="Range Sizes and Weights:",
                font=("Arial", 10, "bold")
            ).pack(anchor=tk.W, padx=5, pady=2)
            
            # Add information for each color
            for color in color_analysis.COLOR_CATEGORIES:
                if color == "white_gray_black":
                    continue  # Skip white_gray_black
                
                if color in range_sizes and color in range_weights:
                    size = range_sizes[color]
                    weight = range_weights[color]
                    
                    color_frame = ttk.Frame(self.range_info_frame)
                    color_frame.pack(fill=tk.X, padx=5, pady=1)
                    
                    # Color name
                    ttk.Label(
                        color_frame,
                        text=f"{color.capitalize()}:",
                        width=10
                    ).pack(side=tk.LEFT, padx=5)
                    
                    # Range size and weight
                    ttk.Label(
                        color_frame,
                        text=f"Size: {size:.0f}°, Weight: {weight:.1f}x"
                    ).pack(side=tk.LEFT, padx=5)
    
    def add_to_category(self, category):
        """
        Add the selected color range to a category.
        
        Args:
            category: Color category
        """
        if not self.current_image_path:
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
            color_params = self.get_color_params()
            
            # Get current hue ranges
            hue_ranges = color_params[category]["hue_ranges"]
            
            # Create a new hue range with +/- 15 degrees
            new_range = [max(0, h - 15), min(360, h + 15)]
            
            # Add the new range
            hue_ranges.append(new_range)
            
            # Update configuration
            if "color_detection_params" not in self.config:
                self.config["color_detection_params"] = {}
            
            self.config["color_detection_params"][category] = color_params[category]
            
            # Save configuration
            config_manager.save_config(self.config, self.config_path)
            
            # Clear cache
            color_analysis.clear_cache()
            
            # Show success message
            messagebox.showinfo(
                "Range Added",
                f"Added hue range {new_range[0]:.0f}° - {new_range[1]:.0f}° to {category.capitalize()} category."
            )
            
            # Switch to settings tab to show the new range
            self.notebook.select(1)  # Select settings tab
            
            # Reload settings tab
            self.notebook.forget(1)  # Remove settings tab
            self.settings_tab = ttk.Frame(self.notebook)
            self.notebook.insert(1, self.settings_tab, text="Color Detection Settings")
            self.create_settings_tab_ui()
            self.notebook.select(1)  # Select settings tab
            
        except Exception as e:
            logger.error(f"Error adding to category: {e}")
            self.status_var.set(f"Error adding to category: {e}")
            messagebox.showerror(
                "Error",
                f"An error occurred while adding to category:\n\n{e}"
            )
    
    def prev_color_picker_image(self):
        """
        Show the previous image in the color picker.
        """
        if self.sample_images:
            index = (self.current_image_index - 1) % len(self.sample_images)
            self.show_color_picker_image(index)
    
    def next_color_picker_image(self):
        """
        Show the next image in the color picker.
        """
        if self.sample_images:
            index = (self.current_image_index + 1) % len(self.sample_images)
            self.show_color_picker_image(index)
    
    def show_color_picker_image(self, index):
        """
        Show the image at the specified index in the color picker.
        
        Args:
            index: Index of the image to show
        """
        if not self.sample_images:
            self.status_var.set("No sample images available")
            return
        
        if index < 0 or index >= len(self.sample_images):
            return
        
        self.current_image_index = index
        self.current_image_path = self.sample_images[index]
        
        try:
            # Load and display image
            img = Image.open(self.current_image_path)
            
            # Resize to fit the canvas while maintaining aspect ratio
            img_width, img_height = img.size
            
            # Get canvas dimensions
            canvas_width = self.color_picker_canvas.winfo_width()
            canvas_height = self.color_picker_canvas.winfo_height()
            
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
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to PhotoImage
            self.current_overlay_image = img
            self.current_overlay_tk = ImageTk.PhotoImage(img)
            
            # Clear canvas
            self.color_picker_canvas.delete("all")
            
            # Create image on canvas
            self.color_picker_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self.current_overlay_tk,
                anchor=tk.CENTER
            )
            
            # Update counter label
            self.color_picker_counter_label.config(
                text=f"{self.current_image_index + 1}/{len(self.sample_images)}"
            )
            
            self.status_var.set(f"Showing image: {os.path.basename(self.current_image_path)}")
            
        except Exception as e:
            logger.error(f"Error showing image in color picker: {e}")
            self.status_var.set(f"Error showing image in color picker: {e}")
    
    def create_limits_tab_ui(self):
        """
        Create the UI for the color selection limits tab.
        """
        # Main frame
        main_frame = ttk.Frame(self.limits_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Color Selection Limits",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)
        
        # Description
        desc_label = ttk.Label(
            main_frame,
            text="Configure the minimum and maximum number of colors to select for each image.\n"
                 "These settings control how many colors are selected, even if they don't meet thresholds.",
            wraplength=800
        )
        desc_label.pack(pady=5)
        
        # Initialize variables
        if "color_selection_limits" not in self.config:
            self.config["color_selection_limits"] = {
                "with_white_gray_black": {"min_colors": 1, "max_colors": 3},
                "without_white_gray_black": {"min_colors": 1, "max_colors": 3}
            }
        
        # Create frame for with_white_gray_black settings
        with_wgb_frame = ttk.LabelFrame(
            main_frame,
            text="When White/Gray/Black is Selected"
        )
        with_wgb_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Min colors for with_white_gray_black
        with_wgb_min_frame = ttk.Frame(with_wgb_frame)
        with_wgb_min_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            with_wgb_min_frame,
            text="Minimum non-white/gray/black colors:"
        ).pack(side=tk.LEFT, padx=5)
        
        with_wgb_min_var = tk.IntVar(
            value=self.config["color_selection_limits"]["with_white_gray_black"]["min_colors"]
        )
        self.with_wgb_min_var = with_wgb_min_var
        
        with_wgb_min_spinbox = ttk.Spinbox(
            with_wgb_min_frame,
            from_=0,
            to=6,  # Max 6 non-white/gray/black colors
            increment=1,
            width=5,
            textvariable=with_wgb_min_var,
            command=self.on_limits_change
        )
        with_wgb_min_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Max colors for with_white_gray_black
        with_wgb_max_frame = ttk.Frame(with_wgb_frame)
        with_wgb_max_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            with_wgb_max_frame,
            text="Maximum non-white/gray/black colors:"
        ).pack(side=tk.LEFT, padx=5)
        
        with_wgb_max_var = tk.IntVar(
            value=self.config["color_selection_limits"]["with_white_gray_black"]["max_colors"]
        )
        self.with_wgb_max_var = with_wgb_max_var
        
        with_wgb_max_spinbox = ttk.Spinbox(
            with_wgb_max_frame,
            from_=0,
            to=6,  # Max 6 non-white/gray/black colors
            increment=1,
            width=5,
            textvariable=with_wgb_max_var,
            command=self.on_limits_change
        )
        with_wgb_max_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Create frame for without_white_gray_black settings
        without_wgb_frame = ttk.LabelFrame(
            main_frame,
            text="When White/Gray/Black is NOT Selected"
        )
        without_wgb_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Min colors for without_white_gray_black
        without_wgb_min_frame = ttk.Frame(without_wgb_frame)
        without_wgb_min_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            without_wgb_min_frame,
            text="Minimum colors:"
        ).pack(side=tk.LEFT, padx=5)
        
        without_wgb_min_var = tk.IntVar(
            value=self.config["color_selection_limits"]["without_white_gray_black"]["min_colors"]
        )
        self.without_wgb_min_var = without_wgb_min_var
        
        without_wgb_min_spinbox = ttk.Spinbox(
            without_wgb_min_frame,
            from_=1,
            to=6,  # Max 6 colors
            increment=1,
            width=5,
            textvariable=without_wgb_min_var,
            command=self.on_limits_change
        )
        without_wgb_min_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Max colors for without_white_gray_black
        without_wgb_max_frame = ttk.Frame(without_wgb_frame)
        without_wgb_max_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            without_wgb_max_frame,
            text="Maximum colors:"
        ).pack(side=tk.LEFT, padx=5)
        
        without_wgb_max_var = tk.IntVar(
            value=self.config["color_selection_limits"]["without_white_gray_black"]["max_colors"]
        )
        self.without_wgb_max_var = without_wgb_max_var
        
        without_wgb_max_spinbox = ttk.Spinbox(
            without_wgb_max_frame,
            from_=1,
            to=6,  # Max 6 colors
            increment=1,
            width=5,
            textvariable=without_wgb_max_var,
            command=self.on_limits_change
        )
        without_wgb_max_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Add explanation
        explanation_frame = ttk.LabelFrame(main_frame, text="How It Works")
        explanation_frame.pack(fill=tk.X, padx=10, pady=10)
        
        explanation_text = (
            "When an image is analyzed:\n\n"
            "1. Colors that meet their thresholds are selected first.\n"
            "2. If white/gray/black is selected, the system will ensure at least the minimum and at most the maximum "
            "number of non-white/gray/black colors are also selected.\n"
            "3. If white/gray/black is NOT selected, the system will ensure at least the minimum and at most the maximum "
            "number of colors are selected.\n"
            "4. If fewer colors meet their thresholds than the minimum, additional colors with the highest percentages "
            "will be selected to reach the minimum.\n"
            "5. If more colors meet their thresholds than the maximum, only the colors with the highest percentages "
            "will be kept, up to the maximum."
        )
        
        explanation_label = ttk.Label(
            explanation_frame,
            text=explanation_text,
            wraplength=800,
            justify=tk.LEFT
        )
        explanation_label.pack(padx=10, pady=10, fill=tk.X)
        
        # Add buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Reset to defaults button
        reset_defaults_button = ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_limits_to_defaults
        )
        reset_defaults_button.pack(side=tk.LEFT, padx=5)
        
        # Apply button
        apply_button = ttk.Button(
            button_frame,
            text="Apply Changes",
            command=self.apply_limits
        )
        apply_button.pack(side=tk.RIGHT, padx=5)
    
    def on_limits_change(self, *args):
        """
        Handle color selection limits change event.
        """
        # Ensure min <= max for with_white_gray_black
        if self.with_wgb_min_var.get() > self.with_wgb_max_var.get():
            self.with_wgb_max_var.set(self.with_wgb_min_var.get())
        
        # Ensure min <= max for without_white_gray_black
        if self.without_wgb_min_var.get() > self.without_wgb_max_var.get():
            self.without_wgb_max_var.set(self.without_wgb_min_var.get())
    
    def reset_limits_to_defaults(self):
        """
        Reset color selection limits to defaults.
        """
        # Confirm with user
        result = messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset color selection limits to defaults?"
        )
        
        if not result:
            return
        
        # Reset to defaults
        self.config["color_selection_limits"] = {
            "with_white_gray_black": {"min_colors": 1, "max_colors": 3},
            "without_white_gray_black": {"min_colors": 1, "max_colors": 3}
        }
        
        # Update variables
        self.with_wgb_min_var.set(1)
        self.with_wgb_max_var.set(3)
        self.without_wgb_min_var.set(1)
        self.without_wgb_max_var.set(3)
        
        # Save configuration
        config_manager.save_config(self.config, self.config_path)
        
        # Re-analyze current image
        self.analyze_current_image()
        
        # Show success message
        messagebox.showinfo(
            "Reset Complete",
            "Color selection limits have been reset to defaults."
        )
    
    def restart_sorting(self):
        """
        Restart sorting by removing all symlinks from color folders and the main folder.
        This provides a fresh start for sorting with new settings.
        """
        # Confirm with user
        result = messagebox.askyesno(
            "Confirm Restart",
            "Are you sure you want to restart sorting?\n\n"
            "This will remove all symlinks from color folders and the main folder,\n"
            "allowing you to start fresh with new color sort settings."
        )
        
        if not result:
            return
        
        # Disable UI during restart
        self.disable_ui()
        self.status_var.set("Restarting sorting...")
        
        # Run restart in a separate thread
        thread = threading.Thread(target=self._restart_sorting_thread)
        thread.daemon = True
        thread.start()
    
    def _restart_sorting_thread(self):
        """
        Restart sorting in a separate thread.
        """
        try:
            # Use the restart_sorting function to remove symlinks from both color folders and main folder
            stats = file_operations.restart_sorting(self.config)
            
            # Update UI
            self.root.after(0, lambda: self.status_var.set(
                f"Restart complete: {stats['total_removed']} symlinks removed, "
                f"{stats['errors']} errors"
            ))
            
            # Show result
            if stats["errors"] > 0:
                self.root.after(0, lambda: messagebox.showwarning(
                    "Restart Complete",
                    f"Restart completed with {stats['errors']} errors.\n\n"
                    f"See log for details."
                ))
            else:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Restart Complete",
                    f"Restart completed successfully.\n\n"
                    f"{stats['total_removed']} symlinks removed."
                ))
            
        except Exception as e:
            logger.error(f"Error restarting sorting: {e}")
            self.root.after(0, lambda: self.status_var.set(f"Error restarting sorting: {e}"))
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"An error occurred while restarting sorting:\n\n{e}"
            ))
        
        finally:
            # Re-enable UI
            self.root.after(0, self.enable_ui)

    def process_new_images_with_tracking(self, config, color_params, settings_hash):
        """
        Process new images with tracking of processed files.
        
        Args:
            config: Configuration dictionary
            color_params: Color detection parameters
            settings_hash: Hash of the current analysis settings
            
        Returns:
            dict: Statistics about the processing
        """
        # Get directories
        base_dir = config["paths"]["base_dir"]
        original_dir = os.path.join(base_dir, config["paths"]["original_dir"])
        
        # Check if original directory exists
        if not os.path.exists(original_dir) or not os.path.isdir(original_dir):
            logger.warning(f"Original directory does not exist: {original_dir}")
            return {"processed": 0, "errors": 0, "categories": {}}
        
        # Get thresholds and color limits
        thresholds = config["color_thresholds"]
        color_limits = config.get("color_selection_limits")
        
        # Get all image files recursively
        image_files = file_operations.get_image_files_recursive(original_dir)
        
        # Filter out already processed files with the same settings
        unprocessed_files = []
        for image_path in image_files:
            if image_path not in self.processed_files.get(settings_hash, []):
                unprocessed_files.append(image_path)
        
        # If all files have been processed with these settings, return empty stats
        if not unprocessed_files:
            logger.info(f"All files already processed with current settings")
            return {"processed": 0, "errors": 0, "categories": {}}
        
        # Initialize stats
        stats = {
            "processed": 0,
            "errors": 0,
            "categories": {}
        }
        
        # Process each unprocessed image
        for image_path in unprocessed_files:
            try:
                # Get filename for symlink creation
                filename = os.path.basename(image_path)
                
                # Analyze and categorize image
                result = color_analysis.analyze_and_categorize(
                    image_path,
                    thresholds,
                    tuple(config["resize_dimensions"]),
                    color_params,
                    color_limits
                )
                
                # Create symlinks for each category
                for category in result["categories"]:
                    # Get color directory
                    color_dir = os.path.join(base_dir, config["paths"]["color_dirs"][category])
                    
                    # Create symlink
                    symlink_path = os.path.join(color_dir, filename)
                    
                    # Check if symlink already exists
                    if os.path.exists(symlink_path):
                        # Skip if already exists
                        continue
                    
                    # Create symlink
                    os.symlink(image_path, symlink_path)
                    
                    # Update stats
                    stats["categories"][category] = stats["categories"].get(category, 0) + 1
                
                # Add to processed files list
                self.processed_files[settings_hash].append(image_path)
                
                # Update stats
                stats["processed"] += 1
                
                # Log progress
                if stats["processed"] % 100 == 0:
                    logger.info(f"Processed {stats['processed']} images")
            
            except Exception as e:
                logger.error(f"Error processing image {image_path}: {e}")
                stats["errors"] += 1
        
        logger.info(f"Processing complete: {stats['processed']} images processed, {stats['errors']} errors")
        return stats
    
    def apply_limits(self):
        """
        Apply color selection limits changes.
        """
        # Update configuration
        self.config["color_selection_limits"] = {
            "with_white_gray_black": {
                "min_colors": self.with_wgb_min_var.get(),
                "max_colors": self.with_wgb_max_var.get()
            },
            "without_white_gray_black": {
                "min_colors": self.without_wgb_min_var.get(),
                "max_colors": self.without_wgb_max_var.get()
            }
        }
        
        # Save configuration
        config_manager.save_config(self.config, self.config_path)
        
        # Re-analyze current image
        self.analyze_current_image()
        
        # Show success message
        messagebox.showinfo(
            "Changes Applied",
            "Color selection limits have been applied and saved."
        )
        
    def create_wallpaper_source_tab_ui(self):
        """
        Create the UI for the wallpaper source tab.
        """
        # Main frame
        main_frame = ttk.Frame(self.wallpaper_source_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Wallpaper Source Selection",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)
        
        # Description
        desc_label = ttk.Label(
            main_frame,
            text="Select how to determine which images will be used as the current active wallpaper folder.",
            wraplength=800
        )
        desc_label.pack(pady=5)
        
        # Create a frame for the radio buttons
        radio_frame = ttk.LabelFrame(main_frame, text="Selection Method")
        radio_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Variable to store the selected option
        self.wallpaper_source_var = tk.StringVar(value=self.config["wallpaper_source"])
        
        # Define the color order for inclusive options
        self.color_order = ["red", "orange", "green", "blue", "pink", "yellow", "white_gray_black"]
        
        # Create radio buttons for each option
        
        # Habits section
        habits_frame = ttk.LabelFrame(radio_frame, text="Habits-Based Selection")
        habits_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Weekly habits (current method)
        weekly_habits_radio = ttk.Radiobutton(
            habits_frame,
            text="Weekly Habits (Current Method)",
            variable=self.wallpaper_source_var,
            value="weekly_habits"
        )
        weekly_habits_radio.pack(anchor=tk.W, padx=20, pady=5)
        
        # Weekly habits (inclusive)
        weekly_habits_inclusive_radio = ttk.Radiobutton(
            habits_frame,
            text="Weekly Habits (Inclusive)",
            variable=self.wallpaper_source_var,
            value="weekly_habits_inclusive"
        )
        weekly_habits_inclusive_radio.pack(anchor=tk.W, padx=20, pady=5)
        
        # Today's habits (to be implemented later)
        daily_habits_radio = ttk.Radiobutton(
            habits_frame,
            text="Today's Habits (Not Yet Implemented)",
            variable=self.wallpaper_source_var,
            value="daily_habits",
            state="disabled"  # Disabled until implemented
        )
        daily_habits_radio.pack(anchor=tk.W, padx=20, pady=5)
        
        # Today's habits (inclusive) (to be implemented later)
        daily_habits_inclusive_radio = ttk.Radiobutton(
            habits_frame,
            text="Today's Habits (Inclusive) (Not Yet Implemented)",
            variable=self.wallpaper_source_var,
            value="daily_habits_inclusive",
            state="disabled"  # Disabled until implemented
        )
        daily_habits_inclusive_radio.pack(anchor=tk.W, padx=20, pady=5)
        
        # Monthly habits (to be implemented later)
        monthly_habits_radio = ttk.Radiobutton(
            habits_frame,
            text="Monthly Habits (Not Yet Implemented)",
            variable=self.wallpaper_source_var,
            value="monthly_habits",
            state="disabled"  # Disabled until implemented
        )
        monthly_habits_radio.pack(anchor=tk.W, padx=20, pady=5)
        
        # Monthly habits (inclusive) (to be implemented later)
        monthly_habits_inclusive_radio = ttk.Radiobutton(
            habits_frame,
            text="Monthly Habits (Inclusive) (Not Yet Implemented)",
            variable=self.wallpaper_source_var,
            value="monthly_habits_inclusive",
            state="disabled"  # Disabled until implemented
        )
        monthly_habits_inclusive_radio.pack(anchor=tk.W, padx=20, pady=5)
        
        # Direct color selection section
        color_frame = ttk.LabelFrame(radio_frame, text="Direct Color Selection")
        color_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Add a single radio button for the direct color selection
        direct_color_radio = ttk.Radiobutton(
            color_frame,
            text="Select specific colors:",
            variable=self.wallpaper_source_var,
            value="direct_color_selection"
        )
        direct_color_radio.pack(anchor=tk.W, padx=20, pady=5)
        
        # Create a frame for the color checkboxes
        color_checkboxes_frame = ttk.Frame(color_frame)
        color_checkboxes_frame.pack(fill=tk.X, padx=40, pady=5)
        
        # Initialize dictionary to store checkbox variables
        self.color_checkbox_vars = {}
        
        # Create a checkbox for each color
        for i, color in enumerate(self.color_order):
            var = tk.BooleanVar(value=False)
            self.color_checkbox_vars[color] = var
            
            checkbox = ttk.Checkbutton(
                color_checkboxes_frame,
                text=color.capitalize(),
                variable=var,
                command=self.update_direct_color_selection
            )
            checkbox.grid(row=i//3, column=i%3, sticky=tk.W, padx=10, pady=2)
        
        # Configure grid columns to be equal width
        for i in range(3):
            color_checkboxes_frame.columnconfigure(i, weight=1)
        
        # Latest images section
        latest_frame = ttk.LabelFrame(radio_frame, text="Latest Images")
        latest_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Latest option
        latest_radio = ttk.Radiobutton(
            latest_frame,
            text="Use images from the most recently added source folder",
            variable=self.wallpaper_source_var,
            value="latest"
        )
        latest_radio.pack(anchor=tk.W, padx=20, pady=5)
        
        # Create a frame for the action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Apply button
        apply_button = ttk.Button(
            button_frame,
            text="Apply and Refresh Plasma",
            command=self.apply_wallpaper_source
        )
        apply_button.pack(side=tk.RIGHT, padx=5)
        
        # Help text
        help_text = ttk.Label(
            main_frame,
            text="Note: Clicking 'Apply and Refresh Plasma' will update the active wallpaper folder and refresh the KDE Plasma desktop to apply the changes.\n\n"
                 "Inclusive options include all colors up to the current color in the order: red, orange, green, blue, pink, yellow, white_gray_black.",
            wraplength=800,
            font=("Arial", 9, "italic")
        )
        help_text.pack(pady=10)
        
        # Initialize the direct color selection if it's the current selection
        if self.wallpaper_source_var.get() == "direct_color_selection":
            self.initialize_direct_color_selection()
    
    def initialize_direct_color_selection(self):
        """
        Initialize the direct color selection checkboxes based on the saved configuration.
        """
        # Check if we have saved selected colors
        if "direct_color_selection" in self.config:
            selected_colors = self.config["direct_color_selection"]
            
            # Set the checkbox values
            for color, var in self.color_checkbox_vars.items():
                var.set(color in selected_colors)
    
    def update_direct_color_selection(self):
        """
        Update the direct color selection based on the checkbox values.
        """
        # Get the selected colors
        selected_colors = [
            color for color, var in self.color_checkbox_vars.items()
            if var.get()
        ]
        
        # Save to configuration
        self.config["direct_color_selection"] = selected_colors
    
    def apply_wallpaper_source(self):
        """
        Apply the selected wallpaper source and refresh Plasma.
        """
        import traceback
        import time
        
        # Generate a unique ID for this operation to track it in logs
        operation_id = f"apply_source_{int(time.time())}"
        logger.debug(f"[{operation_id}] apply_wallpaper_source called")
        
        selected_source = self.wallpaper_source_var.get()
        logger.debug(f"[{operation_id}] Selected source: {selected_source}")
        
        # Save the selection to the configuration
        self.config["wallpaper_source"] = selected_source
        logger.debug(f"[{operation_id}] Saving configuration")
        config_manager.save_config(self.config, self.config_path)
        logger.debug(f"[{operation_id}] Configuration saved")
        
        # Disable UI during processing
        logger.debug(f"[{operation_id}] Disabling UI")
        try:
            self.disable_ui()
            logger.debug(f"[{operation_id}] UI disabled successfully")
        except Exception as e:
            logger.error(f"[{operation_id}] Error disabling UI: {e}")
            logger.error(traceback.format_exc())
            # Continue anyway, but note the error
        
        self.status_var.set("Applying wallpaper source...")
        
        # Prepare parameters for the thread
        params = {
            'selected_source': selected_source,
            'color': None,
            'colors': [],
            'operation_id': operation_id  # Pass the operation ID to child methods
        }
        logger.debug(f"[{operation_id}] Initial params: {params}")
        
        try:
            # Determine which color or method to use
            if selected_source == "weekly_habits":
                # Use the current method (weekly habits)
                logger.debug(f"[{operation_id}] Using weekly habits method")
                self.status_var.set("Using weekly habits to determine wallpaper color...")
                # No need to specify color, the script will determine it from weekly habits
            elif selected_source == "weekly_habits_inclusive":
                # Use weekly habits but include all colors up to the determined color
                logger.debug(f"[{operation_id}] Using weekly habits inclusive method")
                self.status_var.set("Using weekly habits (inclusive) to determine wallpaper colors...")
                # Get the color from weekly habits
                try:
                    # Get weekly average from the file
                    WEEK_AVERAGE_FILE = "/home/twain/noteVault/habitCounters/week_average.txt"
                    logger.debug(f"[{operation_id}] Reading weekly average from {WEEK_AVERAGE_FILE}")
                    
                    with open(WEEK_AVERAGE_FILE, 'r') as f:
                        weekly_average = float(f.read().strip())
                    logger.debug(f"[{operation_id}] Weekly average: {weekly_average}")
                    
                    # Determine color based on count
                    def get_color_from_count(count):
                        if count < 13:
                            return "red"
                        elif 13 < count <= 20:
                            return "orange"
                        elif 20 < count <= 30:
                            return "green"
                        elif 30 < count <= 41:
                            return "blue"
                        elif 41 < count <= 48:
                            return "pink"
                        elif 48 < count <= 55:
                            return "yellow"
                        else:
                            return "white_gray_black"
                    
                    habit_color = get_color_from_count(weekly_average)
                    logger.debug(f"[{operation_id}] Determined habit color: {habit_color}")
                    
                    # Get all colors up to and including the habit color
                    if habit_color in self.color_order:
                        index = self.color_order.index(habit_color)
                        params['colors'] = self.color_order[:index+1]
                        logger.debug(f"[{operation_id}] Using colors up to index {index}: {params['colors']}")
                        self.status_var.set(f"Using colors: {', '.join(params['colors'])}")
                except Exception as e:
                    logger.error(f"[{operation_id}] Error determining habit color: {e}")
                    logger.error(traceback.format_exc())
                    messagebox.showerror(
                        "Error",
                        f"Failed to determine habit color: {e}"
                    )
                    self._safe_enable_ui()
                    return
            elif selected_source == "daily_habits" or selected_source == "daily_habits_inclusive":
                # Not yet implemented
                logger.debug(f"[{operation_id}] Daily habits method not implemented")
                messagebox.showinfo(
                    "Not Implemented",
                    "Daily habits selection is not yet implemented."
                )
                self._safe_enable_ui()
                return
            elif selected_source == "monthly_habits" or selected_source == "monthly_habits_inclusive":
                # Not yet implemented
                logger.debug(f"[{operation_id}] Monthly habits method not implemented")
                messagebox.showinfo(
                    "Not Implemented",
                    "Monthly habits selection is not yet implemented."
                )
                self._safe_enable_ui()
                return
            elif selected_source == "direct_color_selection":
                # Get selected colors from checkboxes
                logger.debug(f"[{operation_id}] Using direct color selection method")
                params['colors'] = [
                    color for color, var in self.color_checkbox_vars.items()
                    if var.get()
                ]
                logger.debug(f"[{operation_id}] Selected colors: {params['colors']}")
                
                if not params['colors']:
                    logger.warning(f"[{operation_id}] No colors selected for direct color selection")
                    messagebox.showwarning(
                        "No Colors Selected",
                        "Please select at least one color for direct color selection."
                    )
                    self._safe_enable_ui()
                    return
                
                self.status_var.set(f"Using selected colors: {', '.join(params['colors'])}")
            elif selected_source == "latest":
                # Use the latest folder
                logger.debug(f"[{operation_id}] Using latest images folder method")
                self.status_var.set("Using latest images folder...")
                params['color'] = "latest"
            elif selected_source.startswith("color_"):
                # Direct color selection (single color)
                color_name = selected_source.replace("color_", "")
                logger.debug(f"[{operation_id}] Using direct color selection for color: {color_name}")
                params['color'] = color_name
                self.status_var.set(f"Using {params['color']} color folder...")
            
            # First update the wallpaper source without refreshing plasma
            logger.debug(f"[{operation_id}] Starting update for wallpaper source")
            
            # CRITICAL SECTION: This is where we need to be extra careful
            try:
                # First, make sure the UI is in a good state before proceeding
                logger.debug(f"[{operation_id}] Ensuring UI is in a good state before update")
                self.root.update_idletasks()
                
                # Update the wallpaper source
                logger.debug(f"[{operation_id}] Calling _update_wallpaper_source")
                self._update_wallpaper_source(params)
                logger.debug(f"[{operation_id}] _update_wallpaper_source completed successfully")
                
                # Re-enable UI before plasma refresh to ensure app stays responsive
                logger.debug(f"[{operation_id}] Re-enabling UI before plasma refresh")
                self._safe_enable_ui()
                
                # Add a small delay to ensure UI is fully responsive
                time.sleep(0.5)
                logger.debug(f"[{operation_id}] Added delay after re-enabling UI")
                
                # Then refresh plasma shell safely
                logger.debug(f"[{operation_id}] Scheduling safe plasma refresh")
                self.status_var.set("Refreshing plasma shell...")
                
                # Use a callback that includes the operation ID for tracking
                def refresh_complete_callback():
                    logger.debug(f"[{operation_id}] Plasma refresh completed")
                    self.status_var.set("Plasma shell refreshed successfully")
                
                self._safe_refresh_plasma(refresh_complete_callback)
                logger.debug(f"[{operation_id}] _safe_refresh_plasma scheduled successfully")
                
            except Exception as e:
                logger.error(f"[{operation_id}] Error in critical section: {e}")
                logger.error(traceback.format_exc())
                self.status_var.set(f"Error during update: {e}")
                messagebox.showerror(
                    "Error",
                    f"An error occurred during the update process:\n\n{e}"
                )
                # Make sure UI is enabled
                self._safe_enable_ui()
            
        except Exception as e:
            logger.error(f"[{operation_id}] Error preparing wallpaper source update: {e}")
            logger.error(traceback.format_exc())
            self.status_var.set(f"Error: {e}")
            messagebox.showerror(
                "Error",
                f"An error occurred while preparing wallpaper source update:\n\n{e}"
            )
            self._safe_enable_ui()
    
    def _update_wallpaper_source(self, params):
        """
        Update the wallpaper source without refreshing plasma.
        
        Args:
            params: Dictionary containing parameters for the update
        """
        try:
            import subprocess
            import os
            import traceback
            
            logger.debug("Starting _update_wallpaper_source")
            
            selected_source = params['selected_source']
            color = params['color']
            colors = params['colors']
            
            logger.debug(f"Parameters: selected_source={selected_source}, color={color}, colors={colors}")
            
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "refresh_wallpaper.py")
            logger.debug(f"Script path: {script_path}")
            
            # Update status
            logger.debug("Setting status to 'Updating wallpaper source...'")
            self.root.after(0, lambda: self.status_var.set("Updating wallpaper source..."))
            
            if colors:
                # For multiple colors, we need to run the script for each color
                logger.debug(f"Processing multiple colors: {colors}")
                success_count = 0
                for c in colors:
                    # Update status for each color
                    logger.debug(f"Processing color: {c}")
                    self.root.after(0, lambda c=c: self.status_var.set(f"Processing color: {c}..."))
                    
                    # Run the script without the --force-refresh flag
                    cmd = ["python3", script_path, c]
                    logger.debug(f"Running command: {' '.join(cmd)}")
                    
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    logger.debug(f"Process started with PID: {process.pid}")
                    
                    # Wait for process to complete
                    logger.debug("Waiting for process to complete...")
                    stdout, stderr = process.communicate()
                    logger.debug(f"Process completed with return code: {process.returncode}")
                    logger.debug(f"stdout: {stdout}")
                    logger.debug(f"stderr: {stderr}")
                    
                    if process.returncode == 0:
                        success_count += 1
                        logger.debug(f"Color {c} processed successfully")
                    else:
                        logger.error(f"Failed to process color {c}: {stderr}")
                
                # Final status update
                if success_count == len(colors):
                    status_message = f"Success: Updated wallpaper sources to: {', '.join(colors)}"
                    logger.debug(status_message)
                    self.root.after(0, lambda: self.status_var.set(status_message))
                else:
                    status_message = f"Warning: Only {success_count} of {len(colors)} colors were successfully applied"
                    logger.warning(status_message)
                    self.root.after(0, lambda: self.status_var.set(status_message))
            else:
                # For single color or method
                logger.debug(f"Processing single color or method: {color}")
                cmd = ["python3", script_path]
                if color:
                    cmd.append(color)
                
                logger.debug(f"Running command: {' '.join(cmd)}")
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                logger.debug(f"Process started with PID: {process.pid}")
                
                # Wait for process to complete
                logger.debug("Waiting for process to complete...")
                stdout, stderr = process.communicate()
                logger.debug(f"Process completed with return code: {process.returncode}")
                logger.debug(f"stdout: {stdout}")
                logger.debug(f"stderr: {stderr}")
                
                if process.returncode == 0:
                    source_name = selected_source
                    if selected_source.startswith("color_"):
                        source_name = selected_source.replace("color_", "")
                    
                    status_message = f"Success: Updated wallpaper source to {source_name.replace('_', ' ').title()}"
                    logger.debug(status_message)
                    self.root.after(0, lambda: self.status_var.set(status_message))
                else:
                    status_message = f"Error: Failed to apply wallpaper source. See log for details."
                    logger.error(status_message)
                    logger.error(f"Error output from refresh_wallpaper.py: {stderr}")
                    self.root.after(0, lambda: self.status_var.set(status_message))
            
        except Exception as e:
            logger.error(f"Error in wallpaper source update: {e}")
            logger.error(traceback.format_exc())
            self.root.after(0, lambda: self.status_var.set(f"Error: {e}"))
            self.root.after(0, self._safe_enable_ui)
    
    # The _apply_wallpaper_source_thread method has been replaced by _update_wallpaper_source
    # and _safe_refresh_plasma methods for better separation of concerns and stability
    
    def _safe_enable_ui(self):
        """
        Safely re-enable the UI with exception handling.
        """
        try:
            logger.debug("Attempting to re-enable UI")
            self.enable_ui()
            logger.debug("UI re-enabled successfully")
        except Exception as e:
            logger.error(f"Error re-enabling UI: {e}")
            logger.error(traceback.format_exc())
            # Try to recover UI
            self._recover_ui()
    
    def _recover_ui(self):
        """
        Attempt to recover the UI if it's in an inconsistent state.
        This is a last resort method to try to restore UI responsiveness.
        """
        import traceback
        
        logger.debug("Attempting emergency UI recovery")
        try:
            # Force update the UI
            self.root.update_idletasks()
            logger.debug("Forced update_idletasks")
            
            # Try to force a complete UI refresh
            self.root.update()
            logger.debug("Forced update")
            
            # Try to force focus to the root window
            self.root.focus_force()
            logger.debug("Forced focus to root window")
            
            # Try to force a geometry update to trigger a redraw
            current_geometry = self.root.geometry()
            logger.debug(f"Current geometry: {current_geometry}")
            
            # Slightly modify the geometry and then restore it
            # This can sometimes help "unstick" a frozen UI
            size_parts = current_geometry.split('+')[0].split('x')
            if len(size_parts) == 2:
                width, height = int(size_parts[0]), int(size_parts[1])
                # Temporarily resize the window
                self.root.geometry(f"{width+1}x{height+1}")
                logger.debug(f"Temporarily resized to: {self.root.geometry()}")
                # Then restore original size
                self.root.after(100, lambda: self.root.geometry(current_geometry))
                logger.debug(f"Scheduled restore to original geometry: {current_geometry}")
            
            # Try to force a redraw of all widgets
            for child in self.root.winfo_children():
                if hasattr(child, "update") and callable(getattr(child, "update")):
                    child.update()
            
            logger.debug("Emergency UI recovery completed")
        except Exception as e:
            logger.error(f"Error in emergency UI recovery: {e}")
            logger.error(traceback.format_exc())
    
    def _safe_refresh_plasma(self, callback=None):
        """
        Safely refresh the plasma shell without freezing the application.
        
        This method creates a separate process to refresh the plasma shell,
        which prevents the refresh from affecting the main application.
        
        Args:
            callback: Optional callback function to call after the refresh
        """
        import subprocess
        import threading
        import traceback
        import time
        import uuid
        
        # Generate a unique ID for this refresh operation
        refresh_id = str(uuid.uuid4())[:8]
        logger.debug(f"[PLASMA-{refresh_id}] Starting safe plasma refresh")
        
        # Explicitly re-enable UI before starting the refresh
        # This ensures the UI is responsive during the refresh
        try:
            self.root.after(0, self._safe_enable_ui)
            logger.debug(f"[PLASMA-{refresh_id}] UI re-enable scheduled before plasma refresh")
        except Exception as e:
            logger.error(f"[PLASMA-{refresh_id}] Error scheduling UI re-enable: {e}")
            logger.error(traceback.format_exc())
        
        # Create a watchdog timer to ensure the UI stays responsive
        def watchdog_timer():
            try:
                logger.debug(f"[PLASMA-{refresh_id}] Watchdog timer activated")
                # Force UI update every 500ms to keep it responsive
                self.root.after(0, lambda: self.root.update_idletasks())
                # Schedule next watchdog check
                self.root.after(500, watchdog_timer)
            except Exception as e:
                logger.error(f"[PLASMA-{refresh_id}] Error in watchdog timer: {e}")
        
        # Start the watchdog timer
        self.root.after(0, watchdog_timer)
        logger.debug(f"[PLASMA-{refresh_id}] Watchdog timer scheduled")
        
        def refresh_thread():
            try:
                # Create a simple script to run the plasma refresh command
                temp_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"temp_plasma_refresh_{refresh_id}.sh")
                logger.debug(f"[PLASMA-{refresh_id}] Creating temporary script: {temp_script_path}")
                
                with open(temp_script_path, 'w') as f:
                    f.write(f"""#!/bin/bash
# This script refreshes the plasma shell and then exits (ID: {refresh_id})
echo "[PLASMA-{refresh_id}] Refreshing plasma shell..."
# Use timeout to ensure the command doesn't hang
timeout 5s dbus-send --session --dest=org.kde.plasmashell --type=method_call /PlasmaShell org.kde.PlasmaShell.refreshCurrentShell > /dev/null 2>&1
RESULT=$?
if [ $RESULT -eq 124 ]; then
    echo "[PLASMA-{refresh_id}] Warning: dbus-send timed out after 5 seconds"
fi
sleep 2  # Add a delay to ensure the refresh completes
echo "[PLASMA-{refresh_id}] Plasma shell refresh completed"
exit 0
""")
                
                # Make the script executable
                os.chmod(temp_script_path, 0o755)
                logger.debug(f"[PLASMA-{refresh_id}] Temporary script created and made executable")
                
                # Run the script in a new process with a timeout
                logger.debug(f"[PLASMA-{refresh_id}] Running plasma refresh script")
                
                # Use a timeout to prevent hanging
                try:
                    process = subprocess.Popen(
                        ["/bin/bash", temp_script_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Set a timeout for the process
                    try:
                        stdout, stderr = process.communicate(timeout=10)  # 10 second timeout
                        logger.debug(f"[PLASMA-{refresh_id}] Plasma refresh completed with return code: {process.returncode}")
                        logger.debug(f"[PLASMA-{refresh_id}] stdout: {stdout}")
                        if stderr:
                            logger.error(f"[PLASMA-{refresh_id}] stderr: {stderr}")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"[PLASMA-{refresh_id}] Process timed out after 10 seconds, terminating")
                        process.kill()
                        stdout, stderr = process.communicate()
                        logger.debug(f"[PLASMA-{refresh_id}] After kill - stdout: {stdout}")
                        logger.debug(f"[PLASMA-{refresh_id}] After kill - stderr: {stderr}")
                except Exception as e:
                    logger.error(f"[PLASMA-{refresh_id}] Error running refresh script: {e}")
                    logger.error(traceback.format_exc())
                
                # Clean up the temporary script
                try:
                    os.remove(temp_script_path)
                    logger.debug(f"[PLASMA-{refresh_id}] Temporary script {temp_script_path} removed")
                except Exception as e:
                    logger.error(f"[PLASMA-{refresh_id}] Error removing temporary script: {e}")
                
                # Add a small delay to ensure the UI has time to recover
                time.sleep(1)
                logger.debug(f"[PLASMA-{refresh_id}] Added delay after plasma refresh")
                
                # Ensure UI is enabled after refresh
                try:
                    self.root.after(0, self._safe_enable_ui)
                    logger.debug(f"[PLASMA-{refresh_id}] UI re-enable scheduled after plasma refresh")
                except Exception as e:
                    logger.error(f"[PLASMA-{refresh_id}] Error scheduling UI re-enable: {e}")
                    logger.error(traceback.format_exc())
                
                # Call the callback if provided
                if callback:
                    logger.debug(f"[PLASMA-{refresh_id}] Scheduling callback function")
                    try:
                        self.root.after(500, callback)  # Add a delay before calling the callback
                    except Exception as e:
                        logger.error(f"[PLASMA-{refresh_id}] Error scheduling callback: {e}")
                
                logger.debug(f"[PLASMA-{refresh_id}] Refresh thread completed successfully")
                
            except Exception as e:
                logger.error(f"[PLASMA-{refresh_id}] Error in refresh thread: {e}")
                logger.error(traceback.format_exc())
                # Ensure UI is enabled even if there's an error
                try:
                    self.root.after(0, self._safe_enable_ui)
                    logger.debug(f"[PLASMA-{refresh_id}] UI re-enable scheduled after error")
                except Exception as e2:
                    logger.error(f"[PLASMA-{refresh_id}] Error scheduling UI re-enable after error: {e2}")
                
                # Still try to call the callback if provided
                if callback:
                    try:
                        self.root.after(500, callback)
                    except Exception as e2:
                        logger.error(f"[PLASMA-{refresh_id}] Error scheduling callback after error: {e2}")
        
        # Start the refresh in a separate thread
        thread = threading.Thread(target=refresh_thread, name=f"plasma-refresh-{refresh_id}")
        thread.daemon = True
        thread.start()
        logger.debug(f"[PLASMA-{refresh_id}] Plasma refresh thread started")
        
        # Schedule a check to make sure the UI is still responsive after a few seconds
        def check_ui_responsive():
            logger.debug(f"[PLASMA-{refresh_id}] Checking UI responsiveness")
            try:
                # Force a UI update
                self.root.update_idletasks()
                # Try to recover UI if needed
                self._recover_ui()
                logger.debug(f"[PLASMA-{refresh_id}] UI responsiveness check completed")
            except Exception as e:
                logger.error(f"[PLASMA-{refresh_id}] Error in UI responsiveness check: {e}")
        
        # Schedule multiple checks at different intervals
        self.root.after(2000, check_ui_responsive)  # Check after 2 seconds
        self.root.after(5000, check_ui_responsive)  # Check after 5 seconds
        self.root.after(10000, check_ui_responsive)  # Check after 10 seconds
    
    def draw_hue_spectrum(self, canvas, highlight_ranges=None):
        """
        Draw a hue spectrum on the canvas.
        
        Args:
            canvas: Canvas to draw on
            highlight_ranges: List of (min, max) ranges to highlight
        """
        # Get canvas dimensions
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        # If the canvas hasn't been fully initialized yet, use default dimensions
        if width < 10 or height < 10:
            width = 600
            height = 30
        
        # Clear canvas
        canvas.delete("all")
        
        # Draw the spectrum
        for i in range(width):
            # Calculate hue value (0-360)
            hue = (i / width) * 360
            
            # Convert HSV to RGB
            r, g, b = colorsys.hsv_to_rgb(hue / 360, 1.0, 1.0)
            
            # Convert to hex color
            color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
            
            # Draw a vertical line
            canvas.create_line(i, 0, i, height, fill=color)
        
        # Draw tick marks and labels
        for i in range(0, 361, 60):
            # Calculate x position
            x = (i / 360) * width
            
            # Draw tick mark
            canvas.create_line(x, height - 5, x, height, fill="black", width=2)
            
            # Draw label
            canvas.create_text(x, height - 10, text=str(i), anchor=tk.S, font=("Arial", 8))
        
        # Highlight ranges if provided
        if highlight_ranges:
            for min_val, max_val in highlight_ranges:
                # Calculate x positions
                x1 = (min_val / 360) * width
                x2 = (max_val / 360) * width
                
                # Draw highlight rectangle
                canvas.create_rectangle(x1, 0, x2, height, outline="red", width=2)
    
    def update_hue_spectrum(self, color):
        """
        Update the hue spectrum for a color with its current ranges.
        
        Args:
            color: Color category
        """
        # Skip white_gray_black
        if color == "white_gray_black":
            return
        
        # Get the spectrum canvas
        canvas = self.color_param_vars[color].get("spectrum_canvas")
        if not canvas:
            return
        
        # Get current hue ranges
        ranges = []
        for min_var, max_var in self.color_param_vars[color]["hue_ranges"]:
            ranges.append((min_var.get(), max_var.get()))
        
        # Draw the spectrum with highlighted ranges
        self.draw_hue_spectrum(canvas, ranges)
    
    def apply_color_params(self):
        """
        Apply color parameter changes.
        """
        # Get current color parameters
        color_params = self.get_color_params()
        
        # Update configuration
        self.config["color_detection_params"] = color_params
        
        # Save configuration
        config_manager.save_config(self.config, self.config_path)
        
        # Clear cache
        color_analysis.clear_cache()
        
        # Re-analyze current image
        self.analyze_current_image()
        
        # Show success message
        messagebox.showinfo(
            "Changes Applied",
            "Color detection parameters have been applied and saved."
        )
    
    def disable_ui(self):
        """
        Disable UI elements during long-running operations.
        """
        import traceback
        logger.debug("Starting UI disable process")
        try:
            # Log the current UI state
            logger.debug(f"Root window state before disable: {self.root.state()}")
            logger.debug(f"Root window attributes before disable: {self.root.winfo_attributes()}")
            
            # Get the current active widget to help with debugging
            try:
                focused_widget = self.root.focus_get()
                if focused_widget:
                    logger.debug(f"Currently focused widget: {focused_widget} ({focused_widget.__class__.__name__})")
                else:
                    logger.debug("No widget currently has focus")
            except Exception as e:
                logger.error(f"Error getting focused widget: {e}")
            
            # Disable all children
            for child in self.root.winfo_children():
                self._disable_widget(child)
            
            # Force update the UI
            self.root.update_idletasks()
            logger.debug("UI disable process completed successfully")
            logger.debug(f"Root window state after disable: {self.root.state()}")
        except Exception as e:
            logger.error(f"Error in disable_ui: {e}")
            logger.error(traceback.format_exc())
    
    def _disable_widget(self, widget):
        """
        Recursively disable a widget and its children.
        
        Args:
            widget: Widget to disable
        """
        try:
            widget_name = widget.winfo_name() if hasattr(widget, "winfo_name") else "unknown"
            widget_class = widget.__class__.__name__
            logger.debug(f"Disabling widget: {widget_name} ({widget_class})")
            
            if hasattr(widget, "state") and callable(getattr(widget, "state")):
                current_state = widget.state()
                logger.debug(f"Widget {widget_name} current state: {current_state}")
                widget.state(["disabled"])
                logger.debug(f"Widget {widget_name} new state: {widget.state()}")
            elif hasattr(widget, "config") and callable(getattr(widget, "config")):
                try:
                    current_state = widget.cget("state") if hasattr(widget, "cget") else "unknown"
                    logger.debug(f"Widget {widget_name} current state: {current_state}")
                    widget.config(state=tk.DISABLED)
                    new_state = widget.cget("state") if hasattr(widget, "cget") else "unknown"
                    logger.debug(f"Widget {widget_name} new state: {new_state}")
                except Exception as e:
                    logger.error(f"Error configuring widget {widget_name}: {e}")
            else:
                logger.debug(f"Widget {widget_name} has no state or config method")
            
            # Recursively disable children
            if hasattr(widget, "winfo_children") and callable(getattr(widget, "winfo_children")):
                for child in widget.winfo_children():
                    self._disable_widget(child)
        except Exception as e:
            logger.error(f"Error disabling widget: {e}")
    
    def enable_ui(self):
        """
        Enable UI elements after long-running operations.
        """
        import traceback
        logger.debug("Starting UI enable process")
        try:
            # Log the current UI state
            logger.debug(f"Root window state before enable: {self.root.state()}")
            logger.debug(f"Root window attributes before enable: {self.root.winfo_attributes()}")
            
            # Get the current active widget to help with debugging
            try:
                focused_widget = self.root.focus_get()
                if focused_widget:
                    logger.debug(f"Currently focused widget before enable: {focused_widget} ({focused_widget.__class__.__name__})")
                else:
                    logger.debug("No widget currently has focus before enable")
            except Exception as e:
                logger.error(f"Error getting focused widget: {e}")
            
            # Enable all children
            for child in self.root.winfo_children():
                self._enable_widget(child)
            
            # Update the UI to ensure changes take effect
            self.root.update_idletasks()
            
            # Force an additional update to ensure UI is responsive
            self.root.update()
            
            logger.debug("UI enable process completed successfully")
            logger.debug(f"Root window state after enable: {self.root.state()}")
            
            # Try to set focus to the root window to ensure it's responsive
            try:
                self.root.focus_force()
                logger.debug("Focus forced to root window")
            except Exception as e:
                logger.error(f"Error forcing focus: {e}")
        except Exception as e:
            logger.error(f"Error in enable_ui: {e}")
            logger.error(traceback.format_exc())
    
    def _enable_widget(self, widget):
        """
        Recursively enable a widget and its children.
        
        Args:
            widget: Widget to enable
        """
        try:
            widget_name = widget.winfo_name() if hasattr(widget, "winfo_name") else "unknown"
            widget_class = widget.__class__.__name__
            widget_id = str(id(widget))
            logger.debug(f"Enabling widget: {widget_name} ({widget_class}) [id: {widget_id}]")
            
            # Log widget geometry and visibility
            if hasattr(widget, "winfo_ismapped") and callable(getattr(widget, "winfo_ismapped")):
                is_mapped = widget.winfo_ismapped()
                logger.debug(f"Widget {widget_name} is mapped: {is_mapped}")
            
            if hasattr(widget, "winfo_viewable") and callable(getattr(widget, "winfo_viewable")):
                is_viewable = widget.winfo_viewable()
                logger.debug(f"Widget {widget_name} is viewable: {is_viewable}")
            
            if hasattr(widget, "winfo_geometry") and callable(getattr(widget, "winfo_geometry")):
                geometry = widget.winfo_geometry()
                logger.debug(f"Widget {widget_name} geometry: {geometry}")
            
            # Enable the widget based on its type
            if hasattr(widget, "state") and callable(getattr(widget, "state")):
                current_state = widget.state()
                logger.debug(f"Widget {widget_name} current state: {current_state}")
                
                # Try to remove disabled state
                try:
                    widget.state(["!disabled"])
                    logger.debug(f"Widget {widget_name} new state: {widget.state()}")
                except Exception as e:
                    logger.error(f"Error changing state for widget {widget_name}: {e}")
                    # Try alternative method
                    try:
                        widget.configure(state="normal")
                        logger.debug(f"Widget {widget_name} state set via configure")
                    except Exception as e2:
                        logger.error(f"Error configuring widget {widget_name}: {e2}")
                
            elif hasattr(widget, "config") and callable(getattr(widget, "config")):
                try:
                    current_state = widget.cget("state") if hasattr(widget, "cget") else "unknown"
                    logger.debug(f"Widget {widget_name} current state: {current_state}")
                    
                    # Try to set normal state
                    widget.config(state=tk.NORMAL)
                    new_state = widget.cget("state") if hasattr(widget, "cget") else "unknown"
                    logger.debug(f"Widget {widget_name} new state: {new_state}")
                except Exception as e:
                    logger.error(f"Error configuring widget {widget_name}: {e}")
            else:
                logger.debug(f"Widget {widget_name} has no state or config method")
            
            # Recursively enable children
            if hasattr(widget, "winfo_children") and callable(getattr(widget, "winfo_children")):
                children = widget.winfo_children()
                logger.debug(f"Widget {widget_name} has {len(children)} children")
                for child in children:
                    self._enable_widget(child)
        except Exception as e:
            logger.error(f"Error enabling widget: {e}")
            import traceback
            logger.error(traceback.format_exc())


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Color Control Panel")
    
    parser.add_argument("--config", type=str,
                        help="Use a specific configuration file")
    
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")
    
    return parser.parse_args()


def main():
    """
    Main function.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging - always enable debug logging for troubleshooting
    logging.getLogger().setLevel(logging.DEBUG)
    
    # Configure root logger with a more detailed format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s')
    
    # Add console handler with detailed formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)
    
    logger.debug("Debug logging enabled with enhanced formatting")
    
    # Set up a file handler to log to a file as well
    try:
        log_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(log_dir, "color_control_panel.log")
        
        # Create a rotating file handler to avoid huge log files
        # Keep 3 backup files of 5MB each
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            mode='a',  # Append mode to preserve previous logs
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
        
        logger.debug(f"Logging to file: {log_file}")
        logger.debug(f"Log rotation enabled: 5MB max size, 3 backup files")
        
        # Log system information
        import platform
        logger.debug(f"Platform: {platform.platform()}")
        logger.debug(f"Python version: {platform.python_version()}")
        logger.debug(f"Tkinter version: {tk.TkVersion}")
        
    except Exception as e:
        logger.error(f"Failed to set up file logging: {e}", exc_info=True)
    
    try:
        # Create Tkinter root
        root = tk.Tk()
        
        # Set up exception handler for Tkinter
        def report_callback_exception(exc, val, tb):
            logger.critical("Unhandled Tkinter exception:", exc_info=(exc, val, tb))
            # Try to show an error message to the user
            try:
                import traceback
                error_message = ''.join(traceback.format_exception(exc, val, tb))
                messagebox.showerror("Unhandled Error",
                                    f"An unhandled error occurred:\n\n{val}\n\nDetails have been logged.")
                logger.debug(f"Error dialog displayed to user")
            except:
                logger.error("Failed to show error dialog", exc_info=True)
        
        # Set the exception handler
        root.report_callback_exception = report_callback_exception
        logger.debug("Custom Tkinter exception handler installed")
        
        # Create control panel
        logger.debug("Creating ColorControlPanel instance")
        app = ColorControlPanel(root, args.config)
        logger.debug("ColorControlPanel instance created successfully")
        
        # Start main loop
        logger.debug("Starting Tkinter main loop")
        root.mainloop()
        logger.debug("Tkinter main loop ended")
        
        return 0
        
    except Exception as e:
        logger.critical(f"Unexpected error in main function: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
