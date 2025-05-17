#!/usr/bin/env python3
"""
Wallpaper Slideshow Main Window

This script provides a tabbed main window for the wallpaper slideshow application,
combining history, image notes, favorites, and settings in a single interface.

Features:
- History tab: View and manage wallpaper history
- Notes tab: Add and edit notes for wallpapers
- Favorites tab: View, add, and manage favorite wallpapers
- Settings tab: Configure slideshow settings like frequency, directory, etc.

Usage:
    This module is used by wallpaper_tray.py
"""

import os
import sys
import json
import configparser
import subprocess
import signal
import shutil
from pathlib import Path
import logging
from datetime import datetime

from PyQt5.QtWidgets import (QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QTextEdit, QPushButton, QListWidget,
                            QListWidgetItem, QSplitter, QFileDialog, QMessageBox,
                            QCheckBox, QSpinBox, QComboBox, QFormLayout, QGroupBox,
                            QDialogButtonBox, QTreeView, QHeaderView, QToolBar, QAction)
from PyQt5.QtGui import QIcon, QPixmap, QImageReader
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject, QTimer, QDir, QFileSystemModel, QModelIndex

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.expanduser('~/.wallpaper_main_window.log')
)
logger = logging.getLogger(__name__)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_DIR = os.path.expanduser("~/.wallpaper_notes")
FAVORITES_DIR = os.path.expanduser("~/.wallpaper_favorites")
FAVORITES_FILE = os.path.join(FAVORITES_DIR, "favorites.json")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.ini")

# Load supported image extensions from config
SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"]
if os.path.exists(CONFIG_FILE):
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        if 'Advanced' in config and 'supported_extensions' in config['Advanced']:
            SUPPORTED_EXTENSIONS = [ext.strip() for ext in config['Advanced']['supported_extensions'].split(',')]
        
        # Get default image directory
        DEFAULT_IMAGE_DIR = os.path.expanduser("~/Pictures")
        if 'General' in config and 'image_directory' in config['General']:
            DEFAULT_IMAGE_DIR = os.path.expanduser(config['General']['image_directory'])
    except Exception as e:
        logger.error(f"Error reading config.ini: {e}")
else:
    DEFAULT_IMAGE_DIR = os.path.expanduser("~/Pictures")
class HistoryTab(QWidget):
    """Tab for viewing the history of wallpapers shown in the slideshow"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setup_ui()
        
        # Load history
        self.history_file = os.path.join(NOTES_DIR, "wallpaper_history.json")
        self.load_history()
    
    def setup_ui(self):
        """Set up the UI elements"""
        main_layout = QVBoxLayout(self)
        
        # Create list widget for wallpaper history
        self.history_list = QListWidget()
        self.history_list.setIconSize(QSize(100, 60))
        self.history_list.itemDoubleClicked.connect(self.on_wallpaper_double_clicked)
        main_layout.addWidget(QLabel("Recently Shown Wallpapers:"))
        main_layout.addWidget(self.history_list)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Refresh button
        refresh_button = QPushButton("Refresh History")
        refresh_button.clicked.connect(self.load_history)
        button_layout.addWidget(refresh_button)
        
        # Set as current button
        set_current_button = QPushButton("Set as Current Wallpaper")
        set_current_button.clicked.connect(self.set_as_current)
        button_layout.addWidget(set_current_button)
        
        # Clear history button
        clear_button = QPushButton("Clear History")
        clear_button.clicked.connect(self.clear_history)
        button_layout.addWidget(clear_button)
        
        main_layout.addLayout(button_layout)
    
    def load_history(self):
        """Load wallpaper history from JSON file"""
        self.history_list.clear()
        
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history_data = json.load(f)
                
                # Add wallpapers to list in reverse order (newest first)
                for entry in reversed(history_data):
                    wallpaper_path = entry.get("path", "")
                    timestamp = entry.get("timestamp", "")
                    
                    if wallpaper_path and os.path.exists(wallpaper_path):
                        item = QListWidgetItem(f"{os.path.basename(wallpaper_path)} - {timestamp}")
                        item.setData(Qt.UserRole, wallpaper_path)
                        
                        # Add thumbnail
                        pixmap = QPixmap(wallpaper_path)
                        if not pixmap.isNull():
                            pixmap = pixmap.scaled(100, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            item.setIcon(QIcon(pixmap))
                        
                        self.history_list.addItem(item)
                
                if self.parent_window:
                    self.parent_window.statusBar().showMessage(f"Loaded {self.history_list.count()} wallpapers from history", 3000)
            except Exception as e:
                logger.error(f"Error loading wallpaper history: {e}")
                if self.parent_window:
                    self.parent_window.statusBar().showMessage("Error loading wallpaper history", 3000)
        else:
            if self.parent_window:
                self.parent_window.statusBar().showMessage("No wallpaper history found", 3000)
    
    def add_to_history(self, wallpaper_path):
        """Add a wallpaper to the history"""
        if not wallpaper_path or not os.path.exists(wallpaper_path):
            return
        
        history_data = []
        
        # Load existing history
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading wallpaper history: {e}")
        
        # Check if this wallpaper is already in history
        for entry in history_data:
            if entry.get("path") == wallpaper_path:
                # Update timestamp and move to end (most recent)
                entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                history_data.remove(entry)
                history_data.append(entry)
                break
        else:
            # Add new entry
            history_data.append({
                "path": wallpaper_path,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Limit history size
        if len(history_data) > 50:
            history_data = history_data[-50:]
        
        # Save history
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
            logger.info(f"Added {wallpaper_path} to wallpaper history")
        except Exception as e:
            logger.error(f"Error saving wallpaper history: {e}")
    
    def on_wallpaper_double_clicked(self, item):
        """Handle double-click on a wallpaper in the history list"""
        wallpaper_path = item.data(Qt.UserRole)
        self.set_wallpaper(wallpaper_path)
    
    def set_as_current(self):
        """Set the selected wallpaper as the current wallpaper"""
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            if self.parent_window:
                self.parent_window.statusBar().showMessage("No wallpaper selected", 3000)
            return
        
        wallpaper_path = selected_items[0].data(Qt.UserRole)
        self.set_wallpaper(wallpaper_path)
    
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
    
    def clear_history(self):
        """Clear the wallpaper history"""
        if QMessageBox.question(
            self, "Confirm Clear History", 
            "Are you sure you want to clear the wallpaper history?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            try:
                if os.path.exists(self.history_file):
                    os.remove(self.history_file)
                
                self.history_list.clear()
                if self.parent_window:
                    self.parent_window.statusBar().showMessage("Wallpaper history cleared", 3000)
                logger.info("Wallpaper history cleared")
            except Exception as e:
                if self.parent_window:
                    self.parent_window.statusBar().showMessage(f"Error clearing history: {str(e)}", 3000)
                logger.error(f"Error clearing wallpaper history: {e}")
CONTROL_SCRIPT = os.path.join(SCRIPT_DIR, "control_slideshow.sh")
GET_CURRENT_WALLPAPER = os.path.join(os.path.dirname(SCRIPT_DIR), "get_current_wallpaper.py")
SET_WALLPAPER_SCRIPT = os.path.join(SCRIPT_DIR, "set_specific_wallpaper.py")
CUSTOM_WALLPAPER_SCRIPT = os.path.join(SCRIPT_DIR, "custom_wallpaper.py")
class NotesTab(QWidget):
    """Tab for viewing and editing notes for wallpapers"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # Initialize variables
        self.current_wallpaper = None
        self.notes_data = {}
        self.load_notes_data()
        self.current_directory = DEFAULT_IMAGE_DIR
        self.navigation_history = []
        self.navigation_position = -1
        
        # Set up UI
        self.setup_ui()
        
        # Create notes directory if it doesn't exist
        os.makedirs(NOTES_DIR, exist_ok=True)
        
        # Populate the list
        self.populate_wallpaper_list()
        
        # Initialize file browser
        self.initialize_file_browser()
        
        # Get current wallpaper
        self.refresh_current_wallpaper()
    
    def setup_ui(self):
        """Set up the UI elements"""
        main_layout = QVBoxLayout(self)
        
        # Create main splitter for file browser and notes area
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Create file browser widget
        file_browser_widget = QWidget()
        file_browser_layout = QVBoxLayout(file_browser_widget)
        file_browser_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add navigation toolbar
        nav_toolbar = QToolBar()
        nav_toolbar.setIconSize(QSize(16, 16))
        
        # Back button
        self.back_button = QAction(QIcon.fromTheme("go-previous"), "Back", self)
        self.back_button.triggered.connect(self.navigate_back)
        self.back_button.setEnabled(False)
        nav_toolbar.addAction(self.back_button)
        
        # Forward button
        self.forward_button = QAction(QIcon.fromTheme("go-next"), "Forward", self)
        self.forward_button.triggered.connect(self.navigate_forward)
        self.forward_button.setEnabled(False)
        nav_toolbar.addAction(self.forward_button)
        
        # Up button
        up_button = QAction(QIcon.fromTheme("go-up"), "Up", self)
        up_button.triggered.connect(self.navigate_up)
        nav_toolbar.addAction(up_button)
        
        # Home button
        home_button = QAction(QIcon.fromTheme("go-home"), "Home", self)
        home_button.triggered.connect(self.navigate_home)
        nav_toolbar.addAction(home_button)
        
        # Add path display
        self.path_display = QLineEdit()
        self.path_display.setReadOnly(True)
        nav_toolbar.addSeparator()
        nav_toolbar.addWidget(self.path_display)
        
        file_browser_layout.addWidget(nav_toolbar)
        
        # Create file system model
        self.file_model = QFileSystemModel()
        self.file_model.setReadOnly(True)
        
        # Set filter for image files
        self.file_model.setNameFilters([f"*{ext}" for ext in SUPPORTED_EXTENSIONS])
        self.file_model.setNameFilterDisables(False)  # Hide non-matching files
        
        # Create tree view for file browser
        self.file_view = QTreeView()
        self.file_view.setModel(self.file_model)
        self.file_view.setRootIndex(self.file_model.setRootPath(self.current_directory))
        
        # Configure tree view
        self.file_view.setAnimated(False)
        self.file_view.setIndentation(20)
        self.file_view.setSortingEnabled(True)
        self.file_view.sortByColumn(0, Qt.AscendingOrder)
        
        # Hide unnecessary columns and adjust header
        self.file_view.setColumnWidth(0, 250)  # Name column
        self.file_view.header().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, self.file_model.columnCount()):
            self.file_view.setColumnWidth(i, 100)
        
        # Connect signals
        self.file_view.clicked.connect(self.on_file_clicked)
        self.file_view.doubleClicked.connect(self.on_file_double_clicked)
        
        file_browser_layout.addWidget(self.file_view)
        
        # Create right side widget with splitter for list and notes
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for list and notes
        notes_splitter = QSplitter(Qt.Horizontal)
        right_layout.addWidget(notes_splitter)
        
        # Create list widget for wallpapers with notes
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        self.wallpaper_list = QListWidget()
        self.wallpaper_list.setMinimumWidth(200)
        self.wallpaper_list.currentItemChanged.connect(self.on_wallpaper_selected)
        list_layout.addWidget(QLabel("Wallpapers with Notes:"))
        list_layout.addWidget(self.wallpaper_list)
        
        # Create notes widget
        notes_widget = QWidget()
        notes_layout = QVBoxLayout(notes_widget)
        
        # Current wallpaper display
        self.wallpaper_label = QLabel("Current Wallpaper: None")
        notes_layout.addWidget(self.wallpaper_label)
        
        # Wallpaper preview
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        notes_layout.addWidget(self.preview_label)
        
        # Notes text edit
        notes_layout.addWidget(QLabel("Notes:"))
        self.notes_edit = QTextEdit()
        notes_layout.addWidget(self.notes_edit)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Save button
        self.save_button = QPushButton("Save Notes")
        self.save_button.clicked.connect(self.save_current_notes)
        button_layout.addWidget(self.save_button)
        
        # Refresh button
        refresh_button = QPushButton("Refresh Current Wallpaper")
        refresh_button.clicked.connect(self.refresh_current_wallpaper)
        button_layout.addWidget(refresh_button)
        
        # Export button
        export_button = QPushButton("Export Notes")
        export_button.clicked.connect(self.export_notes)
        button_layout.addWidget(export_button)
        
        # Import button
        import_button = QPushButton("Import Notes")
        import_button.clicked.connect(self.import_notes)
        button_layout.addWidget(import_button)
        
        notes_layout.addLayout(button_layout)
        
        # Add widgets to notes splitter
        notes_splitter.addWidget(list_widget)
        notes_splitter.addWidget(notes_widget)
        notes_splitter.setStretchFactor(1, 1)  # Make notes side expandable
        
        # Add widgets to main splitter
        main_splitter.addWidget(file_browser_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setStretchFactor(1, 1)  # Make notes area expandable
        
        # Set initial splitter sizes (40% file browser, 60% notes area)
        main_splitter.setSizes([400, 600])
    
    def load_notes_data(self):
        """Load notes data from JSON file"""
        notes_file = os.path.join(NOTES_DIR, "notes_data.json")
        if os.path.exists(notes_file):
            try:
                with open(notes_file, 'r') as f:
                    self.notes_data = json.load(f)
                logger.info(f"Loaded notes data for {len(self.notes_data)} wallpapers")
            except Exception as e:
                logger.error(f"Error loading notes data: {e}")
                self.notes_data = {}
        else:
            self.notes_data = {}
    
    def save_notes_data(self):
        """Save notes data to JSON file"""
        notes_file = os.path.join(NOTES_DIR, "notes_data.json")
        try:
            with open(notes_file, 'w') as f:
                json.dump(self.notes_data, f, indent=2)
            logger.info(f"Saved notes data for {len(self.notes_data)} wallpapers")
        except Exception as e:
            logger.error(f"Error saving notes data: {e}")
    
    def populate_wallpaper_list(self):
        """Populate the list of wallpapers with notes"""
        self.wallpaper_list.clear()
        
        # Add wallpapers with notes
        for wallpaper_path in sorted(self.notes_data.keys()):
            item = QListWidgetItem(os.path.basename(wallpaper_path))
            item.setData(Qt.UserRole, wallpaper_path)
            self.wallpaper_list.addItem(item)
    
    def on_wallpaper_selected(self, current, previous):
        """Handle wallpaper selection from the list"""
        if not current:
            return
        
        wallpaper_path = current.data(Qt.UserRole)
        self.load_wallpaper_notes(wallpaper_path)
    
    def load_wallpaper_notes(self, wallpaper_path):
        """Load notes for the selected wallpaper"""
        if wallpaper_path in self.notes_data:
            self.current_wallpaper = wallpaper_path
            self.wallpaper_label.setText(f"Wallpaper: {os.path.basename(wallpaper_path)}")
            self.notes_edit.setText(self.notes_data[wallpaper_path].get("notes", ""))
            
            # Load preview if the file exists
            if os.path.exists(wallpaper_path):
                pixmap = QPixmap(wallpaper_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.preview_label.setPixmap(pixmap)
                else:
                    self.preview_label.setText("Preview not available")
            else:
                self.preview_label.setText("Image file not found")
        else:
            self.current_wallpaper = None
            self.wallpaper_label.setText("No wallpaper selected")
            self.notes_edit.clear()
            self.preview_label.clear()
    
    def save_current_notes(self):
        """Save notes for the current wallpaper"""
        if not self.current_wallpaper:
            return
        
        notes_text = self.notes_edit.toPlainText()
        
        # Create or update notes entry
        if self.current_wallpaper not in self.notes_data:
            self.notes_data[self.current_wallpaper] = {
                "notes": notes_text,
                "last_updated": datetime.now().isoformat()
            }
        else:
            self.notes_data[self.current_wallpaper]["notes"] = notes_text
            self.notes_data[self.current_wallpaper]["last_updated"] = datetime.now().isoformat()
        
        # Save to file
        self.save_notes_data()
        
        # Refresh the list
        self.populate_wallpaper_list()
        
        # Show confirmation
        if self.parent_window:
            self.parent_window.statusBar().showMessage("Notes saved successfully", 3000)
    
    def refresh_current_wallpaper(self):
        """Get the current wallpaper and load its notes"""
        logger.info("Starting refresh_current_wallpaper in NotesTab")
        try:
            # Run get_current_wallpaper.py to get the current wallpaper
            logger.debug("Running get_current_wallpaper.py with --name-only flag")
            try:
                result = subprocess.run(
                    ["python3", GET_CURRENT_WALLPAPER, "--name-only"],
                    capture_output=True,
                    text=True,
                    check=False  # Changed to False to handle errors manually
                )
                
                # Check return code manually
                if result.returncode != 0:
                    logger.warning(f"get_current_wallpaper.py exited with code {result.returncode}: {result.stderr}")
                    if self.parent_window:
                        self.parent_window.statusBar().showMessage("Could not determine current wallpaper", 3000)
                    return
                
                wallpaper_name = result.stdout.strip()
                
                if not wallpaper_name:
                    logger.warning("get_current_wallpaper.py returned empty output")
                    if self.parent_window:
                        self.parent_window.statusBar().showMessage("Could not determine current wallpaper", 3000)
                    return
            except Exception as e:
                logger.error(f"Exception running get_current_wallpaper.py: {e}")
                if self.parent_window:
                    self.parent_window.statusBar().showMessage("Error getting current wallpaper", 3000)
                return
            
            # Find the full path to the wallpaper
            logger.debug(f"Finding full path for wallpaper: {wallpaper_name}")
            wallpaper_path = self.find_wallpaper_path(wallpaper_name)
            
            if not wallpaper_path:
                logger.warning(f"Could not find full path for wallpaper: {wallpaper_name}")
                if self.parent_window:
                    self.parent_window.statusBar().showMessage(f"Could not find wallpaper: {wallpaper_name}", 3000)
                return
            
            logger.info(f"Current wallpaper: {wallpaper_path}")
            
            # Load notes for this wallpaper
            if wallpaper_path in self.notes_data:
                # Select the item in the list
                for i in range(self.wallpaper_list.count()):
                    item = self.wallpaper_list.item(i)
                    if item.data(Qt.UserRole) == wallpaper_path:
                        self.wallpaper_list.setCurrentItem(item)
                        break
            else:
                # Create a new entry
                self.current_wallpaper = wallpaper_path
                self.wallpaper_label.setText(f"Wallpaper: {os.path.basename(wallpaper_path)}")
                self.notes_edit.clear()
                
                # Load preview
                if os.path.exists(wallpaper_path):
                    pixmap = QPixmap(wallpaper_path)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.preview_label.setPixmap(pixmap)
                    else:
                        self.preview_label.setText("Preview not available")
                else:
                    self.preview_label.setText("Image file not found")
            
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"Current wallpaper: {os.path.basename(wallpaper_path)}", 3000)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting current wallpaper: {e}")
            if self.parent_window:
                self.parent_window.statusBar().showMessage("Error getting current wallpaper", 3000)
        except Exception as e:
            logger.error(f"Unexpected error in refresh_current_wallpaper: {e}")
            if self.parent_window:
                self.parent_window.statusBar().showMessage("Unexpected error refreshing wallpaper", 3000)
    
    def find_wallpaper_path(self, wallpaper_name):
        """Find the full path to a wallpaper by its filename"""
        # First check if we already have this wallpaper in our notes
        for path in self.notes_data.keys():
            if os.path.basename(path) == wallpaper_name:
                return path
        
        # Try to find the wallpaper in common locations
        search_dirs = [
            os.path.expanduser("~/Pictures/Wallpapers"),
            "/usr/share/wallpapers",
            "/usr/share/backgrounds"
        ]
        
        # Add slideshow directories from config.ini
        if os.path.exists(CONFIG_FILE):
            try:
                config = configparser.ConfigParser()
                config.read(CONFIG_FILE)
                if 'General' in config and 'image_directory' in config['General']:
                    img_dir = os.path.expanduser(config['General']['image_directory'])
                    search_dirs.append(img_dir)
            except Exception as e:
                logger.error(f"Error reading config.ini: {e}")
        
        # Search for the wallpaper
        for directory in search_dirs:
            if os.path.exists(directory):
                for root, dirs, files in os.walk(directory):
                    if wallpaper_name in files:
                        return os.path.join(root, wallpaper_name)
        
        # If not found, try to get the full path from get_current_wallpaper.py
        try:
            result = subprocess.run(
                ["python3", GET_CURRENT_WALLPAPER, "--verbose"],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.splitlines():
                if "Full path:" in line:
                    return line.split("Full path:")[1].strip()
        except Exception as e:
            logger.error(f"Error getting full wallpaper path: {e}")
        
        return None
    
    def export_notes(self):
        """Export notes data to a JSON file"""
        if not self.notes_data:
            QMessageBox.information(self, "Export Notes", "No notes to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Notes", os.path.expanduser("~/wallpaper_notes_export.json"), "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w') as f:
                json.dump(self.notes_data, f, indent=2)
            
            QMessageBox.information(
                self, "Export Successful", 
                f"Notes exported successfully to {file_path}"
            )
            logger.info(f"Notes exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(
                self, "Export Failed", 
                f"Failed to export notes: {str(e)}"
            )
            logger.error(f"Error exporting notes: {e}")
    
    def import_notes(self):
        """Import notes data from a JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Notes", os.path.expanduser("~"), "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                imported_data = json.load(f)
            
            # Validate the imported data
            if not isinstance(imported_data, dict):
                raise ValueError("Invalid notes data format")
            
            # Merge with existing notes
            for path, data in imported_data.items():
                if path not in self.notes_data:
                    self.notes_data[path] = data
                else:
                    # Ask user if they want to overwrite existing notes
                    if QMessageBox.question(
                        self, "Confirm Overwrite", 
                        f"Notes for {os.path.basename(path)} already exist. Overwrite?",
                        QMessageBox.Yes | QMessageBox.No
                    ) == QMessageBox.Yes:
                        self.notes_data[path] = data
            
            # Save and refresh
            self.save_notes_data()
            self.populate_wallpaper_list()
            
            QMessageBox.information(
                self, "Import Successful", 
                f"Notes imported successfully from {file_path}"
            )
            logger.info(f"Notes imported from {file_path}")
        except Exception as e:
            QMessageBox.critical(
                self, "Import Failed", 
                f"Failed to import notes: {str(e)}"
            )
            logger.error(f"Error importing notes: {e}")
    
    def initialize_file_browser(self):
        """Initialize the file browser with the default directory"""
        self.navigate_to_directory(self.current_directory)
        
    def navigate_to_directory(self, directory):
        """Navigate to a specific directory in the file browser"""
        if not os.path.exists(directory) or not os.path.isdir(directory):
            logger.warning(f"Directory does not exist: {directory}")
            directory = os.path.expanduser("~/Pictures")
            if not os.path.exists(directory):
                directory = os.path.expanduser("~")
        
        # Update current directory
        self.current_directory = directory
        
        # Update file view
        index = self.file_model.setRootPath(directory)
        self.file_view.setRootIndex(index)
        
        # Update path display
        self.path_display.setText(directory)
        
        # Add to navigation history if this is a new navigation
        if self.navigation_position == len(self.navigation_history) - 1:
            # Remove any forward history
            if self.navigation_position < len(self.navigation_history) - 1:
                self.navigation_history = self.navigation_history[:self.navigation_position + 1]
            
            # Add current directory to history
            self.navigation_history.append(directory)
            self.navigation_position = len(self.navigation_history) - 1
        
        # Update navigation buttons
        self.update_navigation_buttons()
        
    def navigate_back(self):
        """Navigate to the previous directory in history"""
        if self.navigation_position > 0:
            self.navigation_position -= 1
            directory = self.navigation_history[self.navigation_position]
            
            # Update without adding to history
            self.current_directory = directory
            index = self.file_model.setRootPath(directory)
            self.file_view.setRootIndex(index)
            self.path_display.setText(directory)
            
            # Update navigation buttons
            self.update_navigation_buttons()
    
    def navigate_forward(self):
        """Navigate to the next directory in history"""
        if self.navigation_position < len(self.navigation_history) - 1:
            self.navigation_position += 1
            directory = self.navigation_history[self.navigation_position]
            
            # Update without adding to history
            self.current_directory = directory
            index = self.file_model.setRootPath(directory)
            self.file_view.setRootIndex(index)
            self.path_display.setText(directory)
            
            # Update navigation buttons
            self.update_navigation_buttons()
    
    def navigate_up(self):
        """Navigate to the parent directory"""
        parent_dir = os.path.dirname(self.current_directory)
        if parent_dir and parent_dir != self.current_directory:
            self.navigate_to_directory(parent_dir)
    
    def navigate_home(self):
        """Navigate to the home directory (default image directory)"""
        self.navigate_to_directory(DEFAULT_IMAGE_DIR)
    
    def update_navigation_buttons(self):
        """Update the state of navigation buttons"""
        self.back_button.setEnabled(self.navigation_position > 0)
        self.forward_button.setEnabled(self.navigation_position < len(self.navigation_history) - 1)
    
    def on_file_clicked(self, index):
        """Handle file selection in the file browser"""
        file_path = self.file_model.filePath(index)
        
        if os.path.isfile(file_path) and self.is_image_file(file_path):
            # Load the image preview
            self.load_image_preview(file_path)
            
            # Load notes if they exist
            if file_path in self.notes_data:
                self.load_wallpaper_notes(file_path)
            else:
                # Create a new entry
                self.current_wallpaper = file_path
                self.wallpaper_label.setText(f"Wallpaper: {os.path.basename(file_path)}")
                self.notes_edit.clear()
    
    def on_file_double_clicked(self, index):
        """Handle double-click on file or directory in the file browser"""
        file_path = self.file_model.filePath(index)
        
        if os.path.isdir(file_path):
            # Navigate to the directory
            self.navigate_to_directory(file_path)
        elif os.path.isfile(file_path) and self.is_image_file(file_path):
            # Set as wallpaper
            self.set_as_wallpaper(file_path)
    
    def is_image_file(self, file_path):
        """Check if a file is an image based on its extension"""
        _, ext = os.path.splitext(file_path.lower())
        return ext in SUPPORTED_EXTENSIONS
    
    def load_image_preview(self, image_path):
        """Load an image preview into the preview label"""
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(pixmap)
            else:
                self.preview_label.setText("Preview not available")
        else:
            self.preview_label.setText("Image file not found")
    
    def set_as_wallpaper(self, wallpaper_path):
        """Set the selected image as the current wallpaper"""
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
            
            # Refresh current wallpaper
            QTimer.singleShot(500, self.refresh_current_wallpaper)
        except Exception as e:
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"Error setting wallpaper: {str(e)}", 3000)
            logger.error(f"Error setting wallpaper: {e}")
class FavoritesTab(QWidget):
    """Tab for viewing and managing favorite wallpapers"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # Initialize variables
        self.favorites = []
        self.current_directory = DEFAULT_IMAGE_DIR
        self.navigation_history = []
        self.navigation_position = -1
        
        # Set up UI
        self.setup_ui()
        
        # Create favorites directory if it doesn't exist
        os.makedirs(FAVORITES_DIR, exist_ok=True)
        
        # Load favorites
        self.load_favorites()
        
        # Initialize file browser
        self.initialize_file_browser()
        
        # Load use_favorites_only setting from config
        self.load_use_favorites_setting()
    
    def setup_ui(self):
        """Set up the UI elements"""
        main_layout = QVBoxLayout(self)
        
        # Create main splitter for file browser and favorites area
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Add "Use only favorites in slideshow" checkbox at the top
        self.use_favorites_only_checkbox = QCheckBox("Use only favorites in slideshow")
        self.use_favorites_only_checkbox.stateChanged.connect(self.toggle_use_favorites_only)
        main_layout.insertWidget(0, self.use_favorites_only_checkbox)
        
        # Create file browser widget
        file_browser_widget = QWidget()
        file_browser_layout = QVBoxLayout(file_browser_widget)
        file_browser_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add navigation toolbar
        nav_toolbar = QToolBar()
        nav_toolbar.setIconSize(QSize(16, 16))
        
        # Back button
        self.back_button = QAction(QIcon.fromTheme("go-previous"), "Back", self)
        self.back_button.triggered.connect(self.navigate_back)
        self.back_button.setEnabled(False)
        nav_toolbar.addAction(self.back_button)
        
        # Forward button
        self.forward_button = QAction(QIcon.fromTheme("go-next"), "Forward", self)
        self.forward_button.triggered.connect(self.navigate_forward)
        self.forward_button.setEnabled(False)
        nav_toolbar.addAction(self.forward_button)
        
        # Up button
        up_button = QAction(QIcon.fromTheme("go-up"), "Up", self)
        up_button.triggered.connect(self.navigate_up)
        nav_toolbar.addAction(up_button)
        
        # Home button
        home_button = QAction(QIcon.fromTheme("go-home"), "Home", self)
        home_button.triggered.connect(self.navigate_home)
        nav_toolbar.addAction(home_button)
        
        # Add path display
        self.path_display = QLineEdit()
        self.path_display.setReadOnly(True)
        nav_toolbar.addSeparator()
        nav_toolbar.addWidget(self.path_display)
        
        file_browser_layout.addWidget(nav_toolbar)
        
        # Create file system model
        self.file_model = QFileSystemModel()
        self.file_model.setReadOnly(True)
        
        # Set filter for image files
        self.file_model.setNameFilters([f"*{ext}" for ext in SUPPORTED_EXTENSIONS])
        self.file_model.setNameFilterDisables(False)  # Hide non-matching files
        
        # Create tree view for file browser
        self.file_view = QTreeView()
        self.file_view.setModel(self.file_model)
        self.file_view.setRootIndex(self.file_model.setRootPath(self.current_directory))
        
        # Configure tree view
        self.file_view.setAnimated(False)
        self.file_view.setIndentation(20)
        self.file_view.setSortingEnabled(True)
        self.file_view.sortByColumn(0, Qt.AscendingOrder)
        
        # Hide unnecessary columns and adjust header
        self.file_view.setColumnWidth(0, 250)  # Name column
        self.file_view.header().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, self.file_model.columnCount()):
            self.file_view.setColumnWidth(i, 100)
        
        # Connect signals
        self.file_view.clicked.connect(self.on_file_clicked)
        self.file_view.doubleClicked.connect(self.on_file_double_clicked)
        
        file_browser_layout.addWidget(self.file_view)
        
        # Create favorites widget
        favorites_widget = QWidget()
        favorites_layout = QVBoxLayout(favorites_widget)
        
        # Create list widget for favorites
        favorites_layout.addWidget(QLabel("Favorite Wallpapers:"))
        self.favorites_list = QListWidget()
        self.favorites_list.setIconSize(QSize(100, 60))
        self.favorites_list.itemDoubleClicked.connect(self.on_favorite_double_clicked)
        favorites_layout.addWidget(self.favorites_list)
        
        # Wallpaper preview
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        favorites_layout.addWidget(self.preview_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Add to favorites button
        add_button = QPushButton("Add Selected to Favorites")
        add_button.clicked.connect(self.add_selected_to_favorites)
        button_layout.addWidget(add_button)
        
        # Remove from favorites button
        remove_button = QPushButton("Remove from Favorites")
        remove_button.clicked.connect(self.remove_from_favorites)
        button_layout.addWidget(remove_button)
        
        # Set as wallpaper button
        set_button = QPushButton("Set as Wallpaper")
        set_button.clicked.connect(self.set_as_wallpaper)
        button_layout.addWidget(set_button)
        
        favorites_layout.addLayout(button_layout)
        
        # Add widgets to main splitter
        main_splitter.addWidget(file_browser_widget)
        main_splitter.addWidget(favorites_widget)
        main_splitter.setStretchFactor(1, 1)  # Make favorites area expandable
        
        # Set initial splitter sizes (40% file browser, 60% favorites area)
        main_splitter.setSizes([400, 600])
    
    def load_favorites(self):
        """Load favorites from JSON file"""
        self.favorites_list.clear()
        self.favorites = []
        
        # Create favorites file if it doesn't exist
        if not os.path.exists(FAVORITES_FILE):
            with open(FAVORITES_FILE, 'w') as f:
                json.dump({"favorites": []}, f, indent=2)
            logger.info(f"Created new favorites file at {FAVORITES_FILE}")
        
        # Load favorites
        try:
            with open(FAVORITES_FILE, 'r') as f:
                data = json.load(f)
                self.favorites = data.get("favorites", [])
                
            # Check for invalid or missing files and remove them
            valid_favorites = []
            for path in self.favorites:
                if os.path.exists(path) and os.path.isfile(path):
                    valid_favorites.append(path)
                else:
                    logger.warning(f"Removing invalid favorite: {path}")
            
            # Update favorites list if any invalid paths were found
            if len(valid_favorites) != len(self.favorites):
                self.favorites = valid_favorites
                self.save_favorites()
            
            # Add favorites to list
            for wallpaper_path in self.favorites:
                if os.path.exists(wallpaper_path):
                    item = QListWidgetItem(os.path.basename(wallpaper_path))
                    item.setData(Qt.UserRole, wallpaper_path)
                    
                    # Add thumbnail
                    pixmap = QPixmap(wallpaper_path)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(100, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        item.setIcon(QIcon(pixmap))
                    
                    self.favorites_list.addItem(item)
            
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"Loaded {self.favorites_list.count()} favorite wallpapers", 3000)
            logger.info(f"Loaded {len(self.favorites)} favorites")
        except Exception as e:
            logger.error(f"Error loading favorites: {e}")
            if self.parent_window:
                self.parent_window.statusBar().showMessage("Error loading favorites", 3000)
    
    def save_favorites(self):
        """Save favorites to JSON file"""
        try:
            with open(FAVORITES_FILE, 'w') as f:
                json.dump({"favorites": self.favorites}, f, indent=2)
            logger.info(f"Saved {len(self.favorites)} favorites")
        except Exception as e:
            logger.error(f"Error saving favorites: {e}")
            if self.parent_window:
                self.parent_window.statusBar().showMessage("Error saving favorites", 3000)
    
    def add_to_favorites(self, wallpaper_path):
        """Add a wallpaper to favorites"""
        if not wallpaper_path or not os.path.exists(wallpaper_path):
            if self.parent_window:
                self.parent_window.statusBar().showMessage("Wallpaper file not found", 3000)
            return
        
        # Check if already in favorites
        if wallpaper_path in self.favorites:
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"{os.path.basename(wallpaper_path)} is already in favorites", 3000)
            return
        
        # Add to favorites list
        self.favorites.append(wallpaper_path)
        
        # Add to UI list
        item = QListWidgetItem(os.path.basename(wallpaper_path))
        item.setData(Qt.UserRole, wallpaper_path)
        
        # Add thumbnail
        pixmap = QPixmap(wallpaper_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(100, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item.setIcon(QIcon(pixmap))
        
        self.favorites_list.addItem(item)
        
        # Save favorites
        self.save_favorites()
        
        if self.parent_window:
            self.parent_window.statusBar().showMessage(f"Added {os.path.basename(wallpaper_path)} to favorites", 3000)
        logger.info(f"Added {wallpaper_path} to favorites")
    
    def add_selected_to_favorites(self):
        """Add the selected file from the file browser to favorites"""
        selected_indexes = self.file_view.selectedIndexes()
        if not selected_indexes:
            if self.parent_window:
                self.parent_window.statusBar().showMessage("No file selected", 3000)
            return
        
        # Get the file path from the first selected index (column 0)
        for index in selected_indexes:
            if index.column() == 0:  # Name column
                file_path = self.file_model.filePath(index)
                if os.path.isfile(file_path) and self.is_image_file(file_path):
                    self.add_to_favorites(file_path)
                break
    
    def remove_from_favorites(self):
        """Remove the selected wallpaper from favorites"""
        selected_items = self.favorites_list.selectedItems()
        if not selected_items:
            if self.parent_window:
                self.parent_window.statusBar().showMessage("No favorite selected", 3000)
            return
        
        # Get the wallpaper path
        wallpaper_path = selected_items[0].data(Qt.UserRole)
        
        # Remove from favorites list
        if wallpaper_path in self.favorites:
            self.favorites.remove(wallpaper_path)
        
        # Remove from UI list
        self.favorites_list.takeItem(self.favorites_list.row(selected_items[0]))
        
        # Save favorites
        self.save_favorites()
        
        if self.parent_window:
            self.parent_window.statusBar().showMessage(f"Removed {os.path.basename(wallpaper_path)} from favorites", 3000)
        logger.info(f"Removed {wallpaper_path} from favorites")
    
    def on_favorite_double_clicked(self, item):
        """Handle double-click on a favorite in the list"""
        wallpaper_path = item.data(Qt.UserRole)
        self.set_wallpaper(wallpaper_path)
    
    def set_as_wallpaper(self):
        """Set the selected favorite as the current wallpaper"""
        selected_items = self.favorites_list.selectedItems()
        if not selected_items:
            if self.parent_window:
                self.parent_window.statusBar().showMessage("No favorite selected", 3000)
            return
        
        wallpaper_path = selected_items[0].data(Qt.UserRole)
        self.set_wallpaper(wallpaper_path)
    
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
    
    def load_use_favorites_setting(self):
        """Load the use_favorites_only setting from config"""
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            
            use_favorites_only = False
            if 'General' in config and 'use_favorites_only' in config['General']:
                use_favorites_only = config.getboolean('General', 'use_favorites_only')
            
            self.use_favorites_only_checkbox.setChecked(use_favorites_only)
            logger.info(f"Loaded use_favorites_only setting: {use_favorites_only}")
        except Exception as e:
            logger.error(f"Error loading use_favorites_only setting: {e}")
    
    def toggle_use_favorites_only(self, state):
        """Toggle the use_favorites_only setting"""
        try:
            use_favorites_only = bool(state)
            
            # Update config
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            
            if not config.has_section('General'):
                config.add_section('General')
            
            config.set('General', 'use_favorites_only', str(use_favorites_only).lower())
            
            with open(CONFIG_FILE, 'w') as f:
                config.write(f)
            
            logger.info(f"Updated use_favorites_only setting to {use_favorites_only}")
            
            # Restart slideshow to apply changes
            if os.path.exists(RESTART_SCRIPT):
                subprocess.Popen(
                    ["bash", RESTART_SCRIPT],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                if self.parent_window:
                    if use_favorites_only:
                        self.parent_window.statusBar().showMessage("Slideshow will now use only favorite wallpapers", 3000)
                    else:
                        self.parent_window.statusBar().showMessage("Slideshow will now use all wallpapers", 3000)
        except Exception as e:
            logger.error(f"Error updating use_favorites_only setting: {e}")
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"Error updating slideshow settings: {str(e)}", 3000)
    
    def initialize_file_browser(self):
        """Initialize the file browser with the default directory"""
        self.navigate_to_directory(self.current_directory)
    
    def navigate_to_directory(self, directory):
        """Navigate to a specific directory in the file browser"""
        if not os.path.exists(directory) or not os.path.isdir(directory):
            logger.warning(f"Directory does not exist: {directory}")
            directory = os.path.expanduser("~/Pictures")
            if not os.path.exists(directory):
                directory = os.path.expanduser("~")
        
        # Update current directory
        self.current_directory = directory
        
        # Update file view
        index = self.file_model.setRootPath(directory)
        self.file_view.setRootIndex(index)
        
        # Update path display
        self.path_display.setText(directory)
        
        # Add to navigation history if this is a new navigation
        if self.navigation_position == len(self.navigation_history) - 1:
            # Remove any forward history
            if self.navigation_position < len(self.navigation_history) - 1:
                self.navigation_history = self.navigation_history[:self.navigation_position + 1]
            
            # Add current directory to history
            self.navigation_history.append(directory)
            self.navigation_position = len(self.navigation_history) - 1
        
        # Update navigation buttons
        self.update_navigation_buttons()
    
    def navigate_back(self):
        """Navigate to the previous directory in history"""
        if self.navigation_position > 0:
            self.navigation_position -= 1
            directory = self.navigation_history[self.navigation_position]
            
            # Update without adding to history
            self.current_directory = directory
            index = self.file_model.setRootPath(directory)
            self.file_view.setRootIndex(index)
            self.path_display.setText(directory)
            
            # Update navigation buttons
            self.update_navigation_buttons()
    
    def navigate_forward(self):
        """Navigate to the next directory in history"""
        if self.navigation_position < len(self.navigation_history) - 1:
            self.navigation_position += 1
            directory = self.navigation_history[self.navigation_position]
            
            # Update without adding to history
            self.current_directory = directory
            index = self.file_model.setRootPath(directory)
            self.file_view.setRootIndex(index)
            self.path_display.setText(directory)
            
            # Update navigation buttons
            self.update_navigation_buttons()
    
    def navigate_up(self):
        """Navigate to the parent directory"""
        parent_dir = os.path.dirname(self.current_directory)
        if parent_dir and parent_dir != self.current_directory:
            self.navigate_to_directory(parent_dir)
    
    def navigate_home(self):
        """Navigate to the home directory (default image directory)"""
        self.navigate_to_directory(DEFAULT_IMAGE_DIR)
    
    def update_navigation_buttons(self):
        """Update the state of navigation buttons"""
        self.back_button.setEnabled(self.navigation_position > 0)
        self.forward_button.setEnabled(self.navigation_position < len(self.navigation_history) - 1)
    
    def on_file_clicked(self, index):
        """Handle file selection in the file browser"""
        file_path = self.file_model.filePath(index)
        
        if os.path.isfile(file_path) and self.is_image_file(file_path):
            # Load the image preview
            self.load_image_preview(file_path)
    
    def on_file_double_clicked(self, index):
        """Handle double-click on file or directory in the file browser"""
        file_path = self.file_model.filePath(index)
        
        if os.path.isdir(file_path):
            # Navigate to the directory
            self.navigate_to_directory(file_path)
        elif os.path.isfile(file_path) and self.is_image_file(file_path):
            # Add to favorites
            self.add_to_favorites(file_path)
    
    def is_image_file(self, file_path):
        """Check if a file is an image based on its extension"""
        _, ext = os.path.splitext(file_path.lower())
        return ext in SUPPORTED_EXTENSIONS
    
    def load_image_preview(self, image_path):
        """Load an image preview into the preview label"""
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(pixmap)
            else:
                self.preview_label.setText("Preview not available")
        else:
            self.preview_label.setText("Image file not found")

class SettingsTab(QWidget):
    """Tab for configuring slideshow settings"""
    
    # Signal to notify when settings are changed
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # Load current settings
        self.config = configparser.ConfigParser()
        self.load_settings()
        
        # Set up UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI elements"""
        main_layout = QVBoxLayout(self)
        
        # General settings group
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout()
        
        # Image directory
        self.image_dir_edit = QLineEdit()
        self.image_dir_edit.setText(self.config.get('General', 'image_directory', fallback=''))
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_image_directory)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.image_dir_edit)
        dir_layout.addWidget(browse_button)
        general_layout.addRow("Image Directory:", dir_layout)
        
        # Interval
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(5, 86400)  # 5 seconds to 24 hours
        self.interval_spinbox.setValue(int(self.config.get('General', 'interval', fallback='300')))
        self.interval_spinbox.setSuffix(" seconds")
        general_layout.addRow("Change Interval:", self.interval_spinbox)
        
        # Shuffle
        self.shuffle_checkbox = QCheckBox()
        self.shuffle_checkbox.setChecked(self.config.getboolean('General', 'shuffle', fallback=False))
        general_layout.addRow("Shuffle Images:", self.shuffle_checkbox)
        
        general_group.setLayout(general_layout)
        main_layout.addWidget(general_group)
        
        # Advanced settings group
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout()
        
        # Supported extensions
        self.extensions_edit = QLineEdit()
        self.extensions_edit.setText(self.config.get('Advanced', 'supported_extensions', fallback='.jpg, .jpeg, .png, .bmp, .gif, .webp'))
        advanced_layout.addRow("Supported Extensions:", self.extensions_edit)
        
        # PID file
        self.pid_file_edit = QLineEdit()
        self.pid_file_edit.setText(self.config.get('Advanced', 'pid_file', fallback='~/.config/custom_wallpaper_slideshow.pid'))
        advanced_layout.addRow("PID File:", self.pid_file_edit)
        
        # Log file
        self.log_file_edit = QLineEdit()
        self.log_file_edit.setText(self.config.get('Advanced', 'log_file', fallback='~/.custom_wallpaper.log'))
        advanced_layout.addRow("Log File:", self.log_file_edit)
        
        advanced_group.setLayout(advanced_layout)
        main_layout.addWidget(advanced_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        # Apply button
        self.apply_button = QPushButton("Apply Settings")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)
        
        # Reset button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_button)
        
        main_layout.addLayout(button_layout)
        
        # Add stretch to push everything to the top
        main_layout.addStretch(1)
    
    def load_settings(self):
        """Load settings from config.ini"""
        try:
            self.config.read(CONFIG_FILE)
            
            # Ensure required sections exist
            if not self.config.has_section('General'):
                self.config.add_section('General')
            if not self.config.has_section('Advanced'):
                self.config.add_section('Advanced')
                
            logger.info("Settings loaded from config.ini")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            
            # Create default config
            self.reset_to_defaults(silent=True)
    
    def save_settings(self):
        """Save settings to config.ini"""
        try:
            # Update config object with values from UI
            self.update_config_from_ui()
            
            # Write to file
            with open(CONFIG_FILE, 'w') as f:
                self.config.write(f)
            
            if self.parent_window:
                self.parent_window.statusBar().showMessage("Settings saved successfully", 3000)
            logger.info("Settings saved to config.ini")
            
            # Emit signal that settings have changed
            self.settings_changed.emit()
        except Exception as e:
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"Error saving settings: {str(e)}", 3000)
            logger.error(f"Error saving settings: {e}")
    
    def apply_settings(self):
        """Apply settings by restarting the slideshow"""
        try:
            # Disable the apply button while restarting
            self.apply_button.setEnabled(False)
            
            # Save settings first
            self.save_settings()
            
            if self.parent_window:
                self.parent_window.statusBar().showMessage("Restarting slideshow...", 3000)
            
            # Use subprocess.Popen to run the restart script in the background
            # This won't block the UI thread
            subprocess.Popen([RESTART_SCRIPT],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
            
            # Re-enable the apply button after a short delay
            QTimer.singleShot(500, self.enable_apply_button)
            
        except Exception as e:
            if self.parent_window:
                self.parent_window.statusBar().showMessage(f"Error applying settings: {str(e)}", 3000)
            logger.error(f"Error applying settings: {e}")
            self.apply_button.setEnabled(True)
    
    def enable_apply_button(self):
        """Re-enable the apply button"""
        self.apply_button.setEnabled(True)
        if self.parent_window:
            self.parent_window.statusBar().showMessage("Settings applied. Slideshow restarting...", 3000)
    
    def update_config_from_ui(self):
        """Update config object with values from UI"""
        # General section
        self.config.set('General', 'image_directory', self.image_dir_edit.text())
        self.config.set('General', 'interval', str(self.interval_spinbox.value()))
        self.config.set('General', 'shuffle', str(self.shuffle_checkbox.isChecked()).lower())
        
        # Advanced section
        self.config.set('Advanced', 'supported_extensions', self.extensions_edit.text())
        self.config.set('Advanced', 'pid_file', self.pid_file_edit.text())
        self.config.set('Advanced', 'log_file', self.log_file_edit.text())
    
    def reset_to_defaults(self, silent=False):
        """Reset settings to defaults"""
        if not silent:
            if QMessageBox.question(
                self, "Confirm Reset", 
                "Are you sure you want to reset all settings to defaults?",
                QMessageBox.Yes | QMessageBox.No
            ) != QMessageBox.Yes:
                return
        
        # Create default config
        self.config = configparser.ConfigParser()
        self.config.add_section('General')
        self.config.set('General', 'image_directory', os.path.expanduser('~/Pictures/Wallpapers'))
        self.config.set('General', 'interval', '300')
        self.config.set('General', 'shuffle', 'false')
        
        self.config.add_section('Advanced')
        self.config.set('Advanced', 'supported_extensions', '.jpg, .jpeg, .png, .bmp, .gif, .webp')
        self.config.set('Advanced', 'pid_file', '~/.config/custom_wallpaper_slideshow.pid')
        self.config.set('Advanced', 'log_file', '~/.custom_wallpaper.log')
        
        # Update UI
        self.image_dir_edit.setText(self.config.get('General', 'image_directory'))
        self.interval_spinbox.setValue(int(self.config.get('General', 'interval')))
        self.shuffle_checkbox.setChecked(self.config.getboolean('General', 'shuffle'))
        self.extensions_edit.setText(self.config.get('Advanced', 'supported_extensions'))
        self.pid_file_edit.setText(self.config.get('Advanced', 'pid_file'))
        self.log_file_edit.setText(self.config.get('Advanced', 'log_file'))
        
        if not silent:
            if self.parent_window:
                self.parent_window.statusBar().showMessage("Settings reset to defaults", 3000)
            logger.info("Settings reset to defaults")
    
    def browse_image_directory(self):
        """Open file dialog to browse for image directory"""
        current_dir = os.path.expanduser(self.image_dir_edit.text()) if self.image_dir_edit.text() else os.path.expanduser('~')
        
        directory = QFileDialog.getExistingDirectory(
            self, "Select Image Directory", current_dir, QFileDialog.ShowDirsOnly
        )
        
        if directory:
            self.image_dir_edit.setText(directory)
    
# Define the path to the restart script
RESTART_SCRIPT = os.path.join(SCRIPT_DIR, "restart_slideshow.sh")

# Define the path to the wallpaper_favorites.py script
FAVORITES_SCRIPT = os.path.join(SCRIPT_DIR, "wallpaper_favorites.py")
class WallpaperMainWindow(QMainWindow):
    """Main window with tabs for history, notes, favorites, and settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wallpaper Slideshow Manager")
        self.resize(1100, 800)  # Increased size to accommodate file browser
        
        # Create central widget and tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.history_tab = HistoryTab(self)
        self.notes_tab = NotesTab(self)
        self.favorites_tab = FavoritesTab(self)
        self.settings_tab = SettingsTab(self)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.history_tab, "History")
        self.tab_widget.addTab(self.notes_tab, "Image Notes")
        self.tab_widget.addTab(self.favorites_tab, "Favorites")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Connect signals
        self.settings_tab.settings_changed.connect(self.on_settings_changed)
        
        # Create status bar
        self.statusBar().showMessage("Ready", 3000)
        
        logger.info("Main window initialized")
    
    def on_settings_changed(self):
        """Handle settings changed signal"""
        # Refresh tabs if needed
        self.history_tab.load_history()
        self.notes_tab.refresh_current_wallpaper()
    
    def check_wallpaper_changed(self, wallpaper_path):
        """Check if the wallpaper has changed and update tabs"""
        if wallpaper_path and os.path.exists(wallpaper_path):
            # Add to history
            self.history_tab.add_to_history(wallpaper_path)
            
            # Update notes tab if it's visible
            if self.tab_widget.currentWidget() == self.notes_tab:
                self.notes_tab.refresh_current_wallpaper()


def main():
    """Main function to run the application standalone"""
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = WallpaperMainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())