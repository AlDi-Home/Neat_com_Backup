#!/usr/bin/env python3
"""
Reverse Engineer Neat.com Download API from HAR File

This script analyzes a HAR (HTTP Archive) file to understand:
1. Download button click -> API endpoint mapping
2. Authentication headers and tokens needed
3. URL patterns for direct file downloads
4. Request/response structure for downloads

Usage:
    python3 analyze_download_api.py <har_file.har>
"""

import json
import sys
from datetime import datetime
from urllib.parse import urlparse, parse_qs

def parse_timestamp(ts):
    """Convert HAR timestamp to readable datetime"""
    return datetime.fromisoformat(ts.replace('Z', '+00:00'))

def analyze_download_flow(har_file):
    """Analyze HAR file to reverse engineer download API"""

    with open(har_file, 'r') as f:
        har_data = json.load(f)

    entries = har_data['log']['entries']

    print("=" * 80)
    print("NEAT.COM DOWNLOAD API REVERSE ENGINEERING")
    print("=" * 80)
    print(f"\nAnalyzing {len(entries)} HTTP requests...\n")

    # Track different types of requests
    download_requests = []
    export_requests = []
    pdf_requests = []
    entities_requests = []
    auth_headers = {}

    print("\n" + "=" * 80)
    print("STEP 1: IDENTIFYING REQUEST TYPES")
    print("=" * 80)

    for idx, entry in enumerate(entries):
        request = entry['request']
        response = entry['response']
        url = request['url']
        method = request['method']
        status = response['status']

        # Parse URL
        parsed = urlparse(url)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Categorize requests
        if 'download' in path.lower():
            download_requests.append({
                'index': idx,
                'method': method,
                'url': url,
                'path': path,
                'status': status,
                'request': request,
                'response': response,
                'timestamp': entry['startedDateTime']
            })

        if 'export' in path.lower() or 'export' in url.lower():
            export_requests.append({
                'index': idx,
                'method': method,
                'url': url,
                'path': path,
                'status': status,
                'request': request,
                'response': response,
                'timestamp': entry['startedDateTime']
            })

        if '/entities' in path:
            entities_requests.append({
                'index': idx,
                'method': method,
                'url': url,
                'path': path,
                'status': status,
                'request': request,
                'response': response,
                'timestamp': entry['startedDateTime']
            })

        # Check for PDF responses
        content_type = response.get('content', {}).get('mimeType', '')
        if 'pdf' in content_type.lower():
            pdf_requests.append({
                'index': idx,
                'method': method,
                'url': url,
                'path': path,
                'status': status,
                'request': request,
                'response': response,
                'content_type': content_type,
                'timestamp': entry['startedDateTime']
            })

        # Extract authentication headers (from any request)
        for header in request['headers']:
            name = header['name'].lower()
            if any(auth_key in name for auth_key in ['authorization', 'token', 'session', 'cookie', 'x-neat']):
                if name not in auth_headers:
                    auth_headers[name] = header['value']

    # Print findings
    print(f"\n✓ Found {len(download_requests)} download-related requests")
    print(f"✓ Found {len(export_requests)} export-related requests")
    print(f"✓ Found {len(pdf_requests)} PDF responses")
    print(f"✓ Found {len(entities_requests)} entities API calls")

    print("\n" + "=" * 80)
    print("STEP 2: DOWNLOAD REQUESTS ANALYSIS")
    print("=" * 80)

    if download_requests:
        for req in download_requests:
            print(f"\n[Request #{req['index']}] {req['method']} {req['path']}")
            print(f"  Status: {req['status']}")
            print(f"  Full URL: {req['url']}")
            print(f"  Timestamp: {req['timestamp']}")

            # Print request headers
            print(f"\n  Request Headers:")
            for header in req['request']['headers']:
                if header['name'].lower() in ['authorization', 'cookie', 'x-neat-account-id', 'content-type']:
                    print(f"    {header['name']}: {header['value'][:80]}...")

            # Print request body if POST
            if req['method'] == 'POST' and 'postData' in req['request']:
                print(f"\n  Request Body:")
                post_data = req['request'].get('postData', {})
                if 'text' in post_data:
                    try:
                        body = json.loads(post_data['text'])
                        print(f"    {json.dumps(body, indent=6)}")
                    except:
                        print(f"    {post_data['text'][:200]}")
    else:
        print("\n⚠️  No explicit '/download' endpoints found")
        print("    Looking for alternative download mechanisms...")

    print("\n" + "=" * 80)
    print("STEP 3: PDF DOWNLOAD ANALYSIS")
    print("=" * 80)

    if pdf_requests:
        for idx, req in enumerate(pdf_requests, 1):
            print(f"\n[PDF #{idx}] {req['method']} {req['path']}")
            print(f"  Status: {req['status']}")
            print(f"  Content-Type: {req['content_type']}")
            print(f"  Full URL: {req['url']}")
            print(f"  Timestamp: {req['timestamp']}")

            # Check for webid in URL
            if 'webid' in req['url'] or any(len(part) == 24 for part in req['path'].split('/')):
                print(f"  ✓ Likely contains webid in URL path")

            # Print query parameters
            parsed = urlparse(req['url'])
            query = parse_qs(parsed.query)
            if query:
                print(f"\n  Query Parameters:")
                for key, value in query.items():
                    print(f"    {key}: {value}")

            # Print important headers
            print(f"\n  Request Headers:")
            for header in req['request']['headers']:
                if header['name'].lower() in ['authorization', 'cookie', 'x-neat-account-id', 'referer']:
                    print(f"    {header['name']}: {header['value'][:80]}...")
    else:
        print("\n⚠️  No PDF content-type responses found")

    print("\n" + "=" * 80)
    print("STEP 4: AUTHENTICATION ANALYSIS")
    print("=" * 80)

    print(f"\nFound {len(auth_headers)} authentication-related headers:\n")
    for name, value in sorted(auth_headers.items()):
        # Mask sensitive values
        if len(value) > 50:
            display_value = f"{value[:30]}...{value[-10:]}"
        else:
            display_value = value
        print(f"  {name}: {display_value}")

    print("\n" + "=" * 80)
    print("STEP 5: TIMELINE OF DOWNLOAD FLOW")
    print("=" * 80)

    # Create timeline of all relevant requests
    all_relevant = (download_requests + export_requests + pdf_requests)
    all_relevant.sort(key=lambda x: x['timestamp'])

    if all_relevant:
        print("\nChronological flow of download-related requests:\n")
        for idx, req in enumerate(all_relevant, 1):
            ts = parse_timestamp(req['timestamp'])
            print(f"{idx}. [{ts.strftime('%H:%M:%S.%f')[:-3]}] {req['method']:4} {req['path'][:60]}")
            if req in pdf_requests:
                print(f"   └─> ✓ PDF DOWNLOAD (Content-Type: {req['content_type']})")

    print("\n" + "=" * 80)
    print("STEP 6: URL PATTERN ANALYSIS")
    print("=" * 80)

    # Extract patterns from all URLs
    all_paths = set()
    for req in entries:
        path = urlparse(req['request']['url']).path
        if any(keyword in path for keyword in ['export', 'download', 'pdf', 'entities']):
            all_paths.add(path)

    print(f"\nUnique URL patterns ({len(all_paths)} total):\n")
    for path in sorted(all_paths):
        print(f"  {path}")

    print("\n" + "=" * 80)
    print("STEP 7: RECOMMENDED APPROACH")
    print("=" * 80)

    print("\nBased on analysis, here's how to implement direct downloads:\n")

    if pdf_requests:
        example = pdf_requests[0]
        print("1. Download URL Pattern:")
        print(f"   {example['url']}\n")

        print("2. Required Headers:")
        for header in example['request']['headers']:
            if header['name'].lower() in ['authorization', 'cookie', 'x-neat-account-id']:
                print(f"   {header['name']}: <value from session>\n")

        print("3. Method:")
        print(f"   {example['method']}\n")

        print("4. Python Implementation:")
        print("""
   import requests

   def download_file(webid, session_headers):
       url = f"https://app.neat.com/api/v5/entities/{webid}/download"
       headers = {
           'x-neat-account-id': session_headers['account_id'],
           'Cookie': session_headers['cookies'],
       }
       response = requests.get(url, headers=headers)
       return response.content
        """)
    else:
        print("\n⚠️  Could not determine direct download pattern from HAR")
        print("   Please ensure HAR includes a complete download flow")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    return {
        'download_requests': download_requests,
        'export_requests': export_requests,
        'pdf_requests': pdf_requests,
        'entities_requests': entities_requests,
        'auth_headers': auth_headers
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_download_api.py <har_file.har>")
        print("\nPlease provide a HAR file captured during a complete download flow:")
        print("  1. Login to Neat.com")
        print("  2. Open a folder")
        print("  3. Select a file")
        print("  4. Click Export")
        print("  5. Click 'Image as PDF'")
        print("  6. Click 'Download PDF File'")
        print("  7. Save HAR file from browser DevTools")
        sys.exit(1)

    har_file = sys.argv[1]
    results = analyze_download_flow(har_file)
