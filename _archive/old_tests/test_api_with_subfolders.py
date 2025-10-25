#!/usr/bin/env python3
"""
Test API download with recursive subfolder support
"""
import sys
from config import Config
from neat_bot import NeatBot

def main(folder_name):
    print(f"🔍 Testing API Backup with Subfolders: {folder_name}")
    print("=" * 80)

    # Initialize
    config = Config()
    username, password = config.load_credentials()

    if not username or not password:
        print("❌ No saved credentials found!")
        sys.exit(1)

    print(f"✅ Loaded credentials for: {username}")

    # Create bot
    bot = NeatBot(config, status_callback=lambda msg, level: None)

    try:
        # Setup driver
        print("\n📦 Setting up Chrome...")
        bot.setup_driver()

        # Login
        print("\n🔐 Logging in...")
        if not bot.login(username, password):
            print("❌ Login failed!")
            sys.exit(1)

        # Get folders
        print("\n📁 Getting folders...")
        folders = bot.get_folders()

        if not folders:
            print("❌ No folders found!")
            sys.exit(1)

        # Find the requested folder
        print(f"\n🔎 Looking for folder: {folder_name}")
        target_folder = None
        for fname, selector, elem in folders:
            if fname == folder_name:
                target_folder = (fname, selector, elem)
                break

        if not target_folder:
            print(f"❌ Folder '{folder_name}' not found!")
            print("Available folders:")
            for fname, _, _ in folders:
                print(f"  - {fname}")
            sys.exit(1)

        print(f"✅ Found folder: {target_folder[0]}")

        # Export files from this folder (including subfolders)
        print(f"\n📤 Exporting files from {folder_name} (including subfolders)...")
        print("=" * 80)

        success_count, fail_count, errors = bot.export_folder_files(
            target_folder[0],
            target_folder[1],
            "",  # Empty parent path
            target_folder[2]  # Folder element
        )

        print()
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"✅ Successfully exported: {success_count} files")
        print(f"❌ Failed: {fail_count} files")

        if errors:
            print(f"\nErrors:")
            for error in errors[:10]:
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n🧹 Cleaning up...")
        bot.cleanup()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_api_with_subfolders.py \"Folder Name\"")
        print("Example: python3 test_api_with_subfolders.py \"2013 year TAX\"")
        sys.exit(1)

    main(sys.argv[1])
