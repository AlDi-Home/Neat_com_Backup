#!/usr/bin/env python3
"""
Network traffic capture tool for Neat.com API reverse engineering

This script:
1. Opens Chrome with network logging enabled
2. Logs in to Neat.com (with CAPTCHA pause if needed)
3. Opens a specified folder
4. Captures all network requests (XHR/Fetch)
5. Exports one file and captures download requests
6. Saves all captured requests to JSON file for analysis

Usage:
    python3 capture_api_traffic.py "2013 year TAX"
"""

import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
from config import Config

def setup_driver_with_logging():
    """Setup Chrome with network logging enabled"""

    chrome_options = Options()

    # Enable performance logging to capture network traffic
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--v=1')

    # Keep browser visible for manual CAPTCHA solving
    # chrome_options.add_argument('--headless')  # Commented out for visibility

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )

    return driver

def extract_network_requests(driver):
    """Extract all network requests from performance logs"""
    logs = driver.get_log('performance')
    requests = []

    for log in logs:
        try:
            message = json.loads(log['message'])
            method = message['message']['method']

            # Capture network requests and responses
            if method == 'Network.requestWillBeSent':
                request = message['message']['params']['request']
                requests.append({
                    'type': 'request',
                    'url': request['url'],
                    'method': request['method'],
                    'headers': request.get('headers', {}),
                    'postData': request.get('postData', None),
                    'timestamp': message['message']['params']['timestamp']
                })

            elif method == 'Network.responseReceived':
                response = message['message']['params']['response']
                requests.append({
                    'type': 'response',
                    'url': response['url'],
                    'status': response['status'],
                    'headers': response.get('headers', {}),
                    'mimeType': response.get('mimeType', ''),
                    'timestamp': message['message']['params']['timestamp']
                })
        except Exception as e:
            continue

    return requests

def filter_api_requests(requests):
    """Filter for API requests (JSON, XHR, fetch)"""
    api_requests = []

    for req in requests:
        url = req.get('url', '')

        # Filter for Neat API calls
        if any(pattern in url for pattern in [
            '/api/',
            '/graphql',
            'neat.com',
            '.json'
        ]):
            # Exclude static assets
            if not any(ext in url for ext in ['.js', '.css', '.png', '.jpg', '.svg', '.woff']):
                api_requests.append(req)

    return api_requests

def capture_traffic(folder_name=None):
    """Main capture function"""

    print("\n" + "=" * 60)
    print("Neat.com API Traffic Capture")
    print("=" * 60)
    print()

    # Load config
    config = Config()
    credentials = config.load_credentials()

    if not credentials:
        print("❌ ERROR: Credentials not found")
        print("Please run the GUI first to save credentials")
        return

    email, password = credentials
    print(f"✓ Loaded credentials for: {email}")
    print()

    # Setup driver with network logging
    print("Step 1: Setting up Chrome with network logging...")
    driver = setup_driver_with_logging()
    wait = WebDriverWait(driver, 20)
    print("✓ Chrome initialized with performance logging")
    print()

    all_requests = []

    try:
        # Navigate and login
        print("Step 2: Logging in to Neat.com...")
        driver.get('https://app.neat.com/login')
        time.sleep(3)

        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")

        # Enter credentials
        print("Looking for email input...")
        email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        email_input.send_keys(email)

        password_input = driver.find_element(By.NAME, 'password')
        password_input.send_keys(password)

        print("✓ Entered credentials")

        # Check for CAPTCHA
        captcha_selectors = [
            'iframe[src*="recaptcha"]',
            'iframe[src*="hcaptcha"]',
            '[class*="captcha"]'
        ]

        captcha_detected = False
        for selector in captcha_selectors:
            if driver.find_elements(By.CSS_SELECTOR, selector):
                captcha_detected = True
                break

        if captcha_detected:
            print("\n⚠️  CAPTCHA DETECTED!")
            print("Please solve the CAPTCHA manually in the browser window.")
            print("Waiting up to 60 seconds...")

            # Wait for redirect to dashboard
            start_time = time.time()
            while time.time() - start_time < 60:
                if "files/folders" in driver.current_url:
                    print("✓ CAPTCHA solved, redirected to dashboard")
                    break
                time.sleep(1)

        # Submit login if not already on dashboard
        if "files/folders" not in driver.current_url:
            login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            time.sleep(3)

        # Wait for dashboard
        wait.until(EC.url_contains('files/folders'))
        print("✓ Login successful")
        print()

        # Capture requests after login
        login_requests = extract_network_requests(driver)
        all_requests.extend(login_requests)
        print(f"✓ Captured {len(login_requests)} requests during login")
        print()

        # Navigate to folders
        print("Step 3: Opening folder...")

        # Find cabinet
        cabinet = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[data-testid="cabinet-item"]')
        ))

        # Check if cabinet is expanded
        is_expanded = cabinet.get_attribute('aria-expanded') == 'true'
        if not is_expanded:
            cabinet.click()
            time.sleep(1)

        # Find the folder
        folder_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="folder-item"]')
        folder_found = False

        for folder_elem in folder_elements:
            name_elem = folder_elem.find_element(By.CSS_SELECTOR, '.nui-text')
            folder_text = name_elem.text.strip()

            if folder_name and folder_text == folder_name:
                print(f"✓ Found folder: {folder_text}")
                folder_elem.click()
                time.sleep(3)
                folder_found = True
                break

        if not folder_found:
            print(f"❌ Folder '{folder_name}' not found")
            return

        # Capture folder listing requests
        folder_requests = extract_network_requests(driver)
        all_requests.extend(folder_requests)
        print(f"✓ Captured {len(folder_requests)} requests for folder listing")
        print()

        # Set pagination to 100
        print("Step 4: Setting pagination to 100...")
        try:
            pagination_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-testid="pagination-button"]')
            ))
            pagination_btn.click()
            time.sleep(1)

            # Click 100 option
            option_100 = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[text()='100' and not(contains(@class, 'nui-button'))]")
            ))
            option_100.click()
            time.sleep(2)

            print("✓ Set pagination to 100")

            # Capture pagination requests
            pagination_requests = extract_network_requests(driver)
            all_requests.extend(pagination_requests)
            print(f"✓ Captured {len(pagination_requests)} requests for pagination")
        except Exception as e:
            print(f"⚠️  Could not change pagination: {e}")
        print()

        # Try to export one file
        print("Step 5: Exporting one file to capture download API...")
        try:
            # Find first checkbox
            checkbox = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'input[id^="checkbox-"]:not(#header-checkbox)')
            ))

            # Click it
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", checkbox)
            time.sleep(1)
            print("✓ Selected first file")

            # Click Export button
            export_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-testid="export-button"]')
            ))
            export_btn.click()
            time.sleep(1)
            print("✓ Clicked Export button")

            # Click PDF export option
            pdf_option = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(), 'Image as PDF')]")
            ))
            pdf_option.click()
            time.sleep(2)
            print("✓ Clicked PDF export option")

            # Capture export requests
            export_requests = extract_network_requests(driver)
            all_requests.extend(export_requests)
            print(f"✓ Captured {len(export_requests)} requests for file export")
        except Exception as e:
            print(f"⚠️  Could not export file: {e}")
        print()

        # Wait a bit for any async requests
        print("Waiting 5 seconds for any async requests...")
        time.sleep(5)

        # Final capture
        final_requests = extract_network_requests(driver)
        all_requests.extend(final_requests)

    finally:
        driver.quit()
        print("✓ Browser closed")
        print()

    # Filter for API requests only
    print("Step 6: Analyzing captured traffic...")
    api_requests = filter_api_requests(all_requests)

    # Save to file
    output_file = '/tmp/neat_api_traffic.json'
    with open(output_file, 'w') as f:
        json.dump(api_requests, f, indent=2)

    print(f"✓ Captured {len(all_requests)} total requests")
    print(f"✓ Filtered to {len(api_requests)} API requests")
    print(f"✓ Saved to: {output_file}")
    print()

    # Print summary of unique endpoints
    print("=" * 60)
    print("API Endpoints Discovered:")
    print("=" * 60)

    unique_urls = set()
    for req in api_requests:
        if req['type'] == 'request':
            # Remove query params for cleaner view
            url = req['url'].split('?')[0]
            unique_urls.add(url)

    for url in sorted(unique_urls):
        print(f"  {url}")

    print()
    print(f"Total unique endpoints: {len(unique_urls)}")
    print()

    return api_requests

if __name__ == '__main__':
    import sys

    folder_name = "2013 year TAX"
    if len(sys.argv) > 1:
        folder_name = sys.argv[1]

    print(f"\nCapturing API traffic for folder: {folder_name}\n")

    try:
        capture_traffic(folder_name)
        print("=" * 60)
        print("✓ Capture complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Review /tmp/neat_api_traffic.json")
        print("2. Identify endpoints for:")
        print("   - Listing folder contents (all files, not just 12)")
        print("   - Downloading individual files")
        print("3. Test direct API calls with captured auth tokens")
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
