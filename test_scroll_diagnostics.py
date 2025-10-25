#!/usr/bin/env python3
"""
Enhanced diagnostic script to analyze virtual scrolling behavior
and checkpoint loading in Neat.com

This will help us understand:
- How many items the API returns
- How many checkboxes are actually loaded in DOM
- What scrolling strategy works best
- Where checkboxes are being lost
"""
import json
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from config import Config

def diagnose_scrolling(folder_name):
    """Run comprehensive scrolling diagnostics"""

    print("=" * 80)
    print("VIRTUAL SCROLLING DIAGNOSTIC TOOL")
    print("=" * 80)
    print()

    # Load credentials
    config = Config()
    username, password = config.load_credentials()

    if not username or not password:
        print("❌ No saved credentials found!")
        sys.exit(1)

    print(f"✓ Loaded credentials for: {username}")
    print(f"✓ Target folder: {folder_name}")
    print()

    # Create debug output directory
    debug_dir = Path.home() / "NeatDebug" / "scroll_diagnostics"
    debug_dir.mkdir(parents=True, exist_ok=True)
    print(f"Debug files will be saved to: {debug_dir}")
    print()

    # Setup Chrome with performance logging
    print("[1/8] Setting up Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        # Enable CDP
        driver.execute_cdp_cmd('Network.enable', {})

        # Login
        print("[2/8] Logging in...")
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
        print("[3/8] Expanding cabinet...")
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

        # Find and click folder
        print(f"[4/8] Opening folder: {folder_name}...")
        # Use CSS selector like the main code does
        folder_selector = f'[data-testid="mycabinet-{folder_name.lower().replace(" ", "").replace("\'", "")}"]'
        print(f"   Using selector: {folder_selector}")

        try:
            folder = driver.find_element(By.CSS_SELECTOR, folder_selector)
        except:
            # Fallback: try finding by text
            folder_xpath = f"//*[contains(text(), '{folder_name}')]"
            folder = driver.find_element(By.XPATH, folder_xpath)

        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", folder)
        time.sleep(0.5)

        # Click folder
        driver.execute_script("arguments[0].click();", folder)
        print("   ✓ Clicked folder, waiting for page to fully load...")
        time.sleep(8)  # Give more time for initial load

        # Intercept API to get total file count
        print("[5/8] Intercepting API response...")
        print("   (Checking performance logs collected since clicking folder...)")
        entities = []
        checked_request_ids = set()
        all_responses = []

        # Get all performance logs (includes everything since we last cleared or started)
        logs = driver.get_log('performance')
        print(f"   Got {len(logs)} performance log entries total")

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
                        print(f"   Found /api/v5/entities response (request: {request_id[:20]}...)")

                        try:
                            response_body = driver.execute_cdp_cmd(
                                'Network.getResponseBody',
                                {'requestId': request_id}
                            )

                            body_text = response_body.get('body')
                            if body_text:
                                data = json.loads(body_text)

                                if 'entities' in data and len(data['entities']) > 0:
                                    print(f"      Response has {len(data['entities'])} entities")
                                    all_responses.append(data['entities'])
                        except Exception as e:
                            print(f"      Could not get response body: {e}")
            except:
                pass

        if all_responses:
            entities = max(all_responses, key=len)
            print(f"   ✓ API returned {len(entities)} files")

            # Save API data
            api_data_file = debug_dir / "api_entities.json"
            with open(api_data_file, 'w') as f:
                json.dump(entities, f, indent=2)
            print(f"   ✓ Saved API data to: {api_data_file}")
        else:
            print("   ❌ No API response captured!")
            return

        total_files = len(entities)
        print()
        print(f"API ANALYSIS:")
        print(f"  Total files from API: {total_files}")
        print(f"  File webids: {[e.get('webid') for e in entities[:5]]}... (showing first 5)")
        print()

        # Initial DOM state
        print("[6/8] Analyzing initial DOM state...")
        checkboxes = driver.find_elements(
            By.CSS_SELECTOR,
            'input[id^="checkbox-"]:not(#header-checkbox)'
        )
        initial_count = len(checkboxes)
        print(f"   Checkboxes initially loaded: {initial_count}/{total_files}")
        driver.save_screenshot(str(debug_dir / "00_initial_state.png"))

        # Find scrollable container
        print("[7/8] Finding scrollable container...")
        file_list_container = None
        scroll_info = []

        selectors = [
            '[data-testid="file-list"]',
            '[role="list"]',
            '.file-list',
            '.files-container',
            '[class*="FileList"]',
            '[class*="VirtualScroll"]',
            'main',
        ]

        for selector in selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                scroll_height = driver.execute_script("return arguments[0].scrollHeight;", element)
                client_height = driver.execute_script("return arguments[0].clientHeight;", element)
                overflow_y = driver.execute_script("return window.getComputedStyle(arguments[0]).overflowY;", element)

                scroll_info.append({
                    'selector': selector,
                    'scrollHeight': scroll_height,
                    'clientHeight': client_height,
                    'overflowY': overflow_y,
                    'scrollable': scroll_height > client_height
                })

                if scroll_height > client_height:
                    file_list_container = element
                    print(f"   ✓ Found scrollable container: {selector}")
                    print(f"      scrollHeight: {scroll_height}, clientHeight: {client_height}")
                    break
            except:
                continue

        if not file_list_container:
            file_list_container = driver.find_element(By.TAG_NAME, 'body')
            print(f"   Using body as fallback")

        # Save scroll container info
        with open(debug_dir / "scroll_containers.json", 'w') as f:
            json.dump(scroll_info, f, indent=2)

        # Test different scrolling strategies
        print()
        print("[8/8] Testing scrolling strategies...")
        print()

        scroll_log = []

        # Strategy 1: Incremental scrollTop
        print("STRATEGY 1: Incremental scrollTop (500px increments)")
        print("-" * 60)
        max_loaded = initial_count
        scroll_attempts = 0
        max_attempts = 50

        while scroll_attempts < max_attempts:
            checkboxes = driver.find_elements(
                By.CSS_SELECTOR,
                'input[id^="checkbox-"]:not(#header-checkbox)'
            )
            current_count = len(checkboxes)

            if current_count >= total_files:
                print(f"✓ SUCCESS: All {total_files} checkboxes loaded after {scroll_attempts} scrolls!")
                driver.save_screenshot(str(debug_dir / f"strategy1_success_{scroll_attempts}.png"))
                break

            if current_count > max_loaded:
                max_loaded = current_count
                print(f"  Scroll {scroll_attempts}: Loaded {current_count}/{total_files} checkboxes (+{current_count - (scroll_log[-1]['count'] if scroll_log else initial_count)})")
                driver.save_screenshot(str(debug_dir / f"strategy1_scroll_{scroll_attempts}.png"))

            scroll_log.append({
                'attempt': scroll_attempts,
                'strategy': 'scrollTop+500',
                'count': current_count
            })

            # Scroll
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollTop + 500;",
                file_list_container
            )
            time.sleep(0.8)

            scroll_attempts += 1

        final_checkboxes = driver.find_elements(
            By.CSS_SELECTOR,
            'input[id^="checkbox-"]:not(#header-checkbox)'
        )
        final_count = len(final_checkboxes)

        print()
        print("=" * 80)
        print("DIAGNOSTIC RESULTS")
        print("=" * 80)
        print()
        print(f"API returned: {total_files} files")
        print(f"Initially loaded: {initial_count} checkboxes")
        print(f"After scrolling: {final_count} checkboxes")
        print(f"Missing: {total_files - final_count} checkboxes")
        print()

        if final_count < total_files:
            print("⚠️  NOT ALL CHECKBOXES LOADED")
            print()
            print("Missing file webids:")
            loaded_webids = set()
            for cb in final_checkboxes:
                cb_id = cb.get_attribute('id')
                if cb_id:
                    webid = cb_id.replace('checkbox-', '')
                    loaded_webids.add(webid)

            missing_webids = []
            for entity in entities:
                if entity.get('webid') not in loaded_webids:
                    missing_webids.append({
                        'webid': entity.get('webid'),
                        'name': entity.get('name'),
                        'description': entity.get('description', '')
                    })

            for idx, missing in enumerate(missing_webids[:10], 1):
                print(f"  {idx}. {missing['name']} (webid: {missing['webid']})")

            if len(missing_webids) > 10:
                print(f"  ... and {len(missing_webids) - 10} more")

            # Save missing files
            with open(debug_dir / "missing_files.json", 'w') as f:
                json.dump(missing_webids, f, indent=2)
        else:
            print("✓ ALL CHECKBOXES SUCCESSFULLY LOADED!")

        print()
        print("=" * 80)
        print(f"All diagnostic data saved to: {debug_dir}")
        print("=" * 80)

        # Save scroll log
        with open(debug_dir / "scroll_log.json", 'w') as f:
            json.dump(scroll_log, f, indent=2)

        # Save summary
        summary = {
            'folder_name': folder_name,
            'api_total': total_files,
            'initial_loaded': initial_count,
            'final_loaded': final_count,
            'missing_count': total_files - final_count,
            'scroll_attempts': scroll_attempts,
            'success': final_count >= total_files
        }

        with open(debug_dir / "summary.json", 'w') as f:
            json.dump(summary, f, indent=2)

        print()
        input("Press Enter to close browser and exit...")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

        try:
            driver.save_screenshot(str(debug_dir / "error_screenshot.png"))
        except:
            pass

    finally:
        driver.quit()
        print("\nBrowser closed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_scroll_diagnostics.py \"Folder Name\"")
        print("Example: python3 test_scroll_diagnostics.py \"Year 2013 TAX\"")
        sys.exit(1)

    diagnose_scrolling(sys.argv[1])
