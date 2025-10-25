"""
Utility functions for file management and download tracking
"""
import os
import time
from pathlib import Path
from typing import Optional

def wait_for_download(download_dir: str, filename: str, timeout: int = 30) -> bool:
    """
    Wait for a file to finish downloading
    
    Args:
        download_dir: Directory where file is downloading
        filename: Expected filename
        timeout: Maximum seconds to wait
    
    Returns:
        True if download completed, False if timeout
    """
    download_path = Path(download_dir) / filename
    temp_file = Path(download_dir) / f"{filename}.crdownload"
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Check if download is complete (no .crdownload file)
        if download_path.exists() and not temp_file.exists():
            # Wait a bit more to ensure file is fully written
            time.sleep(0.5)
            return True
        
        time.sleep(0.5)
    
    return False

def organize_file(source_path: str, folder_name: str, backup_root: str) -> Optional[str]:
    """
    Move downloaded file to organized folder structure
    
    Args:
        source_path: Path to downloaded file
        folder_name: Name of Neat folder (e.g., "2024 year TAX")
        backup_root: Root backup directory
    
    Returns:
        Final file path or None if failed
    """
    source = Path(source_path)
    if not source.exists():
        return None
    
    # Create nested folder structure
    dest_folder = Path(backup_root) / folder_name
    dest_folder.mkdir(parents=True, exist_ok=True)
    
    # Move file
    dest_path = dest_folder / source.name
    
    # Handle duplicate names
    counter = 1
    while dest_path.exists():
        stem = source.stem
        suffix = source.suffix
        dest_path = dest_folder / f"{stem}_{counter}{suffix}"
        counter += 1
    
    source.rename(dest_path)
    return str(dest_path)

def sanitize_folder_name(name: str) -> str:
    """
    Sanitize folder name/path for filesystem compatibility

    Handles paths with slashes by sanitizing each component separately
    to preserve folder hierarchy.

    Args:
        name: Original folder name or path (e.g., "2013 year TAX/Receipts")

    Returns:
        Safe folder name or path (e.g., "2013 year TAX/Receipts")
    """
    # Split by forward slash to preserve folder hierarchy
    path_parts = name.split('/')

    # Sanitize each part separately
    unsafe_chars = ['<', '>', ':', '"', '\\', '|', '?', '*']
    sanitized_parts = []

    for part in path_parts:
        safe_part = part
        for char in unsafe_chars:
            safe_part = safe_part.replace(char, '_')
        sanitized_parts.append(safe_part.strip())

    # Rejoin with forward slash
    return '/'.join(sanitized_parts)

def get_chrome_download_dir() -> str:
    """
    Get Chrome's default download directory
    
    Returns:
        Path to Chrome download directory
    """
    home = Path.home()
    
    # macOS
    if os.name == 'posix' and os.uname().sysname == 'Darwin':
        return str(home / 'Downloads')
    
    # Windows
    elif os.name == 'nt':
        return str(home / 'Downloads')
    
    # Linux
    else:
        return str(home / 'Downloads')
