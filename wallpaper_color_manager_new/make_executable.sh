#!/bin/bash
# Make all Python scripts executable

# Change to the script directory
cd "$(dirname "$0")"

# Make Python scripts executable
chmod +x *.py
chmod +x utils/*.py

echo "Made Python scripts executable"