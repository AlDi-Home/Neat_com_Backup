# System Architecture Diagram

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE (GUI)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐    │
│  │ Credentials │  │   Settings  │  │  Status Log &    │    │
│  │   Entry     │  │   Config    │  │  Progress Bar    │    │
│  └─────────────┘  └─────────────┘  └──────────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               CONFIGURATION MANAGER                          │
│  ┌──────────────────┐      ┌─────────────────────────┐     │
│  │ Encrypted Creds  │◄────►│   Settings Storage      │     │
│  │  (Fernet)        │      │   (JSON)                │     │
│  └──────────────────┘      └─────────────────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  AUTOMATION ENGINE                           │
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │  Login   │──►│  Discover│──►│  Export  │               │
│  │  to Neat │   │  Folders │   │  Files   │               │
│  └──────────┘   └──────────┘   └──────────┘               │
│                                       │                      │
│                                       ▼                      │
│  ┌─────────────────────────────────────────────┐           │
│  │        Selenium WebDriver (Chrome)          │           │
│  │  ┌─────────┐  ┌──────────┐  ┌───────────┐  │           │
│  │  │Navigate │  │  Select  │  │ Download  │  │           │
│  │  │Folders  │  │  Files   │  │   PDFs    │  │           │
│  │  └─────────┘  └──────────┘  └───────────┘  │           │
│  └─────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FILE MANAGEMENT SYSTEM                          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   Download   │  │   Organize   │  │  Verify & Move  │   │
│  │   Tracking   │──│    Files     │──│   to Backup     │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                 ┌───────────────┐
                 │  FINAL OUTPUT │
                 │               │
                 │   ~/NeatBackup/│
                 │   ├─ 2024/    │
                 │   ├─ 2023/    │
                 │   └─ ...      │
                 └───────────────┘
```

## Component Details

### 1. GUI Layer (`main.py`)
- **TKinter Interface**
- Credential input with show/hide
- Settings configuration
- Real-time status logging
- Progress indication
- Thread management for non-blocking

### 2. Configuration (`config.py`)
- **Credential Encryption** (Fernet symmetric)
- Settings persistence (JSON)
- Secure key management
- Load/save preferences

### 3. Automation Engine (`neat_bot.py`)
- **Selenium WebDriver** initialization
- Chrome automation
- Login flow management
- Folder discovery
- File export workflow
- Error handling & retry logic

### 4. File Management (`utils.py`)
- Download verification
- File organization (nested folders)
- Path sanitization
- Cross-platform compatibility

## Data Flow

```
User Input → Encryption → Storage → Selenium → Neat.com
                                        ↓
                                    Download
                                        ↓
                              Verify & Organize
                                        ↓
                                 Final Backup
```

## Security Model

```
┌─────────────┐
│  Password   │
│  (plaintext)│
└──────┬──────┘
       │
       ▼
┌──────────────┐
│   Fernet     │
│  Encryption  │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  Encrypted File  │
│  creds.enc       │
└──────────────────┘

Key stored separately in key.key
```

## File Processing Pipeline

```
1. Select File (checkbox)
        ↓
2. Click Export Button
        ↓
3. Click PDF Option (dropdown)
        ↓
4. Wait for BLOB URL Link
        ↓
5. Click Download Link
        ↓
6. Monitor Downloads Folder
        ↓
7. Wait for .crdownload removal
        ↓
8. Move to Organized Folder
        ↓
9. Update Progress
        ↓
10. Next File
```

## Error Handling Strategy

```
Try Operation
    ↓
  Success? ─Yes→ Continue
    ↓ No
Log Error
    ↓
Retry? ─Yes→ Retry (max 3x)
    ↓ No
Skip & Continue
    ↓
Report to User
```

## Thread Architecture

```
┌─────────────┐
│  Main GUI   │
│   Thread    │
└──────┬──────┘
       │
       ├──► Update UI
       │
       └──► Start Backup Thread
                    ↓
            ┌───────────────┐
            │ Backup Thread │
            │  (Selenium)   │
            └───────┬───────┘
                    │
                    ├──► Status Callbacks
                    │
                    └──► Completion Signal
```

## Performance Optimization

```
Sequential Processing:
File 1 → Download → Organize → File 2 → ...

Time per file: 10-20 seconds
Total files: 500-1,250
Total time: 2-4 hours

Optimization options:
- Headless mode: -15% time
- Reduced delays: -20% time
- Parallel (not recommended): Rate limiting risk
```
