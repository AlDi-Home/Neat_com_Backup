# Neat Backup Automation - Complete File Index

**Version:** 1.0.0 with GitHub Spec Kit Integration  
**Last Updated:** January 2025

---

## 📁 Project Structure

```
NeatBackupAutomation/
├── 📄 Source Code (Python)
│   ├── main.py (11 KB) - GUI application
│   ├── neat_bot.py (12 KB) - Selenium automation engine
│   ├── config.py (2.7 KB) - Configuration & encryption
│   └── utils.py (2.8 KB) - File management utilities
│
├── 📚 User Documentation
│   ├── README.md (5.1 KB) - Full documentation
│   ├── QUICKSTART.md (4.3 KB) - 5-minute quick start
│   ├── PROJECT_SUMMARY.md (7.5 KB) - Project overview
│   └── ARCHITECTURE.md (1.6 KB) - System architecture
│
├── 🎯 Spec-Driven Development
│   ├── constitution.md (15 KB) - Project principles
│   ├── SPEC_DRIVEN_DEV.md (11 KB) - SDD workflow guide
│   └── specs/
│       └── 001-initial-backup/
│           ├── feature.md (12 KB) - What we built
│           ├── plan.md (14 KB) - How we built it
│           └── quickstart.md (11 KB) - Validation guide
│
├── 🤖 AI Integration (.github/)
│   └── prompts/
│       ├── specify.md (5.2 KB) - /specify command
│       ├── plan.md (8.5 KB) - /plan command
│       └── tasks.md (9.2 KB) - /tasks command
│
└── ⚙️ Configuration
    └── requirements.txt (63 B) - Dependencies
```

---

## 📄 Source Code Files

### **main.py** (11 KB)
**Purpose:** GUI application entry point  
**Framework:** TKinter  
**Key Classes:**
- `NeatBackupGUI` - Main application window

**Responsibilities:**
- User interface rendering
- User input collection
- Background thread management
- Status callback handling

**Entry Point:**
```bash
python3 main.py
```

---

### **neat_bot.py** (12 KB)
**Purpose:** Core Selenium automation engine  
**Framework:** Selenium WebDriver 4.27.1  
**Key Classes:**
- `NeatBot` - Automation controller

**Responsibilities:**
- Chrome WebDriver lifecycle
- Neat.com login automation
- Folder discovery
- File export workflow
- Download monitoring

**Key Methods:**
- `login()` - Authenticate to Neat.com
- `get_folders()` - Discover all folders
- `export_folder_files()` - Export files from folder
- `run_backup()` - Complete backup orchestration

---

### **config.py** (2.7 KB)
**Purpose:** Configuration and credential management  
**Encryption:** Fernet (AES-128)  
**Key Classes:**
- `Config` - Settings and credential manager

**Responsibilities:**
- Credential encryption/decryption
- Settings persistence (JSON)
- Configuration validation

**Storage Locations:**
- Settings: `~/.neat_backup/config.json`
- Credentials: `~/.neat_backup/creds.enc`
- Encryption key: `~/.neat_backup/key.key`

---

### **utils.py** (2.8 KB)
**Purpose:** Utility functions  
**Type:** Pure functions  

**Key Functions:**
- `wait_for_download()` - Monitor download completion
- `organize_file()` - Move file to backup structure
- `sanitize_folder_name()` - Filesystem-safe names
- `get_chrome_download_dir()` - Platform-specific downloads path

---

## 📚 User Documentation

### **README.md** (5.1 KB)
**Audience:** End users and developers  
**Content:**
- Features overview
- Installation instructions
- Usage guide
- Troubleshooting
- Spec-Driven Development section

**When to Read:** First introduction to project

---

### **QUICKSTART.md** (4.3 KB)
**Audience:** First-time users  
**Content:**
- Installation (5 minutes)
- First run setup
- Quick deployment guide
- PDF dropdown selector fix

**When to Read:** Immediate deployment needs

---

### **PROJECT_SUMMARY.md** (7.5 KB)
**Audience:** Project stakeholders  
**Content:**
- Project overview
- Technical architecture
- Development status
- Deployment instructions
- Performance estimates

**When to Read:** Understanding project scope and status

---

### **ARCHITECTURE.md** (1.6 KB)
**Audience:** Developers  
**Content:**
- High-level flow diagram
- Component breakdown
- Technology stack
- Processing pipeline

**When to Read:** Understanding system design

---

## 🎯 Spec-Driven Development Files

### **constitution.md** (15 KB)
**Purpose:** Project principles and non-negotiable standards  
**Audience:** All contributors  
**Content:**
- Technical principles
- Security requirements
- Code quality standards
- Performance targets
- Development standards

**Authority:** Guides ALL development decisions

**Key Sections:**
1. **Technical Principles** - Platform, security, UX
2. **Development Standards** - Code quality, dependencies
3. **Selenium Standards** - Automation best practices
4. **Enterprise Considerations** - Organizational alignment

**When to Consult:** Before ANY code change

---

### **SPEC_DRIVEN_DEV.md** (11 KB)
**Purpose:** Explain Spec-Driven Development workflow  
**Audience:** Developers using Claude Code  
**Content:**
- SDD philosophy
- Four-phase process (/specify, /plan, /tasks, implement)
- Working with Claude Code
- Example walkthrough
- Best practices

**When to Read:** Adding new features

---

### **specs/001-initial-backup/**

#### **feature.md** (12 KB)
**Purpose:** WHAT we're building  
**Content:**
- Problem statement
- User stories (10 stories)
- Functional requirements
- Non-functional requirements
- Success metrics
- Risks & mitigations
- Validation scenarios

**Key Sections:**
- US-001 through US-010 (user stories)
- FR-001 through FR-007 (functional requirements)
- NFR-001 through NFR-006 (non-functional requirements)

---

#### **plan.md** (14 KB)
**Purpose:** HOW to implement the feature  
**Content:**
- Architecture overview
- Technology stack rationale
- Module breakdown
- Data models
- Selenium implementation
- Security architecture
- Performance considerations
- Error handling strategy
- Testing approach

**Key Sections:**
- 4 module breakdowns (main, bot, config, utils)
- Selenium workflow details
- Encryption process flow
- Retry logic patterns

---

#### **quickstart.md** (11 KB)
**Purpose:** Validation scenarios  
**Content:**
- Pre-validation setup
- 7 validation scenarios
- Troubleshooting guide
- Performance benchmarks
- Sign-off checklist

**Scenarios:**
1. Fresh Installation
2. Login & Folder Discovery
3. Single File Export
4. Error Handling
5. Credential Persistence
6. Complete Backup
7. Edge Cases

---

## 🤖 AI Integration Files

### **.github/prompts/specify.md** (5.2 KB)
**Purpose:** Custom `/specify` command for Claude Code  
**Triggers:** User runs `/specify [feature description]`  
**Output:** Generates `specs/[branch]/feature.md`

**Instructions for Claude:**
- Read constitution.md
- Focus on WHAT and WHY
- Generate user stories
- Define acceptance criteria
- Avoid technical details (those go in /plan)

---

### **.github/prompts/plan.md** (8.5 KB)
**Purpose:** Custom `/plan` command for Claude Code  
**Triggers:** User runs `/plan` (after /specify)  
**Output:** Generates `specs/[branch]/plan.md`

**Instructions for Claude:**
- Read feature.md and constitution.md
- Focus on HOW
- Define technical architecture
- Specify implementation approach
- Include code examples
- Address security, performance, testing

---

### **.github/prompts/tasks.md** (9.2 KB)
**Purpose:** Custom `/tasks` command for Claude Code  
**Triggers:** User runs `/tasks` (after /plan)  
**Output:** Generates `specs/[branch]/tasks.md`

**Instructions for Claude:**
- Break plan into 15-60 minute tasks
- Test-first ordering
- Explicit dependencies
- Clear acceptance criteria
- Validation commands

---

## ⚙️ Configuration Files

### **requirements.txt** (63 B)
**Purpose:** Python dependencies  
**Content:**
```
selenium==4.27.1
webdriver-manager==4.0.2
cryptography==44.0.0
```

**Installation:**
```bash
pip3 install -r requirements.txt
```

---

## 📊 File Statistics

| Category | Files | Total Size |
|----------|-------|------------|
| Source Code | 4 | ~28 KB |
| User Docs | 4 | ~19 KB |
| Spec Kit Docs | 6 | ~64 KB |
| AI Prompts | 3 | ~23 KB |
| **Total** | **17** | **~134 KB** |

---

## 🚀 Quick Navigation

### **For End Users:**
1. Start with: `QUICKSTART.md`
2. Then read: `README.md`
3. Reference: `PROJECT_SUMMARY.md`

### **For Developers:**
1. Understand principles: `constitution.md`
2. Learn SDD workflow: `SPEC_DRIVEN_DEV.md`
3. Study implementation: `specs/001-initial-backup/`
4. Reference architecture: `ARCHITECTURE.md`

### **For Adding Features:**
1. Read: `SPEC_DRIVEN_DEV.md`
2. Review: `constitution.md`
3. Run: `/specify [your feature]`
4. Follow: Four-phase SDD process

### **For Troubleshooting:**
1. Check: `QUICKSTART.md` troubleshooting section
2. Review: `specs/001-initial-backup/quickstart.md` validation
3. Search: `README.md` for common issues

---

## 🎯 Key Concepts

### **Constitution Over Code**
`constitution.md` defines non-negotiable principles that guide all development.

### **Specs Are Source of Truth**
Specifications in `specs/` define WHAT gets built. Code implements the specs.

### **Test-First Development**
Write tests before code. Tasks are ordered: tests → implementation → validation.

### **AI-Native Workflow**
Custom prompts in `.github/prompts/` guide Claude Code to generate consistent, high-quality specs and code.

---

## 🔄 Development Workflow

```
1. Read constitution.md
   ↓
2. /specify [feature]
   → specs/[branch]/feature.md
   ↓
3. /plan
   → specs/[branch]/plan.md
   ↓
4. /tasks
   → specs/[branch]/tasks.md
   ↓
5. Implement tasks
   → Update source code
   ↓
6. Validate
   → Manual testing
   ↓
7. Document
   → Update README/docs
```

---

## 📝 Version History

| Version | Files | Changes |
|---------|-------|---------|
| 1.0.0 | 17 | Initial release with full Spec Kit integration |

---

## 📞 Support

**Questions about:**
- **Usage:** See `README.md` and `QUICKSTART.md`
- **Development:** See `SPEC_DRIVEN_DEV.md`
- **Architecture:** See `ARCHITECTURE.md` and `specs/001-initial-backup/plan.md`
- **Principles:** See `constitution.md`

---

**This index provides a complete map of the Neat Backup Automation project structure and documentation.**
