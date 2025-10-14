"""
Test script to backup just one folder

This script backs up a single folder to test the complete workflow
before running the full backup.

Usage: python3 test_single_folder.py [folder_name]
"""

import sys
from pathlib import Path
from config import Config
from neat_bot import NeatBot

def test_single_folder_backup(folder_name=None):
    """Test backup of a single folder"""

    print("=" * 60)
    print("Single Folder Backup Test")
    print("=" * 60)
    print()

    # Load credentials
    config = Config()
    creds = config.load_credentials()

    if not creds:
        print("❌ ERROR: No saved credentials found!")
        print("   Please run the main app first and save credentials.")
        sys.exit(1)

    username, password = creds
    print(f"✓ Loaded credentials for: {username}")
    print()

    # Create bot with status callback
    def status_callback(message, level='info'):
        symbols = {
            'info': 'ℹ',
            'success': '✓',
            'error': '✗',
            'warning': '⚠'
        }
        symbol = symbols.get(level, 'ℹ')
        print(f"{symbol} {message}")

    bot = NeatBot(config, status_callback=status_callback)

    try:
        # Setup driver
        print("Step 1: Initializing WebDriver...")
        bot.setup_driver()
        print()

        # Login
        print("Step 2: Logging in...")
        if not bot.login(username, password):
            print("❌ Login failed!")
            return False
        print()

        # Get folders
        print("Step 3: Discovering folders...")
        print("-" * 60)
        folders = bot.get_folders()
        print("-" * 60)
        print()

        if not folders:
            print("❌ No folders found!")
            return False

        # Select folder to test
        if folder_name:
            # Find the specified folder
            selected = None
            for folder_path, folder_selector in folders:
                if folder_name.lower() in folder_path.lower():
                    selected = (folder_path, folder_selector)
                    break

            if not selected:
                print(f"❌ Folder '{folder_name}' not found!")
                print("\nAvailable folders:")
                for i, (fp, _) in enumerate(folders[:10], 1):
                    print(f"  {i}. {fp}")
                return False
        else:
            # Pick a small folder (one without too many subfolders)
            # Try to find a simple leaf folder
            leaf_folders = [f for f in folders if '/' not in f[0]]
            if leaf_folders:
                selected = leaf_folders[0]
            else:
                selected = folders[0]

        folder_path, folder_selector = selected

        print("=" * 60)
        print(f"Testing backup of folder: {folder_path}")
        print("=" * 60)
        print()

        # Export files from this folder
        print(f"Step 4: Backing up folder '{folder_path}'...")
        print("-" * 60)
        exported_count, failed_count, errors = bot.export_folder_files(folder_path, folder_selector)
        print("-" * 60)
        print()

        # Display results
        total_count = exported_count + failed_count
        if exported_count > 0:
            print("=" * 60)
            print(f"✓ SUCCESS! Backed up {exported_count} files from '{folder_path}'")
            if failed_count > 0:
                print(f"⚠ WARNING: {failed_count} files failed")
            print("=" * 60)
            print()

            backup_dir = config.get('download_dir')
            expected_path = Path(backup_dir) / folder_path

            print(f"Files saved to: {expected_path}")
            print()

            # Check if files exist
            if expected_path.exists():
                files = list(expected_path.glob('*.pdf'))
                print(f"Verified: Found {len(files)} PDF files in backup directory")
                if files:
                    print("\nSample files:")
                    for f in files[:5]:
                        print(f"  - {f.name}")
            else:
                print("⚠ Warning: Backup directory not found (files may be organizing)")

            print()
            print("✓ Single folder backup test PASSED!")
            print("✓ You can now run the full backup with confidence.")
            return True
        else:
            print("=" * 60)
            print("⚠ WARNING: No files were backed up")
            print("=" * 60)
            print()
            print("This could mean:")
            print("  1. The folder is empty")
            print("  2. The PDF dropdown selector needs updating")
            print("  3. Files are still downloading")
            print()
            print("Check the status messages above for errors.")
            return False

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print()
        print("Cleaning up...")
        bot.cleanup()
        print("✓ Done!")
        print()

if __name__ == "__main__":
    # Get folder name from command line if provided
    folder_arg = sys.argv[1] if len(sys.argv) > 1 else None

    if folder_arg:
        print(f"Testing backup of folder: {folder_arg}")
    else:
        print("No folder specified, will pick a simple test folder")

    print()

    success = test_single_folder_backup(folder_arg)
    sys.exit(0 if success else 1)
