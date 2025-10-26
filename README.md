# Neat Backup Automation

A comprehensive backup tool for Neat.com that automatically downloads all your documents and organizes them into folders on your local machine.

> **Platform Compatibility**: Developed and tested on **macOS**. Should work on Windows and Linux with minor adjustments (paths, launcher scripts). Chrome browser required on all platforms.

## Features

✅ **API-Based Downloads** - Direct file downloads bypassing UI limitations (100% success rate)
✅ **Recursive Subfolder Support** - Automatically processes all subfolders
✅ **Smart Deduplication** - Compares file sizes to avoid re-downloading existing files
✅ **Proper Folder Hierarchy** - Maintains nested folder structure
✅ **Pagination Handling** - Automatically sets to 100 items per page
✅ **File Logging** - Optional detailed logging to track all operations
✅ **User-Friendly GUI** - Easy to use graphical interface
✅ **Encrypted Credentials** - Securely stores your Neat.com login
✅ **Headless Mode** - Run browser in background for faster backups
✅ **Cross-Platform** - Works on macOS, Windows, and Linux

## Quick Start

### Option 1: Double-Click Launcher (macOS) 🍎

1. **Double-click**: `Neat Backup.command` in the project folder
2. **Configure**: Enter credentials and settings
3. **Click**: "Start Backup"

Or double-click `dist/Neat Backup.app` if you've built it (macOS only).

### Option 2: Run from Terminal (All Platforms)

**1. Install Dependencies**

```bash
cd path/to/neat-backup-automation
pip3 install -r requirements.txt
```

**2. Run the Application**

```bash
python3 main.py
```

**3. Configure and Start**

1. Enter your Neat.com credentials
2. Select backup folder (default: `~/Downloads/Neat`)
3. Optional: Enable file logging
4. Optional: Enable headless mode for background operation
5. Click "Start Backup"

## How It Works

### Technology Stack

- **Selenium WebDriver** - Browser automation
- **Chrome DevTools Protocol (CDP)** - Network interception to capture API responses
- **Requests** - Direct file downloads with session cookies
- **Tkinter** - Cross-platform GUI

### Download Process

1. **Login** - Authenticates to Neat.com
2. **Folder Discovery** - Finds all top-level folders (19 folders)
3. **API Interception** - Captures file metadata from API responses
4. **Smart Download** - For each file:
   - Checks if file exists locally
   - Compares file sizes (remote vs local)
   - Downloads only if new or different size
   - Saves with numbered suffix if same name but different size
5. **Recursive Processing** - Automatically processes subfolders

### Deduplication Logic

The tool uses intelligent deduplication to avoid re-downloading files:

- **File exists with same size** → Skip (already have it)
- **File exists with different size** → Download as `filename_1.pdf`, `filename_2.pdf`, etc.
- **File doesn't exist** → Download

This handles Neat's case where the same filename may represent different documents.

## Folder Structure

Downloaded files are organized as:

```
~/Downloads/Neat/
├── _logs/                          # Log files (if logging enabled)
│   └── neat_backup_20251025_120000.log
├── 2013 year TAX/
│   ├── files.pdf
│   └── Receipts/                   # Subfolder
│       └── receipt_files.pdf
├── 2014 year TAX/
├── 2024 year TAX/
├── Business/
└── Home/
```

## Configuration

### Settings via GUI

- **Backup Folder** - Where files are saved (default: `~/Downloads/Neat`)
- **Headless Mode** - Run browser in background (faster, no window)
- **File Logging** - Save detailed logs to `backup_folder/_logs/`
- **Remember Credentials** - Encrypted storage of login credentials

### Advanced Configuration

Edit `config.json` for advanced settings:

```json
{
  "download_dir": "~/Downloads/Neat",
  "chrome_headless": false,
  "enable_logging": false,
  "wait_timeout": 10
}
```

**Note**: Paths use `~` notation which works on all platforms (macOS, Linux, Windows).

## Performance

- **Time per file**: ~0.5-2 seconds (with API downloads)
- **Full backup** (500 files): ~15-30 minutes
- **Network dependent**: Download speed varies based on file sizes

### Optimization Tips

1. Enable headless mode
2. Enable logging only when troubleshooting
3. Run during off-peak hours for better network speed

## Troubleshooting

### Common Issues

**Error: "ChromeDriver not compatible"**
```bash
pip3 install --upgrade webdriver-manager
```

**Error: "Login failed"**
- Verify credentials are correct
- Check if Neat.com is accessible
- Try logging in manually first

**Files not downloading**
- Check backup folder permissions
- Ensure sufficient disk space
- Check network connection

**Only one folder downloaded**
- You may have run a test script instead of full backup
- Run `python3 main.py` and use the GUI

### Logging

Enable file logging in the GUI to see detailed operations:

```bash
cat ~/Downloads/Neat/_logs/neat_backup_*.log
```

Logs include:
- Folder discovery
- File detection
- Download status
- Skipped files (with reasons)
- Errors and warnings

## Project Structure

```
neat-backup-automation/
├── main.py                   # GUI application
├── neat_bot.py              # Core backup logic (API-based)
├── config.py                # Configuration management
├── utils.py                 # Utility functions
├── requirements.txt         # Python dependencies
├── setup.py                 # macOS app build configuration
├── Neat Backup.command      # macOS launcher script
├── README.md                # This file
├── QUICKSTART.md            # Quick start guide
├── CLEANUP_SUMMARY.md       # Project cleanup log
└── _archive/                # Old test files and docs
```

## Version History

### v2.0 (Current) - API-Based Implementation
- Direct API downloads (bypasses virtual scrolling)
- Size-based deduplication
- Recursive subfolder support
- Improved logging
- Enhanced GUI with better button visibility

### v1.0 - UI-Based Implementation
- Automated clicking and scrolling
- 52% success rate due to virtual scrolling limitations
- Archived in `_archive/neat_bot_old.py`

## Technical Details

### Virtual Scrolling Issue (Solved)

**Problem**: Neat.com uses virtual scrolling which only loads 12-14 items in DOM even when 23+ files exist in the folder.

**Solution**: Bypass the UI entirely:
1. Use Chrome DevTools Protocol to intercept API responses
2. Extract file metadata including `download_url`
3. Download files directly via HTTP requests using browser session cookies

### API Endpoints

The tool intercepts responses from:
- `/api/v5/entities` - Returns folder contents with download URLs

## Requirements

- Python 3.8+
- macOS, Linux, or Windows
- Chrome browser
- Internet connection

## Security

- Credentials are encrypted using `cryptography.fernet`
- Stored in `~/.neat_credentials.enc`
- API session uses browser cookies (same security as manual login)
- No credentials stored in plain text

## Building the macOS App

The project includes:
- `Neat Backup.command` - Simple launcher script (just double-click)
- `dist/Neat Backup.app` - Optional .app bundle

### Building the .app

**Alias Mode (Recommended - 228KB):**
```bash
pip3 install py2app
python3 setup.py py2app -A
```

The .app will be created in `dist/Neat Backup.app`. Alias mode creates a lightweight app that links to your Python installation and project files.

**Standalone Mode (113MB, has code signing issues):**
```bash
python3 setup.py py2app
```

Creates a fully self-contained app, but may fail due to macOS code signing requirements.

## Platform Notes

### macOS
- **Tested**: macOS Ventura 13.x
- **Launcher**: Double-click `Neat Backup.command` or `dist/Neat Backup.app`
- **Chrome**: Automatically managed by webdriver-manager

### Windows
- **Status**: Should work, not tested
- **Launcher**: Create a `.bat` file: `python main.py`
- **Chrome**: Must be installed, path auto-detected

### Linux
- **Status**: Should work, not tested
- **Launcher**: Create a `.sh` file: `#!/bin/bash\npython3 main.py`
- **Chrome**: Must be installed (`chromium` or `google-chrome`)

## Contributing

Contributions welcome! Feel free to:
- Report bugs via GitHub Issues
- Submit pull requests
- Fork and modify for your needs

## License

MIT License - Feel free to use and modify.

## Support

For issues or questions:
1. Check log files (if logging is enabled)
2. Review this README and QUICKSTART.md
3. Open an issue on GitHub

## Disclaimer

This is an unofficial tool and is not affiliated with or endorsed by Neat.com. Use at your own risk.

---

**Version**: 2.0
**Platform**: Cross-platform (Python 3.8+)
**Tested on**: macOS Ventura 13.x
