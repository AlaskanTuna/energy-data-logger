# src/components/util.py

import os
import logging
import pandas as pd

from config import config

# GLOBAL VARIABLES

log = logging.getLogger(__name__)

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
        if not os.path.exists(directory):
            os.makedirs(directory)
            return []

        files = [f for f in os.listdir(directory) if f.endswith(extension)]
        return sorted(files)
    except Exception as e:
        log.error(f"File Listing Error: {e}", exc_info=True)