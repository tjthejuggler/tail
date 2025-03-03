#!/usr/bin/env python3

import os
import sys
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import random

class ImageColorLabeler:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Color Labeler")
        self.root.geometry("1000x800")
        
        # Define color categories and their key bindings
        self.color_categories = {
            'r': 'red',
            'o': 'orange',
            'g': 'green',
            'b': 'blue',
            'p': 'pink',
            'y': 'yellow',
            'w': 'white_gray_black',
            's': 'skip'  # Skip this image
        }
        
        # Paths
        self.base_dir = "/home/twain/Pictures"
        self.source_dir = os.path.join(self.base_dir, "llm_baby_monster_by_color/white_gray_black")
        self.results_file = os.path.join(self.base_dir, "image_color_labels.json")
        
        # Load existing results if available
        self.labeled_images = {}
        if os.path.exists(self.results_file):
            with open(self.results_file, 'r') as f:
                self.labeled_images = json.load(f)
        
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
        
        # Create UI elements
        self.create_ui()
        
        # Start with the first image
        self.load_next_image()
        
        # Bind keyboard events
        for key in self.color_categories.keys():
            self.root.bind(key, self.on_key_press)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Image display
        self.image_label = ttk.Label(main_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Instructions
        instructions = "Press a key to categorize the image:\n"
        for key, color in self.color_categories.items():
            instructions += f"{key}: {color}\n"
        
        instructions_label = ttk.Label(main_frame, text=instructions, justify=tk.LEFT)
        instructions_label.pack(fill=tk.X, pady=10)
        
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
        
        self.current_image_filename = self.images_to_label[self.current_image_index]
        self.current_image_path = os.path.join(self.source_dir, self.current_image_filename)
        
        # Update progress
        self.progress_var.set((self.current_image_index / len(self.images_to_label)) * 100)
        self.progress_label.config(text=f"{self.current_image_index + 1}/{len(self.images_to_label)}")
        self.filename_label.config(text=f"Current file: {self.current_image_filename}")
        
        # Load and display image
        try:
            image = Image.open(self.current_image_path)
            
            # Resize image to fit the window while maintaining aspect ratio
            window_width = self.root.winfo_width() - 40
            window_height = self.root.winfo_height() - 200
            
            img_width, img_height = image.size
            scale = min(window_width / img_width, window_height / img_height)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            image = image.resize((new_width, new_height), Image.LANCZOS)
            
            self.photo_image = ImageTk.PhotoImage(image)
            self.image_label.config(image=self.photo_image)
            
        except Exception as e:
            print(f"Error loading image {self.current_image_filename}: {e}")
            self.current_image_index += 1
            self.load_next_image()
    
    def on_key_press(self, event):
        key = event.char.lower()
        if key in self.color_categories:
            color = self.color_categories[key]
            
            if color != 'skip':
                # Save the label
                self.labeled_images[self.current_image_filename] = color
                self.save_results()
            
            # Move to next image
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