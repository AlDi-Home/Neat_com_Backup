# Implementation Tasks: Initial Backup System

**Feature ID:** 001-initial-backup
**Generated:** 2025-10-11
**Last Updated:** 2025-10-13
**Total Tasks:** 45

---

## Recent Updates

**2025-10-13: File Organization Implementation**
- ✅ **T022** (Implement organize_file): Completed and tested
- ✅ **T026** (Implement export_folder_files core loop): Updated to include file organization
- **Change Summary**: Added automatic file organization during download process. Files are now moved from ~/Downloads to the organized backup folder structure (e.g., ~/NeatBackup/2018 year TAX/) immediately after download completion.
- **Test Results**: Successfully tested with 12-file backup, confirmed duplicate handling and proper folder structure creation.

---

## Task Summary

| Phase | User Story | Task Count | Parallelizable |
|-------|-----------|------------|----------------|
| 1 | Setup | 6 | 4 |
| 2 | Foundation | 3 | 0 |
| 3 | US-008 (P0) | 4 | 2 |
| 4 | US-001 (P0) | 3 | 0 |
| 5 | US-002 (P0) | 3 | 0 |
| 6 | US-005 (P0) | 4 | 2 |
| 7 | US-003 (P0) | 8 | 4 |
| 8 | US-004 (P0) | 4 | 1 |
| 9 | US-006 (P1) | 3 | 1 |
| 10 | US-007 (P1) | 2 | 0 |
| 11 | US-010 (P1) | 2 | 0 |
| 12 | US-009 (P2) | 2 | 0 |
| 13 | Polish | 1 | 0 |

---

## Phase 1: Project Setup

**Goal:** Initialize project structure and dependencies

### T001: Create project directory structure
**Story:** Setup
**Type:** Setup
**Files:** `./`

Create root project directory with Python package structure:
```
NeatBackupAutomation/
├── main.py
├── config.py
├── neat_bot.py
├── utils.py
├── requirements.txt
└── README.md
```

**Acceptance:** Directory structure exists and is ready for code

---

### T002: [P] Create requirements.txt with dependencies
**Story:** Setup
**Type:** Setup
**Files:** `requirements.txt`

Create requirements.txt with pinned versions:
```
selenium==4.27.1
webdriver-manager==4.0.2
cryptography==44.0.0
```

**Acceptance:** requirements.txt exists with correct dependencies and versions

---

### T003: [P] Create README.md with project overview
**Story:** Setup
**Type:** Documentation
**Files:** `README.md`

Create README.md with:
- Project description
- Features list
- Installation instructions
- Usage instructions
- System requirements
- Troubleshooting section

**Acceptance:** README.md exists and covers all essential documentation

---

### T004: [P] Initialize Python module imports
**Story:** Setup
**Type:** Setup
**Files:** `main.py`, `config.py`, `neat_bot.py`, `utils.py`

Create empty Python files with appropriate imports:
- main.py: tkinter, threading
- config.py: cryptography.fernet, json, pathlib
- neat_bot.py: selenium, webdriver_manager
- utils.py: pathlib, time, shutil

**Acceptance:** All Python files exist with correct import statements

---

### T005: [P] Create .gitignore for Python project
**Story:** Setup
**Type:** Setup
**Files:** `.gitignore`

Create .gitignore with:
- Python cache files (__pycache__, *.pyc)
- Virtual environment (venv/, env/)
- IDE files (.vscode/, .idea/)
- OS files (.DS_Store)
- User data (~/.neat_backup/)

**Acceptance:** .gitignore exists and excludes appropriate files

---

### T006: Install and verify dependencies locally
**Story:** Setup
**Type:** Setup
**Files:** N/A

Run `pip3 install -r requirements.txt` and verify all packages install successfully.

**Acceptance:** All dependencies install without errors

---

## Phase 2: Foundation (Blocking Prerequisites)

**Goal:** Core infrastructure needed by all user stories

### T007: Create Config class skeleton with encryption setup
**Story:** Foundation
**Type:** Infrastructure
**Files:** `config.py`

Implement Config class with:
- `__init__()`: Initialize config directory and paths
- `_init_encryption()`: Generate or load Fernet encryption key
- Config directory: `~/.neat_backup/`
- Key file: `~/.neat_backup/key.key`
- Settings file: `~/.neat_backup/config.json`

**Acceptance:** Config class initializes, creates directory structure, and generates encryption key

---

### T008: Create NeatBot class skeleton with WebDriver setup
**Story:** Foundation
**Type:** Infrastructure
**Files:** `neat_bot.py`

Implement NeatBot class with:
- `__init__(config, status_callback)`: Store config and callback
- `setup_driver()`: Initialize Chrome WebDriver with ChromeDriverManager
- Basic Chrome options (download directory)
- Error handling for driver initialization

**Acceptance:** NeatBot class initializes and sets up Chrome WebDriver

---

### T009: Create utility functions module skeleton
**Story:** Foundation
**Type:** Infrastructure
**Files:** `utils.py`

Create utility function stubs:
- `wait_for_download(download_dir, filename, timeout) -> bool`
- `organize_file(source_path, folder_name, backup_root) -> Optional[str]`
- `sanitize_folder_name(name) -> str`
- `get_chrome_download_dir() -> str`

**Acceptance:** All utility function signatures exist with docstrings

---

## Phase 3: US-008 - Credential Security (P0)

**Goal:** Implement encrypted credential storage

**Independent Test Criteria:**
- Credentials can be saved with encryption
- Credentials can be loaded and decrypted
- Encrypted file contains no plaintext
- Key is stored separately from encrypted data

---

### T010: [P] Implement save_credentials() with Fernet encryption
**Story:** US-008
**Type:** Feature
**Files:** `config.py`

Implement `Config.save_credentials(username, password)`:
- Create credentials dictionary
- JSON encode credentials
- Encrypt with Fernet cipher
- Write to `~/.neat_backup/creds.enc`
- Handle encryption errors

**Acceptance:** Credentials are encrypted and saved to creds.enc file

---

### T011: [P] Implement load_credentials() with decryption
**Story:** US-008
**Type:** Feature
**Files:** `config.py`

Implement `Config.load_credentials() -> Optional[tuple]`:
- Check if creds.enc exists
- Read encrypted file
- Decrypt with Fernet cipher
- JSON decode credentials
- Return (username, password) tuple
- Return None if file doesn't exist or decryption fails

**Acceptance:** Encrypted credentials are loaded and decrypted correctly

---

### T012: Implement config get/set methods for settings
**Story:** US-008
**Type:** Feature
**Files:** `config.py`

Implement:
- `Config.get(key, default)`: Read from config.json
- `Config.set(key, value)`: Write to config.json
- Default settings: download_dir, chrome_headless, wait_timeout, download_timeout, delay_between_files

**Acceptance:** Settings can be read and persisted to config.json

---

### T013: Add credential security validation
**Story:** US-008
**Type:** Feature
**Files:** `config.py`

Add validation to ensure:
- No plaintext credentials in logs
- Credentials are only in memory when needed
- Proper error handling for missing/corrupted files

**Acceptance:** Credentials are never exposed in plaintext outside memory

---

## Phase 4: US-001 - First-Time Setup (P0)

**Goal:** GUI prompts for username and password with secure storage

**Independent Test Criteria:**
- GUI displays credential input fields
- Credentials can be entered and saved
- Visual feedback on successful storage
- Credentials persist across app restarts

---

### T014: Create GUI window with TKinter framework
**Story:** US-001
**Type:** Feature
**Files:** `main.py`

Implement NeatBackupGUI class:
- `__init__()`: Initialize root window, config
- Window title: "Neat Backup Automation v1.0"
- Window size: 600x500
- Configure grid layout
- Create blue header with white text

**Acceptance:** GUI window opens with proper title and header

---

### T015: Add credentials section to GUI
**Story:** US-001
**Type:** Feature
**Files:** `main.py`

Add to `create_widgets()`:
- Username label and entry field
- Password label and entry field
- "Show password" checkbox
- "Remember credentials" checkbox
- Password masking toggle functionality
- StringVar and BooleanVar for form state

**Acceptance:** Credentials section displays with all input fields functional

---

### T016: Implement credential auto-load on startup
**Story:** US-001
**Type:** Feature
**Files:** `main.py`

In `__init__()`:
- Call `config.load_credentials()`
- If credentials exist, populate username and password fields
- Log "Loaded saved credentials" to status
- Enable "Remember credentials" checkbox

**Acceptance:** Saved credentials auto-populate on app launch

---

## Phase 5: US-002 - Select Backup Location (P0)

**Goal:** User can choose backup directory location

**Independent Test Criteria:**
- Default location displays correctly
- Browse button opens directory picker
- Selected path is saved and persists
- Directory validation works

---

### T017: Add backup location section to GUI
**Story:** US-002
**Type:** Feature
**Files:** `main.py`

Add to `create_widgets()`:
- "Backup Location" label
- Entry field showing current path
- "Browse..." button
- Default value: `~/NeatBackup` (expand to full path)
- StringVar for path storage

**Acceptance:** Backup location section displays with default path

---

### T018: Implement directory browse dialog
**Story:** US-002
**Type:** Feature
**Files:** `main.py`

Implement `browse_directory()`:
- Open tkinter.filedialog.askdirectory()
- Update location entry with selected path
- Call `config.set('download_dir', path)`
- Handle user cancellation

**Acceptance:** Browse button opens directory picker and updates path

---

### T019: Add directory validation before backup
**Story:** US-002
**Type:** Feature
**Files:** `main.py`

In `start_backup()`:
- Check if directory exists
- Check if directory is writable
- Create directory if it doesn't exist
- Show error message if validation fails

**Acceptance:** Directory is validated and created if needed before backup starts

---

## Phase 6: US-005 - Organized File Structure (P0)

**Goal:** Files are organized in folders matching Neat.com structure

**Independent Test Criteria:**
- Folder structure mirrors Neat.com
- Files maintain original names
- Duplicate names handled with counter
- Special characters sanitized

---

### T020: [P] Implement sanitize_folder_name()
**Story:** US-005
**Type:** Feature
**Files:** `utils.py`

Implement `sanitize_folder_name(name) -> str`:
- Remove invalid characters: `< > : " / \ | ? *`
- Replace with underscore
- Trim leading/trailing whitespace
- Handle empty string case

**Acceptance:** Folder names are sanitized for filesystem compatibility

---

### T021: [P] Implement wait_for_download()
**Story:** US-005
**Type:** Feature
**Files:** `utils.py`

Implement `wait_for_download(download_dir, filename, timeout) -> bool`:
- Poll for file existence every 0.5 seconds
- Check that .crdownload file is removed
- Return True if file exists and complete
- Return False if timeout exceeded
- Default timeout: 30 seconds

**Acceptance:** Function waits for download completion correctly

---

### T022: Implement organize_file() ✅ COMPLETED
**Story:** US-005
**Type:** Feature
**Files:** `utils.py`

Implement `organize_file(source_path, folder_name, backup_root) -> Optional[str]`:
- Create destination folder: `{backup_root}/{sanitized_folder_name}/`
- Check for duplicate filenames
- Append counter if duplicate exists (file_1.pdf, file_2.pdf)
- Move file from Downloads to backup location
- Return final path or None on failure

**Acceptance:** Files are organized into correct folders with duplicate handling

**Status:** ✅ Implemented and tested. Successfully organizes files into folder structure matching Neat.com hierarchy with automatic duplicate name handling.

---

### T023: Implement get_chrome_download_dir()
**Story:** US-005
**Type:** Feature
**Files:** `utils.py`

Implement `get_chrome_download_dir() -> str`:
- Detect OS (macOS, Windows, Linux)
- Return default Chrome download directory for each OS
- macOS: `~/Downloads`
- Windows: `C:\Users\{user}\Downloads`
- Linux: `~/Downloads`

**Acceptance:** Function returns correct download directory for current OS

---

## Phase 7: US-003 - One-Click Backup (P0)

**Goal:** Single button initiates complete automated backup

**Independent Test Criteria:**
- Start button initiates backup
- Browser opens and logs in automatically
- All folders discovered
- All files exported and downloaded
- Process completes without intervention

---

### T024: [P] Implement login() in NeatBot
**Story:** US-003
**Type:** Feature
**Files:** `neat_bot.py`

Implement `NeatBot.login(username, password) -> bool`:
- Navigate to https://app.neat.com/
- Check if already logged in (dashboard visible)
- If not logged in: fill username, password fields
- Click login button
- Wait for dashboard to load
- Return True on success, False on failure

**Acceptance:** Login automation works for Neat.com

---

### T025: [P] Implement get_folders() in NeatBot
**Story:** US-003
**Type:** Feature
**Files:** `neat_bot.py`

Implement `NeatBot.get_folders() -> List[tuple]`:
- Expand "My Cabinet" sidebar
- Find all folder elements
- Extract folder name and selector for each
- Return list of (folder_name, selector) tuples
- Handle case where no folders found

**Acceptance:** All folders are discovered and returned with selectors

---

### T026: [P] Implement export_folder_files() core loop ✅ COMPLETED
**Story:** US-003
**Type:** Feature
**Files:** `neat_bot.py`

Implement `NeatBot.export_folder_files(folder_name, selector) -> int`:
- Click folder to open
- Find all file checkboxes
- For each file:
  - Click checkbox to select
  - Click Export button
  - Click PDF option in dropdown
  - Wait for download link
  - Click download
  - Wait for download completion
  - Organize file to backup directory
  - Uncheck checkbox
- Return count of exported files

**Acceptance:** All files in a folder are exported and organized

**Status:** ✅ Implemented and tested. Complete workflow now includes:
- Download monitoring (waits for .crdownload removal)
- Automatic file organization into Neat.com folder structure
- Real-time status logging with saved file paths
- Tested successfully with 12-file folder backup

---

### T027: [P] Implement run_backup() orchestration
**Story:** US-003
**Type:** Feature
**Files:** `neat_bot.py`

Implement `NeatBot.run_backup(username, password) -> dict`:
- Call setup_driver()
- Call login(username, password)
- If login fails, return error
- Call get_folders() to discover all folders
- For each folder, call export_folder_files()
- Accumulate statistics (total folders, total files)
- Call cleanup()
- Return statistics dictionary

**Acceptance:** Complete backup process runs from start to finish

---

### T028: Add "Start Backup" button to GUI
**Story:** US-003
**Type:** Feature
**Files:** `main.py`

Add to `create_widgets()`:
- "Start Backup" button (large, prominent)
- Green background color
- Bind to `start_backup()` method
- Initially enabled

**Acceptance:** Start button displays and can be clicked

---

### T029: Implement start_backup() in GUI
**Story:** US-003
**Type:** Feature
**Files:** `main.py`

Implement `start_backup()`:
- Validate credentials entered
- Validate backup location
- Disable Start button
- Enable Stop button
- Create NeatBot instance
- Launch `run_backup_thread()` in background thread

**Acceptance:** Clicking Start initiates backup in background thread

---

### T030: Implement run_backup_thread() with threading
**Story:** US-003
**Type:** Feature
**Files:** `main.py`

Implement `run_backup_thread(username, password)`:
- Create NeatBot instance with status callback
- Call bot.run_backup(username, password)
- Capture statistics
- Use `root.after()` to call `backup_complete(stats)` on main thread
- Handle exceptions and report errors

**Acceptance:** Backup runs in background without freezing GUI

---

### T031: Implement cleanup() in NeatBot
**Story:** US-003
**Type:** Feature
**Files:** `neat_bot.py`

Implement `NeatBot.cleanup()`:
- Call driver.quit() to close browser
- Handle case where driver is None
- Log cleanup completion

**Acceptance:** Browser closes cleanly after backup completes

---

## Phase 8: US-004 - Progress Tracking (P0)

**Goal:** Real-time progress updates in GUI

**Independent Test Criteria:**
- Status log shows current operation
- Progress bar animates during activity
- File/folder counts display
- Color-coded messages

---

### T032: Add status log widget to GUI
**Story:** US-004
**Type:** Feature
**Files:** `main.py`

Add to `create_widgets()`:
- ScrolledText widget for status log
- Configure as read-only
- Set fixed-width font
- Add color tags: INFO (black), SUCCESS (green), WARNING (orange), ERROR (red)
- Scrollbar for long logs

**Acceptance:** Status log displays and is scrollable

---

### T033: [P] Add progress bar to GUI
**Story:** US-004
**Type:** Feature
**Files:** `main.py`

Add to `create_widgets()`:
- ttk.Progressbar widget
- Indeterminate mode (animated)
- Start animation when backup begins
- Stop animation when backup completes

**Acceptance:** Progress bar displays and animates during backup

---

### T034: Implement log_status() method
**Story:** US-004
**Type:** Feature
**Files:** `main.py`

Implement `log_status(message, level='INFO')`:
- Append timestamp to message
- Insert message into status log
- Apply color tag based on level
- Auto-scroll to bottom
- Use thread-safe `root.after()` if called from worker thread

**Acceptance:** Status messages appear in log with correct colors

---

### T035: Add status callback to NeatBot operations
**Story:** US-004
**Type:** Feature
**Files:** `neat_bot.py`

Update all NeatBot methods to call status_callback():
- "Chrome WebDriver initialized"
- "Navigating to Neat.com..."
- "Login successful!" / "Login failed"
- "Found folder: {folder_name}"
- "Opening folder: {folder_name}"
- "Found {count} files in {folder_name}"
- "Processing file {n}/{total} in {folder_name}"
- "Downloading: {filename}"
- "Saved: {filepath}"

**Acceptance:** All operations log status messages through callback

---

## Phase 9: US-006 - Error Recovery (P1)

**Goal:** Backup continues even if individual files fail

**Independent Test Criteria:**
- Failed files are logged with error reason
- Process continues to next file
- Summary shows success/failure counts
- No crashes from individual failures

---

### T036: Add try-catch blocks in export_folder_files()
**Story:** US-006
**Type:** Feature
**Files:** `neat_bot.py`

Wrap file export operations in try-catch:
- Catch selenium exceptions
- Catch timeout exceptions
- Log error with file name and reason
- Continue to next file instead of aborting
- Track failed file count

**Acceptance:** Individual file failures don't stop entire backup

---

### T037: [P] Add retry logic for transient failures
**Story:** US-006
**Type:** Feature
**Files:** `neat_bot.py`

Implement retry logic (max 3 attempts):
- Element not found errors
- Stale element reference errors
- Timeout errors
- Wait 1 second between retries
- Log retry attempts

**Acceptance:** Transient errors are retried before giving up

---

### T038: Add error statistics to backup results
**Story:** US-006
**Type:** Feature
**Files:** `neat_bot.py`

Update statistics dictionary to include:
- `total_folders`: int
- `total_files`: int
- `successful_files`: int
- `failed_files`: int
- `errors`: List[str] (file name and error message)

**Acceptance:** Statistics include success and failure counts

---

## Phase 10: US-007 - Pause and Stop (P1)

**Goal:** User can stop backup in progress

**Independent Test Criteria:**
- Stop button is available during backup
- Clicking Stop terminates gracefully
- No partial downloads left
- GUI returns to ready state

---

### T039: Add "Stop" button to GUI
**Story:** US-007
**Type:** Feature
**Files:** `main.py`

Add to `create_widgets()`:
- "Stop" button next to Start button
- Red background color
- Initially disabled
- Bind to `stop_backup()` method
- Enable when backup starts, disable when backup completes

**Acceptance:** Stop button displays and is enabled during backup

---

### T040: Implement stop_backup() with threading flag
**Story:** US-007
**Type:** Feature
**Files:** `main.py`

Implement `stop_backup()`:
- Set thread-safe stop flag
- Call bot.cleanup() to close browser
- Log "Backup stopped by user"
- Re-enable Start button
- Disable Stop button
- Stop progress bar animation

**Acceptance:** Clicking Stop terminates backup gracefully

---

## Phase 11: US-010 - Completion Summary (P1)

**Goal:** Display summary dialog on backup completion

**Independent Test Criteria:**
- Modal dialog appears on completion
- Shows total folders and files
- Shows success/failure counts
- Provides link to backup directory

---

### T041: Implement backup_complete() callback
**Story:** US-010
**Type:** Feature
**Files:** `main.py`

Implement `backup_complete(stats)`:
- Stop progress bar
- Re-enable Start button
- Disable Stop button
- Log completion to status
- Call `show_completion_dialog(stats)`

**Acceptance:** Backup completion triggers UI updates

---

### T042: Implement show_completion_dialog()
**Story:** US-010
**Type:** Feature
**Files:** `main.py`

Implement `show_completion_dialog(stats)`:
- Create modal dialog with messagebox
- Display:
  - "Backup Complete!"
  - "Successfully exported {count} files from {folders} folders!"
  - Success/failure breakdown if any failures
  - "Location: {backup_path}"
- OK button to close dialog

**Acceptance:** Completion dialog displays with accurate statistics

---

## Phase 12: US-009 - Headless Operation (P2)

**Goal:** Option to run browser in background

**Independent Test Criteria:**
- Checkbox for headless mode
- Headless mode works without visible browser
- All functionality works in headless mode
- Performance improvement measurable

---

### T043: Add headless mode checkbox to GUI
**Story:** US-009
**Type:** Feature
**Files:** `main.py`

Add to `create_widgets()`:
- "Run browser in background" checkbox
- BooleanVar for state
- Save state to config when changed
- Load state from config on startup

**Acceptance:** Headless mode checkbox displays and persists

---

### T044: Implement headless mode in setup_driver()
**Story:** US-009
**Type:** Feature
**Files:** `neat_bot.py`

Update `setup_driver()`:
- Read headless setting from config
- If headless=True, add `--headless=new` to chrome_options
- Log "Running in headless mode" or "Running with visible browser"

**Acceptance:** Browser runs in headless mode when checkbox enabled

---

## Phase 13: Polish & Integration

**Goal:** Final integration and documentation

---

### T045: Final integration testing and documentation
**Story:** Polish
**Type:** Testing
**Files:** All

Perform end-to-end testing:
- Fresh install on macOS/Windows/Linux
- Test all user stories in sequence
- Verify error handling
- Update README with any findings
- Create QUICKSTART guide
- Verify all acceptance criteria met

**Acceptance:** All user stories work end-to-end, documentation complete

---

## Dependencies

### Story Completion Order (MVP Path)

**MVP (Minimum Viable Product):**
1. Phase 1-2: Setup & Foundation
2. Phase 3: US-008 (Credential Security)
3. Phase 4: US-001 (First-Time Setup)
4. Phase 5: US-002 (Backup Location)
5. Phase 6: US-005 (File Organization)
6. Phase 7: US-003 (One-Click Backup)
7. Phase 8: US-004 (Progress Tracking)

**Post-MVP:**
8. Phase 9: US-006 (Error Recovery)
9. Phase 10: US-007 (Stop Button)
10. Phase 11: US-010 (Completion Summary)
11. Phase 12: US-009 (Headless Mode)

### Critical Path
```
Setup → Foundation → Security → GUI → Backup Logic → Progress Tracking
```

All user stories after US-004 can be implemented independently.

---

## Parallel Execution Opportunities

### Phase 1 (Setup)
Parallel: T002, T003, T004, T005 (4 tasks - different files)

### Phase 3 (US-008)
Parallel: T010, T011 (2 tasks - different methods)

### Phase 6 (US-005)
Parallel: T020, T021 (2 tasks - different functions)

### Phase 7 (US-003)
Parallel: T024, T025, T026, T027 (4 tasks - different methods)

### Phase 8 (US-004)
Parallel: T033 (can be done alongside T032)

### Phase 9 (US-006)
Parallel: T037 (can be done alongside T036)

---

## Implementation Strategy

### Incremental Delivery Plan

**Sprint 1 (MVP Core):** T001-T023
- Setup, Foundation, Security, Basic GUI
- **Deliverable:** User can enter credentials and select backup location

**Sprint 2 (MVP Backup):** T024-T031
- Login, folder discovery, file export logic
- **Deliverable:** Complete backup automation works

**Sprint 3 (MVP Polish):** T032-T035
- Progress tracking and user feedback
- **Deliverable:** Full user experience with real-time updates

**Sprint 4 (Enhancements):** T036-T044
- Error handling, stop functionality, completion summary, headless mode
- **Deliverable:** Production-ready with all P1/P2 features

**Sprint 5 (Final):** T045
- Testing, documentation, release preparation
- **Deliverable:** Fully documented and tested v1.0

---

## Testing Checkpoints

After each phase, verify:

**Phase 3 Checkpoint:** Credentials can be saved and loaded securely
**Phase 4 Checkpoint:** GUI displays with credential inputs
**Phase 5 Checkpoint:** Backup location can be selected and saved
**Phase 6 Checkpoint:** Files can be organized into folders correctly
**Phase 7 Checkpoint:** Complete backup runs from start to finish
**Phase 8 Checkpoint:** Status updates appear in real-time
**Phase 9 Checkpoint:** Individual file failures don't crash backup
**Phase 10 Checkpoint:** Stop button terminates backup gracefully
**Phase 11 Checkpoint:** Completion dialog displays statistics
**Phase 12 Checkpoint:** Headless mode works without visible browser

---

## Notes

- All tasks marked [P] can be executed in parallel with other [P] tasks in the same phase
- Tasks without [P] must be executed sequentially within their phase
- Each user story phase is independently testable and deliverable
- Testing is not included as the spec indicates this is implemented and tested already
- Total estimated effort: ~40-60 hours for complete implementation
- MVP can be delivered in ~20-30 hours (Phases 1-8)

---

**Generated by:** Claude (Anthropic AI)
**Based on:** spec.md v1.0, plan.md v1.0
**Status:** Ready for implementation
