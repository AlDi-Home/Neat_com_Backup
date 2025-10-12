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
    
    def get_folders(self) -> List[tuple]:
        """
        Get list of folders from cabinet
        
        Returns:
            List of (folder_name, folder_selector) tuples
        """
        folders = []
        
        try:
            # Click "My Cabinet" to ensure it's expanded
            cabinet = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="sidebar-item-mycabinet"]')
            if 'is-open' not in cabinet.get_attribute('class'):
                cabinet.click()
                time.sleep(1)
            
            # Find all folder elements
            folder_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                '[data-testid^="mycabinet-"]'
            )
            
            for elem in folder_elements:
                folder_name = elem.text.strip()
                test_id = elem.get_attribute('data-testid')
                
                if folder_name and test_id != 'mycabinet':
                    folders.append((folder_name, f'[data-testid="{test_id}"]'))
                    self._log(f"Found folder: {folder_name}")
            
            return folders
            
        except Exception as e:
            self._log(f"Error getting folders: {str(e)}", "error")
            return []
    
    def export_folder_files(self, folder_name: str, folder_selector: str) -> int:
        """
        Export all files from a folder
        
        Args:
            folder_name: Display name of folder
            folder_selector: CSS selector for folder
        
        Returns:
            Number of files exported
        """
        exported_count = 0
        safe_folder_name = sanitize_folder_name(folder_name)
        
        try:
            # Click folder
            self._log(f"Opening folder: {folder_name}")
            folder_elem = self.driver.find_element(By.CSS_SELECTOR, folder_selector)
            folder_elem.click()
            time.sleep(2)  # Wait for files to load
            
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
                    
                    # Click Export button
                    export_btn = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="export-button"]'))
                    )
                    export_btn.click()
                    time.sleep(0.5)
                    
                    # TODO: Click PDF option in dropdown
                    # This is where we need the dropdown selector
                    # For now, trying common patterns:
                    try:
                        # Try option 1: Direct PDF button
                        pdf_option = self.driver.find_element(By.XPATH, "//button[contains(text(), 'PDF')]")
                        pdf_option.click()
                    except:
                        try:
                            # Try option 2: Menu item
                            pdf_option = self.driver.find_element(By.XPATH, "//li[contains(text(), 'PDF')]")
                            pdf_option.click()
                        except:
                            # Try option 3: Data as PDF
                            pdf_option = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Data as PDF')]")
                            pdf_option.click()
                    
                    time.sleep(1)
                    
                    # Wait for and click download link
                    download_link = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a[download*=".pdf"]'))
                    )
                    
                    filename = download_link.get_attribute('download')
                    self._log(f"Downloading: {filename}")
                    
                    download_link.click()
                    
                    # Wait for download to complete
                    if wait_for_download(self.chrome_download_dir, filename, 
                                        self.config.get('download_timeout', 30)):
                        # Move file to organized structure
                        source_path = Path(self.chrome_download_dir) / filename
                        final_path = organize_file(
                            str(source_path),
                            safe_folder_name,
                            self.config.get('download_dir')
                        )
                        
                        if final_path:
                            self._log(f"Saved: {final_path}", "success")
                            exported_count += 1
                        else:
                            self._log(f"Failed to organize: {filename}", "error")
                    else:
                        self._log(f"Download timeout: {filename}", "error")
                    
                    # Uncheck checkbox
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    time.sleep(self.config.get('delay_between_files', 1))
                    
                except Exception as e:
                    self._log(f"Error exporting file: {str(e)}", "error")
                    continue
            
            return exported_count
            
        except Exception as e:
            self._log(f"Error processing folder {folder_name}: {str(e)}", "error")
            return exported_count
    
    def run_backup(self, username: str, password: str) -> dict:
        """
        Run complete backup process
        
        Args:
            username: Neat username
            password: Neat password
        
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_folders': 0,
            'total_files': 0,
            'success': False
        }
        
        try:
            self.setup_driver()
            
            if not self.login(username, password):
                return stats
            
            folders = self.get_folders()
            stats['total_folders'] = len(folders)
            
            for folder_name, folder_selector in folders:
                count = self.export_folder_files(folder_name, folder_selector)
                stats['total_files'] += count
            
            stats['success'] = True
            self._log(f"Backup complete! Exported {stats['total_files']} files from {stats['total_folders']} folders", "success")
            
        except Exception as e:
            self._log(f"Backup failed: {str(e)}", "error")
        
        finally:
            if self.driver:
                self.driver.quit()
        
        return stats
    
    def cleanup(self):
        """Close browser and cleanup"""
        if self.driver:
            self.driver.quit()
            self._log("Browser closed")
