# src/components/util.py

import os
import logging
import pandas as pd

from config import config

# GLOBAL VARIABLES

log = logging.getLogger(__name__)

def initialize_directories():
    """ 
    Initialize necessary directories for the logger.
    """
    dirs = [
        config.DS_DIR,
        config.PL_DIR,
        config.LOG_DIR,
        config.METERS_DIR
    ]
    cache_file = config.CUSTOMER_CACHE_FILE

    try:
        # Initialize directories
        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir, exist_ok=True)
                log.info(f"Initialized directory at '{dir}' successfully.")

        # Initialize customer cache file
        if not os.path.exists(cache_file):
            with open(cache_file, 'w') as f:
                f.write('{}')
    except Exception as e:
        log.error(f"Directory Initialization Error: {e}", exc_info=True)

def clear_screen():
    """
    Clear the terminal screen.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def list_files(file="type"):
    """ 
    List all files of a specific type.
    
    @file: Specify file type
    """
    if file == "ds":
        directory = config.DS_DIR
        extension = ".csv"
    elif file == "pl":
        directory = config.PL_DIR
        extension = ".png"
    elif file == "log":
        directory = config.LOG_DIR
        extension = ".log.gz"
    else:
        log.warning(f"Unknown file type: '{file}'.")
        return []

    try:
        files = [f for f in os.listdir(directory) if f.endswith(extension)]
        return sorted(files)
    except Exception as e:
        log.error(f"File Listing Error: {e}", exc_info=True)