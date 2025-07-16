# src/services/logger_wrapper.py

import threading
import os
import time
import logging

from components import util, logger
from config import config
from services.app_logger import log_manager
from services.database import SessionLocal, LoggerState, archive_csv_to_db
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

# CONSTANTS

log = logging.getLogger(__name__)

# SERVICES

class LoggerService:
    """
    Wrapper around DataLogger.
    Exposes helpers for the web layer.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._logging_thread = None
        self._monitor_thread = None
        self._dl = None
        self._stop_monitor = threading.Event()
        self.start_monitor()

        # Check for pre-existing state to resume logging
        logger_state = self._get_logger_state()
        if logger_state and logger_state.get("status") == "running":
            log.info("Resuming RUNNING state. Continuing data logging session.")
            self.start(from_init=True, initial_state=logger_state)

    # STATE MANAGEMENT

    def _get_logger_state(self):
        """ 
        Get the current logger state from the database.
        """
        db = SessionLocal()
        try:
            state_row = db.query(LoggerState).filter(LoggerState.id == 1).first()
            if state_row:
                return {
                    "status": state_row.status,
                    "csvFile": state_row.csvFile,
                    "startTime": state_row.startTime.isoformat()
                }
            return None
        except SQLAlchemyError as e:
            log.error(f"State Get Error: {e}", exc_info=True)
        finally:
            db.close()

    def _create_logger_state(self, filepath):
        """ 
        Create a new logger state in the database.
        
        @filepath: Path to the CSV file being logged
        """
        db = SessionLocal()
        try:
            # Clear old state first
            db.query(LoggerState).delete()
            new_state = LoggerState(
                id=1,
                status="running",
                csvFile=filepath,
                startTime=datetime.now()
            )
            db.add(new_state)
            db.commit()
        except SQLAlchemyError as e:
            log.error(f"State Creation Error: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    def _clear_logger_state(self):
        """ 
        Clear the logger state from the database.
        """
        db = SessionLocal()
        try:
            db.query(LoggerState).delete()
            db.commit()
            log.info("Logger state cleared.")
        except SQLAlchemyError as e:
            log.error(f"State Clear Error: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    # MAIN THREAD LOGIC

    def start(self, from_init=False, initial_state=None):
        """ 
        Starts the webapp data logging process.
        
        @from_init: Flag to indicate if called from initialization
        @initial_state: Initial state dictionary from existing state
        @return: Dictionary with status and state information
        """
        with self._lock:
            if self._logging_thread and self._logging_thread.is_alive():
                return {"status": "already_running", "state": self._get_logger_state()}

            if from_init:
                csv_filepath = initial_state.get("csvFile")
            else:
                csv_filepath = util.get_current_filename("ds")
            
            if not csv_filepath:
                log.error("Could not determine CSV file path for new session.")
                return {"status": "error", "message": "Could not determine CSV file path."}

            session_name = os.path.splitext(os.path.basename(csv_filepath))[0]
            log_manager.start_session_logging(session_name)

            log.info(f"Starting data logging process for {csv_filepath}")
            self._dl = logger.DataLogger(filename=csv_filepath)
            self._logging_thread = threading.Thread(target=self._dl.log, daemon=True)
            self._create_logger_state(csv_filepath)
            self._logging_thread.start()
            return {"status": "started", "state": self._get_logger_state()}

    def stop(self):
        """ 
        Stops the webapp data logging process.
        
        @return: Dictionary with status of the stop operation
        """
        with self._lock:
            logger_state = self._get_logger_state()
            if logger_state:
                csv_filepath = logger_state.get("csvFile")
            else:
                csv_filepath = None

            self._clear_logger_state()

            if not self._logging_thread or not self._logging_thread.is_alive():
                log_manager.stop_session_logging()
                return {"status": "already_stopped"}

            log.info("Stopping data logging process.")
            log_manager.stop_session_logging()

            if self._dl:
                self._dl.stop()

            self._logging_thread.join(timeout=5)
            self._logging_thread = None
            self._dl = None

            # Insert CSV data into the database
            if csv_filepath:
                archive_csv_to_db(csv_filepath)

            log.info("Data logging process stopped cleanly.")
            return {"status": "stopped"}

    # MONITOR THREAD LOGIC

    def start_monitor(self):
        """
        Starts a thread that monitors the logger.
        """
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        log.info("Heartbeat monitor started.")

    def _monitor_loop(self):
        """
        Main loop of the monitor thread.
        """
        while not self._stop_monitor.is_set():
            time.sleep(5)
            state_exists = os.path.exists(config.STATE_FILE)
            if state_exists and self._logging_thread and not self._logging_thread.is_alive():
                with self._lock:
                    if self._logging_thread and not self._logging_thread.is_alive():
                        log.info("Detected crashed data logging thread. Terminating session and state.")
                        self._clear_logger_state()
                        self._logging_thread = None
                        self._dl = None

    # PUBLIC API

    def get_status(self):
        """ 
        Get the current status of the logger.
        
        @return: Dictionary with status information
        """
        state = self._get_logger_state()
        return state if state else {"status": "inactive"}

    def latest(self):
        """ 
        Get the latest logged data.
        
        @return: Latest data dictionary or None
        """
        if self._dl:
            return self._dl.latest
        return None

    def is_running(self):
        """
        Check if the logger is currently running.
        
        @return: Boolean flag indicating if logger is running
        """
        state = self._get_logger_state()
        return state is not None and state.get("status") == "running"

# GLOBAL INSTANCE

logger_service = LoggerService()