#!/usr/bin/env python3
"""
API traffic capture using Chrome DevTools Protocol (CDP)

Uses Selenium 4's CDP support to capture network traffic in real-time
"""

import json
import time
from pathlib import Path
from neat_bot import NeatBot
from config import Config

def capture_with_cdp(folder_name="2013 year TAX"):
    """Capture API traffic using NeatBot with CDP"""

    print("\n" + "=" * 60)
    print("Neat.com API Traffic Capture (CDP Method)")
    print("=" * 60)
    print()

    config = Config()
    captured_requests = []

    # Load credentials
    credentials = config.load_credentials()
    if not credentials:
        print("❌ Credentials not found")
        return

    username, password = credentials

    # Custom callback to capture requests
    def status_callback(message, level="info"):
        print(message)

    print("Step 1: Initializing NeatBot...")
    bot = NeatBot(config, status_callback)
    bot.setup_driver()
    print("✓ Driver initialized")
    print()

    try:
        print("Step 2: Logging in...")
        if not bot.login(username, password):
            print("❌ Login failed")
            return

        print("✓ Login successful")
        print()

        # Enable Network domain in CDP
        print("Step 3: Enabling CDP Network monitoring...")
        bot.driver.execute_cdp_cmd('Network.enable', {})
        print("✓ Network monitoring enabled")
        print()

        # Set up network event listeners
        def request_interceptor(request):
            """Capture outgoing requests"""
            captured_requests.append({
                'type': 'request',
                'requestId': request.get('requestId'),
                'url': request.get('request', {}).get('url'),
                'method': request.get('request', {}).get('method'),
                'headers': request.get('request', {}).get('headers', {}),
                'postData': request.get('request', {}).get('postData'),
                'timestamp': request.get('timestamp')
            })

        def response_interceptor(response):
            """Capture responses"""
            captured_requests.append({
                'type': 'response',
                'requestId': response.get('requestId'),
                'url': response.get('response', {}).get('url'),
                'status': response.get('response', {}).get('status'),
                'headers': response.get('response', {}).get('headers', {}),
                'mimeType': response.get('response', {}).get('mimeType'),
                'timestamp': response.get('timestamp')
            })

        # Unfortunately, Selenium doesn't support CDP event listeners easily
        # We'll use a different approach - check devtools logs periodically

        print("Step 4: Getting folders...")
        folders = bot.get_folders()
        print(f"✓ Found {len(folders)} folders")
        print()

        # Find target folder
        target_folder = None
        for folder_path, folder_sel in folders:
            if folder_path == folder_name:
                target_folder = (folder_path, folder_sel)
                break

        if not target_folder:
            print(f"❌ Folder '{folder_name}' not found")
            return

        print(f"Step 5: Opening folder '{folder_name}'...")
        print("(Watch browser - checking network traffic)")
        print()

        # Get performance logs before
        start_time = time.time()

        # Open folder
        bot._log(f"Opening folder: {folder_name}")

        # Click the folder to open it
        folder_path, folder_selector = target_folder
        from selenium.webdriver.common.by import By
        folder_elem = bot.driver.find_element(By.CSS_SELECTOR, folder_selector)
        folder_elem.click()
        time.sleep(3)

        # Get performance logs
        logs = bot.driver.get_log('performance')
        print(f"✓ Captured {len(logs)} performance log entries")

        # Parse logs for network requests
        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message['message']['method']

                if method == 'Network.requestWillBeSent':
                    req = message['message']['params']
                    captured_requests.append({
                        'type': 'request',
                        'url': req['request']['url'],
                        'method': req['request']['method'],
                        'headers': req['request'].get('headers', {}),
                        'postData': req['request'].get('postData'),
                        'timestamp': req['timestamp']
                    })

                elif method == 'Network.responseReceived':
                    resp = message['message']['params']
                    captured_requests.append({
                        'type': 'response',
                        'url': resp['response']['url'],
                        'status': resp['response']['status'],
                        'headers': resp['response'].get('headers', {}),
                        'mimeType': resp['response'].get('mimeType'),
                        'timestamp': resp['timestamp']
                    })
            except Exception as e:
                continue

        print(f"✓ Parsed {len(captured_requests)} network events")
        print()

        # Save to file
        output_file = '/tmp/neat_api_traffic.json'
        with open(output_file, 'w') as f:
            json.dump(captured_requests, f, indent=2)

        print(f"✓ Saved to: {output_file}")
        print()

        # Analyze captured traffic
        analyze_traffic(captured_requests)

    finally:
        if bot.driver:
            bot.driver.quit()
            print("✓ Browser closed")

def analyze_traffic(requests):
    """Analyze captured network traffic"""

    print("=" * 60)
    print("Traffic Analysis")
    print("=" * 60)
    print()

    # Filter for API requests
    api_requests = [r for r in requests if is_api_request(r)]
    print(f"Total requests: {len(requests)}")
    print(f"API requests: {len(api_requests)}")
    print()

    # Group by URL pattern
    url_patterns = {}
    for req in api_requests:
        if req['type'] == 'request':
            url = req['url'].split('?')[0]  # Remove query
            method = req['method']
            key = f"{method} {url}"

            if key not in url_patterns:
                url_patterns[key] = []
            url_patterns[key].append(req)

    print("Unique API Endpoints:")
    print("-" * 60)
    for pattern in sorted(url_patterns.keys()):
        count = len(url_patterns[pattern])
        print(f"  [{count}x] {pattern}")

    print()

    # Look for folder/file endpoints
    print("🔍 Folder/File Related Endpoints:")
    print("-" * 60)
    relevant = [p for p in url_patterns.keys() if any(term in p.lower() for term in ['folder', 'file', 'document', 'item', 'list'])]

    if relevant:
        for pattern in relevant:
            print(f"  ✓ {pattern}")
            sample = url_patterns[pattern][0]
            if 'postData' in sample and sample['postData']:
                print(f"    POST: {sample['postData'][:100]}...")
    else:
        print("  ❌ None found")

    print()

def is_api_request(request):
    """Check if request is an API call"""
    url = request.get('url', '')

    # Include patterns
    if any(pattern in url for pattern in ['/api/', '/graphql', 'neat.com']):
        # Exclude static assets
        if not any(ext in url for ext in ['.js', '.css', '.png', '.jpg', '.svg', '.woff', '.ttf', '.ico']):
            return True

    return False

if __name__ == '__main__':
    import sys

    folder_name = "2013 year TAX"
    if len(sys.argv) > 1:
        folder_name = sys.argv[1]

    try:
        capture_with_cdp(folder_name)
        print("=" * 60)
        print("✓ Capture complete!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
