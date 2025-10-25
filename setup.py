"""
Setup script for creating macOS .app bundle for Neat Backup Automation
"""
from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,
    'plist': {
        'CFBundleName': 'Neat Backup',
        'CFBundleDisplayName': 'Neat Backup Automation',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 Alex. All rights reserved.',
        'CFBundleIdentifier': 'com.alex.neatbackup',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': True,
    },
    'packages': ['tkinter', 'selenium', 'requests', 'cryptography'],
    'includes': ['config', 'neat_bot', 'utils'],
    'excludes': ['test_*', 'debug_*', 'capture_*', 'analyze_*'],
}

setup(
    name='Neat Backup Automation',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
