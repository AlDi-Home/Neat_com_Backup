#!/usr/bin/env python3
"""Check what fields are available in API response"""
import sys
import json
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

        # Get first folder
        folders = bot.get_folders()
        if not folders:
            print("ERROR: No folders found")
            sys.exit(1)

        # Open first folder
        folder_name, folder_selector, folder_elem = folders[0]
        print(f"\nOpening folder: {folder_name}")

        if not bot._click_folder(folder_selector, folder_name):
            print("ERROR: Failed to open folder")
            sys.exit(1)

        # Get API response
        documents, _ = bot._intercept_api_response()

        if documents:
            print(f"\nFound {len(documents)} documents")
            print("\nFirst document fields:")
            print(json.dumps(documents[0], indent=2))

            # Check if file_size or size field exists
            if 'file_size' in documents[0]:
                print(f"\n✓ file_size field exists: {documents[0]['file_size']}")
            elif 'size' in documents[0]:
                print(f"\n✓ size field exists: {documents[0]['size']}")
            else:
                print("\n✗ No size field found in API response")
                print("\nAvailable fields:")
                for key in documents[0].keys():
                    print(f"  - {key}: {type(documents[0][key]).__name__}")
        else:
            print("No documents found")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        bot.cleanup()

if __name__ == "__main__":
    main()
