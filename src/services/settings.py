# src/services/settings.py

import logging

from config import config
from services.database import SessionLocal, Setting
from sqlalchemy.exc import SQLAlchemyError

# CONSTANTS

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
        Loads settings from the JSON file or default from the database.
        """
        db = SessionLocal()
        try:
            db_settings = db.query(Setting).all()
            if not db_settings:
                log.warning("No settings found in the database. Using default settings.")
                for key, value in config.DEFAULT_SETTINGS.items():
                    db.add(Setting(key=key, value=str(value)))
                db.commit()
                db_settings = db.query(Setting).all()

            self.data = {}
            temp_data = {s.key: s.value for s in db_settings}
            for key, default_value in config.DEFAULT_SETTINGS.items():
                expected_type = type(default_value)
                try:
                    self.data[key] = expected_type(temp_data.get(key)) # Convert database string value back to original datatype
                except (ValueError, TypeError):
                    self.data[key] = default_value
        except SQLAlchemyError as e:
            log.error(f"DB Loading Error: {e}. Using default settings.", exc_info=True)
            self.data = config.DEFAULT_SETTINGS.copy()
            db.rollback()
        finally:
            db.close()

    def get(self, key):
        """
        Gets a specific setting value.
        
        @key: Setting key to retrieve
        @return: Value of the setting
        """
        return self.data.get(key)

    def get_all(self):
        """
        Get all setting values.
        
        @return: Dictionary of all settings
        """
        return self.data.copy()

    def update(self, new_settings):
        """
        Updates multiple settings and saves them to the database.
        
        @new_settings: Dictionary with new settings to update
        """
        db = SessionLocal()
        try:
            for key, value in new_settings.items():
                if key in config.DEFAULT_SETTINGS:
                    self.data[key] = value
                    db.merge(Setting(key=key, value=str(value)))
            db.commit()
            return True
        except SQLAlchemyError as e:
            log.error(f"DB Update Error: {e}", exc_info=True)
            db.rollback()
            return False
        finally:
            db.close()

# GLOBAL INSTANCE

settings = Settings()