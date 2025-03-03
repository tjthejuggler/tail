# File Operations Design

This document outlines the design of the File Operations module for the Wallpaper Color Manager system.

## Overview

The File Operations module is responsible for:

1. Creating and managing directory structures
2. Creating and managing symlinks between original images and color categories
3. Resetting color categories (clearing symlinks)
4. Managing sample images
5. Handling file system errors and edge cases

## Directory Structure

The system uses the following directory structure:

```
/home/twain/Pictures/
├── llm_baby_monster/                 # Original directory (KDE looks here)
├── llm_baby_monster_original/        # Master copy of all images
├── llm_baby_monster_new/             # Directory for new images awaiting analysis
├── llm_baby_monster_by_color/        # Color-categorized directories
│   ├── red/
│   ├── orange/
│   ├── green/
│   ├── blue/
│   ├── pink/
│   ├── yellow/
│   └── white_gray_black/
├── llm_baby_monster_current/         # Current active color directory
└── llm_baby_monster_retired/         # Retired images no longer used as wallpapers
```

## Key Components

### 1. Directory Management

Functions for creating and verifying the directory structure:

```python
def setup_directory_structure(config):
    """
    Create the necessary directory structure for the wallpaper color management system.
    
    Args:
        config (dict): Configuration dictionary containing path information
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get base directory from config
    base_dir = config["paths"]["base_dir"]
    
    # Define directories to create
    directories = [
        config["paths"]["original_dir"],
        "llm_baby_monster_new",
        "llm_baby_monster_by_color",
    ]
    
    # Add color directories
    for color in config["paths"]["color_dirs"]:
        color_path = config["paths"]["color_dirs"][color]
        if not color_path.startswith("/"):  # Relative path
            directories.append(color_path)
    
    # Create directories if they don't exist
    for directory in directories:
        full_path = os.path.join(base_dir, directory)
        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path)
                logging.info(f"Created directory: {full_path}")
            except Exception as e:
                logging.error(f"Error creating directory {full_path}: {e}")
                return False
    
    return True
```

### 2. Symlink Management

Functions for creating and managing symlinks:

```python
def create_symlinks(image_path, categories, config):
    """
    Create symlinks for an image in the specified color categories.
    
    Args:
        image_path (str): Path to the original image
        categories (list): List of color categories to link to
        config (dict): Configuration dictionary
        
    Returns:
        dict: Dictionary mapping categories to success/failure status
    """
    results = {}
    filename = os.path.basename(image_path)
    base_dir = config["paths"]["base_dir"]
    
    for category in categories:
        # Get the color directory path
        color_dir = os.path.join(base_dir, config["paths"]["color_dirs"][category])
        symlink_path = os.path.join(color_dir, filename)
        
        # Remove existing symlink if it exists
        if os.path.exists(symlink_path):
            try:
                os.remove(symlink_path)
            except Exception as e:
                logging.error(f"Error removing existing symlink {symlink_path}: {e}")
                results[category] = False
                continue
        
        # Create new symlink
        try:
            os.symlink(image_path, symlink_path)
            results[category] = True
        except Exception as e:
            logging.error(f"Error creating symlink {symlink_path}: {e}")
            results[category] = False
    
    return results
```

### 3. Reset Functionality

Functions for resetting color categories:

```python
def reset_categories(config):
    """
    Reset all color categories by removing all symlinks.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        dict: Statistics about the reset operation
    """
    stats = {
        "total_removed": 0,
        "errors": 0,
        "categories_cleared": []
    }
    
    base_dir = config["paths"]["base_dir"]
    
    # Process each color directory
    for color, color_path in config["paths"]["color_dirs"].items():
        color_dir = os.path.join(base_dir, color_path)
        
        if not os.path.exists(color_dir):
            continue
        
        # Count files before removal
        files_before = len([f for f in os.listdir(color_dir) 
                           if os.path.islink(os.path.join(color_dir, f))])
        
        # Remove all symlinks in the directory
        for filename in os.listdir(color_dir):
            file_path = os.path.join(color_dir, filename)
            if os.path.islink(file_path) or os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    stats["total_removed"] += 1
                except Exception as e:
                    logging.error(f"Error removing {file_path}: {e}")
                    stats["errors"] += 1
        
        # Count files after removal
        files_after = len([f for f in os.listdir(color_dir) 
                          if os.path.islink(os.path.join(color_dir, f))])
        
        # If all files were removed successfully
        if files_after == 0 and files_before > 0:
            stats["categories_cleared"].append(color)
    
    return stats
```

### 4. Sample Image Management

Functions for managing sample images:

```python
def setup_sample_images(config):
    """
    Set up the sample images directory and ensure it contains images.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        list: List of sample image paths
    """
    # Get sample images directory
    sample_dir = config.get("sample_images_dir", "sample_images")
    
    # Create absolute path
    if not os.path.isabs(sample_dir):
        # Assume relative to the application directory
        sample_dir = os.path.join(os.path.dirname(__file__), sample_dir)
    
    # Create directory if it doesn't exist
    if not os.path.exists(sample_dir):
        try:
            os.makedirs(sample_dir)
            logging.info(f"Created sample images directory: {sample_dir}")
        except Exception as e:
            logging.error(f"Error creating sample images directory: {e}")
            return []
    
    # Get list of sample images
    sample_images = []
    for filename in os.listdir(sample_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            sample_images.append(os.path.join(sample_dir, filename))
    
    # If no sample images, try to copy some from the original directory
    if not sample_images:
        original_dir = os.path.join(config["paths"]["base_dir"], 
                                   config["paths"]["original_dir"])
        
        if os.path.exists(original_dir):
            # Get a few random images from the original directory
            original_images = [f for f in os.listdir(original_dir) 
                              if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
            
            # Take up to 5 random images
            import random
            sample_count = min(5, len(original_images))
            if sample_count > 0:
                for i in range(sample_count):
                    idx = random.randint(0, len(original_images) - 1)
                    src = os.path.join(original_dir, original_images[idx])
                    dst = os.path.join(sample_dir, original_images[idx])
                    try:
                        shutil.copy2(src, dst)
                        sample_images.append(dst)
                        logging.info(f"Copied sample image: {dst}")
                    except Exception as e:
                        logging.error(f"Error copying sample image: {e}")
    
    return sample_images
```

### 5. Error Handling

Comprehensive error handling for file operations:

```python
def safe_file_operation(operation, *args, **kwargs):
    """
    Safely perform a file operation with proper error handling.
    
    Args:
        operation (callable): The file operation function to call
        *args: Arguments to pass to the operation
        **kwargs: Keyword arguments to pass to the operation
        
    Returns:
        tuple: (result, error_message)
    """
    try:
        result = operation(*args, **kwargs)
        return (result, None)
    except FileNotFoundError:
        return (None, "File or directory not found")
    except PermissionError:
        return (None, "Permission denied")
    except IsADirectoryError:
        return (None, "Expected a file but found a directory")
    except NotADirectoryError:
        return (None, "Expected a directory but found a file")
    except FileExistsError:
        return (None, "File already exists")
    except OSError as e:
        return (None, f"Operating system error: {e}")
    except Exception as e:
        return (None, f"Unexpected error: {e}")
```

## File System Considerations

### 1. Symlink Support

- Ensure the file system supports symbolic links
- Handle cases where symlinks are not supported
- Provide fallback mechanisms (e.g., copy files instead of symlinks)

### 2. File Permissions

- Check and handle permission issues
- Ensure the application has appropriate access rights
- Provide clear error messages for permission problems

### 3. Cross-Platform Compatibility

- Handle path differences between operating systems
- Use os.path for platform-independent path operations
- Test on different file systems

## Performance Considerations

### 1. Batch Operations

- Optimize for batch processing of multiple files
- Use appropriate buffering for file operations
- Consider using multiprocessing for large operations

### 2. Progress Reporting

- Provide progress updates for long-running operations
- Allow cancellation of operations
- Estimate time remaining for large operations

### 3. Error Recovery

- Implement transaction-like behavior where possible
- Roll back changes if an operation fails
- Keep logs of all file operations

## Testing Strategy

### 1. Unit Tests

- Test each file operation function independently
- Verify correct behavior with various inputs
- Test error handling and edge cases

### 2. Integration Tests

- Test interactions between file operations and other modules
- Verify end-to-end workflows
- Test with real file system structures

### 3. Error Simulation

- Simulate various file system errors
- Test recovery mechanisms
- Verify appropriate error messages

## Future Enhancements

### 1. Database Integration

- Store file metadata in a database for faster operations
- Track file history and changes
- Implement more sophisticated search capabilities

### 2. Cloud Storage Support

- Add support for cloud storage providers
- Handle synchronization between local and cloud storage
- Implement appropriate error handling for network issues

### 3. Backup and Restore

- Add functionality to backup the entire system
- Implement restore points
- Provide disaster recovery options