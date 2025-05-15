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

Usage:
    ./wallpaper_tray_new.py
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

from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer

# Import the main window class
from wallpaper_main_window import WallpaperMainWindow

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
        self.main_window.raise_()
        self.main_window.activateWindow()
        
        # Refresh in a separate thread to avoid blocking the UI
        threading.Thread(target=self._refresh_window_thread, daemon=True).start()
    
    def _refresh_window_thread(self):
        """Background thread for refreshing the main window"""
        try:
            # Small delay to ensure window is visible first
            time.sleep(0.1)
            # Refresh the current wallpaper in the notes tab
            self.main_window.notes_tab.refresh_current_wallpaper()
            # Refresh the history tab
            self.main_window.history_tab.load_history()
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
                
                # Update the main window if it's visible
                if self.main_window.isVisible():
                    self.app.processEvents()  # Process any pending events first
                    self.main_window.check_wallpaper_changed(wallpaper_path)
        except Exception as e:
            logger.error(f"Error checking wallpaper change: {e}")
    
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