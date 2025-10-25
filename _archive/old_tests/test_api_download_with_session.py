#!/usr/bin/env python3
"""
Test direct API download using Selenium session cookies
"""
import json
import sys
import time
import requests
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import Config

def test_api_download_with_session():
    """Test downloading via API using browser session"""

    print("=" * 80)
    print("API DOWNLOAD TEST WITH BROWSER SESSION")
    print("=" * 80)
    print()

    # Load credentials
    config = Config()
    username, password = config.load_credentials()

    if not username or not password:
        print("❌ No saved credentials found!")
        sys.exit(1)

    print(f"✓ Loaded credentials for: {username}")
    print()

    # Setup Chrome with performance logging
    print("[1/6] Setting up Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        # Enable CDP
        driver.execute_cdp_cmd('Network.enable', {})

        # Login
        print("[2/6] Logging in...")
        driver.get("https://app.neat.com/")
        time.sleep(3)

        if "files/folders" not in driver.current_url:
            username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"], input[name="username"]'))
            )
            username_field.send_keys(username)

            password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password_field.send_keys(password)

            login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()

            wait.until(lambda d: "files/folders" in d.current_url)
            time.sleep(3)

        print("   ✓ Login successful")

        # Expand cabinet and open folder
        print("[3/6] Opening 2013 year TAX folder...")
        cabinet = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="sidebar-item-mycabinet"]'))
        )

        cabinet_classes = cabinet.get_attribute('class') or ''
        if 'is-open' not in cabinet_classes:
            try:
                toggle_button = cabinet.find_element(By.CSS_SELECTOR, '[data-testid="toggle-folder-open"]')
                toggle_button.click()
            except:
                cabinet.click()
            time.sleep(2)

        # Open folder
        folder_selector = '[data-testid="mycabinet-2013yeartax"]'
        folder = driver.find_element(By.CSS_SELECTOR, folder_selector)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", folder)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", folder)
        print("   ✓ Clicked folder, waiting for page to load...")
        time.sleep(8)

        # Intercept API to get entities
        print("[4/6] Intercepting API response...")
        logs = driver.get_log('performance')
        print(f"   Got {len(logs)} performance log entries")

        entities = []
        checked_request_ids = set()
        all_responses = []

        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message['message']['method']

                if method == 'Network.responseReceived':
                    params = message['message']['params']
                    response = params['response']
                    url = response['url']

                    if '/api/v5/entities' in url and response['status'] == 200:
                        request_id = params['requestId']

                        if request_id in checked_request_ids:
                            continue

                        checked_request_ids.add(request_id)

                        try:
                            response_body = driver.execute_cdp_cmd(
                                'Network.getResponseBody',
                                {'requestId': request_id}
                            )

                            body_text = response_body.get('body')
                            if body_text:
                                data = json.loads(body_text)

                                if 'entities' in data and len(data['entities']) > 0:
                                    all_responses.append(data['entities'])
                        except:
                            pass
            except:
                pass

        if all_responses:
            entities = max(all_responses, key=len)
            print(f"   ✓ Got {len(entities)} entities from API")
        else:
            print("   ❌ No entities found")
            return

        # Get browser cookies for requests session
        print("[5/6] Extracting browser session cookies...")
        cookies = driver.get_cookies()
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))

        print(f"   ✓ Extracted {len(cookies)} cookies")

        # Try downloading first file
        print("[6/6] Testing download...")
        test_entity = entities[0]
        print(f"   File: {test_entity['name']} - {test_entity['description']}")
        print(f"   Webid: {test_entity['webid']}")

        download_url = test_entity['download_url']
        print(f"   URL: {download_url[:80]}...")

        # Make download request with session cookies
        response = session.get(download_url, allow_redirects=True, timeout=30)

        print(f"   Response status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"   Content-Length: {response.headers.get('content-length', 'unknown')}")

        if response.status_code == 200:
            output_dir = Path.home() / "NeatDebug" / "api_downloads"
            output_dir.mkdir(parents=True, exist_ok=True)

            safe_name = f"{test_entity['name']} - {test_entity['description']}".replace('/', '-')
            output_file = output_dir / f"{safe_name}.pdf"

            with open(output_file, 'wb') as f:
                f.write(response.content)

            file_size = output_file.stat().st_size
            print()
            print(f"✅ SUCCESS! Downloaded {file_size:,} bytes")
            print(f"   Saved to: {output_file}")

            # Test download all files
            print()
            print("=" * 80)
            print(f"Attempting to download ALL {len(entities)} files...")
            print("=" * 80)

            success_count = 0
            fail_count = 0

            for idx, entity in enumerate(entities, 1):
                name = entity['name']
                desc = entity['description']
                download_url = entity['download_url']

                print(f"[{idx}/{len(entities)}] {name} - {desc}...", end=' ')

                try:
                    response = session.get(download_url, allow_redirects=True, timeout=30)

                    if response.status_code == 200:
                        safe_name = f"{name} - {desc}".replace('/', '-')
                        output_file = output_dir / f"{safe_name}.pdf"

                        with open(output_file, 'wb') as f:
                            f.write(response.content)

                        file_size = output_file.stat().st_size
                        print(f"✅ ({file_size:,} bytes)")
                        success_count += 1
                    else:
                        print(f"❌ HTTP {response.status_code}")
                        fail_count += 1
                except Exception as e:
                    print(f"❌ {e}")
                    fail_count += 1

                time.sleep(0.5)  # Small delay between requests

            print()
            print("=" * 80)
            print(f"DOWNLOAD COMPLETE: {success_count}/{len(entities)} successful")
            print("=" * 80)

        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print("\nBrowser closed.")

if __name__ == "__main__":
    test_api_download_with_session()
