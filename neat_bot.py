"""
Core Selenium automation for Neat.com backup
"""
import time
from pathlib import Path
from typing import List, Callable, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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
        """Initialize Chrome WebDriver with download settings"""
        chrome_options = Options()
        
        # Download settings
        prefs = {
            "download.default_directory": self.chrome_download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Headless mode option
        if self.config.get('chrome_headless', False):
            chrome_options.add_argument('--headless=new')
        
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, self.config.get('wait_timeout', 10))
        
        self._log("Chrome WebDriver initialized")
    
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
            
            # Submit
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            
            # Wait for dashboard
            self.wait.until(lambda d: "files/folders" in d.current_url)
            
            self._log("Login successful!", "success")
            return True
            
        except Exception as e:
            self._log(f"Login failed: {str(e)}", "error")
            return False
    
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
        Export all files from a folder

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
            # Click folder
            self._log(f"Opening folder: {folder_name}")
            folder_elem = self.driver.find_element(By.CSS_SELECTOR, folder_selector)

            # Scroll element into view and click
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", folder_elem)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", folder_elem)
            time.sleep(3)  # Wait for files to load

            # IMPORTANT: Set Items per page to 100
            self._log("Setting Items per page to 100...")
            try:
                # Find pagination button
                self._log("Looking for pagination button...")
                pagination_btn = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="pagination-pagecount"]'))
                )
                self._log(f"Found pagination button with text: {pagination_btn.text}")

                # Check current value
                current_value = pagination_btn.text.strip()

                if current_value != "100":
                    self._log(f"Current pagination: {current_value}, changing to 100")
                    pagination_btn.click()
                    time.sleep(1)

                    # Click 100 option in dropdown - try multiple selectors
                    option_clicked = False
                    option_selectors = [
                        "//li[text()='100']",
                        "//button[text()='100']",
                        "//div[text()='100']",
                        "//*[@role='option' and text()='100']",
                        "//*[text()='100' and not(contains(@class, 'nui-button'))]"
                    ]

                    for selector in option_selectors:
                        try:
                            option_100 = self.driver.find_element(By.XPATH, selector)
                            option_100.click()
                            option_clicked = True
                            self._log(f"✓ Clicked 100 option using selector: {selector}")
                            break
                        except:
                            continue

                    if not option_clicked:
                        self._log("Could not click 100 option, trying fallback", "warning")
                        # Fallback: find all elements with text "100" and click the last visible one
                        elements = self.driver.find_elements(By.XPATH, "//*[text()='100']")
                        for elem in reversed(elements):
                            try:
                                if elem.is_displayed():
                                    elem.click()
                                    option_clicked = True
                                    self._log("✓ Clicked 100 option (fallback)")
                                    break
                            except:
                                continue

                    time.sleep(2)  # Wait for page to reload with 100 items

                    if option_clicked:
                        self._log("✓ Set Items to 100")
                    else:
                        self._log("⚠ Could not set Items to 100", "warning")
                else:
                    self._log("✓ Items already set to 100")

            except Exception as e:
                self._log(f"Could not set Items to 100: {str(e)}", "warning")
                self._log("Continuing with default pagination...", "warning")

            # Get all file checkboxes (excluding header checkbox)
            checkboxes = self.driver.find_elements(
                By.CSS_SELECTOR,
                'input[id^="checkbox-"]:not(#header-checkbox)'
            )
            
            total_files = len(checkboxes)
            self._log(f"Found {total_files} files in {folder_name}")
            
            for idx, checkbox in enumerate(checkboxes, 1):
                try:
                    self._log(f"Processing file {idx}/{total_files} in {folder_name}")
                    
                    # Get file title for naming
                    file_row = checkbox.find_element(By.XPATH, './ancestor::div[@role="row"]')
                    title_elem = file_row.find_element(By.CSS_SELECTOR, '.nui-text.nui-type-body--small')
                    file_title = title_elem.get_attribute('title') or title_elem.text
                    
                    # Click checkbox
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    time.sleep(0.5)
                    self._log(f"✓ Selected file checkbox")

                    # Step 3: Click Export button
                    self._log(f"Looking for Export button...")
                    export_btn = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="export-button"]'))
                    )
                    self._log(f"✓ Found Export button, clicking...")
                    export_btn.click()
                    time.sleep(1)
                    self._log(f"✓ Clicked Export button")

                    # Step 4: Click "Image as PDF" option
                    # Try multiple selectors for the PDF export option
                    self._log(f"Looking for 'Image as PDF' option...")
                    pdf_clicked = False
                    pdf_selectors = [
                        "//button[contains(text(), 'Image as PDF')]",
                        "//li[contains(text(), 'Image as PDF')]",
                        "//*[contains(text(), 'Image as PDF')]",
                        "//button[contains(text(), 'PDF')]",
                        "//li[contains(text(), 'PDF')]"
                    ]

                    for selector in pdf_selectors:
                        try:
                            pdf_option = self.driver.find_element(By.XPATH, selector)
                            pdf_option.click()
                            pdf_clicked = True
                            self._log(f"✓ Clicked 'Image as PDF' option")
                            break
                        except:
                            continue

                    if not pdf_clicked:
                        self._log("Could not find PDF export option", "error")
                        raise Exception("PDF export option not found")

                    time.sleep(2)  # Wait for modal/window to appear

                    # Step 5: Click "Download PDF File" in the new window/modal
                    self._log(f"Looking for 'Download PDF File' button in modal...")
                    download_btn = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Download PDF File')]"))
                    )
                    self._log(f"✓ Found 'Download PDF File' button, clicking...")
                    download_btn.click()
                    self._log(f"✓ Clicked 'Download PDF File'")

                    # Step 6: IMMEDIATELY close the modal (don't wait for download)
                    time.sleep(0.3)  # Brief pause for click to register

                    close_selectors = [
                        "//button[contains(@aria-label, 'Close')]",
                        "//button[contains(@title, 'Close')]",
                        "//*[@data-testid='close-button']",
                        "//button[contains(@class, 'close')]",
                        "//button[contains(text(), 'Close')]"
                    ]

                    close_clicked = False
                    for selector in close_selectors:
                        try:
                            close_btn = self.driver.find_element(By.XPATH, selector)
                            if close_btn.is_displayed():
                                close_btn.click()
                                self._log("✓ Closed download modal")
                                close_clicked = True
                                break
                        except:
                            continue

                    if not close_clicked:
                        self._log("Could not find close button", "warning")

                    time.sleep(0.3)

                    # Step 7: Wait for download to complete and organize file
                    self._log(f"Waiting for download to complete...")
                    download_dir = get_chrome_download_dir()
                    backup_root = self.config.get('download_dir')

                    # Wait for download to start and get the newest file
                    time.sleep(2)  # Give download a moment to start

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
                                self._log(f"✓ Saved: {Path(final_path).name}")
                                exported_count += 1
                            else:
                                self._log(f"✗ Failed to organize file", "error")
                        else:
                            self._log(f"✗ Download file not found", "error")
                    else:
                        self._log(f"✗ No PDF files found in downloads", "error")

                    # Step 8: Uncheck checkbox
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    self._log(f"✓ Completed file {idx}/{total_files}")

                    # Brief delay before next file
                    time.sleep(0.5)
                    
                except Exception as e:
                    error_msg = f"{file_title if 'file_title' in locals() else f'File {idx}'}: {str(e)}"
                    self._log(f"Error exporting file: {error_msg}", "error")
                    failed_count += 1
                    errors.append(error_msg)
                    # Store failed file info for retry
                    self.failed_files.append({
                        'folder_name': folder_name,
                        'folder_selector': folder_selector,
                        'file_index': idx,
                        'file_title': file_title if 'file_title' in locals() else f'File {idx}',
                        'error': str(e)
                    })
                    continue

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
