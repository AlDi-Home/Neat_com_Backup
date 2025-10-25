# Known Issues and Limitations

## 1. Virtual Scrolling Limitation (Folders with 12+ Files)

**Issue:** Neat.com uses virtual scrolling that only renders ~12 file checkboxes at a time in the viewport, even when pagination is set to show 100 items per page. This means folders with more than 12 files will only process the first 12 files on initial backup.

**Affected Folders:**
- 2013 year TAX (23 files) - processes 12/23
- Any folder with >12 files

**Technical Details:**
- Pagination successfully set to 100 items ✅
- Total file count correctly detected (e.g., "Showing 23 items") ✅
- Virtual scroller only renders visible items ❌
- Aggressive scrolling attempts implemented but insufficient ⚠️

**Workarounds:**

### Option 1: Multiple Backup Runs (Recommended)
Run the backup multiple times. On subsequent runs:
1. Already-downloaded files will be skipped (duplicate detection)
2. New files will be downloaded
3. Eventually all files will be captured

**Usage:**
```bash
python3 main.py  # Run backup
# Check folder: 12/23 files downloaded
python3 main.py  # Run again
# Check folder: 23/23 files downloaded (may need 2-3 runs)
```

### Option 2: Manual Download for Large Folders
For folders with many files:
1. Run automated backup to get bulk of files
2. Manually download remaining files from Neat.com web interface
3. Place in same folder structure: `~/NeatBackup/{FolderName}/`

### Option 3: Reduce Files Per Folder
Organize files in Neat.com into smaller folders (<12 files each) before backup.

**Status:** ⚠️ CONFIRMED LIMITATION (Tested 2025-10-14)

**Attempted Solutions:**
1. ✅ Set pagination to 100 items (verified working)
2. ✅ Aggressive scrolling (window, grid container, checkbox-based)
3. ❌ JavaScript height/overflow manipulation (tested, ineffective)
4. ❌ CSS override attempts (DOM manipulation doesn't force render)

**Root Cause:** Neat.com uses a sophisticated virtual scroller (likely React Window or similar) that maintains a virtualized list state in JavaScript. Simply manipulating CSS properties doesn't trigger the re-render needed to load all items into the DOM.

**Test Results (2013 year TAX folder, 23 files):**
- ✅ Pagination set to 100: Confirmed
- ✅ Total files detected: 23
- ❌ Checkboxes rendered: Only 12
- ❌ JavaScript CSS override: No effect

**Recommendation:** Use Option 1 (Multiple Backup Runs) as primary strategy.

---

## 2. CAPTCHA on Login

**Issue:** Neat.com may present CAPTCHA challenges during login, especially:
- First login from new location
- After multiple login attempts
- Suspicious activity detection

**Solution:** ✅ IMPLEMENTED
- System automatically detects CAPTCHA
- Pauses for up to 60 seconds
- User solves CAPTCHA manually in browser window
- Automation continues after detection

**Usage:**
When you see: `⚠️ CAPTCHA detected! Please solve manually`
1. Look at the browser window that opened
2. Solve the CAPTCHA (click images, checkboxes, etc.)
3. System automatically detects completion and continues

**Prevention:**
- Headless mode disabled by default (reduces CAPTCHA frequency)
- Saved credentials reduce re-login needs
- Reasonable delays between operations

---

## 3. Neat.com UI Changes

**Risk:** Neat.com may update their web interface, breaking CSS selectors.

**Mitigation:**
- Multiple fallback selectors for critical elements
- Detailed error logging for troubleshooting
- Selector update guide in README

**Signs of UI Changes:**
- "Element not found" errors
- Backup stuck at certain step
- Files not downloading despite no errors

**Resolution:**
- Check GitHub issues for updates
- Update selectors in `neat_bot.py`
- Report issue with screenshots

---

## 4. Rate Limiting

**Observation:** No rate limiting detected yet, but possible.

**Prevention:**
- Configurable delays between file downloads (default: 0.5s)
- Sequential processing (not parallel)
- Respectful of server resources

**If Rate Limited:**
- Increase `delay_between_files` in settings
- Run backup during off-peak hours
- Process fewer folders per session
