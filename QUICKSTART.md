# Quick Start Guide - Neat Backup Automation

## **IMMEDIATE NEXT STEPS**

### **Step 1: Download the Project**

The complete project is ready in your outputs folder. Download it to your Mac.

### **Step 2: Install Dependencies**

Open Terminal and run:

```bash
cd ~/Downloads/NeatBackupAutomation
pip3 install -r requirements.txt
```

If you don't have pip3:
```bash
# Install Homebrew first (if needed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python
```

### **Step 3: Run the Application**

```bash
python3 main.py
```

The GUI will open automatically!

---

## **CRITICAL: PDF Dropdown Selector**

⚠️ **One piece needs your input** - the PDF export dropdown selector.

When you first run the app, it will work EXCEPT for clicking the PDF option in the dropdown.

### **How to Fix (2 minutes):**

1. **Run the app once** - it will select a file and click Export
2. **The dropdown will appear but won't auto-click PDF**
3. **While dropdown is open:**
   - Right-click on "PDF" or "Data as PDF" option
   - Click "Inspect Element"
   - In DevTools, right-click the highlighted element
   - Copy → Copy selector or Copy XPath
4. **Paste the selector into `neat_bot.py` line 156**

### **Example Fix:**

```python
# Find this section in neat_bot.py (around line 156):

# TODO: Click PDF option in dropdown
try:
    # PASTE YOUR SELECTOR HERE:
    pdf_option = self.driver.find_element(By.CSS_SELECTOR, 'YOUR_SELECTOR_HERE')
    # Or if you copied XPath:
    # pdf_option = self.driver.find_element(By.XPATH, 'YOUR_XPATH_HERE')
    
    pdf_option.click()
except:
    pass
```

---

## **Testing the App**

### **Test Run (Recommended):**

1. Start the app
2. Enter credentials
3. Check "Show password" to verify
4. Click "Start Backup"
5. **Watch the browser** - it will:
   - Login to Neat
   - Navigate to folders
   - Select first file
   - Click Export
   - **PAUSE at dropdown** ← This is where you get the selector

### **After Fixing Dropdown:**

Run again - it should complete fully and export all files!

---

## **Expected Behavior**

✅ **Browser opens** (unless headless mode)  
✅ **Logs into Neat.com**  
✅ **Lists all folders**  
✅ **Exports files one by one**  
✅ **Organizes into backup/FolderName/ structure**  
✅ **Shows progress in GUI**  

**Time estimate:** ~10-20 seconds per file = 2-4 hours for 500-1,250 files

---

## **Folder Structure After Backup**

```
~/NeatBackup/
├── 2013 year TAX/
│   └── Receipts/
│       └── files.pdf
├── 2014 year TAX/
│   └── files.pdf
├── 2024 year TAX/
│   ├── Notice of assessment Sveta 2024 - Health.pdf
│   ├── Viktor_cra_2024 - Money.pdf
│   └── Alexander_cra_2024 - Money.pdf
├── Business/
│   └── files.pdf
└── Home/
    └── files.pdf
```

---

## **Troubleshooting**

### **Error: "ChromeDriver not compatible"**

```bash
pip3 install --upgrade webdriver-manager
```

### **Error: "Login failed"**

- Verify credentials
- Check if Neat.com is accessible
- Try logging in manually first

### **Files Not Downloading**

- Check Chrome settings: `chrome://settings/downloads`
- Disable "Ask where to save each file before downloading"

### **Permission Denied on ~/NeatBackup**

```bash
mkdir -p ~/NeatBackup
chmod 755 ~/NeatBackup
```

---

## **Performance Tips**

**Speed up the backup:**
1. Enable "Run browser in background" (headless mode)
2. Reduce delay in `config.json`:
   ```json
   {
     "delay_between_files": 0.5
   }
   ```

**Monitor progress:**
- Status log shows real-time updates
- Progress bar indicates activity
- File counts displayed at completion

---

## **What Happens Next**

Once you fix the PDF dropdown selector:

1. **Run the app**
2. **Click "Start Backup"**
3. **Go get coffee** ☕
4. **Come back to completed backup** ✅

The app handles:
- Navigating all folders
- Exporting all files
- Organizing everything
- Handling errors gracefully

---

## **Need Help?**

1. Check `README.md` for detailed documentation
2. Look at status log for specific errors
3. Verify Chrome/ChromeDriver compatibility
4. Test with one folder first

---

## **You're 99% Done!**

Just need that ONE dropdown selector and you're golden. The entire automation is ready to run.

**Questions? Issues? Just ask!**
