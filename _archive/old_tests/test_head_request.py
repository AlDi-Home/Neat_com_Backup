#!/usr/bin/env python3
"""Test if HEAD request works for download URLs"""
import sys
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
        folder_name, folder_selector, folder_elem = folders[0]

        # Open folder
        if not bot._click_folder(folder_selector, folder_name):
            print("ERROR: Failed to open folder")
            sys.exit(1)

        # Get documents
        documents, _ = bot._intercept_api_response()

        if documents:
            doc = documents[0]
            download_url = doc.get('download_url')

            print(f"\nTesting HEAD request for: {doc.get('name')}")
            print(f"Download URL: {download_url[:80]}...")

            # Test HEAD request
            print("\n=== HEAD Request ===")
            try:
                head_response = bot.session.head(download_url, allow_redirects=True, timeout=30)
                print(f"Status: {head_response.status_code}")
                print(f"Headers:")
                for key, value in head_response.headers.items():
                    print(f"  {key}: {value}")

                content_length = head_response.headers.get('Content-Length')
                if content_length:
                    print(f"\n✓ Content-Length: {int(content_length):,} bytes")
                else:
                    print("\n✗ No Content-Length header")

            except Exception as e:
                print(f"✗ HEAD request failed: {e}")

            # Test GET request
            print("\n=== GET Request (partial) ===")
            try:
                get_response = bot.session.get(download_url, allow_redirects=True, timeout=30, stream=True)
                print(f"Status: {get_response.status_code}")
                print(f"Headers:")
                for key, value in get_response.headers.items():
                    print(f"  {key}: {value}")

                content_length = get_response.headers.get('Content-Length')
                if content_length:
                    print(f"\n✓ Content-Length: {int(content_length):,} bytes")
                else:
                    print("\n✗ No Content-Length header")

            except Exception as e:
                print(f"✗ GET request failed: {e}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        bot.cleanup()

if __name__ == "__main__":
    main()
