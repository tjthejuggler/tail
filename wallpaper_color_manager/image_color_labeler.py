#!/usr/bin/env python3

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import random
import shutil

class ImageColorLabeler:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Color Labeler")
        self.root.geometry("1200x900")  # Larger initial window size
        
        # Define color categories
        self.color_categories = {
            'red': 'Red',
            'orange': 'Orange',
            'green': 'Green',
            'blue': 'Blue',
            'pink': 'Pink',
            'yellow': 'Yellow',
            'white_gray_black': 'White/Gray/Black'
        }
        
        # Paths
        self.base_dir = "/home/twain/Pictures"
        self.source_dir = os.path.join(self.base_dir, "llm_baby_monster_original")
        self.retired_dir = "/home/twain/Pictures/llm_baby_monster_retired"
        self.results_file = os.path.join(self.base_dir, "image_color_labels.json")
        
        # Ensure retired directory exists
        if not os.path.exists(self.retired_dir):
            os.makedirs(self.retired_dir)
        
        # Load existing results if available
        self.labeled_images = {}
        if os.path.exists(self.results_file):
            with open(self.results_file, 'r') as f:
                # Convert old format (string) to new format (list) if needed
                data = json.load(f)
                for filename, colors in data.items():
                    if isinstance(colors, str):
                        # Old format - single color as string
                        self.labeled_images[filename] = [colors]
                    else:
                        # New format - multiple colors as list
                        self.labeled_images[filename] = colors
        
        # Get list of images to label
        self.images_to_label = []
        for filename in os.listdir(self.source_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                if filename not in self.labeled_images:
                    self.images_to_label.append(filename)
        
        # Shuffle the images for random order
        random.shuffle(self.images_to_label)
        
        # Initialize variables
        self.current_image_index = 0
        self.current_image_path = None
        self.current_image_filename = None
        self.photo_image = None
        self.selected_colors = []  # Track currently selected colors
        self.color_vars = {}  # Checkbutton variables
        
        # Create UI elements
        self.create_ui()
        
        # Start with the first image
        self.load_next_image()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Image display
        self.image_label = ttk.Label(main_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=10)
        
        # Color selection frame - use a grid layout for checkboxes
        color_frame = ttk.LabelFrame(controls_frame, text="Select Colors (Multiple Allowed)")
        color_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Create a checkbox for each color
        self.color_vars = {}
        row, col = 0, 0
        for color_key, color_name in self.color_categories.items():
            var = tk.BooleanVar(value=False)
            self.color_vars[color_key] = var
            
            cb = ttk.Checkbutton(
                color_frame,
                text=color_name,
                variable=var,
                command=self.update_selected_colors
            )
            cb.grid(row=row, column=col, sticky="w", padx=10, pady=5)
            
            col += 1
            if col > 2:  # 3 columns of checkboxes
                col = 0
                row += 1
        
        # Buttons frame
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Confirm button
        self.confirm_button = ttk.Button(
            button_frame,
            text="Confirm Selection",
            command=self.on_confirm
        )
        self.confirm_button.pack(side=tk.LEFT, padx=5)
        
        # Retire button
        self.retire_button = ttk.Button(
            button_frame,
            text="Retire Image",
            command=self.on_retire
        )
        self.retire_button.pack(side=tk.LEFT, padx=5)
        
        # Skip button
        self.skip_button = ttk.Button(
            button_frame,
            text="Skip Image",
            command=self.on_skip
        )
        self.skip_button.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="0/0")
        self.progress_label.pack(side=tk.RIGHT, padx=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=100)
        self.progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        # Current filename display
        self.filename_label = ttk.Label(main_frame, text="", justify=tk.LEFT)
        self.filename_label.pack(fill=tk.X, pady=5)
    
    def load_next_image(self):
        if self.current_image_index >= len(self.images_to_label):
            self.show_completion_message()
            return
        
        # Reset color selections
        self.selected_colors = []
        for var in self.color_vars.values():
            var.set(False)
        
        # Try to load images until we find one that works or run out of images
        max_attempts = min(10, len(self.images_to_label) - self.current_image_index)
        for _ in range(max_attempts):
            self.current_image_filename = self.images_to_label[self.current_image_index]
            self.current_image_path = os.path.join(self.source_dir, self.current_image_filename)
            
            # Update progress
            self.progress_var.set((self.current_image_index / len(self.images_to_label)) * 100)
            self.progress_label.config(text=f"{self.current_image_index + 1}/{len(self.images_to_label)}")
            self.filename_label.config(text=f"Current file: {self.current_image_filename}")
            
            # Load and display image
            try:
                # Check if the file exists and is readable
                if not os.path.isfile(self.current_image_path) or not os.access(self.current_image_path, os.R_OK):
                    raise FileNotFoundError(f"File not found or not readable: {self.current_image_path}")
                
                # Try to open the image
                image = Image.open(self.current_image_path)
                
                # Verify the image is valid
                image.verify()
                
                # Reopen the image (verify closes the file)
                image = Image.open(self.current_image_path)
                
                # Get image dimensions
                img_width, img_height = image.size
                if img_width <= 0 or img_height <= 0:
                    raise ValueError(f"Invalid image dimensions: {img_width}x{img_height}")
                
                # Resize image to fit the window while maintaining aspect ratio
                # Use fixed larger dimensions for the initial display
                if self.root.winfo_width() < 100:  # Window not fully initialized yet
                    window_width = 800
                    window_height = 600
                else:
                    window_width = self.root.winfo_width() - 40
                    window_height = self.root.winfo_height() - 200
                
                # Ensure window dimensions are positive
                window_width = max(800, window_width)
                window_height = max(600, window_height)
                
                # Use a larger scale factor to make the image bigger
                scale = min(window_width / img_width, window_height / img_height) * 0.9
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # Ensure new dimensions are positive
                new_width = max(1, new_width)
                new_height = max(1, new_height)
                
                image = image.resize((new_width, new_height), Image.LANCZOS)
                
                self.photo_image = ImageTk.PhotoImage(image)
                self.image_label.config(image=self.photo_image)
                
                # Successfully loaded image, return
                return
                
            except Exception as e:
                print(f"Error loading image {self.current_image_filename}: {e}")
                self.current_image_index += 1
                
                # If we've reached the end of the images, show completion message
                if self.current_image_index >= len(self.images_to_label):
                    self.show_completion_message()
                    return
        
        # If we've tried several images and none worked, show an error message
        error_label = ttk.Label(
            self.root,
            text=f"Failed to load multiple images. Please check the image files.",
            foreground="red"
        )
        error_label.pack(pady=10)
        
        # Try again with the next batch of images
        self.load_next_image()
    
    def update_selected_colors(self):
        """Update the list of currently selected colors based on checkbox states"""
        self.selected_colors = []
        for color_key, var in self.color_vars.items():
            if var.get():
                self.selected_colors.append(color_key)
    
    def on_confirm(self):
        """Save the current color selections and move to the next image"""
        if not self.selected_colors:
            messagebox.showwarning("No Selection", "Please select at least one color or skip the image.")
            return
            
        # Save the labels
        self.labeled_images[self.current_image_filename] = self.selected_colors
        self.save_results()
        
        # Move to next image
        self.current_image_index += 1
        self.load_next_image()
    
    def on_retire(self):
        """Retire the current image and move to the next one"""
        if messagebox.askyesno("Confirm Retire",
                              f"Are you sure you want to retire {self.current_image_filename}?\n\n"
                              f"This will move it to {self.retired_dir} and remove it from all color folders."):
            try:
                # Move the file to retired directory
                shutil.move(self.current_image_path, os.path.join(self.retired_dir, self.current_image_filename))
                
                # Remove from labeled images if present
                if self.current_image_filename in self.labeled_images:
                    del self.labeled_images[self.current_image_filename]
                    self.save_results()
                
                messagebox.showinfo("Success", f"Image {self.current_image_filename} has been retired.")
                
                # Move to next image
                self.current_image_index += 1
                self.load_next_image()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to retire image: {e}")
    
    def on_skip(self):
        """Skip the current image and move to the next one"""
        self.current_image_index += 1
        self.load_next_image()
    
    def save_results(self):
        with open(self.results_file, 'w') as f:
            json.dump(self.labeled_images, f, indent=2)
    
    def show_completion_message(self):
        # Clear the image
        self.image_label.config(image='')
        
        # Show completion message
        completion_label = ttk.Label(
            self.root, 
            text="All images have been labeled!\nYou can close this window.",
            font=("Arial", 16)
        )
        completion_label.pack(expand=True)
        
        # Update progress to 100%
        self.progress_var.set(100)
        self.progress_label.config(text=f"{len(self.labeled_images)}/{len(self.labeled_images)}")
    
    def on_close(self):
        self.save_results()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ImageColorLabeler(root)
    root.mainloop()

if __name__ == "__main__":
    main()