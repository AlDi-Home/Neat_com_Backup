#!/usr/bin/env python3
"""
Analyze HAR (HTTP Archive) file to extract Neat.com API endpoints

Usage:
    python3 analyze_har.py [/path/to/file.har]

Default path: /tmp/neat_api_traffic.har
"""

import json
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

def analyze_har(har_path):
    """Analyze HAR file and extract API information"""

    print("\n" + "=" * 70)
    print("Neat.com HAR File Analysis")
    print("=" * 70)
    print()

    if not Path(har_path).exists():
        print(f"❌ HAR file not found: {har_path}")
        print()
        print("To capture HAR file:")
        print("1. Open Chrome DevTools (F12)")
        print("2. Go to Network tab, check 'Preserve log'")
        print("3. Navigate to folder and interact with site")
        print("4. Right-click Network tab -> 'Save all as HAR with content'")
        print(f"5. Save to: {har_path}")
        return

    print(f"Loading: {har_path}")

    with open(har_path, 'r') as f:
        har_data = json.load(f)

    entries = har_data['log']['entries']
    print(f"✓ Loaded {len(entries)} HTTP requests")
    print()

    # Filter for API requests
    api_requests = []
    for entry in entries:
        url = entry['request']['url']

        # Look for API patterns
        if any(pattern in url for pattern in ['/api/', '/graphql', 'neat.com']):
            # Exclude static assets
            if not any(ext in url for ext in ['.js', '.css', '.png', '.jpg', '.svg', '.woff', '.ttf', '.ico', '.map']):
                api_requests.append(entry)

    print(f"✓ Found {len(api_requests)} API requests")
    print()

    # Group by endpoint
    endpoints = {}
    for entry in api_requests:
        url = entry['request']['url']
        method = entry['request']['method']

        # Parse URL
        parsed = urlparse(url)
        path = parsed.path
        query = parse_qs(parsed.query)

        key = f"{method} {path}"

        if key not in endpoints:
            endpoints[key] = []

        endpoints[key].append({
            'url': url,
            'method': method,
            'path': path,
            'query': query,
            'request': entry['request'],
            'response': entry['response']
        })

    # Print summary
    print("=" * 70)
    print("API Endpoints Summary")
    print("=" * 70)
    print()

    for endpoint in sorted(endpoints.keys()):
        count = len(endpoints[endpoint])
        print(f"\n[{count}x] {endpoint}")

        sample = endpoints[endpoint][0]

        # Show query parameters
        if sample['query']:
            print(f"      Query params: {', '.join(sample['query'].keys())}")

        # Show headers (auth)
        headers = sample['request']['headers']
        auth_headers = [h for h in headers if h['name'].lower() in ['authorization', 'x-api-key', 'x-auth-token']]
        if auth_headers:
            for h in auth_headers:
                value = h['value']
                if len(value) > 50:
                    value = value[:50] + "..."
                print(f"      Auth: {h['name']}: {value}")

        # Show request body for POST/PUT
        if sample['method'] in ['POST', 'PUT', 'PATCH']:
            post_data = sample['request'].get('postData', {})
            if post_data:
                text = post_data.get('text', '')
                if text:
                    try:
                        body = json.loads(text)
                        body_preview = json.dumps(body, indent=8)[:200]
                        print(f"      Request body preview:\n{body_preview}...")
                    except:
                        print(f"      Request body: {text[:100]}...")

        # Show response preview
        response = sample['response']
        status = response['status']
        content = response.get('content', {})
        mime_type = content.get('mimeType', '')

        print(f"      Response: {status} {mime_type}")

        if 'text' in content:
            try:
                response_text = content['text']
                response_json = json.loads(response_text)
                response_preview = json.dumps(response_json, indent=8)[:300]
                print(f"      Response preview:\n{response_preview}...")
            except:
                pass

    print()
    print("=" * 70)

    # Look for folder/file related endpoints
    print("\n🔍 Folder/File Related Endpoints")
    print("=" * 70)
    print()

    relevant_keywords = ['folder', 'file', 'document', 'item', 'list', 'export', 'download']
    relevant_endpoints = {}

    for endpoint, requests in endpoints.items():
        if any(keyword in endpoint.lower() for keyword in relevant_keywords):
            relevant_endpoints[endpoint] = requests

    if not relevant_endpoints:
        print("❌ No obvious folder/file endpoints found")
        print()
        print("Try looking at all endpoints above for patterns like:")
        print("  - GraphQL queries")
        print("  - Generic /api/v1/items or /api/v1/data")
        print("  - Base64 encoded paths")
    else:
        for endpoint, requests in relevant_endpoints.items():
            print(f"\n✓ {endpoint}")
            print(f"   Calls: {len(requests)}")

            sample = requests[0]

            # Detailed analysis
            print(f"   Full URL: {sample['url']}")

            if sample['query']:
                print(f"   Query parameters:")
                for key, values in sample['query'].items():
                    print(f"      {key} = {values}")

            # Check response for file list
            response = sample['response']
            content = response.get('content', {})

            if 'text' in content:
                try:
                    response_json = json.loads(content['text'])

                    # Look for arrays (likely file lists)
                    def find_arrays(obj, path=""):
                        arrays = []
                        if isinstance(obj, list):
                            arrays.append((path, len(obj)))
                        elif isinstance(obj, dict):
                            for key, value in obj.items():
                                arrays.extend(find_arrays(value, f"{path}.{key}" if path else key))
                        return arrays

                    arrays = find_arrays(response_json)
                    if arrays:
                        print(f"   Arrays in response:")
                        for path, length in arrays:
                            print(f"      {path}: {length} items")
                            if length == 23:
                                print(f"         🎯 THIS MIGHT BE IT! (matches expected 23 files)")
                            elif length == 12:
                                print(f"         ⚠️  Only 12 items (same as UI)")

                except Exception as e:
                    pass

    print()

    # Save detailed report
    report_path = '/tmp/neat_api_analysis.json'
    with open(report_path, 'w') as f:
        json.dump({
            'total_requests': len(entries),
            'api_requests': len(api_requests),
            'endpoints': {k: len(v) for k, v in endpoints.items()},
            'relevant_endpoints': {k: len(v) for k, v in relevant_endpoints.items()},
            'detailed_endpoints': endpoints
        }, f, indent=2)

    print(f"✓ Detailed report saved to: {report_path}")
    print()

if __name__ == '__main__':
    har_path = '/tmp/neat_api_traffic.har'

    if len(sys.argv) > 1:
        har_path = sys.argv[1]

    analyze_har(har_path)

    print("=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("1. Review the folder/file related endpoints above")
    print("2. Check if any response contains all 23 files")
    print("3. If yes: Extract auth tokens and test direct API calls")
    print("4. If no: Check for pagination parameters in API")
    print()
