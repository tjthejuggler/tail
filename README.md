# Wallpaper Management Tools

This repository contains various tools for managing wallpapers, including a slideshow, tray applications, and a color control panel.

## Available Scripts

### Wallpaper Slideshow

The wallpaper slideshow application displays a rotating set of wallpapers from a configured directory.

To run the wallpaper slideshow tray application:

```bash
./wallpaper_slideshow/run_wallpaper_tray.sh
```

### New Wallpaper Tray

An improved version of the wallpaper tray application with additional features.

To run the new wallpaper tray application:

```bash
./wallpaper_slideshow/run_wallpaper_tray_new.sh
```

### Color Control Panel

The color control panel allows you to manage wallpapers based on their color characteristics.

To run the color control panel:

```bash
./wallpaper_color_manager_new/run_color_control_panel.sh
```

## Other Scripts

The repository also contains various utility scripts for:

- Installing/uninstalling the wallpaper slideshow
- Testing the slideshow
- Restarting the slideshow
- Setting specific wallpapers
- Managing wallpaper favorites

## Directory Structure

- `wallpaper_slideshow/`: Contains the main slideshow application and related scripts
- `wallpaper_color_manager_new/`: Contains the color control panel and color analysis tools

## Configuration

Configuration files are stored in:

- `wallpaper_slideshow/config.ini`: Configuration for the wallpaper slideshow
- `wallpaper_color_manager_new/config.json`: Configuration for the color control panel