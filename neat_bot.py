"""
Enhanced NeatBot with API-based downloads and recursive subfolder support

This version:
- Downloads files directly via API (bypasses virtual scrolling completely)
- Recursively processes subfolders
- Maintains proper folder hierarchy
"""
import json
import time
import requests
from pathlib import Path
from typing import List, Tuple, Callable, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils import sanitize_folder_name

class NeatBot:
    """Enhanced Neat.com backup bot using API downloads"""

    def __init__(self, config, status_callback: Optional[Callable] = None):
        self.config = config
        self.status_callback = status_callback
        self.driver = None
        self.session = None  # requests session for API downloads
        self.wait = None
        self.failed_files = []  # Track failed files for retry functionality

        # Setup file logging
        self.log_file = None
        self._setup_logging()

    def _setup_logging(self):
        """Setup file logging in download folder"""
        # Check if logging is enabled
        if not self.config.get('enable_logging', False):
            self.log_file = None
            return

        try:
            import datetime

            # Create logs folder in download directory
            download_dir = Path(self.config.get('download_dir'))
            log_dir = download_dir / "_logs"
            log_dir.mkdir(exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = log_dir / f"neat_backup_{timestamp}.log"

            self.log_file = open(log_filename, 'w', encoding='utf-8')
            print(f"[INFO] Logging to: {log_filename}")
        except Exception as e:
            print(f"[WARNING] Could not setup file logging: {e}")
            self.log_file = None

    def _log(self, message: str, level: str = 'info'):
        """Log message to console, file, and callback"""
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level.upper()}] {message}"

        # Console output
        print(f"[{level.upper()}] {message}")

        # File output
        if self.log_file:
            try:
                self.log_file.write(log_message + "\n")
                self.log_file.flush()  # Ensure immediate write
            except:
                pass

        # Callback (for GUI)
        if self.status_callback:
            self.status_callback(message, level)

    def setup_driver(self):
        """Initialize Chrome WebDriver with network monitoring"""
        chrome_options = Options()
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        # Disable MacAppCodeSignClone to prevent Chrome from creating code_sign_clone folders
        chrome_options.add_argument('--disable-features=MacAppCodeSignClone')

        if self.config.get('chrome_headless', False):
            chrome_options.add_argument('--headless=new')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, self.config.get('wait_timeout', 10))

        try:
            self.driver.execute_cdp_cmd('Network.enable', {})
            self._log("Chrome WebDriver initialized with network monitoring")
        except Exception as e:
            self._log(f"Network monitoring unavailable: {e}", "warning")

    def login(self, username: str, password: str) -> bool:
        """Login to Neat.com"""
        try:
            self._log("Navigating to Neat.com...")
            self.driver.get("https://app.neat.com/")
            time.sleep(3)

            if "files/folders" in self.driver.current_url:
                self._log("Already logged in!", "success")
                return True

            self._log("Entering credentials...")
            username_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"], input[name="username"]'))
            )
            username_field.send_keys(username)

            password_field = self.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password_field.send_keys(password)

            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()

            self.wait.until(lambda d: "files/folders" in d.current_url)
            self._log("Login successful!", "success")

            # Setup requests session with cookies
            self._setup_session()
            return True

        except Exception as e:
            self._log(f"Login failed: {str(e)}", "error")
            return False

    def _setup_session(self):
        """Setup requests session with browser cookies"""
        self.session = requests.Session()
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
        self._log("API session configured with authentication cookies")

    def _intercept_api_response(self, max_wait: int = 15) -> Tuple[List[dict], List[dict]]:
        """
        Intercept API response to get entities (files and folders)

        Returns:
            Tuple of (documents, folders)
        """
        self._log("Intercepting API response...")

        start_time = time.time()
        checked_request_ids = set()
        all_entities = []
        last_entity_count = 0

        while (time.time() - start_time) < max_wait:
            logs = self.driver.get_log('performance')

            if not logs and (time.time() - start_time) > 2:
                self._log(f"No performance logs yet (waited {int(time.time() - start_time)}s)...", "warning")

            for log in logs:
                try:
                    message = json.loads(log['message'])
                    method = message['message']['method']

                    if method == 'Network.responseReceived':
                        params = message['message']['params']
                        response = params['response']
                        url = response['url']

                        if '/api/v5/entities' in url and response['status'] == 200:
                            request_id = params['requestId']

                            if request_id in checked_request_ids:
                                continue

                            checked_request_ids.add(request_id)

                            try:
                                response_body = self.driver.execute_cdp_cmd(
                                    'Network.getResponseBody',
                                    {'requestId': request_id}
                                )

                                body_text = response_body.get('body')
                                if body_text:
                                    data = json.loads(body_text)
                                    if 'entities' in data:
                                        # Add all entities (even if 0)
                                        all_entities.extend(data['entities'])
                                        current_count = len(all_entities)
                                        if current_count > last_entity_count:
                                            self._log(f"Found {current_count} entities so far...")
                                            last_entity_count = current_count
                            except Exception as e:
                                self._log(f"Error getting response body: {e}", "warning")
                except:
                    pass

            time.sleep(0.5)

        # Separate documents/receipts and folders
        # Note: Neat has different entity types: 'document', 'receipt', 'Folder'
        documents = [e for e in all_entities if e.get('type') in ['document', 'receipt'] and not e.get('trashed')]
        folders = [e for e in all_entities if e.get('type') == 'Folder' and not e.get('trashed')]

        # Debug: check what types we got
        if all_entities and not (documents or folders):
            types_found = set([e.get('type') for e in all_entities])
            trashed_count = len([e for e in all_entities if e.get('trashed')])
            self._log(f"Got {len(all_entities)} entities but they're not downloadable. Types: {types_found}, Trashed: {trashed_count}", "warning")

        # Return documents and folders (even if empty - empty folder is valid)
        if documents or folders or (len(all_entities) > 0):
            self._log(f"✓ Found {len(documents)} files, {len(folders)} subfolders (from {len(all_entities)} total)", "success")
            return (documents, folders)

        # No API response captured at all
        self._log("No API response captured", "warning")
        return ([], [])

    def _set_items_per_page_to_100(self):
        """Set the Items dropdown to 100 to see all files"""
        try:
            # Find the Items dropdown (usually says "100" or "25", etc.)
            # Look for button or dropdown with text containing number
            items_button = self.driver.find_element(By.XPATH, "//button[contains(., 'Items') or contains(@class, 'items') or .//text()[contains(., '25') or contains(., '50') or contains(., '100')]]")

            # Click to open dropdown
            items_button.click()
            time.sleep(0.5)

            # Find and click the "100" option
            option_100 = self.driver.find_element(By.XPATH, "//li[.//text()='100'] | //button[text()='100'] | //*[@role='option'][.//text()='100']")
            option_100.click()
            time.sleep(2)  # Wait for page to reload with 100 items

            self._log("Set items per page to 100")
            return True
        except Exception as e:
            self._log(f"Could not set items to 100 (maybe already set or UI changed): {e}", "warning")
            return False

    def _click_folder(self, folder_selector: str, folder_name: str):
        """Click a folder to open it"""
        try:
            # Clear performance logs before clicking to get fresh API responses
            cleared_logs = self.driver.get_log('performance')
            self._log(f"Cleared {len(cleared_logs)} old performance log entries")

            folder_elem = self.driver.find_element(By.CSS_SELECTOR, folder_selector)
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", folder_elem)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", folder_elem)
            self._log(f"Opened folder: {folder_name}")
            time.sleep(5)  # Wait for initial load

            # Set items per page to 100 to see all files
            self._set_items_per_page_to_100()
            time.sleep(5)  # Wait for API call after changing pagination

            return True
        except Exception as e:
            self._log(f"Error clicking folder {folder_name}: {e}", "error")
            return False

    def _expand_folder_in_sidebar(self, folder_elem) -> bool:
        """Expand a folder in sidebar to reveal subfolders"""
        try:
            # Check if folder has a toggle button (chevron)
            parent = folder_elem.find_element(By.XPATH, './ancestor::li[1]')

            # Look for toggle button
            try:
                toggle = parent.find_element(By.CSS_SELECTOR, '[data-testid="toggle-folder-open"]')
                # Check if already expanded by looking for parent's class
                parent_classes = parent.get_attribute('class') or ''

                if 'is-open' not in parent_classes:
                    toggle.click()
                    time.sleep(1)
                    self._log(f"Expanded folder in sidebar")
                    return True
                else:
                    self._log(f"Folder already expanded in sidebar")
                    return True
            except:
                # No toggle button means no subfolders
                return False

        except Exception as e:
            self._log(f"Could not expand folder: {e}", "warning")
            return False

    def _get_subfolders_from_sidebar(self, parent_folder_elem) -> List[Tuple[str, str]]:
        """Get list of subfolders from sidebar for a given parent folder"""
        try:
            # Find the parent li element
            parent_li = parent_folder_elem.find_element(By.XPATH, './ancestor::li[1]')

            # Find child ul (contains subfolders)
            try:
                child_ul = parent_li.find_element(By.CSS_SELECTOR, 'ul')
            except:
                # No child ul = no subfolders
                return []

            # Find all direct child folder items
            subfolder_elements = child_ul.find_elements(By.CSS_SELECTOR, ':scope > li')

            subfolders = []
            for sf_elem in subfolder_elements:
                try:
                    # Find the folder link within this li
                    folder_link = sf_elem.find_element(By.CSS_SELECTOR, '[data-testid^="mycabinet-"]')
                    test_id = folder_link.get_attribute('data-testid')

                    # Get folder name from title or text
                    try:
                        span = folder_link.find_element(By.CSS_SELECTOR, 'span[title]')
                        name = span.get_attribute('title')
                    except:
                        name = folder_link.text

                    if name:
                        subfolders.append((name, f'[data-testid="{test_id}"]', folder_link))
                except:
                    continue

            return subfolders

        except Exception as e:
            self._log(f"Error getting subfolders from sidebar: {e}", "warning")
            return []

    def export_folder_files(self, folder_name: str, folder_selector: str, folder_path: str = "", folder_elem=None) -> Tuple[int, int, List[str]]:
        """
        Export all files from a folder using API downloads, recursively processing subfolders

        Args:
            folder_name: Display name of folder
            folder_selector: CSS selector for folder
            folder_path: Parent folder path (for nested folders)
            folder_elem: WebElement for folder (used to find subfolders in sidebar)

        Returns:
            Tuple of (successful_count, failed_count, error_list)
        """
        exported_count = 0
        failed_count = 0
        errors = []

        # Build full folder path
        full_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
        safe_folder_path = sanitize_folder_name(full_path)

        try:
            # Get the folder element if not provided
            if not folder_elem:
                try:
                    folder_elem = self.driver.find_element(By.CSS_SELECTOR, folder_selector)
                except:
                    pass

            # Expand folder in sidebar BEFORE clicking (to discover subfolders and possibly trigger API)
            subfolders_from_sidebar = []
            if folder_elem:
                self._expand_folder_in_sidebar(folder_elem)
                time.sleep(2)  # Wait after expanding
                subfolders_from_sidebar = self._get_subfolders_from_sidebar(folder_elem)
                if subfolders_from_sidebar:
                    self._log(f"Found {len(subfolders_from_sidebar)} subfolders in sidebar for {full_path}")

            # Click folder to open it (and trigger API call)
            if not self._click_folder(folder_selector, full_path):
                return (0, 0, [f"{full_path}: Failed to open folder"])

            # Intercept API to get documents
            documents, _ = self._intercept_api_response()

            # Download all documents in this folder
            if documents:
                self._log(f"Downloading {len(documents)} files from {full_path}...")
                backup_root = self.config.get('download_dir')

                for idx, doc in enumerate(documents, 1):
                    try:
                        name = doc.get('name', 'Unknown')
                        description = doc.get('description', '')
                        download_url = doc.get('download_url')
                        file_title = f"{name} - {description}" if description else name

                        self._log(f"[{idx}/{len(documents)}] {name}")

                        if not download_url:
                            self._log(f"✗ No download URL", "error")
                            failed_count += 1
                            errors.append(f"{full_path}/{file_title}: No download URL")
                            continue

                        # Create folder structure
                        folder_dir = Path(backup_root) / safe_folder_path
                        folder_dir.mkdir(parents=True, exist_ok=True)

                        # Prepare filename
                        safe_name = f"{name} - {description}".replace('/', '-').replace('\\', '-')
                        output_file = folder_dir / f"{safe_name}.pdf"

                        # Get remote file size via streaming GET request (HEAD doesn't work with signed URLs)
                        try:
                            size_response = self.session.get(download_url, allow_redirects=True, timeout=30, stream=True)
                            remote_size = int(size_response.headers.get('Content-Length', 0))
                            size_response.close()  # Close without downloading full content
                        except:
                            # If size check fails, we'll download without size verification
                            remote_size = 0

                        # Check if file with same name already exists
                        if output_file.exists():
                            existing_size = output_file.stat().st_size

                            # Compare sizes
                            if remote_size > 0 and existing_size == remote_size:
                                self._log(f"⊙ Already exists ({existing_size:,} bytes), same size, skipping", "info")
                                exported_count += 1
                                continue
                            elif remote_size > 0 and existing_size != remote_size:
                                # Same name but different size - find available numbered suffix
                                self._log(f"⊙ File exists but different size (local: {existing_size:,}, remote: {remote_size:,})", "info")
                                counter = 1
                                while True:
                                    numbered_file = folder_dir / f"{safe_name}_{counter}.pdf"
                                    if not numbered_file.exists():
                                        output_file = numbered_file
                                        self._log(f"  Downloading as _{counter}")
                                        break
                                    else:
                                        # Check if this numbered file matches
                                        numbered_size = numbered_file.stat().st_size
                                        if numbered_size == remote_size:
                                            self._log(f"⊙ Already exists as _{counter} ({numbered_size:,} bytes), same size, skipping", "info")
                                            exported_count += 1
                                            output_file = None  # Signal to skip download
                                            break
                                    counter += 1

                                if output_file is None:
                                    continue  # Skip download
                            else:
                                # Can't determine remote size, skip to be safe
                                self._log(f"⊙ Already exists ({existing_size:,} bytes), skipping (can't verify size)", "info")
                                exported_count += 1
                                continue

                        # Download the file
                        response = self.session.get(download_url, allow_redirects=True, timeout=60)

                        if response.status_code == 200:
                            # Save file
                            with open(output_file, 'wb') as f:
                                f.write(response.content)

                            file_size = output_file.stat().st_size
                            self._log(f"✓ Downloaded ({file_size:,} bytes)", "success")
                            exported_count += 1

                        else:
                            self._log(f"✗ HTTP {response.status_code}", "error")
                            failed_count += 1
                            errors.append(f"{full_path}/{file_title}: HTTP {response.status_code}")

                    except Exception as e:
                        error_msg = f"{full_path}/{file_title}: {str(e)}"
                        self._log(f"✗ Error: {error_msg}", "error")
                        failed_count += 1
                        errors.append(error_msg)

                    time.sleep(0.3)

            # Recursively process subfolders discovered from sidebar
            if subfolders_from_sidebar:
                self._log(f"Processing {len(subfolders_from_sidebar)} subfolders in {full_path}...")

                for subfolder_name, subfolder_selector, subfolder_elem in subfolders_from_sidebar:
                    try:
                        # Recursively export this subfolder
                        sub_exported, sub_failed, sub_errors = self.export_folder_files(
                            subfolder_name,
                            subfolder_selector,
                            full_path,  # Pass current path as parent
                            subfolder_elem  # Pass element for further subfolder discovery
                        )

                        exported_count += sub_exported
                        failed_count += sub_failed
                        errors.extend(sub_errors)

                    except Exception as e:
                        self._log(f"Error processing subfolder {subfolder_name}: {e}", "error")
                        errors.append(f"{full_path}/{subfolder_name}: Failed to process subfolder")

            self._log(f"Completed {full_path}: {exported_count} exported, {failed_count} failed",
                     "success" if failed_count == 0 else "warning")
            return (exported_count, failed_count, errors)

        except Exception as e:
            error_msg = f"{full_path}: {str(e)}"
            self._log(f"Error processing folder: {error_msg}", "error")
            return (exported_count, failed_count, errors)

    def get_folders(self) -> List[Tuple[str, str, object]]:
        """
        Get list of top-level folders from cabinet

        Returns:
            List of (folder_name, folder_selector, folder_element) tuples
        """
        self._log("Getting folders from cabinet...")
        folders = []

        try:
            # Find and expand cabinet
            cabinet = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="sidebar-item-mycabinet"]'))
            )

            cabinet_classes = cabinet.get_attribute('class') or ''
            if 'is-open' not in cabinet_classes:
                try:
                    toggle_button = cabinet.find_element(By.CSS_SELECTOR, '[data-testid="toggle-folder-open"]')
                    toggle_button.click()
                except:
                    cabinet.click()
                time.sleep(3)

            time.sleep(2)

            # Get all top-level folder elements
            folder_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid^="mycabinet-"]')

            for elem in folder_elements:
                try:
                    test_id = elem.get_attribute('data-testid')
                    if test_id == 'sidebar-item-mycabinet':
                        continue

                    folder_span = elem.find_element(By.CSS_SELECTOR, 'span[title]')
                    folder_name = folder_span.get_attribute('title')

                    if folder_name:
                        folders.append((folder_name, f'[data-testid="{test_id}"]', elem))
                except:
                    continue

            self._log(f"Found {len(folders)} top-level folders")
            return folders

        except Exception as e:
            self._log(f"Error getting folders: {str(e)}", "error")
            return []

    def run_backup(self, username: str, password: str) -> dict:
        """Run complete backup with recursive subfolder support"""
        # Clear failed files list from any previous run
        self.failed_files = []

        stats = {
            'total_folders': 0,
            'total_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'errors': [],
            'failed_file_details': [],
            'success': False
        }

        try:
            self.setup_driver()

            if not self.login(username, password):
                return stats

            folders = self.get_folders()
            stats['total_folders'] = len(folders)

            for folder_name, folder_selector, folder_elem in folders:
                success_count, fail_count, folder_errors = self.export_folder_files(
                    folder_name,
                    folder_selector,
                    "",  # Empty parent path for top-level folders
                    folder_elem  # Pass element for subfolder discovery
                )
                stats['successful_files'] += success_count
                stats['failed_files'] += fail_count
                stats['total_files'] += (success_count + fail_count)
                stats['errors'].extend(folder_errors)

                # Track failed files for retry
                for error in folder_errors:
                    self.failed_files.append({
                        'folder': folder_name,
                        'error': error
                    })

            stats['success'] = True
            stats['failed_file_details'] = self.failed_files

            if stats['failed_files'] > 0:
                self._log(
                    f"Backup complete with errors! {stats['successful_files']}/{stats['total_files']} files "
                    f"from {stats['total_folders']} folders. {stats['failed_files']} files failed.",
                    "warning"
                )
            else:
                self._log(
                    f"Backup complete! {stats['successful_files']} files from {stats['total_folders']} folders",
                    "success"
                )

        except Exception as e:
            self._log(f"Backup failed: {str(e)}", "error")

        finally:
            if self.driver:
                self.driver.quit()
            if self.log_file:
                self.log_file.close()
                print("[INFO] Log file closed")

        return stats

    def retry_failed_files(self, username: str, password: str) -> dict:
        """
        Retry downloading failed files

        Note: With the new API-based approach, retrying individual files is less relevant
        since failures are usually due to missing download_url or network issues.
        This method re-runs the full backup to maintain compatibility with the GUI.
        """
        self._log(f"Retrying {len(self.failed_files)} failed files...", "info")

        # For API-based downloads, the best retry strategy is to re-run the full backup
        # since file-level failures are rare and usually indicate larger issues
        stats = self.run_backup(username, password)

        return stats

    def cleanup(self):
        """Close browser and log file"""
        if self.driver:
            self.driver.quit()
            self._log("Browser closed")
        if self.log_file:
            self.log_file.close()
            print("[INFO] Log file closed")
