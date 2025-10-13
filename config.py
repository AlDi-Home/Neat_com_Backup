"""
Configuration and credential management for Neat Backup Automation
"""
import os
import json
from pathlib import Path
from cryptography.fernet import Fernet
from typing import Optional

class Config:
    """Manages application configuration and encrypted credentials"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.neat_backup'
        self.config_file = self.config_dir / 'config.json'
        self.key_file = self.config_dir / 'key.key'
        self.config_dir.mkdir(exist_ok=True)
        
        # Default settings
        self.settings = {
            'download_dir': str(Path.home() / 'NeatBackup'),
            'chrome_headless': False,
            'wait_timeout': 10,
            'download_timeout': 30,
            'delay_between_files': 1
        }
        
        self._load_config()
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize or load encryption key"""
        if not self.key_file.exists():
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
        
        self.cipher = Fernet(self.key_file.read_bytes())
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                saved_config = json.load(f)
                self.settings.update(saved_config)
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def save_credentials(self, username: str, password: str):
        """Encrypt and save credentials"""
        creds = {
            'username': username,
            'password': password
        }
        encrypted = self.cipher.encrypt(json.dumps(creds).encode())
        creds_file = self.config_dir / 'creds.enc'
        creds_file.write_bytes(encrypted)
    
    def load_credentials(self) -> Optional[tuple]:
        """Load and decrypt credentials"""
        creds_file = self.config_dir / 'creds.enc'
        if not creds_file.exists():
            return None
        
        try:
            encrypted = creds_file.read_bytes()
            decrypted = self.cipher.decrypt(encrypted)
            creds = json.loads(decrypted.decode())
            return creds['username'], creds['password']
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value"""
        self.settings[key] = value
        self.save_config()

    def validate(self) -> tuple:
        """
        Validate configuration settings

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Validate download_dir
        download_dir = self.settings.get('download_dir')
        if not download_dir:
            errors.append("download_dir is not set")
        else:
            try:
                path = Path(download_dir)
                # Check if parent directory exists or can be created
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                # Check if directory is writable
                if not os.access(str(path), os.W_OK):
                    errors.append(f"download_dir is not writable: {download_dir}")
            except Exception as e:
                errors.append(f"Invalid download_dir: {str(e)}")

        # Validate chrome_headless (must be boolean)
        chrome_headless = self.settings.get('chrome_headless')
        if chrome_headless is not None and not isinstance(chrome_headless, bool):
            errors.append(f"chrome_headless must be boolean, got {type(chrome_headless)}")

        # Validate numeric timeouts
        numeric_settings = {
            'wait_timeout': (1, 60),
            'download_timeout': (5, 300),
            'delay_between_files': (0, 10)
        }

        for key, (min_val, max_val) in numeric_settings.items():
            value = self.settings.get(key)
            if value is not None:
                if not isinstance(value, (int, float)):
                    errors.append(f"{key} must be numeric, got {type(value)}")
                elif value < min_val or value > max_val:
                    errors.append(f"{key} must be between {min_val} and {max_val}, got {value}")

        return (len(errors) == 0, errors)
