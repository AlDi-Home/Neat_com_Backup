"""
Test script to verify folder discovery without doing full backup

This script logs in and lists all folders in your cabinet to verify
the selectors are working correctly.

Usage: python3 test_folders.py
"""

import sys
from pathlib import Path
from config import Config
from neat_bot import NeatBot

def test_folder_discovery():
    """Test that we can find folders in Neat.com"""

    print("=" * 60)
    print("Neat.com Folder Discovery Test")
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

        # Display results
        if folders:
            print("=" * 60)
            print(f"SUCCESS! Found {len(folders)} folders:")
            print("=" * 60)
            for i, (folder_name, folder_selector) in enumerate(folders, 1):
                print(f"{i:2d}. {folder_name}")
                print(f"     Selector: {folder_selector}")
            print("=" * 60)
            print()
            print("✓ Folder discovery is working correctly!")
            print("✓ You can now run the full backup with confidence.")
            return True
        else:
            print("=" * 60)
            print("❌ No folders found!")
            print("=" * 60)
            print()
            print("This could mean:")
            print("  1. Your cabinet is empty (no folders created)")
            print("  2. The selectors need further adjustment")
            print("  3. The page structure has changed")
            print()
            print("Check the debug files in ~/NeatDebug/ for more info.")
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
    success = test_folder_discovery()
    sys.exit(0 if success else 1)
