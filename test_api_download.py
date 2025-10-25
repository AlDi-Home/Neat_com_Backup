#!/usr/bin/env python3
"""
Test direct API download using the download_url from entities API response
"""
import json
import requests
from pathlib import Path

# Load the API entities data
entities_file = Path.home() / "NeatDebug" / "scroll_diagnostics" / "api_entities.json"

if not entities_file.exists():
    print(f"❌ API entities file not found: {entities_file}")
    print("Run test_scroll_diagnostics.py first to capture API data")
    exit(1)

with open(entities_file) as f:
    entities = json.load(f)

print(f"Loaded {len(entities)} entities from API data")
print()

# Test downloading the first file
test_entity = entities[0]
print(f"Testing download of: {test_entity['name']}")
print(f"  Description: {test_entity['description']}")
print(f"  Webid: {test_entity['webid']}")
print(f"  Download URL: {test_entity['download_url'][:80]}...")
print()

# Try to download
download_url = test_entity['download_url']
output_dir = Path.home() / "NeatDebug" / "api_downloads"
output_dir.mkdir(parents=True, exist_ok=True)

# Sanitize filename
safe_name = f"{test_entity['name']} - {test_entity['description']}".replace('/', '-')
output_file = output_dir / f"{safe_name}.pdf"

print(f"Downloading to: {output_file}")
print()

try:
    # Make the request
    response = requests.get(download_url, allow_redirects=True, timeout=30)

    print(f"Response status: {response.status_code}")
    print(f"Response headers:")
    for key, value in response.headers.items():
        if key.lower() in ['content-type', 'content-length', 'content-disposition']:
            print(f"  {key}: {value}")
    print()

    if response.status_code == 200:
        # Save the file
        with open(output_file, 'wb') as f:
            f.write(response.content)

        file_size = output_file.stat().st_size
        print(f"✅ SUCCESS! Downloaded {file_size} bytes")
        print(f"   Saved to: {output_file}")
        print()
        print(f"File type: {response.headers.get('content-type', 'unknown')}")

        # Check if it's a PDF
        if output_file.suffix == '.pdf' or response.headers.get('content-type') == 'application/pdf':
            print("✅ File is a PDF")
        else:
            print(f"⚠️  File may not be a PDF (content-type: {response.headers.get('content-type')})")
    else:
        print(f"❌ FAILED: HTTP {response.status_code}")
        print(f"Response body: {response.text[:500]}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
