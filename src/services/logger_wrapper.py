# src/services/logger_wrapper.py

import os
import time
import threading
import logging

from config import config
from components import logger
from services.app_logger import log_manager
from components.database import ENGINE, SessionLocal, LoggerState, create_log_table
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# GLOBAL VARIABLES

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
        self._recovery_buffer = 20
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
            recovered_end_time = logger_state.get("endTime")
            if recovered_end_time:
                log.warning(f"Found 'RUNNING' logger state until '{recovered_end_time.isoformat()}'!")
                log.info(f"Resuming scheduled logging session in {self._recovery_buffer}s.")
            else:
                log.warning("Found 'RUNNING' logger state!")
                log.info(f"Resuming default logging session in {self._recovery_buffer}s.")

            if recovered_end_time and datetime.now() >= recovered_end_time:
                log.warning(f"Scheduled End Time has already passed at '{recovered_end_time.isoformat()}'. Stopping scheduled logging session.")
                self.stop(csv_filepath=logger_state.get("csvFile"))
            else:
                time.sleep(self._recovery_buffer)
                self.start(from_init=True, initial_state=logger_state, end_time=recovered_end_time)

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
                    "tableName": state_row.tableName,
                    "startTime": state_row.startTime,
                    "endTime": state_row.endTime,
                    "mode": state_row.mode,
                }
            return None
        except SQLAlchemyError as e:
            log.error(f"State Get Error: {e}", exc_info=True)
        finally:
            db.close()

    def _create_logger_state(self, filepath, table, end_time=None, mode=None):
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
                tableName=table,
                startTime=datetime.now(),
                endTime=end_time,
                mode=mode
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

    def _handle_logging_failure(self):
        """ 
        Handles internal logging failures.
        """
        current_state = self._get_logger_state()
        csv_to_stop = current_state.get("csvFile") if current_state else None

        log.warning("LoggerService received a failure signal from DataLogger thread.")
        self.stop(csv_filepath=csv_to_stop)

    # MAIN THREAD LOGIC

    def start(self, from_init=False, initial_state=None, end_time=None, mode=None):
        """ 
        Starts the webapp data logging process.
        
        @from_init: Flag to indicate if called from initialization
        @initial_state: Initial state dictionary from existing state
        @return: JSON object with status of the start operation
        """
        with self._lock:
            if self._logging_thread and self._logging_thread.is_alive():
                return {"status": "already_running", "state": self._get_logger_state()}

            # Determine file and table names
            if from_init and initial_state:
                csv_filepath = initial_state.get("csvFile")
                table_name = initial_state.get("tableName")
            else:
                session_name = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_filepath = os.path.join(config.DS_DIR, f"{session_name}.csv")
                table_name = session_name
            
            if not csv_filepath or not table_name:
                log.error("Could not determine filepath or table for new log session.")
                return {"status": "error", "message": "Could not determine filepath or table."}

            # Create the dynamic table before starting the logger
            if not create_log_table(table_name):
                log.error(f"Aborting logger start due to failure in creating table '{table_name}'.")
                return {"status": "error", "message": f"Failed to create database table for session."}

            session_name_for_log = os.path.splitext(os.path.basename(csv_filepath))[0]
            log_manager.start_session_logging(session_name_for_log)

            self._dl = logger.DataLogger(
                filename=csv_filepath, 
                table_name=table_name,
                end_time=end_time,
                on_failure_callback=self._handle_logging_failure
            )
            self._logging_thread = threading.Thread(
                target=self._dl.log, 
                daemon=True
            )

            if not from_init:
                self._create_logger_state(csv_filepath, table_name, end_time, mode if mode else "default")

            self._logging_thread.start()

            if end_time:
                log.info(f"Started data logging process for until '{end_time.isoformat()}'.")
            else:
                log.info(f"Started data logging process.")
            return {"status": "started", "state": self._get_logger_state()}

    def stop(self, csv_filepath=None):
        with self._lock:
            if not csv_filepath:
                logger_state = self._get_logger_state()
                if logger_state:
                    csv_filepath = logger_state.get("csvFile")

            session_name = None
            if csv_filepath:
                session_name = os.path.splitext(os.path.basename(csv_filepath))[0]

            self._clear_logger_state()

            if session_name:
                log_manager.stop_session_logging(session_name=session_name)
            else:
                log_manager.stop_session_logging()

            if not self._logging_thread or not self._logging_thread.is_alive():
                return {"status": "already_stopped"}

            log.info("Stopping active data logging thread.")

            if self._dl:
                self._dl.stop()

            self._logging_thread.join(timeout=5)
            self._logging_thread = None
            self._dl = None

            log.info("Data logging session stopped successfully.")
            return {"status": "stopped"}

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
        if self._logging_thread and self._logging_thread.is_alive():
            return True

        # Check the logger state in the database
        state = self._get_logger_state()
        return state is not None and state.get("status") == "running"

# GLOBAL INSTANCE

logger_service = LoggerService()