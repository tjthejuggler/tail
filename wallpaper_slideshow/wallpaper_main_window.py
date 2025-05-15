#!/usr/bin/env python3
"""
Wallpaper Slideshow Main Window

This script provides a tabbed main window for the wallpaper slideshow application,
combining history, image notes, and settings in a single interface.

Features:
- History tab: View and manage wallpaper history
- Notes tab: Add and edit notes for wallpapers
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
from pathlib import Path
import logging
from datetime import datetime

from PyQt5.QtWidgets import (QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QTextEdit, QPushButton, QListWidget,
                            QListWidgetItem, QSplitter, QFileDialog, QMessageBox,
                            QCheckBox, QSpinBox, QComboBox, QFormLayout, QGroupBox,
                            QDialogButtonBox)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject, QTimer

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
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.ini")
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
        
        # Set up UI
        self.setup_ui()
        
        # Create notes directory if it doesn't exist
        os.makedirs(NOTES_DIR, exist_ok=True)
        
        # Populate the list
        self.populate_wallpaper_list()
        
        # Get current wallpaper
        self.refresh_current_wallpaper()
    
    def setup_ui(self):
        """Set up the UI elements"""
        main_layout = QVBoxLayout(self)
        
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
                if self.parent_window:
                    self.parent_window.statusBar().showMessage("Could not determine current wallpaper", 3000)
                return
            
            # Find the full path to the wallpaper
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
class WallpaperMainWindow(QMainWindow):
    """Main window with tabs for history, notes, and settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wallpaper Slideshow Manager")
        self.resize(900, 700)
        
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
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.history_tab, "History")
        self.tab_widget.addTab(self.notes_tab, "Image Notes")
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