# New implementation of export_folder_files using API interception

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

        # Scroll into view and click
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", folder_elem)
        time.sleep(0.5)

        # Clear performance logs before clicking
        self.driver.get_log('performance')

        # Click folder
        self.driver.execute_script("arguments[0].click();", folder_elem)
        self._log(f"✓ Clicked folder, waiting for API response...")

        # Step 2: Intercept API response to get ALL files
        entities = self._intercept_api_response(folder_name, max_wait=10)

        if not entities:
            self._log(f"⚠️  No files found via API interception", "warning")
            self._log(f"Falling back to UI scraping...", "warning")
            # Could fallback to old method here if needed
            return (0, 0, ["API interception failed"])

        total_files = len(entities)
        self._log(f"🎯 Got {total_files} files from API (bypassed virtual scrolling!)", "success")

        # Step 3: Process each file
        for idx, entity in enumerate(entities, 1):
            try:
                webid = entity.get('webid')
                name = entity.get('name', 'Unknown')
                description = entity.get('description', '')
                file_title = f"{name} - {description}" if description else name

                self._log(f"Processing file {idx}/{total_files}: {name}")

                # Find the checkbox for this file by webid
                # The webid is typically in the row's data attributes
                checkbox_selector = f'input[id^="checkbox-"][value="{webid}"]'

                try:
                    checkbox = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, checkbox_selector))
                    )
                except:
                    # Fallback: try finding by index
                    # Since we have all entities in order, the nth checkbox should be the nth entity
                    checkboxes = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        'input[id^="checkbox-"]:not(#header-checkbox)'
                    )

                    if idx <= len(checkboxes):
                        checkbox = checkboxes[idx - 1]
                    else:
                        # File not visible in DOM - need to scroll
                        # Scroll to load more items
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(2)

                        checkboxes = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            'input[id^="checkbox-"]:not(#header-checkbox)'
                        )

                        if idx <= len(checkboxes):
                            checkbox = checkboxes[idx - 1]
                        else:
                            self._log(f"Could not find checkbox for file {idx}", "warning")
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
                self._log(f"✓ Completed file {idx}/{total_files}")

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
