# Neat Backup Automation - Project Constitution

## Purpose

This constitution defines the non-negotiable principles, constraints, and standards that guide all development decisions for the Neat Backup Automation project. These principles ensure consistency, quality, and alignment with organizational needs.

## Project Overview

**Mission**: Automate the complete backup of Neat.com document libraries with enterprise-grade reliability, security, and user experience.

**Target Users**: IT Directors and technical professionals managing document libraries across multiple Neat.com accounts.

**Core Value Proposition**: Transform 20+ hours of manual clicking into a single-click automated backup process, with encrypted credential storage and organized folder structures.

---

## Technical Principles

### 1. Platform & Compatibility

**MUST Requirements:**
- ✅ Python 3.8+ compatibility (minimum version)
- ✅ Cross-platform support (macOS, Windows, Linux)
- ✅ Chrome 141+ browser requirement (documented)
- ✅ No platform-specific code without abstraction layer

**Rationale**: Ensure maximum accessibility across IT environments and future OS versions.

### 2. Security First

**MUST Requirements:**
- ✅ All credentials MUST be encrypted at rest (Fernet symmetric encryption)
- ✅ Encryption keys MUST be stored separately from encrypted data
- ✅ No plaintext credentials in logs, memory dumps, or config files
- ✅ Secure credential transmission (HTTPS only)
- ✅ User consent required before storing credentials

**MUST NOT:**
- ❌ Never store passwords in plaintext
- ❌ Never transmit credentials over unencrypted channels
- ❌ Never log sensitive information

**Rationale**: Protect user credentials and comply with enterprise security requirements.

### 3. User Experience

**MUST Requirements:**
- ✅ GUI-based interface (TKinter)
- ✅ Real-time progress indication
- ✅ Clear status logging with color-coded messages
- ✅ Graceful error handling with user-friendly messages
- ✅ Non-blocking operations (threading required)
- ✅ Ability to pause/stop operations

**MUST NOT:**
- ❌ Never freeze the UI during operations
- ❌ Never require command-line usage for core functionality
- ❌ Never display technical stack traces to end users

**Rationale**: Enable non-developer IT professionals to use the tool confidently.

### 4. Reliability & Error Handling

**MUST Requirements:**
- ✅ Comprehensive error handling at all integration points
- ✅ Automatic retry logic for transient failures (max 3 attempts)
- ✅ Graceful degradation (continue on individual file failures)
- ✅ Complete audit trail in status log
- ✅ Download verification before file organization

**MUST NOT:**
- ❌ Never crash without logging the error
- ❌ Never lose track of progress state
- ❌ Never leave partial/corrupted downloads

**Rationale**: Ensure reliable operation across 500-1,250 files with minimal supervision.

### 5. Data Organization

**MUST Requirements:**
- ✅ Nested folder structure matching Neat.com hierarchy
- ✅ Sanitized folder names (filesystem-safe)
- ✅ Duplicate filename handling (append counter)
- ✅ Preserve original PDF quality
- ✅ Consistent naming convention: `{OriginalTitle} - {Category}.pdf`

**Structure Pattern:**
```
~/NeatBackup/
├── {FolderName}/
│   ├── {FileName} - {Category}.pdf
│   └── ...
└── ...
```

**Rationale**: Mirror Neat.com organization for easy navigation and prevent data loss.

### 6. Performance Standards

**Target Benchmarks:**
- ✅ 10-20 seconds per file (network dependent)
- ✅ Headless mode for 15% speed improvement
- ✅ Configurable delays between operations
- ✅ Memory efficient (no large file buffering)

**MUST NOT:**
- ❌ Never implement parallel downloads (risk of rate limiting)
- ❌ Never cache large files in memory
- ❌ Never block on unnecessary operations

**Rationale**: Balance speed with Neat.com API respect and system resource usage.

---

## Development Standards

### 7. Code Quality

**MUST Requirements:**
- ✅ Type hints for all function signatures (Python 3.8+)
- ✅ Docstrings for all public functions/classes
- ✅ Maximum function length: 50 lines
- ✅ Maximum file length: 300 lines
- ✅ Clear separation of concerns (modular architecture)

**Architecture Pattern:**
```
config.py    → Configuration & encryption
utils.py     → Pure utility functions
neat_bot.py  → Selenium automation engine
main.py      → GUI & orchestration
```

**Rationale**: Maintainable, testable, and extensible codebase.

### 8. Dependencies

**MUST Requirements:**
- ✅ Pin all dependencies to specific versions
- ✅ Minimize external dependencies
- ✅ Use PyPI packages only (no private repos)
- ✅ Document installation requirements clearly

**Current Stack:**
- `selenium==4.27.1` - Browser automation
- `webdriver-manager==4.0.2` - ChromeDriver management
- `cryptography==44.0.0` - Credential encryption

**MUST NOT:**
- ❌ Never use deprecated packages
- ❌ Never add dependencies without justification
- ❌ Never use packages with known security vulnerabilities

**Rationale**: Reduce supply chain risk and ensure reproducible builds.

### 9. Documentation

**MUST Requirements:**
- ✅ README.md with quick start guide
- ✅ QUICKSTART.md for immediate deployment
- ✅ Architecture documentation
- ✅ Inline code comments for complex logic
- ✅ Troubleshooting guide with common issues

**Documentation Hierarchy:**
1. QUICKSTART.md → 5-minute deployment
2. README.md → Full documentation
3. ARCHITECTURE.md → Technical deep-dive
4. Inline comments → Implementation details

**Rationale**: Enable users at all skill levels to deploy and extend.

### 10. Testing Strategy

**MUST Requirements (Future):**
- ✅ Unit tests for utility functions
- ✅ Integration tests for Selenium workflows
- ✅ Manual validation checklist before releases
- ✅ Test on all supported platforms

**Current Status:** Manual testing phase
**Future Goal:** 80% code coverage with automated tests

---

## Selenium Automation Standards

### 11. Browser Automation

**MUST Requirements:**
- ✅ Use explicit waits (WebDriverWait)
- ✅ Never use time.sleep() except for deliberate delays
- ✅ CSS selectors preferred over XPath (more stable)
- ✅ Graceful handling of stale element references
- ✅ Headless mode option for unattended operation

**Selector Priority:**
1. `data-testid` attributes (most stable)
2. Semantic CSS classes
3. XPath as last resort

**Rationale**: Robust automation resistant to UI changes.

### 12. Download Management

**MUST Requirements:**
- ✅ Monitor .crdownload removal for completion
- ✅ Configurable timeout (default 30 seconds)
- ✅ Verify file exists before moving
- ✅ Handle partial downloads gracefully

**Download Flow:**
```
1. Click download link
2. Monitor for .crdownload file
3. Wait for .crdownload removal
4. Verify final file exists
5. Move to organized location
6. Log success/failure
```

**Rationale**: Ensure download completeness before file operations.

---

## Configuration Standards

### 13. Settings Management

**Configuration Hierarchy:**
1. User preferences (GUI settings)
2. Config file (`~/.neat_backup/config.json`)
3. Hardcoded defaults (code)

**MUST Requirements:**
- ✅ All settings in config.json
- ✅ GUI updates config.json automatically
- ✅ Sensible defaults for all settings
- ✅ Settings validation on load

**Standard Settings:**
```json
{
  "download_dir": "~/NeatBackup",
  "chrome_headless": false,
  "wait_timeout": 10,
  "download_timeout": 30,
  "delay_between_files": 1
}
```

---

## Constraints & Limitations

### 14. Known Limitations

**Documented Constraints:**
- ✅ Sequential processing only (no parallel downloads)
- ✅ Chrome browser required
- ✅ Active internet connection required
- ✅ Neat.com rate limiting respected

**Future Enhancements (Not MVP):**
- ⏳ Incremental backup (only new files)
- ⏳ Multi-account support
- ⏳ Cloud upload integration
- ⏳ Scheduling/cron integration

**Rationale**: Focus on core functionality first, iterate based on user feedback.

---

## Enterprise Considerations

### 15. Organizational Alignment

**Juel Group of Companies Context:**
- ✅ IT Director approval for deployment
- ✅ Compatible with existing IT infrastructure
- ✅ No cloud dependencies (runs locally)
- ✅ Audit trail for compliance

**Integration Points:**
- Future: Integration with Laserfiche for backup archival
- Future: ManageEngine ticket creation on failures
- Future: Power BI dashboard for backup metrics

---

## Version Control & Release

### 16. Versioning Standards

**Semantic Versioning:**
- MAJOR.MINOR.PATCH (e.g., 1.0.0)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

**Current Version:** v1.0.0 (Initial Release)

---

## Enforcement

### 17. Constitutional Compliance

**Before Any Code Change:**
1. ✅ Does it align with these principles?
2. ✅ Does it maintain security standards?
3. ✅ Does it preserve user experience?
4. ✅ Does it introduce new dependencies?

**When Principles Conflict:**
- Security > Performance
- Reliability > Speed
- User Experience > Code Elegance

**Constitution Updates:**
- Require explicit justification
- Document in git commit message
- Update version history

---

## Ratification

**Author:** Alex Diomin, IT Director, Juel Group of Companies  
**Date:** January 2025  
**Status:** Active  
**Review Cycle:** Quarterly or as needed

---

This constitution is a living document that guides all development decisions while remaining flexible enough to accommodate growth and learning.