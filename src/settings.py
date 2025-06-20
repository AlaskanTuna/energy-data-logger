# src/settings.py

import json
import os

# CONSTANTS

SETTINGS_FILE = "../data/settings.json"
DEFAULT_SETTINGS = {
    "LOG_INTERVAL": 5,
    "MODBUS_SLAVE_ID": 1,
    "BAUDRATE": 9600,
    "PARITY": 'N',
    "BYTESIZE": 8,
    "STOPBITS": 1,
    "TIMEOUT": 2
}

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
                print(f"[ERROR]: Failed to read settings file. Using default settings.")
                self.data = DEFAULT_SETTINGS.copy()
        else:
            print(f"[WARNING]: No settings file found. Using default settigns.")
            self.data = DEFAULT_SETTINGS.copy()
            self.save_settings()

    def save_settings(self):
        """
        Saves the current settings to the JSON file.
        """
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.data, f, indent=4)
            return True
        except IOError:
            print(f"[ERROR]: Failed to write settings file.")
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
                if isinstance(value, type(self.data[key])):
                    self.data[key] = value
                else:
                    print(f"[WARNING]: Type mismatch for setting '{key}'. Ignoring setting.")
        return self.save_settings()

# GLOBAL INSTANCE

settings = Settings()