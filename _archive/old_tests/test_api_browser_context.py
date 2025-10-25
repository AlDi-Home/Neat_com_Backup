#!/usr/bin/env python3
"""
Test API calls from within authenticated browser context

Instead of trying to replicate authentication externally,
make API calls directly from JavaScript in the authenticated browser session.
"""

import json
import time
from neat_bot import NeatBot
from config import Config

def test_api_in_browser():
    """Test API call from within browser context"""

    print("\n" + "=" * 70)
    print("Neat.com API Test (Browser Context)")
    print("=" * 70)
    print()

    # Load config and login
    config = Config()
    credentials = config.load_credentials()

    if not credentials:
        print("❌ Credentials not found")
        return

    username, password = credentials

    print("Step 1: Login via Selenium...")
    bot = NeatBot(config, lambda msg, level="info": print(msg))
    bot.setup_driver()

    if not bot.login(username, password):
        print("❌ Login failed")
        return

    print("✅ Login successful\n")

    # Navigate to 2013 year TAX folder
    print("Step 2: Opening folder...")
    folders = bot.get_folders()

    target_folder = None
    parent_id = None

    for folder_path, folder_selector in folders:
        if folder_path == "2013 year TAX":
            target_folder = (folder_path, folder_selector)
            break

    if not target_folder:
        print("❌ Folder not found")
        bot.driver.quit()
        return

    # Open the folder
    from selenium.webdriver.common.by import By
    folder_elem = bot.driver.find_element(By.CSS_SELECTOR, target_folder[1])
    folder_elem.click()
    time.sleep(3)

    print(f"✅ Opened folder: {target_folder[0]}\n")

    # Now make API call from JavaScript
    print("Step 3: Making API call from browser JavaScript...")

    # Check current URL
    current_url = bot.driver.current_url
    print(f"Current URL: {current_url}")
    print()

    # Hardcoded parent_id from HAR file
    parent_id = "5342fbc2d94877f18f000076"

    result = bot.driver.execute_async_script("""
        const parentId = arguments[0];
        const callback = arguments[1];  // Selenium async callback

        const xhr = new XMLHttpRequest();
        xhr.open('POST', 'https://api.neat.com/api/v5/entities', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.withCredentials = true;  // Include cookies

        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const data = JSON.parse(xhr.responseText);
                    callback({
                        success: true,
                        status: xhr.status,
                        data: data
                    });
                } catch (e) {
                    callback({
                        success: false,
                        error: 'JSON parse error: ' + e.toString(),
                        responseText: xhr.responseText
                    });
                }
            } else {
                callback({
                    success: false,
                    status: xhr.status,
                    error: 'HTTP ' + xhr.status,
                    responseText: xhr.responseText
                });
            }
        };

        xhr.onerror = function() {
            callback({
                success: false,
                error: 'Network error'
            });
        };

        const payload = JSON.stringify({
            filters: [
                { parent_id: parentId },
                { type: "$all_item_types" }
            ],
            page: 1,
            page_size: "100",
            sort_by: [["created_at", "desc"]],
            utc_offset: -4
        });

        xhr.send(payload);
    """, parent_id)

    print(f"API call result:")
    print(json.dumps(result, indent=2)[:1000])
    print()

    if result.get('success') and 'data' in result:
        data = result['data']

        if 'entities' in data:
            entities = data['entities']
            print(f"✅ SUCCESS! Received {len(entities)} files from API")
            print()

            print("Files:")
            print("-" * 70)
            for i, entity in enumerate(entities[:10], 1):
                name = entity.get('name', 'N/A')
                desc = entity.get('description', 'N/A')
                print(f"[{i:2d}] {name} - {desc}")

            if len(entities) > 10:
                print(f"... and {len(entities) - 10} more")

            print()
            print("=" * 70)
            print("🎉 API METHOD WORKS!")
            print("=" * 70)
            print()
            print("Key Discovery:")
            print("- Browser context has automatic authentication")
            print("- We can use fetch() from JavaScript in Selenium")
            print("- This bypasses virtual scrolling entirely!")
            print()
            print("Next Step: Integrate this into neat_bot.py")

            # Save sample
            with open('/tmp/neat_api_success.json', 'w') as f:
                json.dump(entities, f, indent=2)

            print(f"✓ Sample data saved to /tmp/neat_api_success.json")

            return entities

    else:
        print(f"❌ API call failed: {result}")

    bot.driver.quit()

if __name__ == '__main__':
    test_api_in_browser()
