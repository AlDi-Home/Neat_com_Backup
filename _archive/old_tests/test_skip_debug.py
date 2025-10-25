#!/usr/bin/env python3
"""Test skip logic"""
from pathlib import Path

folder_dir = Path("/Users/alex/Downloads/Neat/2019 year TAX")
name = "116 Vanguard Property Tax 2020 Final"
description = "Property Tax Bill; Taxes"

safe_name = f"{name} - {description}".replace('/', '-').replace('\\', '-')
output_file = folder_dir / f"{safe_name}.pdf"

print(f"Looking for: {output_file}")
print(f"Exists: {output_file.exists()}")

if output_file.exists():
    print("SHOULD SKIP!")
else:
    # Check for numbered duplicates
    counter = 1
    found_existing = False
    while (folder_dir / f"{safe_name}_{counter}.pdf").exists():
        print(f"Found: {safe_name}_{counter}.pdf")
        counter += 1
        found_existing = True

    if found_existing:
        print(f"SHOULD SKIP! (found up to _{counter-1})")
    else:
        print("File doesn't exist, would download")
