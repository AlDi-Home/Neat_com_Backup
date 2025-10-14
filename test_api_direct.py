#!/usr/bin/env python3
"""
Proof of Concept: Direct Neat.com API calls

Tests direct API access to bypass virtual scrolling limitation.

Key Discovery:
- POST /api/v5/entities returns ALL files (23/23) not just 12
- Uses x-neat-account-id header for authentication
- Supports page_size parameter up to 100

Usage:
    python3 test_api_direct.py
"""

import json
import requests
from neat_bot import NeatBot
from config import Config

def extract_session_data(driver):
    """Extract authentication data from Selenium session"""

    # Get cookies
    cookies = {}
    for cookie in driver.get_cookies():
        cookies[cookie['name']] = cookie['value']

    print(f"   Cookies found: {list(cookies.keys())}")

    # Get account ID and token from localStorage
    storage_data = driver.execute_script("""
        const data = {};

        // Get all localStorage items
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            data[key] = localStorage.getItem(key);
        }

        // Also check sessionStorage
        data._sessionStorage = {};
        for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            data._sessionStorage[key] = sessionStorage.getItem(key);
        }

        return data;
    """)

    print(f"   LocalStorage keys: {list(storage_data.keys())}")

    # Look for account ID and tokens
    account_id = None
    oauth_token = None
    jwt_token = None

    # Check specific keys first
    if 'neat::global::account' in storage_data:
        try:
            account_data = json.loads(storage_data['neat::global::account'])
            if isinstance(account_data, dict) and 'id' in account_data:
                account_id = account_data['id']
        except:
            pass

    if 'neat::global::token' in storage_data:
        oauth_token = storage_data['neat::global::token']

    if 'neat::global::jwt' in storage_data:
        jwt_token = storage_data['neat::global::jwt']

    # Fallback: search all keys
    if not account_id or not oauth_token:
        for key, value in storage_data.items():
            if key == '_sessionStorage':
                continue

            # Try to parse JSON values
            if value and ('{' in value or '[' in value):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, dict):
                        if not account_id and 'id' in parsed:
                            account_id = parsed['id']
                        if not oauth_token and 'token' in parsed:
                            oauth_token = parsed['token']
                except:
                    pass

            # Check plain values
            if not account_id and 'account' in key.lower():
                account_id = value

            if not oauth_token and 'token' in key.lower():
                oauth_token = value

    return {
        'cookies': cookies,
        'account_id': account_id,
        'oauth_token': oauth_token,
        'jwt_token': jwt_token,
        'storage_data': storage_data
    }

def test_entities_api(account_id, cookies, parent_id, oauth_token=None):
    """Test the /api/v5/entities endpoint"""

    print("\n" + "=" * 70)
    print("Testing POST /api/v5/entities")
    print("=" * 70)
    print()

    url = "https://api.neat.com/api/v5/entities"

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://app.neat.com',
        'referer': 'https://app.neat.com/',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    # Add authentication headers if available
    if account_id:
        headers['x-neat-account-id'] = account_id

    if oauth_token:
        headers['Authorization'] = f'Bearer {oauth_token}'

    payload = {
        "filters": [
            {
                "parent_id": parent_id
            },
            {
                "type": "$all_item_types"
            }
        ],
        "page": 1,
        "page_size": "100",
        "sort_by": [
            [
                "created_at",
                "desc"
            ]
        ],
        "utc_offset": -4
    }

    print(f"URL: {url}")
    print(f"Account ID: {account_id}")
    print(f"Parent ID (Folder): {parent_id}")
    print()

    print("Making request...")
    print(f"Headers: {headers}")
    print(f"Using cookies: {cookies}")
    print()

    try:
        # Use a session to properly handle cookies
        session = requests.Session()

        # Set cookies on session
        for name, value in cookies.items():
            session.cookies.set(name, value, domain='.neat.com')

        response = session.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            data = response.json()

            if 'entities' in data:
                entities = data['entities']
                print(f"✅ SUCCESS! Received {len(entities)} files")
                print()

                print("Files:")
                print("-" * 70)
                for i, entity in enumerate(entities, 1):
                    name = entity.get('name', 'N/A')
                    desc = entity.get('description', 'N/A')
                    webid = entity.get('webid')
                    entity_type = entity.get('type')

                    print(f"[{i:2d}] {name}")
                    print(f"     Description: {desc}")
                    print(f"     WebID: {webid}")
                    print(f"     Type: {entity_type}")
                    print()

                return entities
            else:
                print("❌ No 'entities' field in response")
                print(json.dumps(data, indent=2)[:500])
        else:
            print(f"❌ ERROR: Status {response.status_code}")
            print(response.text[:500])

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    return None

def test_download_api(account_id, cookies, item_webid):
    """Test the download endpoint"""

    print("\n" + "=" * 70)
    print(f"Testing Download for WebID: {item_webid}")
    print("=" * 70)
    print()

    # First, we need to get a download token
    # Based on HAR file, there should be a way to get download URL

    print("Note: Download requires token generation first")
    print("Need to capture the download initiation request")
    print()

    return None

def main():
    """Main test function"""

    print("\n" + "=" * 70)
    print("Neat.com Direct API Test")
    print("=" * 70)
    print()

    # Load config and login
    config = Config()
    credentials = config.load_credentials()

    if not credentials:
        print("❌ Credentials not found")
        return

    username, password = credentials

    print("Step 1: Login via Selenium to get session data...")
    bot = NeatBot(config, lambda msg, level="info": None)
    bot.setup_driver()

    if not bot.login(username, password):
        print("❌ Login failed")
        return

    print("✅ Login successful")
    print()

    # Extract session data
    print("Step 2: Extracting session data...")
    session_data = extract_session_data(bot.driver)

    account_id = session_data['account_id']
    oauth_token = session_data['oauth_token']
    jwt_token = session_data['jwt_token']
    cookies = session_data['cookies']

    print(f"   Account ID: {account_id}")
    print(f"   OAuth Token: {oauth_token[:50] if oauth_token else None}...")
    print(f"   JWT Token: {jwt_token[:50] if jwt_token else None}...")
    print(f"   Cookies: {len(cookies)} cookies extracted")

    if not account_id:
        print("\n⚠️  Account ID not found in localStorage")
        print("   Dumping storage data for analysis:")
        for key, value in session_data['storage_data'].items():
            if key != '_sessionStorage':
                print(f"   {key}: {str(value)[:100]}...")

    if not oauth_token:
        print("\n⚠️  OAuth token not found")

    print()

    # Get folder ID for "2013 year TAX"
    print("Step 3: Getting folder information...")
    folders = bot.get_folders()

    target_folder = None
    for folder_path, folder_selector in folders:
        if folder_path == "2013 year TAX":
            target_folder = (folder_path, folder_selector)
            break

    if not target_folder:
        print("❌ Folder '2013 year TAX' not found")
        bot.driver.quit()
        return

    print(f"✅ Found folder: {target_folder[0]}")
    print()

    # We need to extract the parent_id from the folder
    # Let's navigate to the folder and capture the API call
    print("Step 4: Opening folder to capture parent_id...")

    from selenium.webdriver.common.by import By
    folder_selector = target_folder[1]
    folder_elem = bot.driver.find_element(By.CSS_SELECTOR, folder_selector)
    folder_elem.click()

    import time
    time.sleep(3)

    # Try to extract parent_id from page
    parent_id = bot.driver.execute_script("""
        // Try to find parent_id in page context
        // It might be in the URL, or in React state, or in API calls

        // Check URL
        const url = window.location.href;
        const match = url.match(/folders?\\/([a-f0-9]+)/i);
        if (match) return match[1];

        return null;
    """)

    # Alternative: Extract from data attributes
    if not parent_id:
        try:
            # The folder selector might contain the ID
            # Format: [data-testid="mycabinet-2013yeartax"]
            # The actual parent_id is stored differently

            # Try to find it in the page source
            page_source = bot.driver.page_source

            # Look for parent_id in API calls or data attributes
            import re
            matches = re.findall(r'"parent_id":\s*"([a-f0-9]+)"', page_source)
            if matches:
                parent_id = matches[0]
                print(f"✅ Found parent_id in page source: {parent_id}")
        except:
            pass

    if not parent_id:
        # Hardcode from HAR file for this test
        parent_id = "5342fbc2d94877f18f000076"  # From captured HAR
        print(f"⚠️  Using hardcoded parent_id from HAR file: {parent_id}")

    print()

    # Keep browser open for cookie session
    print("Step 5: Testing direct API call...")

    # Try JWT token first, fallback to oauth_token
    auth_token = jwt_token if jwt_token else oauth_token

    entities = test_entities_api(account_id, cookies, parent_id, auth_token)

    if entities:
        print("\n" + "=" * 70)
        print("✅ API TEST SUCCESSFUL!")
        print("=" * 70)
        print()
        print(f"Retrieved {len(entities)} files via direct API")
        print("This bypasses the virtual scrolling limitation!")
        print()

        # Test download for first file
        if len(entities) > 0:
            first_file = entities[0]
            test_download_api(account_id, cookies, first_file['webid'])

    # Close browser
    print("\nClosing browser...")
    bot.driver.quit()
    print("✅ Done!")

if __name__ == '__main__':
    main()
