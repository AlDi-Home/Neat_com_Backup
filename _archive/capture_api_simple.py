#!/usr/bin/env python3
"""
Simplified API traffic capture using browser DevTools Protocol

This approach:
1. Uses Chrome DevTools Protocol to capture network traffic
2. Leverages existing neat_bot.py for login
3. Captures traffic while interacting with folder and file export
4. Extracts API endpoints and request/response data
"""

import json
import time
from pathlib import Path
from neat_bot import NeatBot
from config import Config

def analyze_traffic_file():
    """Analyze the captured traffic file"""

    traffic_file = '/tmp/neat_api_traffic.json'

    if not Path(traffic_file).exists():
        print(f"❌ Traffic file not found: {traffic_file}")
        print("\nTo capture traffic:")
        print("1. Open Chrome DevTools (F12)")
        print("2. Go to Network tab")
        print("3. Run test_single_folder.py \"2013 year TAX\"")
        print("4. Right-click in Network tab -> Save all as HAR")
        print("5. Save to /tmp/neat_api_traffic.json")
        return

    print("\n" + "=" * 60)
    print("Analyzing Neat.com API Traffic")
    print("=" * 60)
    print()

    with open(traffic_file, 'r') as f:
        data = json.load(f)

    print(f"✓ Loaded traffic file: {len(data)} requests")
    print()

    # Filter for API requests
    api_requests = []
    for req in data:
        url = req.get('url', '')

        # Look for API patterns
        if any(pattern in url for pattern in [
            '/api/',
            '/graphql',
            'neat.com',
            '.json'
        ]):
            # Exclude static assets
            if not any(ext in url for ext in ['.js', '.css', '.png', '.jpg', '.svg', '.woff', '.ttf']):
                api_requests.append(req)

    print(f"✓ Found {len(api_requests)} API requests")
    print()

    # Group by endpoint
    endpoints = {}
    for req in api_requests:
        if req.get('type') == 'request':
            url = req['url'].split('?')[0]  # Remove query params
            method = req.get('method', 'GET')
            key = f"{method} {url}"

            if key not in endpoints:
                endpoints[key] = []
            endpoints[key].append(req)

    print("=" * 60)
    print("API Endpoints Discovered:")
    print("=" * 60)

    for endpoint in sorted(endpoints.keys()):
        print(f"\n{endpoint}")
        print(f"  Calls: {len(endpoints[endpoint])}")

        # Show sample request details
        sample = endpoints[endpoint][0]
        if 'headers' in sample:
            auth_header = sample['headers'].get('Authorization', None)
            if auth_header:
                print(f"  Auth: {auth_header[:50]}...")

        if 'postData' in sample and sample['postData']:
            try:
                post_data = json.loads(sample['postData'])
                print(f"  POST Data: {json.dumps(post_data, indent=4)[:200]}...")
            except:
                print(f"  POST Data: {sample['postData'][:200]}...")

    print()
    print("=" * 60)

    # Look for folder listing endpoints
    print("\n🔍 Looking for folder listing endpoints...")
    folder_endpoints = [e for e in endpoints.keys() if any(term in e.lower() for term in ['folder', 'file', 'list', 'document'])]

    if folder_endpoints:
        print(f"✓ Found {len(folder_endpoints)} potential endpoints:")
        for ep in folder_endpoints:
            print(f"  - {ep}")
    else:
        print("❌ No obvious folder listing endpoints found")

    print()

def main():
    """Main function"""

    print("\n" + "=" * 60)
    print("Neat.com API Reverse Engineering")
    print("=" * 60)
    print()

    print("MANUAL CAPTURE INSTRUCTIONS:")
    print("-" * 60)
    print("1. Open Chrome and go to: https://app.neat.com")
    print("2. Open DevTools (F12 or Cmd+Option+I)")
    print("3. Go to the Network tab")
    print("4. Check 'Preserve log' checkbox")
    print("5. Login and navigate to '2013 year TAX' folder")
    print("6. Set pagination to 100")
    print("7. Export one file")
    print("8. Right-click in Network tab -> 'Save all as HAR'")
    print("9. Save to: /tmp/neat_api_traffic.json")
    print("-" * 60)
    print()

    input("Press ENTER when you have saved the HAR file...")

    analyze_traffic_file()

if __name__ == '__main__':
    main()
