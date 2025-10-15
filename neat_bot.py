"""
Core Selenium automation for Neat.com backup
"""
import json
import time
from pathlib import Path
from typing import List, Callable, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from utils import wait_for_download, organize_file, sanitize_folder_name, get_chrome_download_dir

class NeatBot:
    """Automated backup bot for Neat.com"""
    
    def __init__(self, config, status_callback: Optional[Callable] = None):
        """
        Initialize the bot
        
        Args:
            config: Configuration object
            status_callback: Function to call with status updates
        """
        self.config = config
        self.status_callback = status_callback
        self.driver = None
        self.chrome_download_dir = get_chrome_download_dir()
        self.failed_files = []  # Store failed files for retry: [(folder_name, folder_selector, file_index)]
        
    def _log(self, message: str, level: str = 'info'):
        """Log message and send to callback"""
        print(f"[{level.upper()}] {message}")
        if self.status_callback:
            self.status_callback(message, level)
    
    def setup_driver(self):
        """Initialize Chrome WebDriver with download settings and network monitoring"""
        chrome_options = Options()

        # Download settings
        prefs = {
            "download.default_directory": self.chrome_download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Enable performance logging for network monitoring (CDP)
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        # Headless mode option
        if self.config.get('chrome_headless', False):
            chrome_options.add_argument('--headless=new')

        # Initialize driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, self.config.get('wait_timeout', 10))

        # Enable CDP Network domain for response interception
        try:
            self.driver.execute_cdp_cmd('Network.enable', {})
            self._log("Chrome WebDriver initialized with network monitoring")
        except Exception as e:
            self._log(f"Chrome WebDriver initialized (network monitoring unavailable: {e})", "warning")
    
    def login(self, username: str, password: str) -> bool:
        """
        Login to Neat.com
        
        Args:
            username: Neat username
            password: Neat password
        
        Returns:
            True if login successful
        """
        try:
            self._log("Navigating to Neat.com...")
            self.driver.get("https://app.neat.com/")
            
            # Wait for login form or already logged in
            time.sleep(3)
            
            # Check if already logged in (folder view appears)
            if "files/folders" in self.driver.current_url:
                self._log("Already logged in!", "success")
                return True
            
            # Otherwise, login
            self._log("Entering credentials...")

            # Find and fill username
            username_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"], input[name="username"], input[id*="user"]'))
            )
            username_field.send_keys(username)

            # Find and fill password
            password_field = self.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password_field.send_keys(password)

            # Check for CAPTCHA before submitting
            time.sleep(2)

            # Look for common CAPTCHA elements
            captcha_detected = False
            captcha_selectors = [
                'iframe[src*="recaptcha"]',
                'iframe[src*="hcaptcha"]',
                '[class*="captcha"]',
                '#captcha',
                '[data-testid*="captcha"]'
            ]

            for selector in captcha_selectors:
                try:
                    captcha_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if captcha_elem.is_displayed():
                        captcha_detected = True
                        break
                except:
                    continue

            if captcha_detected:
                self._log("⚠️  CAPTCHA detected! Please solve the CAPTCHA manually in the browser window.", "warning")
                self._log("Waiting up to 60 seconds for CAPTCHA to be solved...", "warning")

                # Wait for CAPTCHA to be solved (either URL changes or CAPTCHA disappears)
                wait_start = time.time()
                captcha_solved = False

                while (time.time() - wait_start) < 60:
                    if "files/folders" in self.driver.current_url:
                        captcha_solved = True
                        self._log("✓ CAPTCHA appears to be solved (redirected to dashboard)", "success")
                        break

                    # Check if login button is still visible and CAPTCHA is gone
                    try:
                        captcha_still_present = False
                        for selector in captcha_selectors:
                            try:
                                captcha_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if captcha_elem.is_displayed():
                                    captcha_still_present = True
                                    break
                            except:
                                continue

                        if not captcha_still_present:
                            self._log("✓ CAPTCHA solved, proceeding with login", "success")
                            captcha_solved = True
                            break
                    except:
                        pass

                    time.sleep(2)

                if not captcha_solved:
                    self._log("CAPTCHA solving timeout. Please try again.", "error")
                    return False

            # Submit (if not already on dashboard from CAPTCHA flow)
            # Wait a moment for any redirect to complete
            time.sleep(2)

            if "files/folders" not in self.driver.current_url:
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                    login_button.click()

                    # Wait for dashboard
                    self.wait.until(lambda d: "files/folders" in d.current_url)
                except Exception as e:
                    # Check if we're already on dashboard (CAPTCHA might have auto-submitted)
                    time.sleep(2)
                    if "files/folders" in self.driver.current_url:
                        self._log("Already on dashboard after CAPTCHA", "success")
                    else:
                        raise e
            else:
                self._log("Already on dashboard, skipping login button", "success")
            
            self._log("Login successful!", "success")
            return True

        except Exception as e:
            self._log(f"Login failed: {str(e)}", "error")
            return False

    def _intercept_api_response(self, folder_name: str, max_wait: int = 10) -> list:
        """
        Intercept the /api/v5/entities API response to get all files in folder

        This method monitors network traffic and extracts the API response
        containing all files, bypassing the virtual scrolling limitation.

        Args:
            folder_name: Name of folder for logging
            max_wait: Maximum seconds to wait for API response

        Returns:
            List of entity dictionaries with file data, or empty list if failed
        """
        import time as time_module

        self._log(f"Monitoring network for API response...")

        start_time = time_module.time()
        checked_request_ids = set()
        all_responses = []  # Collect all responses to find the largest one

        while (time_module.time() - start_time) < max_wait:
            try:
                # Get performance logs (gets ALL logs, not just new ones)
                logs = self.driver.get_log('performance')

                self._log(f"Got {len(logs)} performance log entries...")

                # Look for /api/v5/entities responses
                for log in logs:
                    try:
                        message = json.loads(log['message'])
                        method = message['message']['method']

                        # Check for response received
                        if method == 'Network.responseReceived':
                            params = message['message']['params']
                            response = params['response']
                            url = response['url']

                            # Check if this is the entities endpoint
                            if '/api/v5/entities' in url and response['status'] == 200:
                                request_id = params['requestId']

                                # Skip if we've already tried this request ID
                                if request_id in checked_request_ids:
                                    continue

                                checked_request_ids.add(request_id)

                                self._log(f"Found API response (request ID: {request_id[:20]}...), extracting body...")

                                # Get the response body
                                try:
                                    response_body = self.driver.execute_cdp_cmd(
                                        'Network.getResponseBody',
                                        {'requestId': request_id}
                                    )

                                    body_text = response_body.get('body')
                                    if body_text:
                                        data = json.loads(body_text)

                                        if 'entities' in data:
                                            entities = data['entities']

                                            if len(entities) > 0:
                                                self._log(f"Found response with {len(entities)} entities")
                                                all_responses.append(entities)
                                            else:
                                                self._log(f"API response had 0 entities, skipping...")

                                except Exception as e:
                                    self._log(f"Could not get response body: {e}", "warning")
                                    continue

                    except Exception as e:
                        continue

            except Exception as e:
                self._log(f"Error reading logs: {e}", "warning")

            # Small delay before next check
            time_module.sleep(1)

        # Return the response with the MOST entities (main content area, not sidebar)
        if all_responses:
            largest_response = max(all_responses, key=len)
            self._log(f"✓ Intercepted API response: {len(largest_response)} files (largest of {len(all_responses)} responses)", "success")
            return largest_response

        self._log(f"Timeout waiting for API response after {max_wait}s", "warning")
        self._log(f"Checked {len(checked_request_ids)} request IDs", "warning")
        return []

    def _expand_folder_if_needed(self, folder_element):
        """
        Expand a folder if it has subfolders (has chevron button)

        Args:
            folder_element: The folder element to check and expand

        Returns:
            True if folder was expanded or already open, False if no subfolders
        """
        try:
            # Check if folder has a toggle button (meaning it has subfolders)
            toggle_buttons = folder_element.find_elements(By.CSS_SELECTOR, '[data-testid="toggle-folder-open"]')

            if not toggle_buttons:
                return False  # No subfolders

            toggle_button = toggle_buttons[0]

            # Check if already expanded (chevron-down vs chevron-right)
            svg_icon = toggle_button.find_element(By.CSS_SELECTOR, 'svg use')
            href = svg_icon.get_attribute('href')

            if 'chevron-right' in href:
                # Folder is collapsed, expand it
                toggle_button.click()
                time.sleep(1)  # Wait for subfolders to load
                return True
            else:
                # Already expanded
                return True

        except Exception as e:
            return False

    def _get_folders_simple(self) -> List[tuple]:
        """
        Get all folders without recursion (simpler, more reliable)

        Returns:
            List of (folder_name, folder_selector) tuples
        """
        folders = []
        processed_ids = set()

        try:
            # Find all folder elements currently visible
            folder_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                '[data-testid^="mycabinet-"]'
            )

            self._log(f"Found {len(folder_elements)} folder elements to process")

            for elem in folder_elements:
                try:
                    test_id = elem.get_attribute('data-testid')

                    if not test_id:
                        continue

                    if test_id == 'sidebar-item-mycabinet' or test_id in processed_ids:
                        continue

                    # Get folder name from title attribute
                    try:
                        folder_span = elem.find_element(By.CSS_SELECTOR, 'span[title]')
                        folder_name = folder_span.get_attribute('title')
                    except Exception as e:
                        self._log(f"Could not get folder name for {test_id}: {e}", "warning")
                        continue

                    if not folder_name:
                        self._log(f"Empty folder name for {test_id}", "warning")
                        continue

                    # Add this folder to the list
                    folders.append((folder_name, f'[data-testid="{test_id}"]'))
                    processed_ids.add(test_id)

                except Exception as e:
                    self._log(f"Error processing folder element: {e}", "warning")
                    continue

            return folders

        except Exception as e:
            self._log(f"Error in folder discovery: {str(e)}", "error")
            return folders

    def get_folders(self) -> List[tuple]:
        """
        Get list of all folders and subfolders from cabinet (recursive)

        Returns:
            List of (folder_path, folder_selector) tuples
            folder_path includes parent folders: "2024 year TAX/Receipts"
        """
        self._log("=== get_folders() called ===")
        folders = []

        try:
            # Find and expand "My Cabinet"
            self._log("Looking for cabinet...")
            cabinet = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="sidebar-item-mycabinet"]'))
            )
            self._log(f"Found cabinet: {cabinet.text}")

            # Check if cabinet is already expanded (has 'is-open' class)
            cabinet_classes = cabinet.get_attribute('class') or ''
            if 'is-open' not in cabinet_classes:
                self._log("Expanding cabinet...")
                # Click the toggle button or the cabinet itself to expand
                try:
                    toggle_button = cabinet.find_element(By.CSS_SELECTOR, '[data-testid="toggle-folder-open"]')
                    toggle_button.click()
                except:
                    # Fallback: click the cabinet itself
                    cabinet.click()
                time.sleep(3)  # Wait for folders to load
                self._log("Cabinet expanded")
            else:
                self._log("Cabinet already expanded")

            # Always wait a bit more to ensure folders are fully loaded
            time.sleep(2)

            # Get all folders (simple approach - just top-level folders)
            self._log("Discovering folders...")
            folders = self._get_folders_simple()

            if folders:
                self._log(f"Found {len(folders)} folders")
                for folder_name, _ in folders:
                    self._log(f"Found folder: {folder_name}")
            else:
                self._log("No folders found", "warning")

            return folders

        except Exception as e:
            self._log(f"Error getting folders: {str(e)}", "error")
            return []

    def export_folder_files(self, folder_name: str, folder_selector: str) -> tuple:
        """
        Export all files from a folder using API interception

        Instead of scraping the DOM and fighting virtual scrolling,
        this method intercepts the browser's own API call to get ALL files.

        Args:
            folder_name: Display name of folder
            folder_selector: CSS selector for folder

        Returns:
            Tuple of (successful_count, failed_count, error_list)
        """
        exported_count = 0
        failed_count = 0
        errors = []
        safe_folder_name = sanitize_folder_name(folder_name)

        try:
            # Step 1: Click folder to open it (triggers API call)
            self._log(f"Opening folder: {folder_name}")
            folder_elem = self.driver.find_element(By.CSS_SELECTOR, folder_selector)

            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", folder_elem)
            time.sleep(0.5)

            # Click folder
            self.driver.execute_script("arguments[0].click();", folder_elem)
            self._log(f"✓ Clicked folder, waiting for page to load...")
            time.sleep(6)  # Give page time to fully load and make all API calls

            # Step 2: Intercept API response to get ALL files
            # We want the LARGEST response (main content), not sidebar responses
            entities = self._intercept_api_response(folder_name, max_wait=5)

            if not entities:
                self._log(f"⚠️  No files found via API interception", "warning")
                self._log(f"Falling back to UI scraping...", "warning")
                # Could fallback to old method here if needed
                return (0, 0, ["API interception failed"])

            total_files = len(entities)
            self._log(f"🎯 Got {total_files} files from API (bypassed virtual scrolling!)", "success")

            # Step 2.5: Pre-scroll to load ALL checkboxes into DOM before processing
            # Use REAL mouse wheel scrolling to trigger virtual scroll properly
            self._log(f"Pre-scrolling to load all {total_files} items into DOM...")
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.common.keys import Keys

            max_loaded = 0
            scroll_attempts = 0
            max_scroll_attempts = 30

            # Find the scrollable container (the file list area)
            # Try multiple selectors to find the actual scrollable element
            file_list_container = None
            selectors = [
                '[data-testid="file-list"]',
                '[role="list"]',
                '.file-list',
                '.files-container',
                '[class*="FileList"]',
                '[class*="VirtualScroll"]',
                'main',
            ]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    # Check if this element can scroll
                    scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", element)
                    client_height = self.driver.execute_script("return arguments[0].clientHeight;", element)
                    if scroll_height > client_height:
                        file_list_container = element
                        self._log(f"Found scrollable container: {selector}")
                        break
                except:
                    continue

            if not file_list_container:
                # Fallback to body
                file_list_container = self.driver.find_element(By.TAG_NAME, 'body')
                self._log(f"Using body as scroll container")

            while scroll_attempts < max_scroll_attempts:
                checkboxes = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    'input[id^="checkbox-"]:not(#header-checkbox)'
                )
                current_count = len(checkboxes)

                if current_count >= total_files:
                    self._log(f"✓ All {total_files} checkboxes loaded in DOM!", "success")
                    break

                if current_count > max_loaded:
                    max_loaded = current_count
                    self._log(f"Loaded {current_count}/{total_files} checkboxes...")

                # Try scrolling the container element directly
                # Increment scrollTop to trigger virtual scroll loading
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollTop + 500;",
                    file_list_container
                )
                time.sleep(0.8)

                scroll_attempts += 1

            if max_loaded < total_files:
                self._log(f"⚠️  Only loaded {max_loaded}/{total_files} checkboxes after scrolling", "warning")
                self._log(f"Will process available files only", "warning")

            # Scroll back to top using Page Up keys
            for _ in range(10):
                ActionChains(self.driver).send_keys(Keys.PAGE_UP).perform()
                time.sleep(0.1)
            time.sleep(1)

            # Step 3: Process each file
            for idx, entity in enumerate(entities, 1):
                try:
                    webid = entity.get('webid')
                    name = entity.get('name', 'Unknown')
                    description = entity.get('description', '')
                    file_title = f"{name} - {description}" if description else name

                    self._log(f"Processing file {idx}/{total_files}: {name}")

                    # Find the checkbox for this file by webid or index
                    # Try multiple strategies
                    checkbox = None

                    # Strategy 1: Try to find by webid
                    try:
                        checkbox = self.driver.find_element(By.CSS_SELECTOR, f'input[id="checkbox-{webid}"]')
                        self._log(f"Found checkbox by webid")
                    except:
                        pass

                    # Strategy 2: Find by index if still not found
                    if not checkbox:
                        # Scroll slowly to the approximate position where this file should be
                        # Each file takes roughly 80-100px of height
                        estimated_scroll_position = (idx - 1) * 90

                        # Scroll to that position
                        self.driver.execute_script(f"window.scrollTo(0, {estimated_scroll_position});")
                        time.sleep(1)

                        # Now try to find checkbox
                        checkboxes = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            'input[id^="checkbox-"]:not(#header-checkbox)'
                        )

                        # Look for our checkbox in the currently rendered list
                        for cb in checkboxes:
                            cb_id = cb.get_attribute('id')
                            if cb_id and webid in cb_id:
                                checkbox = cb
                                self._log(f"Found checkbox by scrolling to position")
                                break

                    if not checkbox:
                        self._log(f"Could not find checkbox for file {idx}: {name}", "warning")
                        failed_count += 1
                        errors.append(f"{file_title}: Checkbox not found")
                        continue

                    # Click checkbox to select
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                    time.sleep(0.3)
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    time.sleep(0.5)
                    self._log(f"✓ Selected file checkbox")

                    # Click Export button
                    self._log(f"Looking for Export button...")
                    export_btn = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="export-button"]'))
                    )
                    self._log(f"✓ Found Export button, clicking...")
                    export_btn.click()
                    time.sleep(1)
                    self._log(f"✓ Clicked Export button")

                    # Click 'Image as PDF' option
                    self._log(f"Looking for 'Image as PDF' option...")
                    pdf_option = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Image as PDF')]"))
                    )
                    self._log(f"✓ Found PDF option, clicking...")
                    pdf_option.click()
                    time.sleep(2)
                    self._log(f"✓ Clicked PDF export option")

                    # Click 'Download PDF File' link to actually start the download
                    self._log(f"Looking for 'Download PDF File' link...")
                    try:
                        download_link = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Download PDF File')]"))
                        )
                        self._log(f"✓ Found download link, clicking...")
                        download_link.click()
                        time.sleep(1)
                        self._log(f"✓ Clicked download link")
                    except Exception as e:
                        self._log(f"No 'Download PDF File' link found (maybe direct download?): {e}", "warning")

                    # Wait for download to complete and organize file
                    self._log(f"Waiting for download to complete...")
                    download_dir = get_chrome_download_dir()
                    backup_root = self.config.get('download_dir')

                    # Wait for download to start
                    time.sleep(2)

                    # Find the most recently downloaded file
                    download_path = Path(download_dir)
                    pdf_files = list(download_path.glob('*.pdf'))

                    if pdf_files:
                        # Sort by modification time and get newest
                        newest_file = max(pdf_files, key=lambda p: p.stat().st_mtime)

                        # Wait for .crdownload to disappear
                        crdownload = Path(str(newest_file) + '.crdownload')
                        wait_timeout = 30
                        wait_start = time.time()

                        while crdownload.exists() and (time.time() - wait_start) < wait_timeout:
                            time.sleep(0.5)

                        # Additional wait to ensure file is fully written
                        time.sleep(1)

                        # Organize file into folder structure
                        if newest_file.exists():
                            final_path = organize_file(str(newest_file), safe_folder_name, backup_root)

                            if final_path:
                                self._log(f"✓ Saved: {Path(final_path).name}", "success")
                                exported_count += 1
                            else:
                                self._log(f"✗ Failed to organize file", "error")
                                failed_count += 1
                                errors.append(f"{file_title}: Failed to organize")
                        else:
                            self._log(f"✗ Download file not found", "error")
                            failed_count += 1
                            errors.append(f"{file_title}: Download not found")
                    else:
                        self._log(f"✗ No PDF files found in downloads", "error")
                        failed_count += 1
                        errors.append(f"{file_title}: No PDF in downloads")

                    # Uncheck checkbox
                    self.driver.execute_script("arguments[0].click();", checkbox)

                    # Close any open modal/overlay to prepare for next file
                    try:
                        # Try to find and click close button
                        close_buttons = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            'button[aria-label="Close"], button.nui-modal-close, button.nui-dialog-close'
                        )
                        for btn in close_buttons:
                            if btn.is_displayed():
                                btn.click()
                                time.sleep(0.3)
                                break
                        else:
                            # Fallback: press ESC key to close modal
                            from selenium.webdriver.common.keys import Keys
                            from selenium.webdriver.common.action_chains import ActionChains
                            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                            time.sleep(0.3)
                    except Exception as e:
                        # If no modal to close, that's fine
                        pass

                    self._log(f"✓ Completed file {idx}/{total_files}")

                    # After every 6 files, scroll to refresh the virtual scroll
                    # Use keyboard scrolling to trigger proper virtual scroll behavior
                    if idx % 6 == 0 and idx < total_files:
                        self._log(f"Scrolling to refresh file list and load next batch...")
                        from selenium.webdriver.common.action_chains import ActionChains
                        from selenium.webdriver.common.keys import Keys

                        # Scroll down with Page Down to load more items
                        for _ in range(5):
                            ActionChains(self.driver).send_keys(Keys.PAGE_DOWN).perform()
                            time.sleep(0.3)

                        # Scroll back up with Page Up
                        for _ in range(5):
                            ActionChains(self.driver).send_keys(Keys.PAGE_UP).perform()
                            time.sleep(0.3)

                        self._log(f"✓ Scrolled to refresh view")

                    # Brief delay before next file
                    time.sleep(0.5)

                except Exception as e:
                    error_msg = f"{file_title}: {str(e)}"
                    self._log(f"Error exporting file: {error_msg}", "error")
                    failed_count += 1
                    errors.append(error_msg)

                    # Try to uncheck any selected checkbox
                    try:
                        checked_boxes = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            'input[id^="checkbox-"]:checked:not(#header-checkbox)'
                        )
                        for cb in checked_boxes:
                            self.driver.execute_script("arguments[0].click();", cb)
                    except:
                        pass

                    # Brief delay before continuing
                    time.sleep(1)

            self._log(f"Completed folder: {exported_count} exported, {failed_count} failed", "success" if failed_count == 0 else "warning")
            return (exported_count, failed_count, errors)

        except Exception as e:
            error_msg = f"Folder {folder_name}: {str(e)}"
            self._log(f"Error processing folder: {error_msg}", "error")
            return (exported_count, failed_count, errors)

    def run_backup(self, username: str, password: str) -> dict:
        """
        Run complete backup process
        
        Args:
            username: Neat username
            password: Neat password
        
        Returns:
            Statistics dictionary
        """
        # Clear failed files list from any previous run
        self.failed_files = []

        stats = {
            'total_folders': 0,
            'total_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'errors': [],
            'failed_file_details': [],  # Will be populated at end
            'success': False
        }
        
        try:
            self.setup_driver()
            
            if not self.login(username, password):
                return stats
            
            folders = self.get_folders()
            stats['total_folders'] = len(folders)

            for folder_name, folder_selector in folders:
                success_count, fail_count, folder_errors = self.export_folder_files(folder_name, folder_selector)
                stats['successful_files'] += success_count
                stats['failed_files'] += fail_count
                stats['total_files'] += (success_count + fail_count)
                stats['errors'].extend(folder_errors)

            stats['success'] = True
            stats['failed_file_details'] = self.failed_files  # Store for retry functionality

            # Log completion summary
            if stats['failed_files'] > 0:
                self._log(
                    f"Backup complete with errors! Successfully exported {stats['successful_files']}/{stats['total_files']} files "
                    f"from {stats['total_folders']} folders. {stats['failed_files']} files failed.",
                    "warning"
                )
            else:
                self._log(
                    f"Backup complete! Successfully exported {stats['successful_files']} files from {stats['total_folders']} folders",
                    "success"
                )
            
        except Exception as e:
            self._log(f"Backup failed: {str(e)}", "error")
        
        finally:
            if self.driver:
                self.driver.quit()
        
        return stats
    
    def retry_failed_files(self, username: str, password: str) -> dict:
        """
        Retry previously failed files

        Args:
            username: Neat username
            password: Neat password

        Returns:
            Statistics dictionary with retry results
        """
        if not self.failed_files:
            self._log("No failed files to retry", "warning")
            return {
                'total_files': 0,
                'successful_files': 0,
                'failed_files': 0,
                'errors': [],
                'success': True
            }

        self._log(f"=== Retrying {len(self.failed_files)} failed files ===", "info")

        stats = {
            'total_files': len(self.failed_files),
            'successful_files': 0,
            'failed_files': 0,
            'errors': [],
            'failed_file_details': [],
            'success': False
        }

        # Store copy of failed files and clear the list
        files_to_retry = self.failed_files.copy()
        self.failed_files = []

        try:
            self.setup_driver()

            if not self.login(username, password):
                stats['errors'].append("Login failed")
                return stats

            # Group files by folder for efficiency
            files_by_folder = {}
            for file_info in files_to_retry:
                folder_key = (file_info['folder_name'], file_info['folder_selector'])
                if folder_key not in files_by_folder:
                    files_by_folder[folder_key] = []
                files_by_folder[folder_key].append(file_info)

            # Process each folder
            for (folder_name, folder_selector), files in files_by_folder.items():
                self._log(f"Retrying {len(files)} files in folder: {folder_name}")

                # Re-export the entire folder
                # This will naturally handle all files including previously failed ones
                self._log(f"Re-exporting folder: {folder_name}")
                success, fail, errors = self.export_folder_files(folder_name, folder_selector)
                stats['successful_files'] += success
                stats['failed_files'] += fail
                stats['errors'].extend(errors)

            stats['success'] = True
            stats['failed_file_details'] = self.failed_files

            if stats['failed_files'] > 0:
                self._log(
                    f"Retry complete! {stats['successful_files']}/{stats['total_files']} files succeeded. "
                    f"{stats['failed_files']} still failed.",
                    "warning"
                )
            else:
                self._log(
                    f"Retry successful! All {stats['successful_files']} files exported.",
                    "success"
                )

        except Exception as e:
            self._log(f"Retry failed: {str(e)}", "error")
            stats['errors'].append(str(e))

        finally:
            if self.driver:
                self.driver.quit()

        return stats

    def cleanup(self):
        """Close browser and cleanup"""
        if self.driver:
            self.driver.quit()
            self._log("Browser closed")
