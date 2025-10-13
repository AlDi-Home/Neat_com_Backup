"""
Debug Helper Script for Neat.com Selector Discovery

This script logs into Neat.com, takes screenshots, and saves the page HTML
to help identify the correct CSS selectors for folders.

Usage: python3 debug_selectors.py <username> <password>
   or: python3 debug_selectors.py  (will load from saved credentials)
"""

import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import Config

def debug_neat_selectors():
    """
    Debug script to capture Neat.com page structure
    """
    # Get credentials
    print("=" * 60)
    print("Neat.com Selector Debug Tool")
    print("=" * 60)
    print()

    # Try to get credentials from command line or saved config
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
        print("Using credentials from command line arguments")
    else:
        config = Config()
        creds = config.load_credentials()
        if creds:
            username, password = creds
            print("Using saved credentials from config")
        else:
            print("ERROR: No credentials found!")
            print("Usage: python3 debug_selectors.py <username> <password>")
            print("   or: Save credentials first using the main app")
            sys.exit(1)

    # Create debug output directory
    debug_dir = Path.home() / "NeatDebug"
    debug_dir.mkdir(exist_ok=True)
    print(f"\nDebug files will be saved to: {debug_dir}")

    # Setup Chrome driver
    print("\n[1/6] Initializing Chrome WebDriver...")
    chrome_options = Options()
    # Run in visible mode so we can see what's happening
    chrome_options.add_argument('--start-maximized')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        # Navigate to Neat.com
        print("[2/6] Navigating to Neat.com...")
        driver.get("https://app.neat.com/")
        time.sleep(3)

        # Take screenshot of login page
        driver.save_screenshot(str(debug_dir / "01_login_page.png"))
        print(f"   ✓ Saved: 01_login_page.png")

        # Login
        print("[3/6] Logging in...")
        if "files/folders" not in driver.current_url:
            # Find username field
            username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"], input[name="username"], input[id*="user"]'))
            )
            username_field.send_keys(username)

            # Find password field
            password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password_field.send_keys(password)

            # Submit
            login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()

            # Wait for dashboard
            wait.until(lambda d: "files/folders" in d.current_url)
            time.sleep(3)

        print("   ✓ Login successful!")

        # Take screenshot of main dashboard
        print("[4/6] Capturing main dashboard...")
        driver.save_screenshot(str(debug_dir / "02_dashboard.png"))
        print(f"   ✓ Saved: 02_dashboard.png")

        # Save full page HTML
        print("[5/6] Saving page HTML...")
        page_html = driver.page_source
        (debug_dir / "page_source.html").write_text(page_html, encoding='utf-8')
        print(f"   ✓ Saved: page_source.html")

        # Try to find sidebar elements and log what we find
        print("[6/6] Analyzing sidebar structure...")

        analysis = []
        analysis.append("=" * 60)
        analysis.append("SIDEBAR ANALYSIS")
        analysis.append("=" * 60)
        analysis.append("")

        # Look for elements containing "Cabinet" or "My Cabinet"
        analysis.append("--- Elements containing 'Cabinet' text ---")
        try:
            cabinet_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Cabinet')]")
            for i, elem in enumerate(cabinet_elements[:10], 1):  # Limit to first 10
                try:
                    analysis.append(f"{i}. Tag: {elem.tag_name}")
                    analysis.append(f"   Text: {elem.text[:50]}")
                    analysis.append(f"   Class: {elem.get_attribute('class')}")
                    analysis.append(f"   ID: {elem.get_attribute('id')}")
                    analysis.append(f"   data-testid: {elem.get_attribute('data-testid')}")
                    analysis.append(f"   role: {elem.get_attribute('role')}")
                    analysis.append("")
                except:
                    pass
        except Exception as e:
            analysis.append(f"Error finding Cabinet elements: {e}")

        analysis.append("")
        analysis.append("--- Elements with data-testid attributes ---")
        try:
            testid_elements = driver.find_elements(By.XPATH, "//*[@data-testid]")
            for i, elem in enumerate(testid_elements[:20], 1):  # Limit to first 20
                try:
                    testid = elem.get_attribute('data-testid')
                    if 'cabinet' in testid.lower() or 'folder' in testid.lower() or 'sidebar' in testid.lower():
                        analysis.append(f"{i}. data-testid: {testid}")
                        analysis.append(f"   Tag: {elem.tag_name}")
                        analysis.append(f"   Text: {elem.text[:50] if elem.text else '(empty)'}")
                        analysis.append(f"   Class: {elem.get_attribute('class')}")
                        analysis.append("")
                except:
                    pass
        except Exception as e:
            analysis.append(f"Error finding data-testid elements: {e}")

        analysis.append("")
        analysis.append("--- Elements with role='treeitem' ---")
        try:
            treeitem_elements = driver.find_elements(By.XPATH, "//*[@role='treeitem']")
            analysis.append(f"Found {len(treeitem_elements)} treeitem elements")
            for i, elem in enumerate(treeitem_elements[:10], 1):
                try:
                    analysis.append(f"{i}. Tag: {elem.tag_name}")
                    analysis.append(f"   Text: {elem.text[:50] if elem.text else '(empty)'}")
                    analysis.append(f"   Class: {elem.get_attribute('class')}")
                    analysis.append(f"   data-testid: {elem.get_attribute('data-testid')}")
                    analysis.append("")
                except:
                    pass
        except Exception as e:
            analysis.append(f"Error finding treeitem elements: {e}")

        analysis.append("")
        analysis.append("--- Sidebar container elements ---")
        try:
            sidebar_selectors = [
                "nav",
                "[role='navigation']",
                ".sidebar",
                "[class*='sidebar']",
                "[class*='Sidebar']"
            ]
            for selector in sidebar_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        analysis.append(f"Found {len(elements)} elements with selector: {selector}")
                        elem = elements[0]
                        analysis.append(f"   Class: {elem.get_attribute('class')}")
                        analysis.append(f"   ID: {elem.get_attribute('id')}")
                        analysis.append("")
                except:
                    pass
        except Exception as e:
            analysis.append(f"Error finding sidebar elements: {e}")

        # Save analysis
        analysis_text = "\n".join(analysis)
        (debug_dir / "selector_analysis.txt").write_text(analysis_text, encoding='utf-8')
        print(f"   ✓ Saved: selector_analysis.txt")

        # Print key findings to console
        print("\n" + "=" * 60)
        print("KEY FINDINGS:")
        print("=" * 60)
        print(analysis_text)

        # Wait a bit before closing so user can see the browser
        print("\n" + "=" * 60)
        print("Browser will remain open for 10 seconds...")
        print("You can inspect the page manually if needed.")
        print("=" * 60)
        time.sleep(10)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

        # Save error screenshot
        try:
            driver.save_screenshot(str(debug_dir / "error_screenshot.png"))
            print(f"Error screenshot saved to: {debug_dir / 'error_screenshot.png'}")
        except:
            pass

    finally:
        driver.quit()
        print("\n" + "=" * 60)
        print("DEBUG COMPLETE!")
        print("=" * 60)
        print(f"\nAll debug files saved to: {debug_dir}")
        print("\nFiles created:")
        print("  - 01_login_page.png - Screenshot of login page")
        print("  - 02_dashboard.png - Screenshot of main dashboard")
        print("  - page_source.html - Full page HTML source")
        print("  - selector_analysis.txt - Analysis of sidebar elements")
        print("\nNext steps:")
        print("  1. Review the screenshots to verify login worked")
        print("  2. Check selector_analysis.txt for correct selectors")
        print("  3. Search page_source.html for folder elements")
        print("=" * 60)

if __name__ == "__main__":
    debug_neat_selectors()
