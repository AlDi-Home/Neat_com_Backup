#!/usr/bin/env python3
"""
Debug script to find the correct scrollable container in Neat.com
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import config

# Load credentials
cfg = config.Config()
email, password = cfg.load_credentials()
creds = {'email': email, 'password': password}

# Setup driver
chrome_options = Options()
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 10)

try:
    # Login
    print("Logging in...")
    driver.get('https://app.neat.com/login')
    time.sleep(2)
    
    email_input = driver.find_element(By.NAME, 'email')
    password_input = driver.find_element(By.NAME, 'password')
    email_input.send_keys(creds['email'])
    password_input.send_keys(creds['password'])
    
    login_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    login_btn.click()
    time.sleep(5)
    
    # Open folder
    print("Opening folder...")
    folder = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '2013 year TAX')]")))
    folder.click()
    time.sleep(5)
    
    # Find all scrollable elements
    print("\n=== FINDING SCROLLABLE ELEMENTS ===\n")
    
    all_elements = driver.find_elements(By.CSS_SELECTOR, '*')
    scrollable_elements = []
    
    for element in all_elements:
        try:
            tag = element.tag_name
            scroll_height = driver.execute_script("return arguments[0].scrollHeight;", element)
            client_height = driver.execute_script("return arguments[0].clientHeight;", element)
            overflow_y = driver.execute_script("return window.getComputedStyle(arguments[0]).overflowY;", element)
            class_name = element.get_attribute('class') or ''
            role = element.get_attribute('role') or ''
            test_id = element.get_attribute('data-testid') or ''
            
            if scroll_height > client_height and scroll_height > 100:
                scrollable_elements.append({
                    'tag': tag,
                    'class': class_name[:50],
                    'role': role,
                    'testid': test_id,
                    'scrollHeight': scroll_height,
                    'clientHeight': client_height,
                    'overflowY': overflow_y,
                    'scrollable': scroll_height - client_height
                })
        except:
            pass
    
    # Sort by how scrollable they are
    scrollable_elements.sort(key=lambda x: x['scrollable'], reverse=True)
    
    print(f"Found {len(scrollable_elements)} scrollable elements:\n")
    for i, elem in enumerate(scrollable_elements[:10], 1):
        print(f"{i}. {elem['tag']}")
        if elem['class']:
            print(f"   class: {elem['class']}")
        if elem['role']:
            print(f"   role: {elem['role']}")
        if elem['testid']:
            print(f"   data-testid: {elem['testid']}")
        print(f"   scrollHeight: {elem['scrollHeight']}, clientHeight: {elem['clientHeight']}")
        print(f"   overflowY: {elem['overflowY']}")
        print(f"   scrollable distance: {elem['scrollable']}px\n")
    
    # Save screenshot
    driver.save_screenshot('/tmp/neat_folder_view.png')
    print("Screenshot saved to /tmp/neat_folder_view.png")
    
    input("\nPress Enter to close browser...")
    
finally:
    driver.quit()
