#!/usr/bin/env python3
"""
Create a tray icon for the wallpaper slideshow application
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_tray_icon(output_path, size=(128, 128)):
    """Create a tray icon for the wallpaper slideshow application"""
    # Create a new image with a transparent background
    icon = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # Calculate dimensions
    width, height = size
    padding = width // 10
    inner_width = width - 2 * padding
    inner_height = height - 2 * padding
    
    # Draw a rounded rectangle for the wallpaper frame
    draw.rounded_rectangle(
        [(padding, padding), (width - padding, height - padding)],
        radius=width // 10,
        fill=(30, 144, 255, 200),  # Dodger blue, semi-transparent
        outline=(255, 255, 255, 255),
        width=2
    )
    
    # Draw a smaller rounded rectangle for the "photo"
    photo_padding = width // 6
    draw.rounded_rectangle(
        [(photo_padding, photo_padding), (width - photo_padding, height - photo_padding)],
        radius=width // 20,
        fill=(240, 240, 240, 255),  # Light gray
        outline=(200, 200, 200, 255),
        width=1
    )
    
    # Draw a simple landscape in the photo
    # Sky
    draw.rectangle(
        [(photo_padding + 2, photo_padding + 2), 
         (width - photo_padding - 2, height // 2)],
        fill=(135, 206, 235, 255)  # Sky blue
    )
    
    # Ground
    draw.rectangle(
        [(photo_padding + 2, height // 2), 
         (width - photo_padding - 2, height - photo_padding - 2)],
        fill=(34, 139, 34, 255)  # Forest green
    )
    
    # Sun
    sun_radius = width // 12
    draw.ellipse(
        [(width // 3 - sun_radius, photo_padding + 10 - sun_radius // 2),
         (width // 3 + sun_radius, photo_padding + 10 + sun_radius * 3 // 2)],
        fill=(255, 215, 0, 255)  # Gold
    )
    
    # Draw a small clock icon to represent slideshow
    clock_center = (width - width // 4, height - height // 4)
    clock_radius = width // 10
    
    # Clock face
    draw.ellipse(
        [(clock_center[0] - clock_radius, clock_center[1] - clock_radius),
         (clock_center[0] + clock_radius, clock_center[1] + clock_radius)],
        fill=(255, 255, 255, 230),
        outline=(0, 0, 0, 255),
        width=2
    )
    
    # Clock hands
    # Hour hand
    draw.line(
        [clock_center, 
         (clock_center[0], clock_center[1] - clock_radius * 0.6)],
        fill=(0, 0, 0, 255),
        width=3
    )
    
    # Minute hand
    draw.line(
        [clock_center, 
         (clock_center[0] + clock_radius * 0.7, clock_center[1])],
        fill=(0, 0, 0, 255),
        width=2
    )
    
    # Save the icon
    icon.save(output_path)
    print(f"Icon created at: {output_path}")
    return output_path

if __name__ == "__main__":
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "wallpaper_tray_icon.png")
    
    create_tray_icon(output_path)