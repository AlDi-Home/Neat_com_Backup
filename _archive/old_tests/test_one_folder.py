"""
Test backup of a single folder
"""
import sys
from config import Config
from neat_bot import NeatBot

def main(folder_name):
    print(f"🔍 Testing Backup of: {folder_name}")
    print("=" * 50)

    # Initialize
    config = Config()

    # Try to load saved credentials
    username, password = config.load_credentials()
    if not username or not password:
        print("❌ No saved credentials found!")
        sys.exit(1)

    print(f"✅ Loaded credentials for: {username}")

    # Create bot
    bot = NeatBot(config, status_callback=lambda msg, level: print(f"[{level.upper()}] {msg}"))

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
        for fname, selector in folders:
            if fname == folder_name:
                target_folder = (fname, selector)
                break

        if not target_folder:
            print(f"❌ Folder '{folder_name}' not found!")
            print("Available folders:")
            for fname, _ in folders:
                print(f"  - {fname}")
            sys.exit(1)

        print(f"✅ Found folder: {target_folder[0]}")
        print(f"   Selector: {target_folder[1]}")

        # Export files from this folder
        print(f"\n📤 Exporting files from {folder_name}...")
        count = bot.export_folder_files(target_folder[0], target_folder[1])

        print(f"\n✅ Exported {count} files from {folder_name}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n🧹 Cleaning up...")
        bot.cleanup()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_one_folder.py \"Folder Name\"")
        sys.exit(1)

    main(sys.argv[1])
