# Technical Plan: Initial Backup System

**Feature ID:** 001-initial-backup  
**Plan Version:** 1.0  
**Last Updated:** January 2025

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE (GUI)                      │
│                        main.py                               │
│  • TKinter GUI framework                                     │
│  • Threading for non-blocking operations                     │
│  • Real-time status callbacks                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               CONFIGURATION MANAGER                          │
│                     config.py                                │
│  • Fernet encryption for credentials                         │
│  • JSON-based settings persistence                           │
│  • Key management (~/.neat_backup/key.key)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  AUTOMATION ENGINE                           │
│                     neat_bot.py                              │
│  • Selenium WebDriver initialization                         │
│  • Chrome automation (login, navigate, export)               │
│  • Error handling and retry logic                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FILE MANAGEMENT SYSTEM                          │
│                     utils.py                                 │
│  • Download monitoring                                       │
│  • File organization (nested folders)                        │
│  • Path sanitization                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Technologies

**Language:** Python 3.8+
- **Rationale:** Cross-platform, extensive library support, readable syntax
- **Minimum Version:** 3.8 (for type hints, walrus operator)

**Browser Automation:** Selenium WebDriver 4.27.1
- **Rationale:** Industry standard, mature API, excellent Chrome support
- **Alternative Considered:** Playwright (rejected: heavier, less stable ChromeDriver management)

**Encryption:** cryptography 44.0.0 (Fernet)
- **Rationale:** Symmetric encryption, simple API, secure defaults
- **Algorithm:** AES-128 in CBC mode with HMAC authentication

**GUI Framework:** TKinter (built-in)
- **Rationale:** No external dependencies, cross-platform, sufficient for needs
- **Alternative Considered:** PyQt (rejected: licensing complexity, overkill)

**Driver Management:** webdriver-manager 4.0.2
- **Rationale:** Automatic ChromeDriver download/version matching
- **Fallback:** Manual ChromeDriver installation documented

---

## Module Breakdown

### 1. main.py (GUI Application)

**Responsibilities:**
- User interface rendering
- User input collection
- Background thread management
- Status callback handling

**Key Classes:**

```python
class NeatBackupGUI:
    def __init__(self)
    def create_widgets(self)
    def start_backup(self)
    def run_backup_thread(self, username, password)
    def log_status(self, message, level)
    def backup_complete(self, stats)
```

**Threading Model:**
- Main thread: GUI event loop (TKinter)
- Worker thread: Backup operation (Selenium)
- Communication: Status callbacks via `root.after()`

**State Management:**
- Form inputs: TKinter StringVar, BooleanVar
- Backup state: Thread-local in worker
- Progress: Updated via callback to main thread

---

### 2. config.py (Configuration Manager)

**Responsibilities:**
- Credential encryption/decryption
- Settings persistence
- Configuration validation

**Key Classes:**

```python
class Config:
    def __init__(self)
    def _init_encryption(self)
    def save_credentials(self, username, password)
    def load_credentials(self) -> Optional[tuple]
    def get(self, key, default)
    def set(self, key, value)
```

**File Locations:**
- Config directory: `~/.neat_backup/`
- Settings: `~/.neat_backup/config.json`
- Credentials: `~/.neat_backup/creds.enc`
- Encryption key: `~/.neat_backup/key.key`

**Encryption Flow:**
```
Plaintext → JSON encode → Fernet encrypt → Binary file
Binary file → Fernet decrypt → JSON decode → Plaintext
```

---

### 3. neat_bot.py (Automation Engine)

**Responsibilities:**
- Chrome WebDriver lifecycle
- Neat.com login automation
- Folder discovery
- File export workflow
- Download monitoring

**Key Classes:**

```python
class NeatBot:
    def __init__(self, config, status_callback)
    def setup_driver(self)
    def login(self, username, password) -> bool
    def get_folders(self) -> List[tuple]
    def export_folder_files(self, folder_name, selector) -> int
    def run_backup(self, username, password) -> dict
    def cleanup(self)
```

**Selenium Workflow:**

```
1. setup_driver()
   ├─ Initialize Chrome with download prefs
   ├─ Configure headless mode (optional)
   └─ Set WebDriverWait timeout

2. login(username, password)
   ├─ Navigate to app.neat.com
   ├─ Check if already logged in
   ├─ Fill credentials if needed
   └─ Wait for dashboard

3. get_folders()
   ├─ Expand "My Cabinet" sidebar
   ├─ Find all folder elements
   └─ Return (name, selector) tuples

4. export_folder_files(folder_name, selector)
   ├─ Click folder to open
   ├─ Get all file checkboxes
   ├─ For each file:
   │  ├─ Click checkbox
   │  ├─ Click Export button
   │  ├─ Click PDF option (dropdown)
   │  ├─ Wait for download link
   │  ├─ Click download
   │  ├─ Monitor download completion
   │  ├─ Organize file
   │  └─ Uncheck checkbox
   └─ Return exported count

5. cleanup()
   └─ driver.quit()
```

**Selector Strategy:**

Priority order:
1. `data-testid` attributes (most stable)
2. Unique CSS classes
3. XPath (last resort)

**Critical Selectors:**
```python
FOLDER_SELECTOR = '[data-testid="mycabinet-{folder_name}"]'
CHECKBOX_SELECTOR = 'input[id^="checkbox-"]:not(#header-checkbox)'
EXPORT_BUTTON = '[data-testid="export-button"]'
DOWNLOAD_LINK = 'a[download*=".pdf"]'
```

**Error Handling:**
- Login failures: Return False, log error
- Element not found: Retry with fallback selectors (max 3)
- Download timeout: Log error, continue to next file
- Stale element: Re-locate element, retry operation

---

### 4. utils.py (Utility Functions)

**Responsibilities:**
- Download completion verification
- File organization
- Path sanitization
- Platform detection

**Key Functions:**

```python
def wait_for_download(download_dir, filename, timeout) -> bool
def organize_file(source_path, folder_name, backup_root) -> Optional[str]
def sanitize_folder_name(name) -> str
def get_chrome_download_dir() -> str
```

**Download Verification Logic:**

```python
while time_elapsed < timeout:
    if file_exists and no_crdownload:
        return True
    sleep(0.5)
return False
```

**File Organization Flow:**

```
1. Create destination folder structure
   ~/NeatBackup/{sanitized_folder_name}/

2. Determine final filename
   - Check for duplicates
   - Append counter if exists (file_1.pdf, file_2.pdf)

3. Move file from Downloads to backup location

4. Return final path or None on failure
```

**Path Sanitization:**
- Remove: `< > : " / \ | ? *`
- Replace with: `_`
- Trim whitespace

---

## Data Models

### Configuration Schema

```json
{
  "download_dir": "~/NeatBackup",
  "chrome_headless": false,
  "wait_timeout": 10,
  "download_timeout": 30,
  "delay_between_files": 1
}
```

### Encrypted Credentials Schema

```json
{
  "username": "user@example.com",
  "password": "encrypted_password"
}
```

### Backup Statistics Schema

```python
{
    'total_folders': int,
    'total_files': int,
    'success': bool,
    'errors': List[str]  # Future enhancement
}
```

---

## Selenium Implementation Details

### WebDriver Configuration

```python
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

if headless:
    chrome_options.add_argument('--headless=new')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
```

### Explicit Wait Strategy

```python
wait = WebDriverWait(driver, timeout)

# Wait for element presence
element = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
)

# Wait for element clickable
button = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
)
```

### JavaScript Execution (when needed)

```python
# Click element that's obscured
driver.execute_script("arguments[0].click();", element)

# Scroll into view
driver.execute_script("arguments[0].scrollIntoView();", element)
```

---

## Security Architecture

### Credential Storage

**Encryption Process:**
```
1. User enters password → GUI
2. JSON.dumps({'username': u, 'password': p})
3. Fernet.encrypt(json_bytes)
4. Write to ~/.neat_backup/creds.enc
```

**Decryption Process:**
```
1. Read ~/.neat_backup/creds.enc
2. Fernet.decrypt(encrypted_bytes)
3. JSON.loads(decrypted_bytes)
4. Return (username, password)
```

**Key Generation:**
```python
if not key_file.exists():
    key = Fernet.generate_key()  # 32-byte URL-safe base64
    key_file.write_bytes(key)

cipher = Fernet(key_file.read_bytes())
```

**Security Properties:**
- Algorithm: AES-128 (via Fernet)
- Mode: CBC with PKCS7 padding
- Authentication: HMAC-SHA256
- Key derivation: Secure random generation

---

## File System Layout

### Application Directory

```
~/.neat_backup/
├── config.json       # User settings
├── creds.enc         # Encrypted credentials
└── key.key           # Encryption key (keep secure!)
```

### Backup Directory

```
~/NeatBackup/          # Or user-configured location
├── 2024 year TAX/
│   ├── Notice of assessment Sveta 2024 - Health.pdf
│   ├── Viktor_cra_2024 - Money.pdf
│   └── ...
├── 2023 year TAX/
│   └── ...
└── Business/
    └── ...
```

---

## Performance Considerations

### Bottlenecks

1. **Network I/O** (Primary)
   - Download speed: User's internet connection
   - Neat.com API response time
   - Mitigation: Configurable timeouts

2. **Selenium Overhead** (Secondary)
   - Browser rendering: ~200-500ms per operation
   - Element location: ~50-100ms per find
   - Mitigation: Headless mode, optimized selectors

3. **Disk I/O** (Minimal)
   - File moves: Fast (same disk)
   - Write operations: Negligible

### Optimization Strategies

**Current:**
- Sequential processing (reliable, rate-limit friendly)
- Headless mode option (~15% faster)
- Configurable delays (trade speed vs. stability)

**Future Considerations:**
- Parallel downloads (requires rate limit research)
- Connection pooling (browser reuse)
- Download queue optimization

---

## Error Handling Strategy

### Error Categories

**Category 1: Fatal Errors (Stop Execution)**
- Login failure
- Chrome driver initialization failure
- Config file corruption

**Category 2: Recoverable Errors (Retry)**
- Element not found (retry with fallback selector)
- Stale element reference (re-locate and retry)
- Transient network issues (retry up to 3x)

**Category 3: Non-Blocking Errors (Log & Continue)**
- Single file download failure
- File organization failure
- Individual folder access denied

### Retry Logic

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        operation()
        break
    except RetryableException as e:
        if attempt == max_retries - 1:
            log_error(e)
            continue_to_next()
        else:
            time.sleep(1)
```

---

## Testing Strategy

### Manual Testing Checklist

**Pre-Release Validation:**
- [ ] Fresh install on macOS
- [ ] Fresh install on Windows
- [ ] Fresh install on Linux
- [ ] Credential save/load cycle
- [ ] Backup with saved credentials
- [ ] Backup without saving credentials
- [ ] Headless mode operation
- [ ] Stop backup mid-process
- [ ] Network interruption handling
- [ ] Duplicate filename handling
- [ ] Special character in folder names
- [ ] 100+ file backup completion

### Future Automated Testing

**Unit Tests (utils.py):**
- Path sanitization
- Download verification logic
- File organization

**Integration Tests (neat_bot.py):**
- Login flow (mock Neat.com)
- Folder discovery
- Export workflow

**End-to-End Tests:**
- Complete backup simulation
- Error scenarios

---

## Deployment

### Installation Steps

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Run application
python3 main.py
```

### System Requirements

**Minimum:**
- Python 3.8+
- Chrome browser 141+
- 100 MB free disk space
- Internet connection

**Recommended:**
- Python 3.10+
- Chrome browser latest
- 1 GB free disk space (for large libraries)
- Stable high-speed internet

---

## Monitoring & Observability

### Logging Strategy

**GUI Status Log:**
- Level: INFO, WARNING, ERROR, SUCCESS
- Color-coded for visibility
- Timestamped entries
- Scrollable history

**Future Enhancements:**
- File-based logging
- Structured log format (JSON)
- Log rotation
- Metrics collection (files/minute, success rate)

---

## Scalability Considerations

### Current Limits

- **Files:** 1,000-2,000 (tested scenario)
- **Folders:** 20-30 (practical limit)
- **Time:** 2-4 hours (sequential processing)

### Future Scalability

**Vertical Scaling:**
- Faster internet connection
- More CPU cores (for parallel processing)
- SSD storage (faster file operations)

**Horizontal Scaling:**
- Multi-account support
- Distributed backup (multiple machines)

---

## Maintenance

### Selector Maintenance

**When Neat.com UI Changes:**
1. User reports errors
2. Inspect new UI elements
3. Update selectors in `neat_bot.py`
4. Test on all platforms
5. Release patch version

**Monitoring:**
- User error reports
- Periodic manual testing
- Selenium exception patterns

### Dependency Updates

**Update Cycle:** Quarterly review

```bash
# Check for updates
pip list --outdated

# Update and test
pip install --upgrade selenium webdriver-manager cryptography
python3 main.py  # Test thoroughly
```

---

## Risk Mitigation

### Technical Risks

**Risk:** ChromeDriver version mismatch  
**Mitigation:** webdriver-manager auto-updates

**Risk:** Selenium element not found  
**Mitigation:** Retry with fallback selectors

**Risk:** Download timeout on slow connections  
**Mitigation:** Configurable timeout (default 30s)

**Risk:** Disk space exhaustion  
**Mitigation:** Pre-check available space (future)

### Operational Risks

**Risk:** Neat.com rate limiting  
**Mitigation:** Sequential processing, respectful delays

**Risk:** Credential compromise  
**Mitigation:** Fernet encryption, separate key storage

**Risk:** Data loss during backup  
**Mitigation:** Verify downloads before organizing

---

## Future Enhancements

### Phase 2 Features (v2.0)

1. **Incremental Backup**
   - Compare local files to Neat.com
   - Only download new/modified files
   - Significantly faster for repeated backups

2. **Multi-Account Support**
   - Manage multiple Neat.com accounts
   - Switch between accounts in GUI
   - Separate backup directories

3. **Cloud Integration**
   - Auto-upload to Google Drive
   - OneDrive/Dropbox support
   - Configurable sync rules

4. **Scheduling**
   - Cron job integration
   - Windows Task Scheduler support
   - Email notifications

5. **Advanced Reporting**
   - HTML/PDF backup reports
   - Backup history tracking
   - File change detection

---

## Approval

**Technical Lead:** Claude (Anthropic AI)  
**Reviewed By:** Alex Diomin, IT Director  
**Implementation Status:** Complete  
**Version:** 1.0.0

---

This technical plan serves as the implementation blueprint for the Neat Backup Automation system.
