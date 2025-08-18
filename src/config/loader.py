# src/config/loader.py

import json
import logging

from config import config

# GLOBAL VARIABLES

log = logging.getLogger(__name__)

def load_meter_config(model_name: str):
    """
    Loads the register map for a given meter model from a JSON file.
    
    @model_name: The name of the meter model to load
    """
    try:
        file_path = config.ROOT / "src" / "config" / "meters" / f"{model_name}.json"
        with open(file_path, 'r') as f:
            register_map = json.load(f)

        log.info(f"Meter configuration file loaded from '{file_path}' successfully.")
        return register_map
    except FileNotFoundError:
        log.error(f"Load Meter Error: Configuration file not found at '{file_path}'.")
        raise ValueError(f"Could not find configuration for meter model '{model_name}'.")
    except json.JSONDecodeError as e:
        log.error(f"Load Meter Error: Failed to parse JSON from '{file_path}': {e}", exc_info=True)
        raise ValueError(f"Configuration file for '{model_name}' is not a valid JSON.")
    except Exception as e:
        log.error(f"Load Meter Error: An unexpected error occurred while loading meter config '{model_name}': {e}", exc_info=True)
        raise ValueError(f"Could not load configuration for '{model_name}'.")