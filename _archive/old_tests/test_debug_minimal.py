"""
Minimal test to debug folder discovery
"""
import sys
from config import Config
from neat_bot import NeatBot

def main():
    print("🔍 Minimal Folder Discovery Test")
    print("=" * 50)

    # Initialize
    config = Config()

    # Try to load saved credentials
    username, password = config.load_credentials()
    if not username or not password:
        print("❌ No saved credentials found!")
        print("Please run main.py first to save credentials.")
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

        print("\n📁 Getting folders...")
        folders = bot.get_folders()

        print(f"\n✅ Found {len(folders)} folders:")
        for folder_name, selector in folders:
            print(f"  - {folder_name}")
            print(f"    Selector: {selector}")

        if not folders:
            print("\n❌ No folders found - check log messages above")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n🧹 Cleaning up...")
        bot.cleanup()

if __name__ == "__main__":
    main()
