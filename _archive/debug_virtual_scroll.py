"""
Debug script to investigate Neat.com's virtual scrolling implementation
and find ways to force all items to render.
"""
import time
from config import Config
from neat_bot import NeatBot

def debug_virtual_scroll():
    """Debug the virtual scrolling behavior"""

    config = Config()
    creds = config.load_credentials()

    if not creds:
        print("❌ No credentials found. Run main app first.")
        return

    username, password = creds

    def log_callback(msg, level='info'):
        print(f"[{level.upper()}] {msg}")

    bot = NeatBot(config, log_callback)

    try:
        # Setup and login
        bot.setup_driver()

        if not bot.login(username, password):
            print("❌ Login failed")
            return

        # Get folders
        folders = bot.get_folders()

        # Find 2013 year TAX folder
        target_folder = None
        for folder_name, folder_selector in folders:
            if "2013" in folder_name and "TAX" in folder_name:
                target_folder = (folder_name, folder_selector)
                break

        if not target_folder:
            print("❌ Could not find 2013 year TAX folder")
            return

        folder_name, folder_selector = target_folder
        print(f"\n{'='*60}")
        print(f"Investigating: {folder_name}")
        print(f"{'='*60}\n")

        # Open folder
        folder_elem = bot.driver.find_element(By.CSS_SELECTOR, folder_selector)
        bot.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", folder_elem)
        time.sleep(0.5)
        bot.driver.execute_script("arguments[0].click();", folder_elem)
        time.sleep(3)

        # Set pagination to 100
        print("Setting pagination to 100...")
        try:
            pagination_btn = bot.driver.find_element(By.CSS_SELECTOR, '[data-testid="pagination-pagecount"]')
            bot.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pagination_btn)
            time.sleep(0.5)
            bot.driver.execute_script("arguments[0].click();", pagination_btn)
            time.sleep(1)

            option_100 = bot.driver.find_element(By.XPATH, "//*[text()='100' and not(contains(@class, 'nui-button'))]")
            bot.driver.execute_script("arguments[0].click();", option_100)
            time.sleep(4)
            print("✓ Pagination set to 100\n")
        except Exception as e:
            print(f"⚠️  Could not set pagination: {e}\n")

        # Get total file count
        try:
            subtitle_elem = bot.driver.find_element(By.CSS_SELECTOR, '[data-testid="gridheader-subtitle"]')
            subtitle_text = subtitle_elem.text
            print(f"Subtitle says: {subtitle_text}")

            import re
            match = re.search(r'Showing (\d+) items?', subtitle_text)
            if match:
                total_files = int(match.group(1))
                print(f"Expected total files: {total_files}\n")
        except:
            total_files = None

        # JavaScript inspection
        print("Executing JavaScript to inspect virtual scroller...\n")

        js_code = """
        // Find the grid container
        const grid = document.querySelector('[role="grid"]');
        const rows = document.querySelectorAll('[role="row"]');
        const checkboxes = document.querySelectorAll('input[id^="checkbox-"]:not(#header-checkbox)');

        // Get scroll container
        const scrollContainer = grid ? grid.closest('[style*="overflow"]') : null;

        return {
            gridFound: !!grid,
            gridHeight: grid ? grid.scrollHeight : null,
            gridClientHeight: grid ? grid.clientHeight : null,
            rowCount: rows.length,
            checkboxCount: checkboxes.length,
            scrollContainerFound: !!scrollContainer,
            scrollContainerHeight: scrollContainer ? scrollContainer.scrollHeight : null,
            scrollContainerClientHeight: scrollContainer ? scrollContainer.clientHeight : null,
            gridClasses: grid ? grid.className : null,
            scrollContainerClasses: scrollContainer ? scrollContainer.className : null
        };
        """

        info = bot.driver.execute_script(js_code)

        print("Virtual Scroller Info:")
        print(f"  Grid found: {info['gridFound']}")
        print(f"  Grid height: {info['gridHeight']}px")
        print(f"  Grid visible height: {info['gridClientHeight']}px")
        print(f"  Rows found: {info['rowCount']}")
        print(f"  Checkboxes found: {info['checkboxCount']}")
        print(f"  Scroll container found: {info['scrollContainerFound']}")
        print(f"  Scroll container height: {info['scrollContainerHeight']}px")
        print(f"  Grid classes: {info['gridClasses']}")
        print(f"\n")

        # Try to find virtual scroller library
        print("Checking for virtual scroller library...\n")

        detect_lib_js = """
        // Check for common virtual scroller attributes/classes
        const grid = document.querySelector('[role="grid"]');
        const parent = grid ? grid.parentElement : null;

        const indicators = {
            reactWindow: !!document.querySelector('[data-testid*="virtual"]'),
            reactVirtualized: !!document.querySelector('.ReactVirtualized__Grid'),
            tanstackVirtual: grid && grid.hasAttribute('data-virtual'),
            customScroller: grid && (grid.style.transform || grid.style.translate),
            parentStyles: parent ? parent.style.cssText : null,
            gridStyles: grid ? grid.style.cssText : null
        };

        return indicators;
        """

        lib_info = bot.driver.execute_script(detect_lib_js)
        print("Library Detection:")
        for key, value in lib_info.items():
            print(f"  {key}: {value}")
        print("\n")

        # Try to force render all items
        print("Attempting to force render all items...\n")

        force_render_js = """
        const grid = document.querySelector('[role="grid"]');
        const scrollContainer = grid ? grid.closest('[style*="overflow"]') : grid;

        if (!scrollContainer) return {success: false, message: 'No scroll container found'};

        // Strategy 1: Disable virtual scrolling by expanding height
        const originalHeight = scrollContainer.style.height;
        scrollContainer.style.height = 'auto';
        scrollContainer.style.maxHeight = 'none';

        // Strategy 2: Scroll to very bottom
        scrollContainer.scrollTop = scrollContainer.scrollHeight;

        // Wait a bit for rendering
        return new Promise(resolve => {
            setTimeout(() => {
                const checkboxes = document.querySelectorAll('input[id^="checkbox-"]:not(#header-checkbox)');
                resolve({
                    success: true,
                    newCheckboxCount: checkboxes.length,
                    message: 'Attempted height manipulation'
                });
            }, 2000);
        });
        """

        result = bot.driver.execute_script(force_render_js)
        time.sleep(2)

        print(f"Force render result: {result}")

        # Check how many checkboxes we have now
        checkboxes = bot.driver.find_elements(By.CSS_SELECTOR, 'input[id^="checkbox-"]:not(#header-checkbox)')
        print(f"Checkboxes after manipulation: {len(checkboxes)}")

        if total_files:
            print(f"Expected: {total_files}, Got: {len(checkboxes)}")
            if len(checkboxes) >= total_files:
                print("\n✅ SUCCESS! All items rendered!")
            else:
                print(f"\n⚠️  Still missing {total_files - len(checkboxes)} items")

        print("\nPress Ctrl+C to exit (keeping browser open for inspection)...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nClosing...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        bot.cleanup()

if __name__ == "__main__":
    from selenium.webdriver.common.by import By
    debug_virtual_scroll()
