# Quick Start Guide - Neat Backup Automation

Get up and running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- Neat.com account credentials

## Installation Steps

### 1. Install Dependencies

Open Terminal and navigate to the project folder:

```bash
cd path/to/neat-backup-automation
pip3 install -r requirements.txt
```

If you don't have pip3 installed:

```bash
# Install Homebrew (if needed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python
```

### 2. Launch the Application

```bash
python3 main.py
```

The GUI window will open automatically.

## First Time Setup

### Step 1: Enter Credentials

1. Enter your Neat.com username (email)
2. Enter your password
3. Check "Show password" to verify it's correct
4. Check "Remember credentials" to save them securely

### Step 2: Configure Backup Settings

1. **Backup Folder**: Default is `~/Downloads/Neat`
   - Click "Browse..." to change location

2. **Run browser in background**: Unchecked by default
   - Check this for faster backups (no browser window)

3. **Enable file logging**: Unchecked by default
   - Check this to save detailed logs to `backup_folder/_logs/`
   - Useful for troubleshooting

### Step 3: Start Backup

Click the green **"Start Backup"** button!

## What Happens Next

1. **Browser opens** (unless headless mode is enabled)
2. **Logs into Neat.com** with your credentials
3. **Discovers folders** (shows "Found 19 top-level folders")
4. **For each folder**:
   - Opens the folder
   - Sets pagination to 100 items
   - Downloads all files (skips existing files)
   - Processes subfolders recursively
5. **Completion message** shows total files downloaded

## Progress Monitoring

Watch the **Status** section for real-time updates.

## Expected Results

After completion, your files will be organized with proper folder hierarchy.

## Smart Features

### Automatic Deduplication

The tool automatically skips files you already have:

- **Same filename, same size** → Skipped
- **Same filename, different size** → Downloads as `filename_1.pdf`
- **New file** → Downloads normally

### Resume Capability

If backup is interrupted, just click "Start Backup" again - already downloaded files are automatically skipped.

## Typical Timeline

- **Small library** (100 files): ~5-10 minutes
- **Medium library** (500 files): ~20-30 minutes
- **Large library** (1000+ files): ~1-2 hours

## Tips for Best Results

1. **First backup**: Disable headless mode to watch the process
2. **Subsequent backups**: Enable headless mode for speed
3. **Enable logging** when troubleshooting issues
4. **Disable sleep mode** for large backups
5. **Use wired connection** for faster/stable downloads

---

**Ready to start?** Just run `python3 main.py` and click the green button!

**Questions?** Check README.md for detailed documentation.
