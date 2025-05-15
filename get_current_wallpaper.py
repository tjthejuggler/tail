#!/usr/bin/env python3
"""
Get Current Wallpaper

This script identifies the current wallpaper image being displayed on KDE Plasma.
It works with slideshow wallpapers that change every 15 seconds.

Usage:
    python3 get_current_wallpaper.py [--verbose]
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
import logging
import numpy as np
from PIL import Image
import tempfile
import cv2
from skimage.metrics import structural_similarity as ssim

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Get the current KDE wallpaper image")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--all-screens", action="store_true", help="Show wallpaper for all screens")
    parser.add_argument("--threshold", type=float, default=0.1, help="Similarity threshold (lower is stricter)")
    parser.add_argument("--crop", action="store_true", help="Crop screenshot to remove desktop elements")
    parser.add_argument("--crop-top", type=int, default=60, help="Pixels to crop from top")
    parser.add_argument("--crop-bottom", type=int, default=60, help="Pixels to crop from bottom")
    parser.add_argument("--crop-left", type=int, default=0, help="Pixels to crop from left")
    parser.add_argument("--crop-right", type=int, default=0, help="Pixels to crop from right")
    parser.add_argument("--resolution", type=str, default="800x600", help="Resolution for comparison (WxH)")
    parser.add_argument("--method", type=str, choices=["ssim", "mse"], default="ssim",
                        help="Comparison method: ssim (higher is better) or mse (lower is better)")
    parser.add_argument("--name-only", action="store_true", help="Output only the filename without any additional text")
    parser.add_argument("--confidence", type=float, default=0.8, help="Confidence threshold to stop comparing (0.0-1.0)")
    parser.add_argument("--max-images", type=int, default=100, help="Maximum number of images to compare (0 = all)")
    parser.add_argument("--fast", action="store_true", help="Use fast mode (lower resolution, early stopping)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with additional output")
    parser.add_argument("--scan-dir", type=str, help="Manually specify a directory to scan for wallpapers")
    parser.add_argument("--kde-config-only", action="store_true", help="Only use KDE configuration to determine wallpaper")
    return parser.parse_args()

def take_screenshot():
    """Take a screenshot of the desktop."""
    try:
        # Create a temporary file for the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Use KDE's spectacle to take a screenshot
        cmd = ["spectacle", "-b", "-n", "-o", temp_path]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.debug(f"Screenshot saved to {temp_path}")
        return temp_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Error taking screenshot with spectacle: {e}")
        
        # Fallback to scrot if spectacle fails
        try:
            cmd = ["scrot", temp_path]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.debug(f"Screenshot saved to {temp_path} using scrot")
            return temp_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Error taking screenshot with scrot: {e}")
            
            # Fallback to imagemagick's import
            try:
                cmd = ["import", "-window", "root", temp_path]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logger.debug(f"Screenshot saved to {temp_path} using import")
                return temp_path
            except subprocess.CalledProcessError as e:
                logger.error(f"Error taking screenshot with import: {e}")
                return None

def crop_image(image_path, top=60, bottom=60, left=0, right=0):
    """
    Crop an image to remove desktop elements.
    
    Args:
        image_path: Path to the image
        top: Pixels to crop from top
        bottom: Pixels to crop from bottom
        left: Pixels to crop from left
        right: Pixels to crop from right
        
    Returns:
        PIL.Image: Cropped image
    """
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        # Calculate crop box
        crop_box = (
            left,
            top,
            width - right,
            height - bottom
        )
        
        # Crop image
        cropped = img.crop(crop_box)
        logger.debug(f"Cropped image from {img.size} to {cropped.size}")
        
        return cropped
    except Exception as e:
        logger.error(f"Error cropping image: {e}")
        return Image.open(image_path)  # Return original image on error

def compare_images(img1, img2, method="ssim", resize_to=(800, 600)):
    """
    Compare two images and return a similarity score.
    Higher score means more similar for SSIM, lower score means more similar for MSE.
    
    Args:
        img1: First image (PIL.Image or path)
        img2: Second image (PIL.Image or path)
        method: Comparison method ("ssim" or "mse")
        resize_to: Resolution to resize images to
        
    Returns:
        float: Similarity score
    """
    try:
        # Open images if paths are provided
        if isinstance(img1, str):
            img1 = Image.open(img1)
        if isinstance(img2, str):
            img2 = Image.open(img2)
        
        # Convert to RGB if needed
        if img1.mode != 'RGB':
            img1 = img1.convert('RGB')
        if img2.mode != 'RGB':
            img2 = img2.convert('RGB')
        
        # Resize images to the same dimensions
        img1 = img1.resize(resize_to)
        img2 = img2.resize(resize_to)
        
        # Convert to numpy arrays
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # Calculate histogram similarity (more robust to scaling and positioning)
        hist_score = 0.0
        for i in range(3):  # For each RGB channel
            hist1 = cv2.calcHist([arr1], [i], None, [256], [0, 256])
            hist2 = cv2.calcHist([arr2], [i], None, [256], [0, 256])
            hist1 = cv2.normalize(hist1, hist1).flatten()
            hist2 = cv2.normalize(hist2, hist2).flatten()
            hist_score += cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        hist_score /= 3.0  # Average across channels
        
        if method == "ssim":
            # Convert to grayscale for SSIM
            gray1 = cv2.cvtColor(arr1, cv2.COLOR_RGB2GRAY)
            gray2 = cv2.cvtColor(arr2, cv2.COLOR_RGB2GRAY)
            
            # Calculate SSIM (higher is better)
            ssim_score, _ = ssim(gray1, gray2, full=True)
            
            # Combine SSIM and histogram scores (both higher is better)
            combined_score = 0.7 * ssim_score + 0.3 * hist_score
            logger.debug(f"SSIM: {ssim_score:.4f}, Hist: {hist_score:.4f}, Combined: {combined_score:.4f}")
            return combined_score
        else:
            # Calculate mean squared error (lower is better)
            mse = np.mean((arr1 - arr2) ** 2)
            
            # Normalize to 0-1 range
            max_possible_mse = 255 ** 2 * 3  # Max possible difference per pixel (RGB)
            normalized_mse = mse / max_possible_mse
            
            # For MSE, lower is better, but for hist_score higher is better
            # So we invert hist_score and combine (both lower is better)
            combined_score = 0.7 * normalized_mse + 0.3 * (1.0 - hist_score)
            logger.debug(f"MSE: {normalized_mse:.4f}, Hist: {1.0-hist_score:.4f}, Combined: {combined_score:.4f}")
            return combined_score
    except Exception as e:
        logger.error(f"Error comparing images: {e}")
        if method == "ssim":
            return 0.0  # Worst SSIM score
        else:
            return float('inf')  # Worst MSE score

def get_current_wallpaper_info_from_kde(logger):
    """
    Retrieves current wallpaper information by parsing the KDE config file directly.
    Returns a tuple: (current_wallpaper_path, list_of_slideshow_source_directories, found_slideshow_plugin_config)
    Returns (None, [], False) if information cannot be retrieved.
    """
    config_path = os.path.expanduser("~/.config/plasma-org.kde.plasma.desktop-appletsrc")
    if not os.path.exists(config_path):
        logger.error(f"KDE config file not found: {config_path}")
        return None, [], False

    with open(config_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_wallpaper_path = None
    slideshow_dirs = []
    found_slideshow_plugin_config = False

    for idx, line in enumerate(lines):
        if line.strip().startswith("[Containments]") and "Wallpaper" in line and "org.kde.slideshow" in line and "General" in line:
            found_slideshow_plugin_config = True
            j = idx + 1
            image_path_in_block = None
            slide_paths_in_block = []
            while j < len(lines) and not lines[j].strip().startswith("["):
                l = lines[j].strip()
                if l.startswith("Image="):
                    image_path_in_block = l[len("Image="):]
                elif l.startswith("SlidePaths="):
                    paths = l[len("SlidePaths="):].split(",")
                    for p_uri in paths:
                        p = p_uri.strip()
                        if p.startswith("file://"):
                            p = p[len("file://"):]
                        if p:
                            slide_paths_in_block.append(p)
                j += 1
            if image_path_in_block and not current_wallpaper_path:
                current_wallpaper_path = image_path_in_block if not image_path_in_block.startswith("file://") else image_path_in_block[len("file://"):]
            slideshow_dirs.extend(slide_paths_in_block)

    valid_slideshow_dirs = []
    for d in sorted(set(slideshow_dirs)):
        if os.path.isdir(d):
            valid_slideshow_dirs.append(d)
    if current_wallpaper_path:
        logger.info(f"Current wallpaper from config: {current_wallpaper_path}")
    if valid_slideshow_dirs:
        logger.info(f"Valid slideshow source directories from config: {valid_slideshow_dirs}")
    return current_wallpaper_path, valid_slideshow_dirs, found_slideshow_plugin_config

def get_potential_wallpaper_images(logger, kde_discovered_dirs=None, user_scan_dir=None):
    images = []
    search_paths_with_source = []
    if user_scan_dir:
        if os.path.exists(user_scan_dir) and os.path.isdir(user_scan_dir):
            logger.debug(f"Using manually specified scan directory: {user_scan_dir}")
            search_paths_with_source.append((user_scan_dir, "user"))
        else:
            logger.warning(f"Specified scan directory does not exist or is not a directory: {user_scan_dir}")
    if kde_discovered_dirs:
        for ddir in kde_discovered_dirs:
            if os.path.exists(ddir) and os.path.isdir(ddir):
                search_paths_with_source.append((ddir, "kde"))
            else:
                logger.warning(f"KDE configured wallpaper directory does not exist or not a dir: {ddir}")
    if not search_paths_with_source:
        logger.debug("No wallpaper directories to scan.")
        return []
    final_search_paths = []
    seen_paths = set()
    for path, source in search_paths_with_source:
        if path not in seen_paths:
            final_search_paths.append((path, source))
            seen_paths.add(path)
    logger.debug(f"Scanning for images in: {final_search_paths}")
    for target_dir, source_type in final_search_paths:
        logger.debug(f"Scanning {target_dir} (non-recursively)...")
        try:
            for item_name in os.listdir(target_dir):
                item_path = os.path.join(target_dir, item_name)
                actual_path = item_path
                is_link = os.path.islink(item_path)
                if is_link:
                    try:
                        actual_path = os.path.realpath(item_path)
                    except OSError as e:
                        logger.warning(f"Could not resolve symlink {item_path}: {e}")
                        continue
                if os.path.isfile(actual_path) and actual_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                    images.append((item_path, actual_path))
        except OSError as e:
            logger.error(f"Could not list directory {target_dir}: {e}")
            continue
    unique_images_by_target = {}
    for original_path, target_path in images:
        if target_path not in unique_images_by_target:
            unique_images_by_target[target_path] = original_path
    deduplicated_images = [(orig, target) for target, orig in unique_images_by_target.items()]
    logger.debug(f"Found {len(deduplicated_images)} potential wallpaper images from provided directories.")
    return deduplicated_images

def find_current_wallpaper(screenshot_path, args, slideshow_images):
    """
    Find the current wallpaper by comparing the screenshot with all wallpaper images.
    Args:
        screenshot_path: Path to the screenshot
        args: Command line arguments
        slideshow_images: List of (symlink_path, target_path) tuples to compare
    Returns:
        tuple: (best_match_path, similarity_score)
    """
    if not slideshow_images:
        logger.warning("No slideshow images provided for comparison.")
        return None, 0.0 if args.method == "ssim" else float('inf')
    if args.fast:
        args.resolution = "400x300"
        args.confidence = 0.7
        if args.max_images == 0 or args.max_images > 20:
            args.max_images = 20
    try:
        width, height = map(int, args.resolution.split('x'))
        resize_to = (width, height)
    except ValueError:
        logger.warning(f"Invalid resolution format: {args.resolution}, using default 800x600")
        resize_to = (800, 600)
    if args.crop:
        screenshot_img = crop_image(
            screenshot_path,
            top=args.crop_top,
            bottom=args.crop_bottom,
            left=args.crop_left,
            right=args.crop_right
        )
    else:
        screenshot_img = Image.open(screenshot_path)
    if args.max_images > 0 and args.max_images < len(slideshow_images):
        logger.debug(f"Limiting comparison to {args.max_images} images")
        slideshow_images = slideshow_images[:args.max_images]
    best_match = None
    if args.method == "ssim":
        best_score = 0.0
        confidence_threshold = args.confidence
    else:
        best_score = float('inf')
        confidence_threshold = 1.0 - args.confidence
    for _, target in slideshow_images:
        score = compare_images(screenshot_img, target, method=args.method, resize_to=resize_to)
        if args.method == "ssim":
            if score > best_score:
                best_score = score
                best_match = target
                if score >= confidence_threshold:
                    logger.debug(f"Confidence threshold reached: {score:.4f} >= {confidence_threshold}")
                    break
        else:
            if score < best_score:
                best_score = score
                best_match = target
                if score <= confidence_threshold:
                    logger.debug(f"Confidence threshold reached: {score:.4f} <= {confidence_threshold}")
                    break
    logger.debug(f"Best match: {os.path.basename(best_match) if best_match else None} with score {best_score:.4f}")
    return best_match, best_score

def main():
    args = parse_arguments()
    if args.verbose or args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.debug("Debug output enabled")

    current_wallpaper_path, slideshow_dirs_from_kde, config_indicates_slideshow = get_current_wallpaper_info_from_kde(logger)

    is_slideshow = config_indicates_slideshow and bool(slideshow_dirs_from_kde)
    if is_slideshow:
        logger.info("Config indicates an active slideshow plugin with source directories.")
    elif config_indicates_slideshow and not slideshow_dirs_from_kde:
        logger.info("Config indicates slideshow plugin, but no valid source directories found. Treating as single image or error.")
        is_slideshow = False
    else:
        logger.info("Config does not indicate an active slideshow plugin, or no slideshow directories found.")

    if args.all_screens:
        all_imgs = get_potential_wallpaper_images(logger, slideshow_dirs_from_kde, args.scan_dir)
        if all_imgs:
            if not args.name_only:
                print("All potential wallpaper images from configured/scanned directories:")
            for original_path, target_path in all_imgs:
                filename = os.path.basename(target_path)
                if args.name_only:
                    print(filename)
                else:
                    path_info = f"({target_path})" if original_path == target_path else f"({original_path} -> {target_path})"
                    print(f"{filename} {path_info}")
        else:
            if not args.name_only:
                print("No slideshow/wallpaper images found in configured or scanned directories.")
        return

    if not is_slideshow and current_wallpaper_path:
        filename = os.path.basename(current_wallpaper_path)
        if args.name_only:
            print(filename)
        else:
            print(f"Current wallpaper (from KDE config, single image): {filename}")
            if args.verbose or args.debug:
                print(f"Full path: {current_wallpaper_path}")
        sys.exit(0)

    if is_slideshow:
        logger.info("Proceeding with screenshot comparison for slideshow.")
        screenshot_path = take_screenshot()
        if not screenshot_path:
            if not args.name_only:
                print("Failed to take a screenshot for slideshow comparison.")
            sys.exit(1)
        try:
            if args.debug:
                debug_screenshot = os.path.expanduser("~/wallpaper_debug_screenshot.png")
                try:
                    import shutil
                    shutil.copy2(screenshot_path, debug_screenshot)
                    logger.debug(f"Saved debug screenshot to {debug_screenshot}")
                except Exception as e:
                    logger.error(f"Failed to save debug screenshot: {e}")
            potential_images = get_potential_wallpaper_images(logger, kde_discovered_dirs=slideshow_dirs_from_kde, user_scan_dir=None)
            if not potential_images:
                if not args.name_only:
                    print(f"No images found in slideshow directories {slideshow_dirs_from_kde} for comparison.")
                sys.exit(1)
            wallpaper_path_sc, score_sc = find_current_wallpaper(screenshot_path, args, potential_images)
            if wallpaper_path_sc:
                filename = os.path.basename(wallpaper_path_sc)
                if args.name_only:
                    print(filename)
                else:
                    print(f"Current wallpaper (slideshow, via comparison): {filename}")
                    if args.verbose or args.debug:
                        print(f"Full path: {wallpaper_path_sc}")
                        if args.method == "ssim":
                            print(f"Match score: {score_sc:.4f} (higher is better)")
                        else:
                            print(f"Match score: {score_sc:.4f} (lower is better)")
                if args.debug:
                    debug_match = os.path.expanduser("~/wallpaper_debug_match.png")
                    try:
                        import shutil
                        shutil.copy2(wallpaper_path_sc, debug_match)
                        logger.debug(f"Saved matched wallpaper to {debug_match}")
                    except Exception as e:
                        logger.error(f"Failed to save matched wallpaper: {e}")
            else:
                if not args.name_only:
                    print("Could not determine current wallpaper using screenshot comparison for slideshow.")
                if current_wallpaper_path:
                    if not args.name_only:
                        print(f"(Config reported: {os.path.basename(current_wallpaper_path)})")
        finally:
            if screenshot_path and os.path.exists(screenshot_path):
                os.unlink(screenshot_path)
                logger.debug(f"Deleted temporary screenshot {screenshot_path}")
        sys.exit(0)

    if not args.name_only:
        print("Could not determine current wallpaper.")
        if slideshow_dirs_from_kde:
            print(f"KDE reported slideshow directories: {slideshow_dirs_from_kde}")
        elif args.scan_dir:
            print(f"Scanned directory: {args.scan_dir}")
        else:
            print("No wallpaper directories configured or specified for fallback search.")
    sys.exit(1)

if __name__ == "__main__":
    main()