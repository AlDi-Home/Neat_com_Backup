# HAR Analysis Findings - Second Capture

## Summary

Analyzed `neat_api_traffic2.har` which captured user interactions including:
- Login (no password prompt due to saved credentials)
- Navigating between folders ("2013 year TAX" → "2014 year TAX" → back)
- Selecting/unselecting files at beginning and end of list

## Key Discoveries

### 1. API Endpoint Confirmation ✅

**The `/api/v5/entities` endpoint works perfectly and returns ALL files:**

```
Call #1 and #9 both requested folder: 5342fbc2d94877f18f000076 ("2013 year TAX")
Response: 23 items (ALL files, not just 12!)
```

**Request Format**:
```json
POST https://api.neat.com/api/v5/entities

{
  "filters": [
    { "parent_id": "5342fbc2d94877f18f000076" },
    { "type": "$all_item_types" }
  ],
  "page": 1,
  "page_size": "100",
  "sort_by": [["created_at", "desc"]],
  "utc_offset": -4
}
```

**Response**:
```json
{
  "entities": [
    {
      "webid": "5537b5dc79313e5966000297",
      "name": "Transaction receipt",
      "description": "Apr. 22, 2015",
      "type": "document",
      "created_at": "2015-04-22T..."
    },
    // ... 22 more
  ]
}
```

---

### 2. Authentication Structure 🔑

**Headers Used in Successful Calls**:
```
content-type: application/json
x-neat-account-id: 533f2f35eca98e8f09000a92
```

**No Authorization header!**
**No Cookie header!**

This means:
- Either authentication is handled at the browser/session level
- Or HAR didn't capture certain security headers
- Or authentication is via request origin/referer checking

---

### 3. Token Renewal Endpoint 🔄

**POST /v3/renew** - Refreshes authentication tokens

**Request**:
```json
{
  "accountId": "533f2f35eca98e8f09000a92",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response**:
```json
{
  "userId": "533f2f35eca98e8f09000a90",
  "oauthToken": "92339c110c231086529916d429fc0a29dcf7bcc29b8b7cbcfbb7f2100eeeb6a6",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**JWT Payload** (decoded):
```json
{
  "data": {
    "oauthToken": "92339c110c231086529916d429fc0a29dcf7bcc29b8b7cbcfbb7f2100eeeb6a6",
    "accountId": "533f2f35eca98e8f09000a92",
    "userId": "533f2f35eca98e8f09000a90",
    "scope": "APP_NEAT_COM",
    "groups": ["USER", "ACCOUNT_OWNER"]
  },
  "iat": 1760484787,
  "exp": 1760485687,
  "iss": "Gatekeeper Service"
}
```

Tokens expire in ~15 minutes (exp - iat = 900 seconds).

---

### 4. Multiple API Calls Captured 📊

Found **9 POST /api/v5/entities** calls in this session:

| Call | parent_id | Folder | Files Returned |
|------|-----------|--------|----------------|
| #1 | 5342fbc2d94877f18f000076 | 2013 year TAX | **23 items** ✅ |
| #2 | 5342fbae11494097b6000bfa | Root | 0 items |
| #3 | 5342fbae11494097b6000bff | Alex's Cabinet | 16 items (folders) |
| #4 | 5342fbae11494097b6000bfd | Another folder | 3 items |
| #6 | 5342fbc2d94877f18f000076 | 2013 year TAX subfolder | 1 item |
| #7 | 5342fbc4d94877f18f000089 | 2014 year TAX | 1 item |
| #8 | 5342fbc4d94877f18f000089 | 2014 year TAX | **17 items** ✅ |
| #9 | 5342fbc2d94877f18f000076 | 2013 year TAX | **23 items** ✅ |

**Key Observation**: When navigating to a folder, the API returns **ALL files**, not limited to 12!

---

### 5. Folder ID Extraction 📍

**From URL Pattern**:
```
https://app.neat.com/files/folders/5342fbc2d94877f18f000076/?account=533f2f35eca98e8f09000a92
                                   ^^^^^^^^^^^^^^^^^^^^^^^^
                                   This is the parent_id!
```

We can extract `parent_id` directly from the browser URL after opening a folder.

---

### 6. No Cookies in HAR ❌

**Finding**: No `Set-Cookie` headers found in any responses.

**Implications**:
1. Authentication is purely token-based (localStorage)
2. No HTTP-only cookies blocking JavaScript access
3. All auth state manageable from browser context

---

## Why External API Calls Still Fail

Despite having:
- ✅ Correct endpoint
- ✅ Correct request format
- ✅ Account ID
- ✅ OAuth token
- ✅ JWT token

External `requests` library calls fail with **401 Unauthorized**.

**Possible Reasons**:

1. **Origin/Referer Validation**
   - Server checks `Origin: https://app.neat.com`
   - External calls from Python don't match

2. **CORS Pre-flight**
   - Browser handles OPTIONS requests automatically
   - Python requests don't

3. **Session/Cookie Not Captured**
   - HAR may not capture HTTP-only cookies
   - Browser session state exists but isn't visible

4. **Token Binding**
   - Tokens might be bound to IP/user-agent/fingerprint
   - Can't be used from different context

5. **WebDriver Detection**
   - Even from browser context, fetch() is blocked
   - Anti-automation measures

---

## Successful Approach: Intercept Browser's API Calls

Since the browser successfully makes authenticated API calls, the solution is:

### Method: Chrome DevTools Protocol Network Interception

1. **Enable CDP Network Monitoring**
   ```python
   driver.execute_cdp_cmd('Network.enable', {})
   ```

2. **Navigate to Folder** (triggers API call)
   ```python
   folder_elem.click()
   ```

3. **Monitor Performance Logs**
   ```python
   logs = driver.get_log('performance')
   ```

4. **Find /api/v5/entities Response**
   ```python
   for log in logs:
       if '/api/v5/entities' in log:
           request_id = extract_request_id(log)
   ```

5. **Get Response Body**
   ```python
   response = driver.execute_cdp_cmd('Network.getResponseBody', {
       'requestId': request_id
   })
   entities = json.loads(response['body'])['entities']
   ```

6. **Extract All 23 File IDs**
   - Now we have webids for all files
   - Can download them one by one
   - Bypasses virtual scrolling!

---

## Implementation Plan

### Phase 1: Proof of Concept
- [x] Capture HAR file
- [x] Analyze API structure
- [x] Confirm API returns all files
- [ ] Test CDP network interception ← **NEXT STEP**

### Phase 2: Integration
- [ ] Modify `export_folder_files()` in neat_bot.py
- [ ] Add CDP network monitoring
- [ ] Intercept API response instead of UI scraping
- [ ] Extract all file webids
- [ ] Download files using webids

### Phase 3: Testing
- [ ] Test with 2013 year TAX (23 files)
- [ ] Test with 2014 year TAX (17 files)
- [ ] Test with folder >100 files
- [ ] Verify all files downloaded

---

## Recommendation

**Pursue CDP Interception Approach**

**Pros**:
- ✅ Uses browser's legitimate authentication
- ✅ No external API replication needed
- ✅ Gets ALL files (bypasses virtual scrolling)
- ✅ Relatively simple to implement
- ✅ Robust and maintainable

**Cons**:
- Requires CDP (Chrome DevTools Protocol)
- Slightly more complex than current UI scraping
- Browser-dependent (Chrome/Chromium only)

**Estimated Effort**: 2-3 hours

**Alternative**: Stick with multi-run workaround (1 hour to optimize)

---

## Files

- `/Users/alex/Projects/Neat/neat_api_traffic2.har` - Full capture
- `/tmp/neat_api_analysis.json` - Parsed data
- [analyze_har.py](analyze_har.py) - Analysis tool

---

## Next Steps

**Option A: CDP Interception** (Recommended if you want proper fix)
1. Test `test_intercept_api_response.py`
2. Verify we can get response bodies
3. Integrate into neat_bot.py

**Option B: Multi-Run Optimization** (Recommended if you want quick solution)
1. Accept current limitation
2. Add auto-retry logic
3. Improve progress tracking

**Decision Point**: Which path do you want to pursue?
