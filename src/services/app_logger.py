# src/services/app_logger.py

import logging
import os
import gzip

from config import config

# CONSTANTS

log = logging.getLogger(__name__)

# SERVICES

class BufferHandler(logging.Handler):
    """ 
    Handler to buffer log records in memory.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buffer = []

    def emit(self, record):
        self.buffer.append(record)

class LogManager:
    """ 
    Manages activity logging throughout the application.
    """
    _instance = None
    _log_handler = None
    _buffer_handler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._setup_base_logger()
        return cls._instance

    def _setup_base_logger(self):
        """ 
        Sets up the base logger for the application.
        """
        if not os.path.exists(config.LOG_DIR):
            os.makedirs(config.LOG_DIR)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO) # Log verbosity level

        if any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
            return

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # CONSOLE HANDLER

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # BUFFER HANDLER

        self._buffer_handler = BufferHandler()
        root_logger.addHandler(self._buffer_handler)
        log.info("Application logger initialized and started successfully.")

    def start_session_logging(self, filename):
        """
        Starts logging to a specific file for a data logging session.
        
        @filename: Name of the log file
        """
        if self._log_handler:
            log.warning("A session log handler is already active.")
            self.stop_session_logging()

        log_filepath = os.path.join(config.LOG_DIR, f"{filename}.log")
        log.info(f"Starting log session for: '{log_filepath}'.")

        try:
            os.makedirs(config.LOG_DIR, exist_ok=True)
        except OSError as e:
            log.error(f"Log Handler Error: Could not create log directory '{config.LOG_DIR}': {e}")
            return

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # FILE HANDLER

        file_handler = logging.FileHandler(log_filepath, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)

        if self._buffer_handler:
            for record in self._buffer_handler.buffer: # Flush buffer into file handler
                file_handler.handle(record)

            logging.getLogger().removeHandler(self._buffer_handler) # Clear the buffer after flushing
            self._buffer_handler = None

        # Add the handler to the root logger
        logging.getLogger().addHandler(file_handler)
        self._log_handler = file_handler

    def stop_session_logging(self, compress=True, session_name=None):
        """
        Stops logging to the session file ands compresses it.
        
        @compress: Flag to compress log file after session ends
        @session_name: Filename of the session for compression target
        """
        log_filepath = None
        
        if self._log_handler:
            log_filepath = self._log_handler.baseFilename
            logging.getLogger().removeHandler(self._log_handler)
            self._log_handler.close()
            self._log_handler = None
            log.info(f"Closed active log handler for '{log_filepath}'.")
        elif session_name:
            log_filepath = os.path.join(config.LOG_DIR, f"{session_name}.log")
            log.info(f"Stopping session log for '{log_filepath}' via recovery.")
        else:
            log.info("No active session or session name provided to stop.")
            return

        if not self._buffer_handler:
            self._buffer_handler = BufferHandler()
            logging.getLogger().addHandler(self._buffer_handler)

        if compress and log_filepath and os.path.exists(log_filepath):
            try:
                with open(log_filepath, 'rb') as f_in:
                    with gzip.open(f"{log_filepath}.gz", 'wb') as f_out:
                        f_out.writelines(f_in)
                os.remove(log_filepath)
                log.info(f"Successfully compressed log file to '{log_filepath}.gz'.")
            except Exception as e:
                log.error(f"Failed to compress log file '{log_filepath}': {e}", exc_info=True)

# GLOBAL INSTANCE

log_manager = LogManager()