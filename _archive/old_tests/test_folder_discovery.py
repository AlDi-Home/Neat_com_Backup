#!/usr/bin/env python3
"""Test folder discovery to see why only one folder is found"""
import sys
from neat_bot import NeatBot
from config import Config

def test_folder_discovery():
    """Test folder discovery"""
    config = Config()
    bot = NeatBot(config)

    # Get credentials
    creds = config.load_credentials()
    if not creds:
        print("ERROR: No saved credentials found")
        sys.exit(1)

    username, password = creds
    print(f"Using username: {username}")

    try:
        # Setup and login
        print("\n=== Setting up browser ===")
        bot.setup_driver()

        print("\n=== Logging in ===")
        if not bot.login(username, password):
            print("ERROR: Login failed")
            sys.exit(1)

        print("\n=== Getting folders ===")
        folders = bot.get_folders()

        print(f"\n=== Found {len(folders)} folders ===")
        for i, (folder_name, selector, elem) in enumerate(folders, 1):
            print(f"{i}. {folder_name}")
            print(f"   Selector: {selector}")
            print(f"   Element visible: {elem.is_displayed()}")

        if len(folders) == 0:
            print("\nNo folders found! Checking cabinet state...")

            # Try to find cabinet element
            from selenium.webdriver.common.by import By
            cabinet = bot.driver.find_element(By.CSS_SELECTOR, '[data-testid="sidebar-item-mycabinet"]')
            print(f"Cabinet found: {cabinet is not None}")
            print(f"Cabinet classes: {cabinet.get_attribute('class')}")

            # Check all elements with mycabinet prefix
            all_elements = bot.driver.find_elements(By.CSS_SELECTOR, '[data-testid^="mycabinet"]')
            print(f"\nAll elements with 'mycabinet' prefix: {len(all_elements)}")
            for elem in all_elements[:10]:  # Show first 10
                test_id = elem.get_attribute('data-testid')
                print(f"  - {test_id}")
                try:
                    span = elem.find_element(By.CSS_SELECTOR, 'span[title]')
                    title = span.get_attribute('title')
                    print(f"    Title: {title}")
                except:
                    print(f"    No title found")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n=== Cleaning up ===")
        bot.cleanup()

if __name__ == "__main__":
    test_folder_discovery()
