#!/usr/bin/env python3
"""
Wallpaper Slideshow System Tray Application

This script provides a system tray icon for controlling the wallpaper slideshow
and allows associating notes with the current wallpaper.

Features:
- System tray icon with right-click menu for controlling slideshow
- Left-click to open a note-taking window for the current wallpaper
- Options to navigate forward/backward, open color control panel, etc.
- Automatic startup with KDE

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
from pathlib import Path
import logging
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction, 
                            QMainWindow, QTextEdit, QVBoxLayout, QWidget,
                            QPushButton, QHBoxLayout, QLabel, QListWidget,
                            QListWidgetItem, QSplitter, QFileDialog, QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QTimer, QSize

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
CONTROL_SCRIPT = os.path.join(SCRIPT_DIR, "control_slideshow.sh")
COLOR_CONTROL_PANEL = os.path.join(os.path.dirname(SCRIPT_DIR), "wallpaper_color_manager_new/color_control_panel.py")
GET_CURRENT_WALLPAPER = os.path.join(os.path.dirname(SCRIPT_DIR), "get_current_wallpaper.py")
PID_FILE = os.path.expanduser("~/.config/custom_wallpaper_slideshow.pid")
ICON_PATH = os.path.join(SCRIPT_DIR, "wallpaper_tray_icon.png")
DEFAULT_ICON = "preferences-desktop-wallpaper"
class WallpaperNotesWindow(QMainWindow):
    """Window for viewing and editing notes for wallpapers"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wallpaper Notes")
        self.resize(800, 600)
        
        # Initialize variables
        self.current_wallpaper = None
        self.notes_data = {}
        self.load_notes_data()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for list and notes
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create list widget for wallpapers with notes
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        self.wallpaper_list = QListWidget()
        self.wallpaper_list.setMinimumWidth(250)
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
        
        # Add widgets to splitter
        splitter.addWidget(list_widget)
        splitter.addWidget(notes_widget)
        splitter.setStretchFactor(1, 1)  # Make notes side expandable
        
        # Create notes directory if it doesn't exist
        os.makedirs(NOTES_DIR, exist_ok=True)
        
        # Populate the list
        self.populate_wallpaper_list()
        
        # Get current wallpaper
        self.refresh_current_wallpaper()
    
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
        self.statusBar().showMessage("Notes saved successfully", 3000)
    
    def refresh_current_wallpaper(self):
        """Get the current wallpaper and load its notes"""
        try:
            # Run get_current_wallpaper.py to get the current wallpaper
            result = subprocess.run(
                ["python3", GET_CURRENT_WALLPAPER, "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )
            
            wallpaper_name = result.stdout.strip()
            
            if not wallpaper_name:
                logger.warning("Could not determine current wallpaper")
                self.statusBar().showMessage("Could not determine current wallpaper", 3000)
                return
            
            # Find the full path to the wallpaper
            wallpaper_path = self.find_wallpaper_path(wallpaper_name)
            
            if not wallpaper_path:
                logger.warning(f"Could not find full path for wallpaper: {wallpaper_name}")
                self.statusBar().showMessage(f"Could not find wallpaper: {wallpaper_name}", 3000)
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
            
            self.statusBar().showMessage(f"Current wallpaper: {os.path.basename(wallpaper_path)}", 3000)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting current wallpaper: {e}")
            self.statusBar().showMessage("Error getting current wallpaper", 3000)
    
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
class WallpaperHistoryWindow(QMainWindow):
    """Window for viewing the history of wallpapers shown in the slideshow"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wallpaper History")
        self.resize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
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
        
        # Load history
        self.history_file = os.path.join(NOTES_DIR, "wallpaper_history.json")
        self.load_history()
    
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
                
                self.statusBar().showMessage(f"Loaded {self.history_list.count()} wallpapers from history", 3000)
            except Exception as e:
                logger.error(f"Error loading wallpaper history: {e}")
                self.statusBar().showMessage("Error loading wallpaper history", 3000)
        else:
            self.statusBar().showMessage("No wallpaper history found", 3000)
    
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
            self.statusBar().showMessage("No wallpaper selected", 3000)
            return
        
        wallpaper_path = selected_items[0].data(Qt.UserRole)
        self.set_wallpaper(wallpaper_path)
    
    def set_wallpaper(self, wallpaper_path):
        """Set a wallpaper as the current wallpaper"""
        if not wallpaper_path or not os.path.exists(wallpaper_path):
            self.statusBar().showMessage("Wallpaper file not found", 3000)
            return
        
        try:
            # Use set_specific_wallpaper.py to set the wallpaper
            set_wallpaper_script = os.path.join(SCRIPT_DIR, "set_specific_wallpaper.py")
            subprocess.run(
                ["python3", set_wallpaper_script, wallpaper_path],
                check=True
            )
            
            self.statusBar().showMessage(f"Set wallpaper to {os.path.basename(wallpaper_path)}", 3000)
            logger.info(f"Set wallpaper to {wallpaper_path}")
        except Exception as e:
            self.statusBar().showMessage(f"Error setting wallpaper: {str(e)}", 3000)
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
                self.statusBar().showMessage("Wallpaper history cleared", 3000)
                logger.info("Wallpaper history cleared")
            except Exception as e:
                self.statusBar().showMessage(f"Error clearing history: {str(e)}", 3000)
                logger.error(f"Error clearing wallpaper history: {e}")
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
        
        # Create windows (but don't show them yet)
        self.notes_window = WallpaperNotesWindow()
        self.history_window = WallpaperHistoryWindow()
        
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
        
        # Initial check if slideshow is running
        QTimer.singleShot(1000, self.check_slideshow_status)
        
        logger.info("Wallpaper tray application started")
    
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
        
        # Notes action
        notes_action = QAction("Open Notes", self.menu)
        notes_action.triggered.connect(self.show_notes_window)
        self.menu.addAction(notes_action)
        
        # History action
        history_action = QAction("Wallpaper History", self.menu)
        history_action.triggered.connect(self.show_history_window)
        self.menu.addAction(history_action)
        
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
            QTimer.singleShot(100, self.show_notes_window)
    
    def show_notes_window(self):
        """Show the notes window"""
        # Show the window first, then refresh in the background
        self.notes_window.show()
        self.notes_window.raise_()
        self.notes_window.activateWindow()
        
        # Refresh in a separate thread to avoid blocking the UI
        threading.Thread(target=self._refresh_notes_thread, daemon=True).start()
    
    def _refresh_notes_thread(self):
        """Background thread for refreshing notes"""
        try:
            # Small delay to ensure window is visible first
            time.sleep(0.1)
            self.notes_window.refresh_current_wallpaper()
        except Exception as e:
            logger.error(f"Error refreshing notes: {e}")
    
    def show_history_window(self):
        """Show the history window"""
        self.history_window.load_history()
        self.history_window.show()
        self.history_window.raise_()
        self.history_window.activateWindow()
    
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
            # First stop the slideshow
            subprocess.run([CONTROL_SCRIPT, "stop"], check=True)
            logger.info("Stopping slideshow")
            
            # Wait a moment for the slideshow to stop
            time.sleep(1)
            
            # Start the slideshow again
            custom_wallpaper_script = os.path.join(SCRIPT_DIR, "custom_wallpaper.py")
            subprocess.Popen(["python3", custom_wallpaper_script])
            logger.info("Starting slideshow")
            
            # Wait a moment for the slideshow to start
            time.sleep(1)
            
            # Update status
            self.check_slideshow_status()
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
            # Run get_current_wallpaper.py to get the current wallpaper
            result = subprocess.run(
                ["python3", GET_CURRENT_WALLPAPER, "--name-only", "--fast"],
                capture_output=True,
                text=True,
                check=True
            )
            
            wallpaper_name = result.stdout.strip()
            
            if not wallpaper_name:
                return
            
            # Find the full path to the wallpaper
            wallpaper_path = self._find_wallpaper_path_cached(wallpaper_name)
            
            if not wallpaper_path:
                return
            
            # Check if the wallpaper has changed
            if wallpaper_path != self.current_wallpaper:
                logger.info(f"Wallpaper changed to: {wallpaper_path}")
                self.current_wallpaper = wallpaper_path
                
                # Add to history
                self.history_window.add_to_history(wallpaper_path)
                
                # Update notes window if it's visible - use the main thread
                if self.notes_window.isVisible():
                    self.app.processEvents()  # Process any pending events first
                    self.notes_window.refresh_current_wallpaper()
        except Exception as e:
            logger.error(f"Error checking wallpaper change: {e}")
    
    # Cache for wallpaper paths to avoid repeated filesystem operations
    _wallpaper_path_cache = {}
    
    def _find_wallpaper_path_cached(self, wallpaper_name):
        """Cached version of find_wallpaper_path to improve performance"""
        # Check cache first
        if wallpaper_name in self._wallpaper_path_cache:
            return self._wallpaper_path_cache[wallpaper_name]
        
        # Not in cache, use the notes window's method
        wallpaper_path = self.notes_window.find_wallpaper_path(wallpaper_name)
        
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
    
    def run(self):
        """Run the application"""
        return self.app.exec_()


def main():
    """Main function"""
    # Create and run the application
    app = WallpaperTrayApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())