#!/usr/bin/env python3
"""
Test to detect subfolders within a parent folder
"""
import json
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import Config

def test_subfolder_detection():
    print("=" * 80)
    print("SUBFOLDER DETECTION TEST")
    print("=" * 80)
    print()

    # Load credentials
    config = Config()
    username, password = config.load_credentials()

    print(f"✓ Loaded credentials for: {username}")
    print()

    # Setup Chrome
    chrome_options = Options()
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        driver.execute_cdp_cmd('Network.enable', {})

        # Login
        print("[1/3] Logging in...")
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

        # Expand cabinet
        print("[2/3] Expanding cabinet and opening folder...")
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

        # Open 2013 year TAX folder
        folder_selector = '[data-testid="mycabinet-2013yeartax"]'
        folder = driver.find_element(By.CSS_SELECTOR, folder_selector)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", folder)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", folder)
        print("   ✓ Opened '2013 year TAX' folder")
        time.sleep(8)

        # Intercept API to get entities
        print("[3/3] Analyzing API response...")
        logs = driver.get_log('performance')

        entities = []
        folders_found = []
        checked_request_ids = set()

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
                                if 'entities' in data:
                                    entities.extend(data['entities'])
                        except:
                            pass
            except:
                pass

        print(f"   ✓ Found {len(entities)} entities total")
        print()

        # Analyze entities
        print("=" * 80)
        print("ENTITY ANALYSIS")
        print("=" * 80)

        entity_types = {}
        for entity in entities:
            etype = entity.get('type', 'unknown')
            entity_types[etype] = entity_types.get(etype, 0) + 1

        print(f"\nEntity types found:")
        for etype, count in entity_types.items():
            print(f"  {etype}: {count}")

        # Look for folders specifically
        folders = [e for e in entities if e.get('type') == 'folder']
        documents = [e for e in entities if e.get('type') == 'document']

        print(f"\nFolders (subfolders): {len(folders)}")
        for folder in folders:
            print(f"  - {folder.get('name')} (webid: {folder.get('webid')})")

        print(f"\nDocuments: {len(documents)}")
        print(f"  (showing first 5)")
        for doc in documents[:5]:
            print(f"  - {doc.get('name')}")

        # Check DOM for folder elements
        print()
        print("=" * 80)
        print("DOM FOLDER ELEMENTS")
        print("=" * 80)

        # Look for folder elements in the file list
        folder_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid*="folder"]')
        print(f"\nFound {len(folder_elements)} folder-related elements in DOM:")
        for elem in folder_elements[:10]:
            try:
                test_id = elem.get_attribute('data-testid')
                text = elem.text[:50] if elem.text else ''
                print(f"  - {test_id}: {text}")
            except:
                pass

        # Save all entity data for analysis
        output_file = "/Users/alex/NeatDebug/subfolder_entities.json"
        with open(output_file, 'w') as f:
            json.dump(entities, f, indent=2)
        print(f"\nSaved all entities to: {output_file}")

        input("\nPress Enter to close browser...")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()

if __name__ == "__main__":
    test_subfolder_detection()
