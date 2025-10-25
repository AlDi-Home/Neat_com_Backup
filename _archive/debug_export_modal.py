"""
Debug script to capture screenshots of the PDF export modal

This script will:
1. Login to Neat.com
2. Open a folder
3. Set Items to 100
4. Select a file
5. Click Export
6. Take screenshots of the export options
7. Save HTML of the modal

Usage: python3 debug_export_modal.py [folder_name]
"""

import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import Config

def debug_export_modal(folder_name=None):
    """Debug the PDF export modal workflow"""

    print("=" * 60)
    print("PDF Export Modal Debug Tool")
    print("=" * 60)
    print()

    # Load credentials
    config = Config()
    creds = config.load_credentials()

    if not creds:
        print("❌ ERROR: No saved credentials found!")
        sys.exit(1)

    username, password = creds
    print(f"✓ Loaded credentials for: {username}")
    print()

    # Create debug output directory
    debug_dir = Path.home() / "NeatDebug"
    debug_dir.mkdir(exist_ok=True)
    print(f"Debug files will be saved to: {debug_dir}")
    print()

    # Setup Chrome driver (visible mode)
    print("[1/10] Initializing Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        # Login
        print("[2/10] Logging in to Neat.com...")
        driver.get("https://app.neat.com/")
        time.sleep(3)

        if "files/folders" not in driver.current_url:
            username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"], input[name="username"]'))
            )
            username_field.send_keys(username)

            password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password_field.send_keys(password)

            login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()

            wait.until(lambda d: "files/folders" in d.current_url)
            time.sleep(3)

        print("   ✓ Login successful!")
        driver.save_screenshot(str(debug_dir / "01_after_login.png"))

        # Find and expand cabinet
        print("[3/10] Expanding cabinet...")
        cabinet = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="sidebar-item-mycabinet"]'))
        )

        cabinet_classes = cabinet.get_attribute('class') or ''
        if 'is-open' not in cabinet_classes:
            try:
                toggle_button = cabinet.find_element(By.CSS_SELECTOR, '[data-testid="toggle-folder-open"]')
                toggle_button.click()
            except:
                cabinet.click()
            time.sleep(2)

        # Find a test folder
        print("[4/10] Finding test folder...")
        if folder_name:
            # Find specific folder
            folder_xpath = f"//*[@data-testid and contains(text(), '{folder_name}')]"
            test_folder = driver.find_element(By.XPATH, folder_xpath)
        else:
            # Use first available folder
            folders = driver.find_elements(By.CSS_SELECTOR, '[data-testid^="mycabinet-"]')
            test_folder = folders[0] if folders else None

        if not test_folder:
            print("❌ No folders found!")
            return

        folder_name_actual = test_folder.find_element(By.CSS_SELECTOR, 'span[title]').get_attribute('title')
        print(f"   ✓ Selected folder: {folder_name_actual}")

        # Click folder to open it
        print("[5/10] Opening folder...")
        test_folder.click()
        time.sleep(3)
        driver.save_screenshot(str(debug_dir / "02_folder_opened.png"))

        # IMPORTANT: Set Items to 100
        print("[6/10] Setting Items selector to 100...")
        try:
            # Look for Items dropdown/selector (usually bottom-left)
            items_selectors = [
                "//select[contains(@aria-label, 'Items')]",
                "//select[contains(@id, 'items')]",
                "//*[contains(text(), 'Items')]/..//select",
                "//select[@class*='items']",
                "//button[contains(text(), 'Items')]"
            ]

            items_control = None
            for selector in items_selectors:
                try:
                    items_control = driver.find_element(By.XPATH, selector)
                    print(f"   ✓ Found Items control with selector: {selector}")
                    break
                except:
                    continue

            if items_control:
                if items_control.tag_name == 'select':
                    # It's a dropdown
                    from selenium.webdriver.support.ui import Select
                    select = Select(items_control)
                    try:
                        select.select_by_value('100')
                        print("   ✓ Set Items to 100")
                    except:
                        select.select_by_visible_text('100')
                        print("   ✓ Set Items to 100")
                else:
                    # It's a button, click it
                    items_control.click()
                    time.sleep(0.5)
                    # Find 100 option
                    option_100 = driver.find_element(By.XPATH, "//*[text()='100']")
                    option_100.click()
                    print("   ✓ Set Items to 100")

                time.sleep(2)  # Wait for page to reload
                driver.save_screenshot(str(debug_dir / "03_items_set_to_100.png"))
            else:
                print("   ⚠ Could not find Items control")

        except Exception as e:
            print(f"   ⚠ Error setting Items: {e}")

        # Find first file checkbox
        print("[7/10] Selecting first file...")
        checkboxes = driver.find_elements(
            By.CSS_SELECTOR,
            'input[id^="checkbox-"]:not(#header-checkbox)'
        )

        if not checkboxes:
            print("❌ No files found in folder!")
            return

        first_checkbox = checkboxes[0]
        driver.execute_script("arguments[0].scrollIntoView(true);", first_checkbox)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", first_checkbox)
        time.sleep(1)

        print("   ✓ File selected")
        driver.save_screenshot(str(debug_dir / "04_file_selected.png"))

        # Click Export button
        print("[8/10] Clicking Export button...")
        export_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="export-button"]'))
        )
        export_btn.click()
        time.sleep(2)

        driver.save_screenshot(str(debug_dir / "05_export_menu_opened.png"))
        print("   ✓ Export menu opened - screenshot saved")

        # Save HTML of export menu
        page_html = driver.page_source
        (debug_dir / "export_menu_source.html").write_text(page_html, encoding='utf-8')
        print("   ✓ Export menu HTML saved")

        # Look for export options
        print("[9/10] Analyzing export options...")
        export_options = driver.find_elements(By.XPATH, "//*[contains(text(), 'PDF') or contains(text(), 'Image')]")

        analysis = []
        analysis.append("=" * 60)
        analysis.append("EXPORT OPTIONS FOUND:")
        analysis.append("=" * 60)

        for i, option in enumerate(export_options[:10], 1):
            try:
                analysis.append(f"{i}. Text: {option.text}")
                analysis.append(f"   Tag: {option.tag_name}")
                analysis.append(f"   Class: {option.get_attribute('class')}")
                analysis.append(f"   data-testid: {option.get_attribute('data-testid')}")
                analysis.append("")
            except:
                pass

        analysis_text = "\n".join(analysis)
        (debug_dir / "export_options_analysis.txt").write_text(analysis_text, encoding='utf-8')
        print(analysis_text)

        # Try to click "Image as PDF" or similar
        print("[10/10] Attempting to click PDF option...")
        pdf_options = [
            "//button[contains(text(), 'Image as PDF')]",
            "//li[contains(text(), 'Image as PDF')]",
            "//*[contains(text(), 'Image as PDF')]",
            "//button[contains(text(), 'PDF')]",
            "//li[contains(text(), 'PDF')]",
            "//*[contains(text(), 'PDF')]"
        ]

        pdf_clicked = False
        for selector in pdf_options:
            try:
                pdf_button = driver.find_element(By.XPATH, selector)
                print(f"   Found PDF option: {pdf_button.text}")
                pdf_button.click()
                pdf_clicked = True
                print("   ✓ Clicked PDF option")
                time.sleep(3)
                break
            except:
                continue

        if pdf_clicked:
            driver.save_screenshot(str(debug_dir / "06_pdf_modal_opened.png"))

            # Save HTML of PDF modal
            modal_html = driver.page_source
            (debug_dir / "pdf_modal_source.html").write_text(modal_html, encoding='utf-8')

            # Look for Download button
            print("\nLooking for Download button...")
            download_options = driver.find_elements(
                By.XPATH,
                "//*[contains(text(), 'Download')]"
            )

            modal_analysis = []
            modal_analysis.append("=" * 60)
            modal_analysis.append("DOWNLOAD BUTTONS FOUND:")
            modal_analysis.append("=" * 60)

            for i, option in enumerate(download_options, 1):
                try:
                    modal_analysis.append(f"{i}. Text: {option.text}")
                    modal_analysis.append(f"   Tag: {option.tag_name}")
                    modal_analysis.append(f"   Class: {option.get_attribute('class')}")
                    modal_analysis.append(f"   data-testid: {option.get_attribute('data-testid')}")
                    modal_analysis.append("")
                except:
                    pass

            modal_text = "\n".join(modal_analysis)
            (debug_dir / "download_buttons_analysis.txt").write_text(modal_text, encoding='utf-8')
            print(modal_text)

        # Keep browser open for inspection
        print("\n" + "=" * 60)
        print("Browser will remain open for 30 seconds...")
        print("Inspect the page manually if needed.")
        print("=" * 60)
        time.sleep(30)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

        try:
            driver.save_screenshot(str(debug_dir / "error_screenshot.png"))
        except:
            pass

    finally:
        driver.quit()
        print("\n" + "=" * 60)
        print("DEBUG COMPLETE!")
        print("=" * 60)
        print(f"\nAll debug files saved to: {debug_dir}")
        print("\nFiles created:")
        print("  - 01_after_login.png")
        print("  - 02_folder_opened.png")
        print("  - 03_items_set_to_100.png")
        print("  - 04_file_selected.png")
        print("  - 05_export_menu_opened.png")
        print("  - 06_pdf_modal_opened.png (if PDF clicked)")
        print("  - export_menu_source.html")
        print("  - export_options_analysis.txt")
        print("  - pdf_modal_source.html (if PDF clicked)")
        print("  - download_buttons_analysis.txt (if PDF clicked)")
        print("=" * 60)

if __name__ == "__main__":
    folder_arg = sys.argv[1] if len(sys.argv) > 1 else None
    debug_export_modal(folder_arg)
