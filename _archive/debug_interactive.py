"""
Interactive debug script to record user actions and analyze pagination.

This script will:
1. Login to Neat.com
2. Open the specified folder (2013 year TAX)
3. Inject JavaScript to monitor all DOM events
4. Let YOU interact manually (click first doc, scroll, click last doc)
5. Record all events, scrolls, clicks, and state changes
6. Analyze the captured data to find pagination hooks
"""
import time
import json
from config import Config
from neat_bot import NeatBot
from selenium.webdriver.common.by import By

def interactive_debug():
    """Interactive debug session with event recording"""

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
        print("\n" + "="*70)
        print("INTERACTIVE DEBUG SESSION - Pagination Analysis")
        print("="*70)

        # Setup and login
        print("\n[1] Initializing browser...")
        bot.setup_driver()

        print("[2] Logging in (solve CAPTCHA if prompted)...")
        if not bot.login(username, password):
            print("❌ Login failed")
            return

        print("✅ Login successful!\n")

        # Get folders and find target
        print("[3] Finding 2013 year TAX folder...")
        folders = bot.get_folders()

        target_folder = None
        for folder_name, folder_selector in folders:
            if "2013" in folder_name and "TAX" in folder_name:
                target_folder = (folder_name, folder_selector)
                break

        if not target_folder:
            print("❌ Could not find 2013 year TAX folder")
            return

        folder_name, folder_selector = target_folder
        print(f"✅ Found: {folder_name}\n")

        # Open folder
        print("[4] Opening folder...")
        folder_elem = bot.driver.find_element(By.CSS_SELECTOR, folder_selector)
        bot.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", folder_elem)
        time.sleep(0.5)
        bot.driver.execute_script("arguments[0].click();", folder_elem)
        time.sleep(3)

        # Set pagination to 100
        print("[5] Setting pagination to 100...")
        try:
            pagination_btn = bot.driver.find_element(By.CSS_SELECTOR, '[data-testid="pagination-pagecount"]')
            bot.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pagination_btn)
            time.sleep(0.5)
            bot.driver.execute_script("arguments[0].click();", pagination_btn)
            time.sleep(1)

            option_100 = bot.driver.find_element(By.XPATH, "//*[text()='100' and not(contains(@class, 'nui-button'))]")
            bot.driver.execute_script("arguments[0].click();", option_100)
            time.sleep(4)
            print("✅ Pagination set to 100\n")
        except Exception as e:
            print(f"⚠️  Could not set pagination: {e}\n")

        # Check initial state
        print("[6] Analyzing initial state...")
        initial_checkboxes = bot.driver.find_elements(By.CSS_SELECTOR, 'input[id^="checkbox-"]:not(#header-checkbox)')
        print(f"   Initial checkboxes visible: {len(initial_checkboxes)}")

        try:
            subtitle_elem = bot.driver.find_element(By.CSS_SELECTOR, '[data-testid="gridheader-subtitle"]')
            print(f"   Total files: {subtitle_elem.text}")
        except:
            pass

        print("\n" + "="*70)
        print("INJECTING EVENT MONITOR...")
        print("="*70 + "\n")

        # Inject comprehensive event monitoring JavaScript
        monitor_js = """
        window.debugEvents = [];
        window.domSnapshots = [];

        // Monitor scroll events
        const scrollContainers = document.querySelectorAll('[role="grid"], [style*="overflow"]');
        scrollContainers.forEach((container, index) => {
            container.addEventListener('scroll', (e) => {
                window.debugEvents.push({
                    type: 'scroll',
                    timestamp: Date.now(),
                    container: `Container ${index}`,
                    scrollTop: e.target.scrollTop,
                    scrollHeight: e.target.scrollHeight,
                    clientHeight: e.target.clientHeight
                });
            });
        });

        // Monitor click events
        document.addEventListener('click', (e) => {
            window.debugEvents.push({
                type: 'click',
                timestamp: Date.now(),
                target: e.target.tagName,
                className: e.target.className,
                id: e.target.id,
                textContent: e.target.textContent?.substring(0, 50)
            });
        }, true);

        // Monitor DOM mutations (new checkboxes added)
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1) { // Element node
                            const hasCheckbox = node.querySelector && node.querySelector('input[id^="checkbox-"]');
                            if (hasCheckbox || (node.id && node.id.startsWith('checkbox-'))) {
                                window.debugEvents.push({
                                    type: 'checkbox_added',
                                    timestamp: Date.now(),
                                    nodeId: node.id,
                                    nodeTag: node.tagName
                                });
                            }
                        }
                    });
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Take DOM snapshot periodically
        setInterval(() => {
            const checkboxes = document.querySelectorAll('input[id^="checkbox-"]:not(#header-checkbox)');
            window.domSnapshots.push({
                timestamp: Date.now(),
                checkboxCount: checkboxes.length,
                scrollTop: document.querySelector('[role="grid"]')?.scrollTop || 0
            });
        }, 1000);

        console.log('✅ Event monitoring active!');
        return true;
        """

        monitoring_enabled = bot.driver.execute_script(monitor_js)
        if monitoring_enabled:
            print("✅ Event monitoring enabled!\n")

        print("="*70)
        print("READY FOR MANUAL INTERACTION")
        print("="*70)
        print("""
Please perform the following actions in the browser window:

1. Click on the FIRST document checkbox (top of list)
2. Scroll DOWN to see more documents
3. Click on the LAST visible document checkbox (bottom of list)
4. Scroll DOWN again if needed
5. Note how many checkboxes you can see total

The script will wait 60 seconds for you to interact.
You can also press Ctrl+C when done (it will still capture data).
        """)

        print("⏱️  Starting 60-second interaction window...\n")
        try:
            time.sleep(60)
        except KeyboardInterrupt:
            print("\n✅ Interaction complete (interrupted by user)")

        print("\n" + "="*70)
        print("CAPTURING RESULTS...")
        print("="*70 + "\n")

        # Retrieve captured events
        print("[7] Retrieving captured events...")
        events = bot.driver.execute_script("return window.debugEvents;")
        snapshots = bot.driver.execute_script("return window.domSnapshots;")

        print(f"   Captured {len(events)} events")
        print(f"   Captured {len(snapshots)} DOM snapshots\n")

        # Save to file for analysis
        debug_data = {
            'events': events,
            'snapshots': snapshots,
            'initial_checkboxes': len(initial_checkboxes)
        }

        with open('/tmp/neat_debug_data.json', 'w') as f:
            json.dump(debug_data, f, indent=2)

        print("✅ Debug data saved to: /tmp/neat_debug_data.json\n")

        # Analyze events
        print("="*70)
        print("EVENT ANALYSIS")
        print("="*70 + "\n")

        scroll_events = [e for e in events if e['type'] == 'scroll']
        click_events = [e for e in events if e['type'] == 'click']
        checkbox_events = [e for e in events if e['type'] == 'checkbox_added']

        print(f"📊 Event Summary:")
        print(f"   Scroll events: {len(scroll_events)}")
        print(f"   Click events: {len(click_events)}")
        print(f"   Checkboxes added: {len(checkbox_events)}\n")

        if scroll_events:
            print("📜 Scroll Events:")
            for i, event in enumerate(scroll_events[:5], 1):
                print(f"   {i}. scrollTop: {event['scrollTop']}, scrollHeight: {event['scrollHeight']}")
            if len(scroll_events) > 5:
                print(f"   ... and {len(scroll_events) - 5} more")
            print()

        if checkbox_events:
            print("✅ New Checkboxes Added:")
            for i, event in enumerate(checkbox_events, 1):
                print(f"   {i}. Node ID: {event.get('nodeId', 'N/A')}")
            print()

        # Check final checkbox count
        final_checkboxes = bot.driver.find_elements(By.CSS_SELECTOR, 'input[id^="checkbox-"]:not(#header-checkbox)')
        print(f"📦 Checkbox Count:")
        print(f"   Initial: {len(initial_checkboxes)}")
        print(f"   Final: {len(final_checkboxes)}")
        print(f"   Difference: +{len(final_checkboxes) - len(initial_checkboxes)}\n")

        # Analyze DOM snapshots for patterns
        if snapshots:
            print("📸 DOM Snapshot Timeline:")
            for i, snap in enumerate(snapshots[::2], 1):  # Every 2nd snapshot
                print(f"   T+{i*2}s: {snap['checkboxCount']} checkboxes, scrollTop: {snap['scrollTop']}px")
            print()

        # Look for patterns
        print("="*70)
        print("PATTERN ANALYSIS")
        print("="*70 + "\n")

        if len(final_checkboxes) > len(initial_checkboxes):
            print(f"✅ SUCCESS! {len(final_checkboxes) - len(initial_checkboxes)} new checkboxes loaded!\n")
            print("🔍 Analyzing what triggered the load...")

            # Find scroll positions when new checkboxes appeared
            if checkbox_events and scroll_events:
                print("\n📍 Scroll positions when checkboxes appeared:")
                for cb_event in checkbox_events:
                    # Find nearest scroll event before checkbox appeared
                    prior_scrolls = [s for s in scroll_events if s['timestamp'] < cb_event['timestamp']]
                    if prior_scrolls:
                        last_scroll = prior_scrolls[-1]
                        print(f"   Checkbox added after scroll to: {last_scroll['scrollTop']}px")
        else:
            print("⚠️  No new checkboxes loaded during interaction.\n")
            print("Possible causes:")
            print("   - Virtual scroller didn't trigger")
            print("   - Need different scroll pattern")
            print("   - Need to interact with specific elements")

        print("\n" + "="*70)
        print("Keeping browser open for inspection...")
        print("Press Ctrl+C to exit")
        print("="*70 + "\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nClosing...")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n[8] Cleaning up...")
        bot.cleanup()
        print("✅ Done!\n")

if __name__ == "__main__":
    interactive_debug()
