# API Traffic Capture Instructions

## Goal
Capture Neat.com's API requests to identify endpoints for listing all files in a folder (bypassing the virtual scrolling limitation).

## Step-by-Step Manual Capture

### 1. Open Chrome with DevTools
1. Open Google Chrome
2. Press `F12` (or `Cmd+Option+I` on Mac) to open Developer Tools
3. Click on the **Network** tab
4. Check the **Preserve log** checkbox (important!)
5. Optionally: Filter by `Fetch/XHR` to see only API calls

### 2. Login and Navigate
1. Go to https://app.neat.com
2. Login with your credentials (solve CAPTCHA if needed)
3. Navigate to Alex's Cabinet
4. Click on **"2013 year TAX"** folder

### 3. Interact with Pagination
1. Set "Items per page" to **100**
2. Observe the Network tab - look for requests when you change pagination
3. Look for requests containing:
   - `folder`
   - `file`
   - `document`
   - `item`
   - `list`

### 4. Capture Download Request
1. Select one file (click checkbox)
2. Click **Export** button
3. Click **"Image as PDF"**
4. Watch for download-related API requests

###5. Save the HAR File
1. Right-click anywhere in the Network tab
2. Select **"Save all as HAR with content"**
3. Save to: `/tmp/neat_api_traffic.har`

## What to Look For

### Folder Listing Endpoint
We need to find:
- **URL pattern**: Something like `/api/folders/{id}/files` or `/graphql`
- **Query parameters**: Look for `limit`, `offset`, `page`, `pageSize`
- **Response**: Should contain ALL 23 files, not just 12

**Key Question**: Does the API return all 23 files even though UI only shows 12?

### File Download Endpoint
- **URL pattern**: `/api/files/{id}/download` or `/api/files/{id}/export`
- **Authentication**: Check Authorization header
- **File ID**: How files are identified

## Analysis Script

Once you have `/tmp/neat_api_traffic.har`, run:

```bash
python3 analyze_har.py
```

This will:
1. Parse the HAR file
2. Extract API endpoints
3. Identify folder listing calls
4. Show request/response details
5. Generate test API calls

## Expected Outcomes

### Best Case
- API returns all 23 files in a single response
- We can bypass UI virtual scrolling entirely
- Direct API calls for listing + downloading

### Alternative Case
- API also limits to 12 files per request
- But provides `offset` or `page` parameters
- We can paginate through API instead of UI

### Worst Case
- API matches UI behavior (only 12 files)
- No pagination parameters
- Need to stick with UI automation or multi-run approach

## Next Steps After Capture

1. **Analyze HAR file** - Identify key endpoints
2. **Test API calls** - Use `curl` or Python `requests` to replicate
3. **Extract auth tokens** - Capture cookies/headers needed
4. **Build API client** - Create Python wrapper for Neat API
5. **Integrate** - Replace Selenium UI automation with direct API calls
