# API Reverse Engineering Results

## Executive Summary

✅ **Successfully identified Neat.com API endpoint that returns ALL files**
❌ **Unable to replicate authentication externally**
✅ **Confirmed API bypasses virtual scrolling (23/23 files returned)**

---

## Key Discoveries

### 1. The API Endpoint

**Endpoint**: `POST https://api.neat.com/api/v5/entities`

**Request Format**:
```json
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
    // ... 22 more items
  ]
}
```

**🎯 Critical Finding**: API returns **ALL 23 files** in one response, not just 12!

---

### 2. Authentication Structure

**Headers Required**:
- `Content-Type: application/json`
- `x-neat-account-id: {account_id}`
- `Authorization: Bearer {jwt_token}` (attempted but failed)

**Token Storage** (LocalStorage):
```javascript
neat::global::account     // Contains account ID
neat::global::token       // OAuth token
neat::global::jwt         // JWT token (contains oauthToken inside)
neat::global::user        // User data
```

**JWT Structure** (Decoded):
```json
{
  "data": {
    "oauthToken": "92339c110c...",
    "accountId": "533f2f35eca98e8f09000a92",
    "userId": "533f2f35eca98e8f09000a90",
    "scope": "APP_NEAT_COM",
    "groups": ["USER", "ACCOUNT_OWNER"]
  },
  "iat": 1760419113,
  "exp": 1760420013,
  "iss": "Gatekeeper Service"
}
```

---

### 3. Folder ID Extraction

**From URL**:
```
https://app.neat.com/files/folders/5342fbc2d94877f18f000076/?account=533f2f35eca98e8f09000a92
                                   ^^^^^^^^^^^^^^^^^^^^^^^^
                                        parent_id
```

The `parent_id` needed for the API call is embedded in the folder URL!

---

## Attempts Made

### Attempt 1: Direct API Call with Requests Library ❌

**Approach**: Extract tokens from localStorage, make external HTTP request

**Code**: [test_api_direct.py](test_api_direct.py)

**Result**: `401 Unauthorized - Could not find a valid OAuth token`

**Issues**:
- JWT token validation failing
- OAuth token format unclear
- Cookie-based authentication complexity
- Possible anti-bot detection

---

### Attempt 2: Fetch from Browser Context ❌

**Approach**: Use `fetch()` from JavaScript within authenticated browser

**Code**: [test_api_browser_context.py](test_api_browser_context.py)

**Result**: `TypeError: Failed to fetch`

**Issues**:
- CORS blocking cross-origin requests (app.neat.com → api.neat.com)
- Even with `credentials: 'include'`
- XMLHttpRequest also blocked with "Network error"

---

### Attempt 3: HAR File Analysis ✅

**Approach**: Capture network traffic manually, analyze requests

**Tool**: [analyze_har.py](analyze_har.py)

**Result**: **SUCCESS** - Identified complete API structure

**Files**:
- `/tmp/neat_api_traffic.har` - Raw capture
- `/tmp/neat_api_analysis.json` - Parsed analysis

**Key Finding**: Confirmed API returns all 23 files

---

## Why External API Calls Fail

### Root Causes

1. **Complex OAuth Flow**
   - Multi-token system (JWT, OAuth, refresh tokens)
   - Tokens have interdependencies
   - Server-side validation beyond just header presence

2. **Anti-Bot Protection**
   - Possible WebDriver detection
   - Request origin validation
   - Timing/behavioral analysis

3. **CORS Restrictions**
   - Browser security prevents cross-origin fetch
   - Even from same domain (app.neat.com → api.neat.com)

4. **Cookie Complexity**
   - Session cookies not captured in HAR
   - Domain-specific cookie rules
   - HTTP-only cookies inaccessible to JavaScript

---

## Potential Solutions (Not Yet Implemented)

### Option A: Intercept Browser's Own API Calls

**Concept**: Monitor network traffic from browser's natural page loading

**Approach**:
1. Use Chrome DevTools Protocol to monitor network
2. Let page load folder naturally (it calls API)
3. Intercept the API response
4. Extract all 23 file IDs from response

**Pros**:
- Uses browser's legitimate authentication
- No need to replicate OAuth flow
- Bypasses CORS

**Cons**:
- Requires CDP integration
- More complex implementation
- Still limited by browser session

**Estimated Effort**: 2-3 hours

---

### Option B: Undetected ChromeDriver

**Concept**: Use `undetected-chromedriver` to avoid WebDriver detection

**Approach**:
```python
import undetected_chromedriver as uc
driver = uc.Chrome()
```

**Pros**:
- May bypass anti-bot detection
- Could enable external API calls
- Same code structure

**Cons**:
- May still face OAuth issues
- Additional dependency
- No guarantee of success

**Estimated Effort**: 1-2 hours

---

### Option C: Browser Extension

**Concept**: Chrome extension with native access to cookies/auth

**Approach**:
- Extension has full cookie access
- Can make authenticated API calls
- No CORS restrictions
- Better user experience

**Pros**:
- Most robust solution
- Best authentication handling
- Professional approach

**Cons**:
- Requires JavaScript extension development
- Distribution/installation complexity
- Separate codebase

**Estimated Effort**: 8-12 hours

---

### Option D: Accept Multi-Run Workaround

**Concept**: Optimize the existing approach (run backup 2-3 times)

**Current Status**: **FUNCTIONAL**

**Improvements**:
1. Add progress tracking across runs
2. Smarter duplicate detection
3. Show "12/23 files on first run" messaging
4. Auto-retry until all files processed

**Pros**:
- ✅ Already working
- ✅ No new development needed
- ✅ Reliable
- ✅ Simple to maintain

**Cons**:
- Slower (multiple runs)
- Not elegant
- Inefficient

**Estimated Effort**: 1 hour (optimization only)

---

## Recommendation

Given the findings, I recommend **Option D: Optimize Multi-Run Workaround**

**Rationale**:
1. **It works reliably** - No authentication complexity
2. **Low maintenance** - No fragile API integration
3. **Quick to improve** - 1 hour vs 2-12 hours for alternatives
4. **Future-proof** - Not dependent on API structure
5. **User-acceptable** - "Run 2-3 times" is reasonable for backup tool

**Improvements to Make**:
```python
# Add to main.py
def auto_retry_until_complete(bot, max_runs=3):
    """Auto-retry backup until all files processed"""
    for run in range(1, max_runs + 1):
        print(f"Run {run}/{max_runs}...")

        stats = bot.backup_all_folders()

        if stats['failed_count'] == 0:
            print("✅ All files backed up!")
            break

        if run < max_runs:
            print(f"Some files pending, starting run {run+1}...")
```

---

## Alternative: If You Want to Pursue API Approach

If the multi-run workaround is unacceptable, the most promising path forward is:

1. **Option A (Intercept Browser API Calls)** - 2-3 hours
2. **Option B (Undetected ChromeDriver)** - 1-2 hours
3. **Option C (Browser Extension)** - 8-12 hours (professional solution)

---

## Files & Resources

### Analysis Tools
- [API_CAPTURE_INSTRUCTIONS.md](API_CAPTURE_INSTRUCTIONS.md) - Manual capture guide
- [analyze_har.py](analyze_har.py) - HAR file analyzer
- [PAGINATION_ANALYSIS.md](PAGINATION_ANALYSIS.md) - Virtual scrolling analysis

### Test Scripts
- [test_api_direct.py](test_api_direct.py) - Direct API testing
- [test_api_browser_context.py](test_api_browser_context.py) - Browser JS testing

### Captured Data
- `/tmp/neat_api_traffic.har` - Network capture
- `/tmp/neat_api_analysis.json` - Parsed analysis

---

## Conclusion

**We successfully identified the API endpoint and confirmed it returns all files**, solving the virtual scrolling limitation in theory. However, **authentication complexity makes external API calls impractical** without significant additional investment.

**The multi-run workaround remains the most reliable and maintainable solution.**

**Current Status**: ✅ Virtual scrolling **understood and documented**
**Recommended Path**: ✅ Optimize multi-run workflow
**Alternative Paths**: Available if multi-run is unacceptable

---

## Next Steps

1. **Immediate**: Optimize multi-run workaround (1 hour)
2. **Optional**: Try Option A or B if desired (2-4 hours)
3. **Long-term**: Consider browser extension (professional product)

Let me know which path you'd like to pursue!
