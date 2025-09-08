# src/services/logger_wrapper.py

import os
import time
import threading
import logging

from config import config
from config.loader import load_meter_config
from components import logger
from services.app_logger import log_manager
from components.settings import settings
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
                log.warning(f"Found 'RUNNING' logger state until '{recovered_end_time.isoformat()}' in '{logger_state.get('tableName')}'!")
                log.info(f"Resuming scheduled logging session in {self._recovery_buffer}s.")
            else:
                log.warning(f"Found 'RUNNING' logger state in '{logger_state.get('tableName')}'!")
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
            state_row = db.query(LoggerState).filter(LoggerState.status == "running").first()
            if state_row:
                return {
                    "tableName": state_row.tableName,
                    "status": state_row.status,
                    "csvFile": state_row.csvFile,
                    "startTime": state_row.startTime,
                    "endTime": state_row.endTime,
                    "mode": state_row.mode,
                    "meterModel": state_row.meterModel
                }
            return None
        except SQLAlchemyError as e:
            log.error(f"State Get Error: {e}", exc_info=True)
        finally:
            db.close()

    def _create_logger_state(self, filepath, table_name, active_model, end_time=None, mode=None):
        """ 
        Create a new logger state in the database.
        
        @filepath: Path to the CSV file being logged
        @table_name: Name of the database table being logged to
        @active_mode: The energy meter model being logged
        @end_time: The end time for the logging session if available
        @mode: The mode of the logging session
        """
        db = SessionLocal()
        try:
            new_state = LoggerState(
                tableName=table_name,
                status="running",
                csvFile=filepath,
                startTime=datetime.now(),
                endTime=end_time,
                mode=mode,
                meterModel=active_model
            )
            db.add(new_state)
            db.commit()
        except SQLAlchemyError as e:
            log.error(f"State Creation Error: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    def _update_logger_state_on_stop(self, table_name):
        """
        Updates a session's state in the historical log.

        @table_name: Name of the database table being logged to
        """
        db = SessionLocal()
        try:
            session = db.query(LoggerState).filter_by(tableName=table_name).first()
            if session:
                session.status = "stopped"
                db.commit()
                log.info(f"Stopped logger state session '{table_name}' successfully.")
        except SQLAlchemyError as e:
            log.error(f"State Update Error: {e}", exc_info=True)
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

            try:
                active_model = settings.get("ACTIVE_METER_MODEL")
                if not active_model:
                    raise ValueError("ACTIVE_METER_MODEL setting is not defined.")
                register_map = load_meter_config(active_model)
            except ValueError as e:
                log.error(f"Logger Service Error: {e}")
                return {"status": "error", "message": str(e)}

            # Determine file and table names
            if from_init and initial_state:
                csv_filepath = initial_state.get("csvFile")
                table_name = initial_state.get("tableName")
            else:
                session_name = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_filepath = os.path.join(config.DS_DIR, f"{session_name}.csv")
                table_name = session_name

            if not csv_filepath or not table_name:
                log.error("Logger Service Error: Could not determine filepath or table.")
                return {"status": "error", "message": "Could not determine filepath or table."}

            # Create the dynamic table before starting the logger
            if not create_log_table(table_name, register_map):
                log.error(f"Logger Service Error: Failure in creating table '{table_name}'.")
                return {"status": "error", "message": f"Failed to create database table for session."}

            session_name_for_log = os.path.splitext(os.path.basename(csv_filepath))[0]
            log_manager.start_session_logging(session_name_for_log)

            try:
                self._dl = logger.DataLogger(
                    filename=csv_filepath,
                    table_name=table_name,
                    register_map=register_map,
                    end_time=end_time,
                    on_failure_callback=self._handle_logging_failure
                )
            except (ConnectionError, ValueError) as e:
                log.error(f"DataLogger Initialization Error: {e}")
                log_manager.stop_session_logging(session_name=session_name_for_log)
                return {"status": "error", "message": f"Meter connection failed: {e}"}

            self._logging_thread = threading.Thread(
                target=self._dl.log, 
                daemon=True
            )

            if not from_init:
                self._create_logger_state(csv_filepath, table_name, active_model, end_time, mode if mode else "default")

            self._logging_thread.start()

            if end_time:
                log.info(f"Started scheduled data logging process for '{table_name}' until '{end_time.isoformat()}' successfully.")
            else:
                log.info(f"Started default data logging process for '{table_name}' successfully.")
            return {"status": "started", "state": self._get_logger_state()}

    def stop(self, csv_filepath=None):
        with self._lock:
            db = SessionLocal()
            running_state = db.query(LoggerState).filter_by(status="running").first()
            db.close()

            table_to_stop = None
            session_name_to_stop = None

            if running_state:
                table_to_stop = running_state.tableName
                session_name_to_stop = os.path.splitext(os.path.basename(running_state.csvFile))[0]
                self._update_logger_state_on_stop(table_to_stop)
            elif csv_filepath:
                session_name_to_stop = os.path.splitext(os.path.basename(csv_filepath))[0]

            if session_name_to_stop:
                log_manager.stop_session_logging(session_name=session_name_to_stop)
            else:
                log.warning("Stop called but no running session found to stop its log file.")

            if not self._logging_thread or not self._logging_thread.is_alive():
                if running_state:
                    log.warning(f"Thread was not running. State for '{running_state.tableName}' was running. Updating state to 'stopped'.")
                return {"status": "already_stopped"}

            if self._dl:
                self._dl.stop()

            self._logging_thread.join(timeout=5)
            self._logging_thread = None
            self._dl = None

            log.info("Stopped data logging thread successfully.")
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