#!/usr/bin/env python3
"""Test the new size-based deduplication logic"""
import sys
from pathlib import Path
from neat_bot import NeatBot
from config import Config

def main():
    config = Config()
    bot = NeatBot(config)

    creds = config.load_credentials()
    if not creds:
        print("ERROR: No saved credentials found")
        sys.exit(1)

    username, password = creds

    try:
        bot.setup_driver()

        if not bot.login(username, password):
            print("ERROR: Login failed")
            sys.exit(1)

        # Get first folder (2013 year TAX)
        folders = bot.get_folders()
        if not folders:
            print("ERROR: No folders found")
            sys.exit(1)

        # Test with first folder
        folder_name, folder_selector, folder_elem = folders[0]
        print(f"\nTesting deduplication with folder: {folder_name}")
        print("This folder already has files downloaded, so we'll test:")
        print("1. Files with same size should be skipped")
        print("2. Files with different size (if any) should download with _1 suffix")
        print("\n" + "=" * 80)

        # Export files (should detect existing files and skip or download with suffix)
        success_count, fail_count, errors = bot.export_folder_files(
            folder_name,
            folder_selector,
            "",
            folder_elem
        )

        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"✅ Successfully processed: {success_count} files")
        print(f"❌ Failed: {fail_count} files")

        if errors:
            print(f"\nErrors:")
            for error in errors[:10]:
                print(f"  - {error}")

        # Check for any _1 files (indicating different size)
        download_dir = Path(config.get('download_dir')) / folder_name
        numbered_files = list(download_dir.glob("*_[0-9].pdf"))
        if numbered_files:
            print(f"\n📝 Found {len(numbered_files)} files with numbered suffixes:")
            for f in numbered_files[:5]:
                print(f"  - {f.name} ({f.stat().st_size:,} bytes)")
        else:
            print("\n✓ No numbered suffixes - all files had matching sizes")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        bot.cleanup()

if __name__ == "__main__":
    main()
