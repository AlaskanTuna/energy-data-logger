# src/services/settings.py

import json
import os
import logging

from config import config

# CONSTANTS

SETTINGS_FILE = "../data/settings.json"
DEFAULT_SETTINGS = {
    "LOG_INTERVAL": 900,
    "MODBUS_SLAVE_ID": 1,
    "BAUDRATE": 9600,
    "PARITY": 'N',
    "BYTESIZE": 8,
    "STOPBITS": 1,
    "TIMEOUT": 2
}
log = logging.getLogger(__name__)

# SERVICES

class Settings:
    """
    Manages application settings.
    """
    _instance = None

    def __new__(cls):
        """
        Singleton instance creation.
        """
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance.load_settings()
        return cls._instance

    def load_settings(self):
        """
        Loads settings from the JSON file or default.
        """
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    loaded = json.load(f)
                    self.data = DEFAULT_SETTINGS.copy()
                    self.data.update(loaded)
            except (IOError, json.JSONDecodeError):
                log.error(f"Failed to read settings file. Using default settings.")
                self.data = DEFAULT_SETTINGS.copy()
        else:
            log.warning(f"No settings file found. Using default settings.")
            self.data = DEFAULT_SETTINGS.copy()
            self.save_settings()

    def save_settings(self):
        """
        Saves the current settings to the JSON file.
        """
        try:
            if not os.path.exists(config.DS_DIR):
                os.makedirs(config.DS_DIR, exist_ok=True)

            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.data, f, indent=4)
            return True
        except IOError:
            log.error(f"Failed to write settings file.")
            return False

    def get(self, key):
        """
        Gets a specific setting value.
        """
        return self.data.get(key)

    def get_all(self):
        """
        Returns all current settings.
        """
        return self.data.copy()

    def update(self, new_settings):
        """
        Updates multiple settings and saves them.
        """
        for key, value in new_settings.items():
            if key in self.data:
                expected_type = type(DEFAULT_SETTINGS[key])
                try:
                    self.data[key] = expected_type(value)
                except (ValueError, TypeError):
                    log.warning(f"Invalid type. Could not set '{key}' to '{value}'.")
        return self.save_settings()

# GLOBAL INSTANCE

settings = Settings()