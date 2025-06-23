# src/services/logger_wrapper.py

import threading
import os
import json
import time
import logging

from components import util, logger
from config import config
from services.app_logger import log_manager
from datetime import datetime

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
        state = self._read_state()
        if state and state.get("status") == "running":
            log.info("Resuming RUNNING state. Continuing data logging thread.")
            self.start(from_init=True, initial_state=state)

    # STATE MANAGEMENT

    def _read_state(self):
        if os.path.exists(config.STATE_FILE):
            try:
                with open(config.STATE_FILE, 'r') as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError): return None
        return None

    def _write_state(self, csv_filepath):
        state = {
            "status": "running",
            "startTime": datetime.now().isoformat(),
            "csvFile": csv_filepath
        }
        try:
            with open(config.STATE_FILE, 'w') as f:
                json.dump(state, f, indent=4)
        except IOError:
            log.error(f"Could not write to state file.")

    def _clear_state(self):
        if os.path.exists(config.STATE_FILE):
            os.remove(config.STATE_FILE)
            log.info("State file cleared.")

    # MAIN THREAD LOGIC

    def start(self, from_init=False, initial_state=None):
        with self._lock:
            if self._logging_thread and self._logging_thread.is_alive():
                return {"status": "already_running", "state": self._read_state()}

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
            self._write_state(csv_filepath)
            self._logging_thread.start()
            return {"status": "started", "state": self._read_state()}

    def stop(self):
        with self._lock:
            self._clear_state()

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
                        self._clear_state()
                        self._logging_thread = None
                        self._dl = None

    # PUBLIC API

    def get_status(self):
        """ 
        Returns the current status of the logger.
        """
        state = self._read_state()
        return state if state else {"status": "inactive"}

    def latest(self):
        """ 
        Returns the latest logged data.
        """
        if self._dl:
            return self._dl.latest
        return None

    def is_running(self):
        """
        Checks if the logger should be running based on the state file.
        """
        state = self._read_state()
        return state is not None and state.get("status") == "running"

# GLOBAL INSTANCE

logger_service = LoggerService()