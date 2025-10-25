#!/bin/bash
# Neat Backup Automation Launcher
# Double-click this file to launch the application

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to that directory
cd "$DIR"

# Run the Python application
python3 main.py
