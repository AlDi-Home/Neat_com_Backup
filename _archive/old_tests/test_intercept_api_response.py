#!/usr/bin/env python3
"""
Intercept API Response from Browser's Own Network Call

Since the browser successfully makes API calls, we'll:
1. Navigate to a folder
2. Monitor network traffic using Chrome DevTools Protocol
3. Intercept the /api/v5/entities response
4. Extract all file data from the response

This bypasses all authentication issues since we use the browser's own requests.
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import Config

def setup_driver_with_network_monitoring():
    """Setup Chrome with network capture enabled"""

    chrome_options = Options()

    # Enable performance logging
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

def extract_api_responses(driver):
    """Extract API responses from performance logs"""

    logs = driver.get_log('performance')
    api_responses = []

    for log in logs:
        try:
            message = json.loads(log['message'])
            method = message['message']['method']

            # Look for response received events
            if method == 'Network.responseReceived':
                params = message['message']['params']
                response = params['response']
                url = response['url']

                # Check if this is the entities endpoint
                if '/api/v5/entities' in url and response['status'] == 200:
                    request_id = params['requestId']

                    api_responses.append({
                        'request_id': request_id,
                        'url': url,
                        'timestamp': params['timestamp']
                    })

        except Exception as e:
            continue

    return api_responses

def get_response_body(driver, request_id):
    """Get the response body for a specific request"""

    try:
        response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
        body = response.get('body')

        if body:
            return json.loads(body)
    except Exception as e:
        print(f"Could not get response body: {e}")

    return None

def test_intercept():
    """Main test function"""

    print("\n" + "=" * 70)
    print("API Response Interception Test")
    print("=" * 70)
    print()

    # Load credentials
    config = Config()
    credentials = config.load_credentials()

    if not credentials:
        print("❌ Credentials not found")
        return

    username, password = credentials

    print("Step 1: Setting up driver with network monitoring...")
    driver = setup_driver_with_network_monitoring()
    wait = WebDriverWait(driver, 20)
    print("✅ Driver ready")
    print()

    try:
        # Enable Network domain for CDP
        driver.execute_cdp_cmd('Network.enable', {})
        print("✅ Network monitoring enabled")
        print()

        # Login
        print("Step 2: Logging in...")
        driver.get("https://app.neat.com/")
        time.sleep(3)

        # Check if already logged in
        if "files/folders" in driver.current_url:
            print("✅ Already logged in")
        else:
            # Enter credentials
            email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
            email_input.send_keys(username)

            password_input = driver.find_element(By.NAME, 'password')
            password_input.send_keys(password)

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
                print("\n⚠️  CAPTCHA detected - please solve manually")

                # Wait for redirect
                start_time = time.time()
                while time.time() - start_time < 60:
                    if "files/folders" in driver.current_url:
                        print("✅ CAPTCHA solved")
                        break
                    time.sleep(1)

            # Submit if not redirected
            if "files/folders" not in driver.current_url:
                login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                login_button.click()
                time.sleep(3)

            wait.until(EC.url_contains('files/folders'))

        print("✅ Login successful")
        print()

        # Navigate to 2013 year TAX folder
        print("Step 3: Opening folder '2013 year TAX'...")

        # Find folder
        time.sleep(2)  # Wait for page to fully load

        folder_selector = '[data-testid="mycabinet-2013yeartax"]'
        folder_elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, folder_selector)))

        # Clear old logs
        driver.get_log('performance')

        # Click folder (this will trigger API call)
        folder_elem.click()

        print("✅ Folder clicked, waiting for API response...")
        time.sleep(4)  # Give time for API call to complete

        # Extract API responses
        print()
        print("Step 4: Extracting API responses from network logs...")

        api_responses = extract_api_responses(driver)

        if not api_responses:
            print("❌ No API responses captured")
            print("This might mean:")
            print("  - Network.enable didn't work properly")
            print("  - API call happened before we started monitoring")
            print("  - Need to re-click folder to trigger API call")

            # Try clicking folder again
            print()
            print("Trying to click folder again...")
            driver.get_log('performance')  # Clear logs

            # Click folder again
            folder_elem = driver.find_element(By.CSS_SELECTOR, folder_selector)
            folder_elem.click()
            time.sleep(4)

            api_responses = extract_api_responses(driver)

        if api_responses:
            print(f"✅ Found {len(api_responses)} API response(s)")
            print()

            # Get the response body for each
            for i, resp_info in enumerate(api_responses, 1):
                print(f"API Response #{i}:")
                print(f"  URL: {resp_info['url']}")
                print(f"  Request ID: {resp_info['request_id']}")
                print()

                # Try to get the body
                body = get_response_body(driver, resp_info['request_id'])

                if body and 'entities' in body:
                    entities = body['entities']
                    print(f"  ✅ SUCCESS! Got {len(entities)} files from API")
                    print()

                    print("  Files:")
                    print("  " + "-" * 68)
                    for j, entity in enumerate(entities[:10], 1):
                        name = entity.get('name', 'N/A')
                        desc = entity.get('description', 'N/A')
                        webid = entity.get('webid')
                        print(f"  [{j:2d}] {name} - {desc}")
                        print(f"       webid: {webid}")

                    if len(entities) > 10:
                        print(f"  ... and {len(entities) - 10} more")

                    print()
                    print("=" * 70)
                    print("🎉 SUCCESS! We intercepted the API response!")
                    print("=" * 70)
                    print()
                    print("This proves we can:")
                    print("✅ Monitor browser's network traffic")
                    print("✅ Intercept API responses")
                    print("✅ Extract all file data (bypassing virtual scrolling)")
                    print()
                    print("Next: Integrate this into neat_bot.py")

                    # Save to file
                    with open('/tmp/intercepted_entities.json', 'w') as f:
                        json.dumps(entities, f, indent=2)

                    print(f"✅ Saved to /tmp/intercepted_entities.json")

                    return entities
                else:
                    print(f"  ❌ Could not get response body")
        else:
            print("❌ Still no API responses captured")
            print()
            print("Alternative: Check performance logs manually")

            # Show some logs for debugging
            logs = driver.get_log('performance')
            entities_logs = [l for l in logs if 'entities' in str(l)]
            print(f"Found {len(entities_logs)} logs mentioning 'entities'")

    finally:
        print()
        input("Press ENTER to close browser...")
        driver.quit()

if __name__ == '__main__':
    test_intercept()
