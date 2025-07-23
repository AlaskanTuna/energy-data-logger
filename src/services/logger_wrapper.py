# src/services/logger_wrapper.py

import threading
import os
import logging

from components import util, logger
from services.app_logger import log_manager
from services.database import ENGINE, SessionLocal, LoggerState, archive_csv_to_db
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# CONSTANTS

log = logging.getLogger(__name__)
jobstores = {
    "default": SQLAlchemyJobStore(engine=ENGINE, tablename="scheduler_jobs")
}

# SERVICES

class LoggerService:
    """
    Wrapper around DataLogger.
    Exposes helpers for the web layer.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._logging_thread = None
        self._dl = None

        # Initialize the log scheduler
        self._scheduler = BackgroundScheduler(jobstores=jobstores)
        self._scheduler.start()
        log.info("Scheduler initialized and started successfully.")

        # Check for pre-existing state to resume logging
        logger_state = self._get_logger_state()
        if logger_state and logger_state.get("status") == "running":
            if not self._scheduler.get_jobs():
                log.info("Recovery Mode: Found 'RUNNING' state and no jobs, resuming Default Logging session.")
                self.start(from_init=True, initial_state=logger_state)
            else:
                log.info("Recovery Mode: Found 'RUNNING' state and active jobs, resuming Scheduled Logging session.")

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
            log.info("Logger state cleared successfully.")
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
        @return: JSON object with status of the start operation
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

            self._dl = logger.DataLogger(filename=csv_filepath)
            self._logging_thread = threading.Thread(target=self._dl.log, daemon=True)
            self._create_logger_state(csv_filepath)
            self._logging_thread.start()
            log.info(f"Starting data logging process for {csv_filepath}.")
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

            log.info("Data logging session stopped successfully.")
            return {"status": "stopped"}

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