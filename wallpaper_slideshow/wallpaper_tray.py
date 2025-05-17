#!/usr/bin/env python3
"""
Wallpaper Slideshow System Tray Application

This script provides a system tray icon for controlling the wallpaper slideshow
and allows accessing a tabbed main window with history, notes, and settings.

Features:
- System tray icon with right-click menu for controlling slideshow
- Left-click to open the main window with tabs for history, notes, and settings
- Options to navigate forward/backward, open color control panel, etc.
- Automatic startup with KDE
- File browser integration for selecting wallpapers
- Dolphin integration for right-click context menu

Usage:
    ./wallpaper_tray.py
"""

import os
import sys
import json
import time
import signal
import subprocess
import threading
import configparser
import importlib.util
from pathlib import Path
import logging
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction,
                            QMainWindow, QTextEdit, QVBoxLayout, QWidget,
                            QPushButton, QHBoxLayout, QLabel, QListWidget,
                            QListWidgetItem, QSplitter, QFileDialog, QMessageBox,
                            QTreeView, QHeaderView, QToolBar, QComboBox, QLineEdit,
                            QTabWidget, QFormLayout, QGroupBox, QCheckBox, QSpinBox,
                            QDialogButtonBox, QFileSystemModel)

# Import the FavoritesTab class
try:
    from favorites_tab import FavoritesTab
except ImportError:
    # Try with full path
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from favorites_tab import FavoritesTab
from PyQt5.QtGui import QIcon, QPixmap, QImageReader
from PyQt5.QtCore import Qt, QTimer, QSize, QDir, QModelIndex, pyqtSignal, QObject

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.expanduser('~/.wallpaper_tray.log')
)
logger = logging.getLogger(__name__)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_DIR = os.path.expanduser("~/.wallpaper_notes")
FAVORITES_DIR = os.path.expanduser("~/.wallpaper_favorites")
FAVORITES_FILE = os.path.join(FAVORITES_DIR, "favorites.json")
CONTROL_SCRIPT = os.path.join(SCRIPT_DIR, "control_slideshow.sh")
COLOR_CONTROL_PANEL = os.path.join(os.path.dirname(SCRIPT_DIR), "wallpaper_color_manager_new/color_control_panel.py")
GET_CURRENT_WALLPAPER = os.path.join(os.path.dirname(SCRIPT_DIR), "get_current_wallpaper.py")
TRACK_CURRENT_WALLPAPER = os.path.join(SCRIPT_DIR, "track_current_wallpaper.py")
CURRENT_WALLPAPER_FILE = os.path.expanduser("~/.current_wallpaper")
PID_FILE = os.path.expanduser("~/.config/custom_wallpaper_slideshow.pid")
ICON_PATH = os.path.join(SCRIPT_DIR, "wallpaper_tray_icon.png")
DEFAULT_ICON = "preferences-desktop-wallpaper"
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.ini")
SET_WALLPAPER_SCRIPT = os.path.join(SCRIPT_DIR, "set_specific_wallpaper.py")
CUSTOM_WALLPAPER_SCRIPT = os.path.join(SCRIPT_DIR, "custom_wallpaper.py")
RESTART_SCRIPT = os.path.join(SCRIPT_DIR, "restart_slideshow.sh")
ADD_TO_FAVORITES_SCRIPT = os.path.join(SCRIPT_DIR, "kde_shortcuts/add_to_favorites.sh")

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
        # Check if we're in the main thread
        if threading.current_thread() is not threading.main_thread():
            logger.warning("refresh_current_wallpaper called from non-main thread!")
            # Use QTimer to call this method from the main thread
            QTimer.singleShot(0, self.refresh_current_wallpaper)
            return
            
        logger.info("Starting refresh_current_wallpaper in WallpaperNotesWindow (main thread)")
        try:
            # First try to get the current wallpaper from the tracking file
            wallpaper_path = None
            
            if os.path.exists(CURRENT_WALLPAPER_FILE):
                try:
                    with open(CURRENT_WALLPAPER_FILE, 'r') as f:
                        wallpaper_path = f.read().strip()
                    
                    if wallpaper_path and os.path.exists(wallpaper_path):
                        logger.info(f"Got current wallpaper from tracking file: {wallpaper_path}")
                    else:
                        logger.warning(f"Invalid wallpaper path in tracking file: {wallpaper_path}")
                        wallpaper_path = None
                except Exception as e:
                    logger.error(f"Error reading current wallpaper file: {e}")
                    wallpaper_path = None
            
            # If tracking file didn't work, try the tracking module
            if not wallpaper_path:
                try:
                    if os.path.exists(TRACK_CURRENT_WALLPAPER):
                        # Import the module dynamically
                        spec = importlib.util.spec_from_file_location("track_current_wallpaper", TRACK_CURRENT_WALLPAPER)
                        tracker = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(tracker)
                        
                        # Get the current wallpaper
                        wallpaper_path = tracker.get_current_wallpaper()
                        if wallpaper_path:
                            logger.info(f"Got current wallpaper from tracking module: {wallpaper_path}")
                except Exception as e:
                    logger.error(f"Error using tracking module: {e}")
                    wallpaper_path = None
            
            # If tracking system didn't work, fall back to the old method
            if not wallpaper_path:
                logger.debug("Tracking system failed, falling back to get_current_wallpaper.py")
                try:
                    result = subprocess.run(
                        ["python3", GET_CURRENT_WALLPAPER, "--name-only"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
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
                    
                    # Find the full path to the wallpaper
                    logger.debug(f"Finding full path for wallpaper: {wallpaper_name}")
                    wallpaper_path = self.find_wallpaper_path(wallpaper_name)
                    
                    if not wallpaper_path:
                        logger.warning(f"Could not find full path for wallpaper: {wallpaper_name}")
                        if self.parent_window:
                            self.parent_window.statusBar().showMessage(f"Could not find wallpaper: {wallpaper_name}", 3000)
                        return
                except Exception as e:
                    logger.error(f"Exception running get_current_wallpaper.py: {e}")
                    if self.parent_window:
                        self.parent_window.statusBar().showMessage("Error getting current wallpaper", 3000)
                    return
            
            logger.info(f"Current wallpaper: {wallpaper_path}")
            
            # Load notes for this wallpaper
            if wallpaper_path in self.notes_data:
                # Select the item in the list
                for i in range(self.wallpaper_list.count()):
                    item = self.wallpaper_list.item(i)
                    if item and item.data(Qt.UserRole) == wallpaper_path:
                        self.wallpaper_list.setCurrentItem(item)
                        logger.info("Selected existing wallpaper in list")
                        break
            else:
                # Create a new entry
                self.current_wallpaper = wallpaper_path
                self.wallpaper_label.setText(f"Wallpaper: {os.path.basename(wallpaper_path)}")
                self.notes_edit.clear()
                logger.info("Created new entry for wallpaper")
                
                # Load preview
                try:
                    if os.path.exists(wallpaper_path):
                        pixmap = QPixmap(wallpaper_path)
                        if not pixmap.isNull():
                            pixmap = pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            self.preview_label.setPixmap(pixmap)
                            logger.info("Loaded preview image successfully")
                        else:
                            self.preview_label.setText("Preview not available (null pixmap)")
                            logger.warning("Failed to load preview - null pixmap")
                    else:
                        self.preview_label.setText("Image file not found")
                        logger.warning(f"Image file not found: {wallpaper_path}")
                except Exception as e:
                    self.preview_label.setText("Error loading preview")
                    logger.error(f"Error loading preview: {e}")
            
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
        config_path = os.path.join(SCRIPT_DIR, "config.ini")
        if os.path.exists(config_path):
            try:
                import configparser
                config = configparser.ConfigParser()
                config.read(config_path)
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
            set_wallpaper_script = os.path.join(SCRIPT_DIR, "set_specific_wallpaper.py")
            subprocess.run(
                ["python3", set_wallpaper_script, wallpaper_path],
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
class WallpaperMainWindow(QMainWindow):
    """Main window with tabs for history, notes, and settings"""
    
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
        self.settings_tab = SettingsTab(self)
        self.favorites_tab = FavoritesTab(self)
        
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

class WallpaperTrayApp:
    """System tray application for controlling wallpaper slideshow"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running when windows are closed
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon()
        self.setup_icon()
        
        # Create menu
        self.menu = QMenu()
        self.setup_menu()
        
        # Set menu for tray icon
        self.tray_icon.setContextMenu(self.menu)
        
        # Connect signals
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # Create main window (but don't show it yet)
        self.main_window = WallpaperMainWindow()
        
        # Show tray icon
        self.tray_icon.show()
        
        # Set up timer to check for wallpaper changes - use a longer interval to reduce CPU usage
        self.current_wallpaper = None
        self.wallpaper_check_timer = QTimer()
        self.wallpaper_check_timer.timeout.connect(self.check_wallpaper_changed)
        self.wallpaper_check_timer.start(10000)  # Check every 10 seconds instead of 5
        
        # Use a separate timer for slideshow status to reduce lag
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_slideshow_status)
        self.status_timer.start(30000)  # Check every 30 seconds
        
        # Initial check if slideshow is running and start it if not
        QTimer.singleShot(1000, self.check_and_start_slideshow)
        
        # Variable to store image path from signal handler
        self.signal_image_path = None
        
        # Set up signal handler for SIGUSR1 (used by open_notes_for_wallpaper.py)
        signal.signal(signal.SIGUSR1, self.handle_sigusr1)
        
        # Create notes directory if it doesn't exist
        os.makedirs(NOTES_DIR, exist_ok=True)
        
        logger.info("Wallpaper tray application started")
    
    def check_and_start_slideshow(self):
        """Check if slideshow is running and start it if not"""
        if not os.path.exists(PID_FILE):
            logger.info("Slideshow not running on startup, starting it automatically")
            try:
                # Start the slideshow
                custom_wallpaper_script = os.path.join(SCRIPT_DIR, "custom_wallpaper.py")
                subprocess.Popen(["python3", custom_wallpaper_script])
                
                # Wait a moment for the slideshow to start
                time.sleep(1)
                
                # Update status
                self.check_slideshow_status()
                
                # Show notification
                self.tray_icon.showMessage("Slideshow", "Wallpaper slideshow started automatically")
            except Exception as e:
                logger.error(f"Error starting slideshow on startup: {e}")
                self.tray_icon.showMessage("Error", f"Failed to start slideshow: {str(e)}")
        else:
            # Just check status if already running
            self.check_slideshow_status()
    
    def setup_icon(self):
        """Set up the system tray icon"""
        if os.path.exists(ICON_PATH):
            self.tray_icon.setIcon(QIcon(ICON_PATH))
        else:
            # Use default icon from system theme
            self.tray_icon.setIcon(QIcon.fromTheme(DEFAULT_ICON))
    
    def setup_menu(self):
        """Set up the context menu for the tray icon"""
        # Add actions to menu
        
        # Main window action
        main_window_action = QAction("Open Wallpaper Manager", self.menu)
        main_window_action.triggered.connect(self.show_main_window)
        self.menu.addAction(main_window_action)
        
        self.menu.addSeparator()
        
        # Next wallpaper action
        next_action = QAction("Next Wallpaper", self.menu)
        next_action.triggered.connect(self.next_wallpaper)
        self.menu.addAction(next_action)
        
        # Previous wallpaper action
        prev_action = QAction("Previous Wallpaper", self.menu)
        prev_action.triggered.connect(self.prev_wallpaper)
        self.menu.addAction(prev_action)
        
        # Pause/Resume action
        self.pause_action = QAction("Pause Slideshow", self.menu)
        self.pause_action.triggered.connect(self.toggle_pause)
        self.menu.addAction(self.pause_action)
        
        self.menu.addSeparator()
        
        # Favorite current wallpaper action
        favorite_action = QAction("Favorite Current Wallpaper", self.menu)
        favorite_action.triggered.connect(self.favorite_current_wallpaper)
        self.menu.addAction(favorite_action)
        
        # View favorites action
        view_favorites_action = QAction("View Favorites", self.menu)
        view_favorites_action.triggered.connect(self.view_favorites)
        self.menu.addAction(view_favorites_action)
        
        # Color control panel action
        color_action = QAction("Color Control Panel", self.menu)
        color_action.triggered.connect(self.open_color_control_panel)
        self.menu.addAction(color_action)
        
        self.menu.addSeparator()
        
        # Restart action
        restart_action = QAction("Restart Slideshow", self.menu)
        restart_action.triggered.connect(self.restart_slideshow)
        self.menu.addAction(restart_action)
        
        # Quit action
        quit_action = QAction("Quit", self.menu)
        quit_action.triggered.connect(self.quit_app)
        self.menu.addAction(quit_action)
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger:  # Left click
            # Use a small delay to improve responsiveness
            QTimer.singleShot(100, self.show_main_window)
    
    def show_main_window(self):
        """Show the main window"""
        # Show the window first, then refresh in the background
        self.main_window.show()
        # Ensure window is not minimized and is active
        self.main_window.setWindowState(self.main_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.main_window.raise_()
        self.main_window.activateWindow()
        
        # Force processing of events to ensure window activation
        self.app.processEvents()
        
        # Refresh in a separate thread to avoid blocking the UI
        threading.Thread(target=self._refresh_window_thread, daemon=True).start()
    
    def _refresh_window_thread(self):
        """Background thread for refreshing the main window"""
        try:
            # Small delay to ensure window is visible first
            time.sleep(0.1)
            
            # Use QTimer to call UI methods from the main thread
            QTimer.singleShot(0, self._refresh_window_in_main_thread)
        except Exception as e:
            logger.error(f"Error in refresh window thread: {e}")
            
    def _refresh_window_in_main_thread(self):
        """Refresh the window in the main thread"""
        try:
            # Refresh the current wallpaper in the notes tab
            self.main_window.notes_tab.refresh_current_wallpaper()
            # Refresh the history tab
            self.main_window.history_tab.load_history()
            # Refresh the favorites tab
            self.main_window.favorites_tab.load_favorites()
        except Exception as e:
            logger.error(f"Error refreshing main window: {e}")
    
    def next_wallpaper(self):
        """Show the next wallpaper"""
        try:
            subprocess.run([CONTROL_SCRIPT, "next"], check=True)
            logger.info("Showing next wallpaper")
            
            # Wait a moment for the wallpaper to change
            QTimer.singleShot(500, self.check_wallpaper_changed)
        except Exception as e:
            logger.error(f"Error showing next wallpaper: {e}")
            self.tray_icon.showMessage("Error", f"Failed to show next wallpaper: {str(e)}")
    
    def prev_wallpaper(self):
        """Show the previous wallpaper"""
        try:
            subprocess.run([CONTROL_SCRIPT, "prev"], check=True)
            logger.info("Showing previous wallpaper")
            
            # Wait a moment for the wallpaper to change
            QTimer.singleShot(500, self.check_wallpaper_changed)
        except Exception as e:
            logger.error(f"Error showing previous wallpaper: {e}")
            self.tray_icon.showMessage("Error", f"Failed to show previous wallpaper: {str(e)}")
    
    def toggle_pause(self):
        """Toggle pause/resume slideshow"""
        try:
            subprocess.run([CONTROL_SCRIPT, "pause"], check=True)
            logger.info("Toggling pause/resume")
            
            # Update pause action text
            self.check_slideshow_status()
        except Exception as e:
            logger.error(f"Error toggling pause/resume: {e}")
            self.tray_icon.showMessage("Error", f"Failed to toggle pause/resume: {str(e)}")
    
    def favorite_current_wallpaper(self):
        """Add the current wallpaper to favorites"""
        try:
            # Use the add_to_favorites script
            if os.path.exists(ADD_TO_FAVORITES_SCRIPT):
                subprocess.run([ADD_TO_FAVORITES_SCRIPT], check=True)
                logger.info("Added current wallpaper to favorites using script")
                
                # Refresh favorites tab if main window is open
                if hasattr(self, 'main_window') and self.main_window.isVisible():
                    self.main_window.favorites_tab.load_favorites()
                
                return
            
            # Fallback to manual method if script doesn't exist
            # Create favorites directory if it doesn't exist
            os.makedirs(FAVORITES_DIR, exist_ok=True)
            
            # Get current wallpaper
            wallpaper_path = self.get_current_wallpaper_path()
            
            if not wallpaper_path:
                logger.error("Could not determine current wallpaper")
                self.tray_icon.showMessage("Error", "Could not determine current wallpaper")
                return
            
            # Check if favorites file exists, create if not
            if not os.path.exists(FAVORITES_FILE):
                with open(FAVORITES_FILE, 'w') as f:
                    json.dump({"favorites": []}, f, indent=2)
                logger.info(f"Created new favorites file at {FAVORITES_FILE}")
            
            # Load favorites
            try:
                with open(FAVORITES_FILE, 'r') as f:
                    data = json.load(f)
                    favorites = data.get("favorites", [])
                
                # Check if already in favorites
                if wallpaper_path in favorites:
                    logger.info(f"Wallpaper {wallpaper_path} is already in favorites")
                    self.tray_icon.showMessage("Wallpaper Favorites", f"{os.path.basename(wallpaper_path)} is already in favorites")
                    return
                
                # Add to favorites
                favorites.append(wallpaper_path)
                
                # Save favorites
                with open(FAVORITES_FILE, 'w') as f:
                    json.dump({"favorites": favorites}, f, indent=2)
                
                logger.info(f"Added {wallpaper_path} to favorites")
                self.tray_icon.showMessage("Wallpaper Favorites", f"Added {os.path.basename(wallpaper_path)} to favorites")
                
                # Refresh favorites tab if main window is open
                if hasattr(self, 'main_window') and self.main_window.isVisible():
                    self.main_window.favorites_tab.load_favorites()
                
            except Exception as e:
                logger.error(f"Error adding to favorites: {e}")
                self.tray_icon.showMessage("Error", f"Failed to add to favorites: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in favorite_current_wallpaper: {e}")
            self.tray_icon.showMessage("Error", f"Failed to add current wallpaper to favorites: {str(e)}")
    
    def view_favorites(self):
        """Show the favorites tab in the main window"""
        try:
            # Show the main window
            self.main_window.show()
            self.main_window.setWindowState(self.main_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
            self.main_window.raise_()
            self.main_window.activateWindow()
            
            # Force processing of events to ensure window activation
            self.app.processEvents()
            
            # Select the favorites tab
            for i in range(self.main_window.tab_widget.count()):
                if self.main_window.tab_widget.tabText(i) == "Favorites":
                    self.main_window.tab_widget.setCurrentIndex(i)
                    break
            
            # Refresh the favorites tab
            self.main_window.favorites_tab.load_favorites()
            
            logger.info("Opened favorites tab")
        except Exception as e:
            logger.error(f"Error opening favorites tab: {e}")
            self.tray_icon.showMessage("Error", f"Failed to open favorites tab: {str(e)}")
    
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
        
        # If tracking file didn't work, try the tracking module
        try:
            if os.path.exists(TRACK_CURRENT_WALLPAPER):
                # Import the module dynamically
                spec = importlib.util.spec_from_file_location("track_current_wallpaper", TRACK_CURRENT_WALLPAPER)
                tracker = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(tracker)
                
                # Get the current wallpaper
                wallpaper_path = tracker.get_current_wallpaper()
                if wallpaper_path:
                    logger.debug(f"Got current wallpaper from tracking module: {wallpaper_path}")
                    return wallpaper_path
        except Exception as e:
            logger.error(f"Error using tracking module: {e}")
        
        # If tracking system didn't work, fall back to the old method
        try:
            result = subprocess.run(
                ["python3", GET_CURRENT_WALLPAPER, "--verbose"],
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
    
    def open_color_control_panel(self):
        """Open the color control panel"""
        try:
            subprocess.Popen(["python3", COLOR_CONTROL_PANEL])
            logger.info("Opening color control panel")
        except Exception as e:
            logger.error(f"Error opening color control panel: {e}")
            self.tray_icon.showMessage("Error", f"Failed to open color control panel: {str(e)}")
    
    def restart_slideshow(self):
        """Restart the slideshow"""
        try:
            # Check if the slideshow is running by checking for PID file
            if os.path.exists(PID_FILE):
                try:
                    # Try to stop the slideshow
                    subprocess.run([CONTROL_SCRIPT, "stop"], check=True)
                    logger.info("Stopping slideshow")
                    
                    # Wait a moment for the slideshow to stop
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"Error stopping slideshow: {e}")
                    # If stopping fails, try to remove the PID file
                    try:
                        os.remove(PID_FILE)
                        logger.info("Removed stale PID file")
                    except Exception as pid_e:
                        logger.error(f"Error removing PID file: {pid_e}")
            else:
                logger.info("Slideshow not running, starting fresh")
            
            # Start the slideshow
            custom_wallpaper_script = os.path.join(SCRIPT_DIR, "custom_wallpaper.py")
            subprocess.Popen(["python3", custom_wallpaper_script])
            logger.info("Starting slideshow")
            
            # Wait a moment for the slideshow to start
            time.sleep(1)
            
            # Update status
            self.check_slideshow_status()
            
            # Show success message
            self.tray_icon.showMessage("Slideshow", "Slideshow restarted successfully")
        except Exception as e:
            logger.error(f"Error restarting slideshow: {e}")
            self.tray_icon.showMessage("Error", f"Failed to restart slideshow: {str(e)}")
    
    def quit_app(self):
        """Quit the application"""
        # Don't stop the slideshow when quitting the app
        logger.info("Quitting application")
        self.app.quit()
    
    def check_slideshow_status(self):
        """Check if the slideshow is running and if it's paused"""
        # Use a thread to avoid blocking the UI
        threading.Thread(target=self._check_slideshow_status_thread, daemon=True).start()
    
    def _check_slideshow_status_thread(self):
        """Background thread for checking slideshow status"""
        try:
            # Check if PID file exists
            if not os.path.exists(PID_FILE):
                logger.warning("PID file not found, slideshow may not be running")
                self.app.processEvents()  # Process any pending events
                self.tray_icon.setToolTip("Wallpaper Slideshow (Not Running)")
                return
            
            # Read PID from file
            with open(PID_FILE, 'r') as f:
                pid = f.read().strip()
            
            # Check if process is running
            try:
                os.kill(int(pid), 0)  # Signal 0 doesn't kill the process, just checks if it exists
                
                # Process is running, check if it's paused
                result = subprocess.run([CONTROL_SCRIPT, "status"], capture_output=True, text=True, check=True)
                
                # Update UI in the main thread
                if "paused" in result.stdout.lower():
                    self.app.processEvents()  # Process any pending events
                    self.pause_action.setText("Resume Slideshow")
                    self.tray_icon.setToolTip("Wallpaper Slideshow (Paused)")
                else:
                    self.app.processEvents()  # Process any pending events
                    self.pause_action.setText("Pause Slideshow")
                    self.tray_icon.setToolTip("Wallpaper Slideshow (Running)")
                
                logger.info(f"Slideshow status: {result.stdout.strip()}")
            except ProcessLookupError:
                logger.warning(f"Process with PID {pid} is not running")
                self.app.processEvents()  # Process any pending events
                self.tray_icon.setToolTip("Wallpaper Slideshow (Not Running)")
            except ValueError:
                logger.warning(f"Invalid PID: {pid}")
                self.app.processEvents()  # Process any pending events
                self.tray_icon.setToolTip("Wallpaper Slideshow (Unknown Status)")
        except Exception as e:
            logger.error(f"Error checking slideshow status: {e}")
            self.app.processEvents()  # Process any pending events
            self.tray_icon.setToolTip("Wallpaper Slideshow (Error)")
    
    def check_wallpaper_changed(self):
        """Check if the wallpaper has changed and update history"""
        # Use a thread to avoid blocking the UI
        threading.Thread(target=self._check_wallpaper_thread, daemon=True).start()
    
    def _check_wallpaper_thread(self):
        """Background thread for checking wallpaper changes"""
        try:
            logger.debug("Starting wallpaper change check in background thread")
            
            # First try to get the current wallpaper from the tracking file
            wallpaper_path = None
            
            if os.path.exists(CURRENT_WALLPAPER_FILE):
                try:
                    with open(CURRENT_WALLPAPER_FILE, 'r') as f:
                        wallpaper_path = f.read().strip()
                    
                    if wallpaper_path and os.path.exists(wallpaper_path):
                        logger.debug(f"Got current wallpaper from tracking file: {wallpaper_path}")
                    else:
                        logger.debug(f"Invalid wallpaper path in tracking file: {wallpaper_path}")
                        wallpaper_path = None
                except Exception as e:
                    logger.error(f"Error reading current wallpaper file: {e}")
                    wallpaper_path = None
            
            # If tracking file didn't work, try the tracking module
            if not wallpaper_path:
                try:
                    if os.path.exists(TRACK_CURRENT_WALLPAPER):
                        # Import the module dynamically
                        spec = importlib.util.spec_from_file_location("track_current_wallpaper", TRACK_CURRENT_WALLPAPER)
                        tracker = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(tracker)
                        
                        # Get the current wallpaper
                        wallpaper_path = tracker.get_current_wallpaper()
                        if wallpaper_path:
                            logger.debug(f"Got current wallpaper from tracking module: {wallpaper_path}")
                except Exception as e:
                    logger.error(f"Error using tracking module: {e}")
                    wallpaper_path = None
            
            # If tracking system didn't work, fall back to the old method
            if not wallpaper_path:
                logger.debug("Tracking system failed, falling back to get_current_wallpaper.py")
                try:
                    result = subprocess.run(
                        ["python3", GET_CURRENT_WALLPAPER, "--name-only", "--fast"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if result.returncode != 0:
                        logger.warning(f"get_current_wallpaper.py exited with code {result.returncode}: {result.stderr}")
                        return
                    
                    wallpaper_name = result.stdout.strip()
                    
                    if not wallpaper_name:
                        logger.debug("get_current_wallpaper.py returned empty output")
                        return
                    
                    # Find the full path to the wallpaper
                    wallpaper_path = self._find_wallpaper_path_cached(wallpaper_name)
                    
                    if not wallpaper_path:
                        logger.debug(f"Could not find full path for wallpaper: {wallpaper_name}")
                        return
                except Exception as e:
                    logger.error(f"Exception running get_current_wallpaper.py in background thread: {e}")
                    return
            
            # Store the wallpaper path for the main thread to use
            self.detected_wallpaper_path = wallpaper_path
            
            # Check if the wallpaper has changed
            if wallpaper_path != self.current_wallpaper:
                logger.info(f"Wallpaper changed to: {wallpaper_path}")
                self.current_wallpaper = wallpaper_path
                
                # Update the main window if it's visible - but do it in the main thread
                if self.main_window.isVisible():
                    # Use QTimer to update UI in the main thread
                    QTimer.singleShot(0, lambda: self._update_main_window_wallpaper(wallpaper_path))
            else:
                logger.debug("Wallpaper has not changed")
        except Exception as e:
            logger.error(f"Unexpected error checking wallpaper change: {e}")
            
    def _update_main_window_wallpaper(self, wallpaper_path):
        """Update the main window with the new wallpaper in the main thread"""
        try:
            self.main_window.check_wallpaper_changed(wallpaper_path)
        except Exception as e:
            logger.error(f"Error updating main window with new wallpaper: {e}")
    
    # Cache for wallpaper paths to avoid repeated filesystem operations
    _wallpaper_path_cache = {}
    
    def _find_wallpaper_path_cached(self, wallpaper_name):
        """Cached version of find_wallpaper_path to improve performance"""
        # Check cache first
        if wallpaper_name in self._wallpaper_path_cache:
            return self._wallpaper_path_cache[wallpaper_name]
        
        # Not in cache, use the notes tab's method
        wallpaper_path = self.main_window.notes_tab.find_wallpaper_path(wallpaper_name)
        
        # Cache the result
        if wallpaper_path:
            self._wallpaper_path_cache[wallpaper_name] = wallpaper_path
            
            # Limit cache size
            if len(self._wallpaper_path_cache) > 100:
                # Remove oldest entries
                keys = list(self._wallpaper_path_cache.keys())
                for key in keys[:50]:  # Remove half of the entries
                    del self._wallpaper_path_cache[key]
        
        return wallpaper_path
    
    def handle_sigusr1(self, signum, frame):
        """Handle SIGUSR1 signal (used to open notes for a specific image)"""
        logger.info("Received SIGUSR1 signal")
        
        # Since this is called from a signal handler (different thread context),
        # we need to be careful about thread safety
        
        # Check for temporary file with image path
        temp_file = os.path.join(NOTES_DIR, "open_image.tmp")
        if os.path.exists(temp_file):
            try:
                with open(temp_file, 'r') as f:
                    image_path = f.read().strip()
                
                logger.info(f"Read image path from temp file: {image_path}")
                
                # Don't remove the temp file immediately in case we need to retry
                
                if not image_path:
                    logger.error("Empty image path in temp file")
                    return
                
                if not os.path.exists(image_path):
                    logger.error(f"Image file does not exist: {image_path}")
                    return
                
                logger.info(f"Opening notes for image: {image_path}")
                
                # Store the path in a class variable
                self.signal_image_path = image_path
                
                # Use QTimer to safely call the method from the main thread
                # This is crucial for thread safety in Qt
                QTimer.singleShot(100, self._handle_sigusr1_in_main_thread)
                
            except Exception as e:
                logger.error(f"Error handling SIGUSR1 signal: {e}")
    
    def _handle_sigusr1_in_main_thread(self):
        """Handle the SIGUSR1 signal processing in the main thread"""
        try:
            # Get the image path from the class variable
            image_path = self.signal_image_path
            
            # Open notes for the wallpaper
            self.open_notes_for_wallpaper(image_path)
            
            # Only remove the temp file after successful processing
            temp_file = os.path.join(NOTES_DIR, "open_image.tmp")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.info("Removed temporary file after successful processing")
                except Exception as e:
                    logger.error(f"Error removing temporary file: {e}")
        except Exception as e:
            logger.error(f"Error in _handle_sigusr1_in_main_thread: {e}")
    def run(self):
        """Run the application"""
        return self.app.exec_()
    
    def open_notes_for_wallpaper(self, wallpaper_path):
        """Open notes for a specific wallpaper"""
        # This method must be called from the main thread
        if threading.current_thread() is not threading.main_thread():
            logger.error("open_notes_for_wallpaper called from non-main thread!")
            # Use QTimer to call this method from the main thread
            QTimer.singleShot(0, lambda: self.open_notes_for_wallpaper(wallpaper_path))
            return
            
        logger.info(f"Opening notes for wallpaper: {wallpaper_path}")
        
        # Validate the wallpaper path
        if not wallpaper_path:
            logger.error("Empty wallpaper path provided")
            return
            
        if not os.path.exists(wallpaper_path):
            logger.error(f"Wallpaper file does not exist: {wallpaper_path}")
            if self.main_window.isVisible():
                self.main_window.statusBar().showMessage(f"Error: Wallpaper file not found: {wallpaper_path}", 3000)
            return
            
        # Get absolute path to ensure consistency
        wallpaper_path = os.path.abspath(wallpaper_path)
        logger.info(f"Using absolute path: {wallpaper_path}")
        
        try:
            # Show the main window
            self.main_window.show()
            self.main_window.setWindowState(self.main_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
            self.main_window.raise_()
            self.main_window.activateWindow()
            
            # Force processing of events to ensure window activation
            self.app.processEvents()
            
            # Select the notes tab
            for i in range(self.main_window.tab_widget.count()):
                if self.main_window.tab_widget.tabText(i) == "Image Notes":
                    self.main_window.tab_widget.setCurrentIndex(i)
                    break
            
            # Process events again to ensure tab switch is complete
            self.app.processEvents()
            
            # Check if this wallpaper already has notes
            if wallpaper_path in self.main_window.notes_tab.notes_data:
                # Find and select the item in the list
                for i in range(self.main_window.notes_tab.wallpaper_list.count()):
                    item = self.main_window.notes_tab.wallpaper_list.item(i)
                    if item and item.data(Qt.UserRole) == wallpaper_path:
                        self.main_window.notes_tab.wallpaper_list.setCurrentItem(item)
                        logger.info("Selected existing wallpaper in list")
                        break
            else:
                # Create a new entry
                self.main_window.notes_tab.current_wallpaper = wallpaper_path
                self.main_window.notes_tab.wallpaper_label.setText(f"Wallpaper: {os.path.basename(wallpaper_path)}")
                self.main_window.notes_tab.notes_edit.clear()
                logger.info("Created new entry for wallpaper")
                
                # Load preview
                try:
                    pixmap = QPixmap(wallpaper_path)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.main_window.notes_tab.preview_label.setPixmap(pixmap)
                        logger.info("Loaded preview image successfully")
                    else:
                        self.main_window.notes_tab.preview_label.setText("Preview not available (null pixmap)")
                        logger.warning("Failed to load preview - null pixmap")
                except Exception as e:
                    self.main_window.notes_tab.preview_label.setText("Error loading preview")
                    logger.error(f"Error loading preview: {e}")
            
            # Focus on the notes edit field
            self.main_window.notes_tab.notes_edit.setFocus()
            
            # Show status message
            self.main_window.statusBar().showMessage(f"Ready to add notes for {os.path.basename(wallpaper_path)}", 3000)
            
            # Process events again to ensure UI is updated
            self.app.processEvents()
            
        except Exception as e:
            logger.error(f"Error in open_notes_for_wallpaper: {e}")



def main():
    """Main function"""
    # Check for command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Wallpaper Slideshow Tray Application")
    parser.add_argument("--open-notes", metavar="PATH", help="Open notes for the specified wallpaper")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set up logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    try:
        # Create the application
        app = WallpaperTrayApp()
        
        # If --open-notes is specified, open notes for the specified wallpaper
        if args.open_notes:
            # Validate the path
            if not args.open_notes:
                logger.error("Empty path provided with --open-notes")
            elif not os.path.exists(args.open_notes):
                logger.error(f"File not found: {args.open_notes}")
            else:
                # Wait a moment for the app to initialize
                logger.info(f"Will open notes for {args.open_notes} after initialization")
                QTimer.singleShot(1000, lambda: app.open_notes_for_wallpaper(args.open_notes))
        
        # Run the application
        return app.run()
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())