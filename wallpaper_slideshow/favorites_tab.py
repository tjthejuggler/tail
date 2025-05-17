#!/usr/bin/env python3
"""
Favorites Tab for Wallpaper Slideshow Manager

This module provides a tab for managing favorite wallpapers in the wallpaper slideshow system.
It allows users to:
- View a list of favorite wallpapers
- Add new wallpapers to favorites
- Remove wallpapers from favorites
- Set a favorite as the current wallpaper
- Use only favorites for the slideshow
"""

import os
import json
import subprocess
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
                            QListWidgetItem, QPushButton, QFileDialog, QMessageBox,
                            QCheckBox, QSplitter, QGroupBox, QFormLayout)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.expanduser('~/.wallpaper_tray.log')
)
logger = logging.getLogger(__name__)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FAVORITES_DIR = os.path.expanduser("~/.wallpaper_favorites")
FAVORITES_FILE = os.path.join(FAVORITES_DIR, "favorites.json")
SET_WALLPAPER_SCRIPT = os.path.join(SCRIPT_DIR, "set_specific_wallpaper.py")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.ini")
CURRENT_WALLPAPER_FILE = os.path.expanduser("~/Projects/tail/current-wallpaper")

# Load supported image extensions from config
SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"]

class FavoritesTab(QWidget):
    """Tab for managing favorite wallpapers"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # Create favorites directory if it doesn't exist
        os.makedirs(FAVORITES_DIR, exist_ok=True)
        
        # Initialize favorites data
        self.favorites = []
        self.load_favorites()
        
        # Set up UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI elements"""
        main_layout = QVBoxLayout(self)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left side - Favorites list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Favorites list
        left_layout.addWidget(QLabel("Favorite Wallpapers:"))
        self.favorites_list = QListWidget()
        self.favorites_list.setIconSize(QSize(100, 60))
        self.favorites_list.itemDoubleClicked.connect(self.on_favorite_double_clicked)
        left_layout.addWidget(self.favorites_list)
        
        # Buttons for favorites list
        buttons_layout = QHBoxLayout()
        
        # Set as current button
        set_current_button = QPushButton("Set as Current Wallpaper")
        set_current_button.clicked.connect(self.set_as_current)
        buttons_layout.addWidget(set_current_button)
        
        # Remove button
        remove_button = QPushButton("Remove from Favorites")
        remove_button.clicked.connect(self.remove_from_favorites)
        buttons_layout.addWidget(remove_button)
        
        left_layout.addLayout(buttons_layout)
        
        # Right side - Preview and options
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Preview group
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        preview_layout.addWidget(self.preview_label)
        
        # Wallpaper info
        self.wallpaper_info_label = QLabel("No wallpaper selected")
        preview_layout.addWidget(self.wallpaper_info_label)
        
        right_layout.addWidget(preview_group)
        
        # Add new favorites group
        add_group = QGroupBox("Add New Favorites")
        add_layout = QVBoxLayout(add_group)
        
        # Add current wallpaper button
        add_current_button = QPushButton("Add Current Wallpaper to Favorites")
        add_current_button.clicked.connect(self.add_current_to_favorites)
        add_layout.addWidget(add_current_button)
        
        # Browse for wallpaper button
        browse_button = QPushButton("Browse for Wallpapers to Add")
        browse_button.clicked.connect(self.browse_for_wallpapers)
        add_layout.addWidget(browse_button)
        
        right_layout.addWidget(add_group)
        
        # Slideshow options group
        options_group = QGroupBox("Slideshow Options")
        options_layout = QVBoxLayout(options_group)
        
        # Use only favorites checkbox
        self.use_favorites_checkbox = QCheckBox("Use only favorites for slideshow")
        self.use_favorites_checkbox.setToolTip("When checked, the slideshow will only show wallpapers from your favorites list")
        self.use_favorites_checkbox.stateChanged.connect(self.on_use_favorites_changed)
        options_layout.addWidget(self.use_favorites_checkbox)
        
        # Load the current state of the checkbox
        self.load_use_favorites_state()
        
        right_layout.addWidget(options_group)
        
        # Add stretch to push everything to the top
        right_layout.addStretch(1)
        
        # Add widgets to main splitter
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setStretchFactor(0, 1)  # Make favorites list expandable
        
        # Set initial splitter sizes (60% list, 40% options)
        main_splitter.setSizes([600, 400])
        
        # Populate the favorites list
        self.populate_favorites_list()
    
    def load_favorites(self):
        """Load favorites from JSON file"""
        if os.path.exists(FAVORITES_FILE):
            try:
                with open(FAVORITES_FILE, 'r') as f:
                    data = json.load(f)
                    self.favorites = data.get("favorites", [])
                logger.info(f"Loaded {len(self.favorites)} favorites from {FAVORITES_FILE}")
            except Exception as e:
                logger.error(f"Error loading favorites: {e}")
                self.favorites = []
        else:
            self.favorites = []
            # Create empty favorites file
            self.save_favorites()
    
    def save_favorites(self):
        """Save favorites to JSON file"""
        try:
            with open(FAVORITES_FILE, 'w') as f:
                json.dump({"favorites": self.favorites}, f, indent=2)
            logger.info(f"Saved {len(self.favorites)} favorites to {FAVORITES_FILE}")
        except Exception as e:
            logger.error(f"Error saving favorites: {e}")
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"Error saving favorites: {str(e)}", 3000)
    
    def populate_favorites_list(self):
        """Populate the list of favorite wallpapers"""
        self.favorites_list.clear()
        
        for wallpaper_path in self.favorites:
            if os.path.exists(wallpaper_path):
                item = QListWidgetItem(os.path.basename(wallpaper_path))
                item.setData(Qt.UserRole, wallpaper_path)
                
                # Add thumbnail
                try:
                    pixmap = QPixmap(wallpaper_path)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(100, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        item.setIcon(QIcon(pixmap))
                except Exception as e:
                    logger.error(f"Error creating thumbnail for {wallpaper_path}: {e}")
                
                self.favorites_list.addItem(item)
            else:
                logger.warning(f"Favorite wallpaper not found: {wallpaper_path}")
        
        if self.parent_window:
            self.parent_window.statusBar().showMessage(f"Loaded {self.favorites_list.count()} favorite wallpapers", 3000)
    
    def on_favorite_double_clicked(self, item):
        """Handle double-click on a favorite wallpaper"""
        wallpaper_path = item.data(Qt.UserRole)
        self.set_wallpaper(wallpaper_path)
        self.show_preview(wallpaper_path)
    
    def set_as_current(self):
        """Set the selected wallpaper as the current wallpaper"""
        selected_items = self.favorites_list.selectedItems()
        if not selected_items:
            if self.parent_window:
                self.parent_window.statusBar().showMessage("No wallpaper selected", 3000)
            return
        
        wallpaper_path = selected_items[0].data(Qt.UserRole)
        self.set_wallpaper(wallpaper_path)
        self.show_preview(wallpaper_path)
    
    def set_wallpaper(self, wallpaper_path):
        """Set a wallpaper as the current wallpaper"""
        if not wallpaper_path or not os.path.exists(wallpaper_path):
            if self.parent_window:
                self.parent_window.statusBar().showMessage("Wallpaper file not found", 3000)
            return
        
        try:
            # Use set_specific_wallpaper.py to set the wallpaper
            subprocess.run(
                ["python3", SET_WALLPAPER_SCRIPT, wallpaper_path],
                check=True
            )
            
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"Set wallpaper to {os.path.basename(wallpaper_path)}", 3000)
            logger.info(f"Set wallpaper to {wallpaper_path}")
        except Exception as e:
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"Error setting wallpaper: {str(e)}", 3000)
            logger.error(f"Error setting wallpaper: {e}")
    
    def remove_from_favorites(self):
        """Remove the selected wallpaper from favorites"""
        selected_items = self.favorites_list.selectedItems()
        if not selected_items:
            if self.parent_window:
                self.parent_window.statusBar().showMessage("No wallpaper selected", 3000)
            return
        
        wallpaper_path = selected_items[0].data(Qt.UserRole)
        
        # Confirm removal
        if QMessageBox.question(
            self, "Confirm Removal",
            f"Remove {os.path.basename(wallpaper_path)} from favorites?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            # Remove from favorites list
            if wallpaper_path in self.favorites:
                self.favorites.remove(wallpaper_path)
                self.save_favorites()
                
                # Update UI
                self.populate_favorites_list()
                self.preview_label.clear()
                self.wallpaper_info_label.setText("No wallpaper selected")
                
                if self.parent_window:
                    self.parent_window.statusBar().showMessage(f"Removed {os.path.basename(wallpaper_path)} from favorites", 3000)
                logger.info(f"Removed {wallpaper_path} from favorites")
    
    def add_current_to_favorites(self):
        """Add the current wallpaper to favorites"""
        # Get current wallpaper path
        wallpaper_path = self.get_current_wallpaper_path()
        
        if not wallpaper_path:
            if self.parent_window:
                self.parent_window.statusBar().showMessage("Could not determine current wallpaper", 3000)
            return
        
        self.add_to_favorites(wallpaper_path)
    
    def get_current_wallpaper_path(self):
        """Get the path to the current wallpaper"""
        # First try to get from tracking file
        if os.path.exists(CURRENT_WALLPAPER_FILE):
            try:
                with open(CURRENT_WALLPAPER_FILE, 'r') as f:
                    wallpaper_path = f.read().strip()
                
                if wallpaper_path and os.path.exists(wallpaper_path):
                    logger.debug(f"Got current wallpaper from tracking file: {wallpaper_path}")
                    return wallpaper_path
            except Exception as e:
                logger.error(f"Error reading current wallpaper file: {e}")
        
        # If tracking file didn't work, try the get_current_wallpaper.py script
        try:
            get_current_wallpaper = os.path.join(os.path.dirname(SCRIPT_DIR), "get_current_wallpaper.py")
            result = subprocess.run(
                ["python3", get_current_wallpaper, "--verbose"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "Full path:" in line:
                        wallpaper_path = line.split("Full path:")[1].strip()
                        if wallpaper_path and os.path.exists(wallpaper_path):
                            logger.debug(f"Got current wallpaper from get_current_wallpaper.py: {wallpaper_path}")
                            return wallpaper_path
        except Exception as e:
            logger.error(f"Error running get_current_wallpaper.py: {e}")
        
        return None
    
    def browse_for_wallpapers(self):
        """Open file dialog to browse for wallpapers to add to favorites"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Wallpapers to Add to Favorites",
            os.path.expanduser("~/Pictures"),
            f"Image Files ({' '.join('*' + ext for ext in SUPPORTED_EXTENSIONS)})"
        )
        
        if not file_paths:
            return
        
        # Add each selected file to favorites
        added_count = 0
        for file_path in file_paths:
            if self.add_to_favorites(file_path):
                added_count += 1
        
        if self.parent_window:
            self.parent_window.statusBar().showMessage(f"Added {added_count} wallpapers to favorites", 3000)
    
    def add_to_favorites(self, wallpaper_path):
        """Add a wallpaper to favorites"""
        if not wallpaper_path or not os.path.exists(wallpaper_path):
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"Wallpaper file not found: {wallpaper_path}", 3000)
            return False
        
        # Check if already in favorites
        if wallpaper_path in self.favorites:
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"{os.path.basename(wallpaper_path)} is already in favorites", 3000)
            return False
        
        # Add to favorites
        self.favorites.append(wallpaper_path)
        self.save_favorites()
        
        # Update UI
        self.populate_favorites_list()
        
        # Show preview
        self.show_preview(wallpaper_path)
        
        if self.parent_window:
            self.parent_window.statusBar().showMessage(f"Added {os.path.basename(wallpaper_path)} to favorites", 3000)
        logger.info(f"Added {wallpaper_path} to favorites")
        
        return True
    
    def show_preview(self, wallpaper_path):
        """Show a preview of the selected wallpaper"""
        if not wallpaper_path or not os.path.exists(wallpaper_path):
            self.preview_label.clear()
            self.wallpaper_info_label.setText("Wallpaper file not found")
            return
        
        try:
            # Get file info
            file_size = os.path.getsize(wallpaper_path) / (1024 * 1024)  # Convert to MB
            
            # Load image to get dimensions
            pixmap = QPixmap(wallpaper_path)
            if not pixmap.isNull():
                # Get dimensions
                width = pixmap.width()
                height = pixmap.height()
                
                # Scale for preview
                pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(pixmap)
                
                # Update info label
                self.wallpaper_info_label.setText(
                    f"File: {os.path.basename(wallpaper_path)}\n"
                    f"Size: {file_size:.2f} MB\n"
                    f"Dimensions: {width}x{height}"
                )
            else:
                self.preview_label.setText("Preview not available")
                self.wallpaper_info_label.setText(f"File: {os.path.basename(wallpaper_path)}")
        except Exception as e:
            logger.error(f"Error showing preview: {e}")
            self.preview_label.setText("Error loading preview")
            self.wallpaper_info_label.setText(f"File: {os.path.basename(wallpaper_path)}")
    
    def on_use_favorites_changed(self, state):
        """Handle change in the 'Use only favorites for slideshow' checkbox"""
        use_favorites = (state == Qt.Checked)
        
        try:
            # Update the wallpaper_color_manager_new/config.json file
            config_path = os.path.join(os.path.dirname(SCRIPT_DIR), "wallpaper_color_manager_new/config.json")
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Update the config
                config["use_favorites_only"] = use_favorites
                
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                
                logger.info(f"Updated use_favorites_only setting to {use_favorites}")
                
                # Show message
                if self.parent_window:
                    if use_favorites:
                        self.parent_window.statusBar().showMessage("Slideshow will now use only favorite wallpapers", 3000)
                    else:
                        self.parent_window.statusBar().showMessage("Slideshow will now use all wallpapers", 3000)
                
                # Restart the slideshow to apply changes
                restart_script = os.path.join(SCRIPT_DIR, "restart_slideshow.sh")
                if os.path.exists(restart_script):
                    subprocess.Popen([restart_script])
                    logger.info("Restarting slideshow to apply changes")
            else:
                logger.error(f"Config file not found: {config_path}")
                if self.parent_window:
                    self.parent_window.statusBar().showMessage("Error: Config file not found", 3000)
        except Exception as e:
            logger.error(f"Error updating use_favorites_only setting: {e}")
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"Error updating settings: {str(e)}", 3000)
    
    def load_use_favorites_state(self):
        """Load the current state of the 'Use only favorites for slideshow' setting"""
        try:
            config_path = os.path.join(os.path.dirname(SCRIPT_DIR), "wallpaper_color_manager_new/config.json")
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                use_favorites = config.get("use_favorites_only", False)
                self.use_favorites_checkbox.setChecked(use_favorites)
                logger.info(f"Loaded use_favorites_only setting: {use_favorites}")
        except Exception as e:
            logger.error(f"Error loading use_favorites_only setting: {e}")
            # Default to unchecked
            self.use_favorites_checkbox.setChecked(False)