# src/logger_wrapper.py

import threading
import os
import json
import time
from datetime import datetime
from logger import DataLogger
from util import get_current_filename

# CONSTANTS

STATE_FILE = "../data/logger.state"

class LoggerService:
    """
    A self-monitoring wrapper around DataLogger.
    It uses a main logging thread and a separate monitor thread to ensure
    the system state is always synchronized with reality.
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
            print("[INFO]: Resuming 'running' state. Continuing logging thread from initialization.")
            self.start(from_init=True, initial_state=state)

    # STATE MANAGEMENT

    def _read_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
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
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=4)
        except IOError:
            print(f"[ERROR]: Could not write to state file.")

    def _clear_state(self):
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            print("[INFO]: State file cleared.")

    # MAIN THREAD LOGIC

    def start(self, from_init=False, initial_state=None):
        with self._lock:
            if self._logging_thread and self._logging_thread.is_alive():
                return {"status": "already_running", "state": self._read_state()}

            if from_init:
                csv_filepath = initial_state.get("csvFile")
            else:
                csv_filepath = get_current_filename("ds")
            
            if not csv_filepath:
                return {"status": "error", "message": "Could not determine CSV file path."}

            print(f"[INFO] Starting logging process for {csv_filepath}")

            self._dl = DataLogger(filename=csv_filepath)
            self._logging_thread = threading.Thread(target=self._dl.log, daemon=True)
            self._write_state(csv_filepath)
            self._logging_thread.start()
            return {"status": "started", "state": self._read_state()}

    def stop(self):
        with self._lock:
            self._clear_state()

            if not self._logging_thread or not self._logging_thread.is_alive():
                return {"status": "already_stopped"}

            print("[INFO]: Stopping logging process.")

            if self._dl:
                self._dl.stop()

            self._logging_thread.join(timeout=5)
            self._logging_thread = None
            self._dl = None

            print("[INFO]: Logging process stopped cleanly.")
            return {"status": "stopped"}

    # MONITOR THREAD LOGIC

    def start_monitor(self):
        """
        Starts a thread that monitors the logger.
        """
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        print("[INFO]: Heartbeat monitor started.")

    def _monitor_loop(self):
        """
        Main loop of the monitor thread.
        """
        while not self._stop_monitor.is_set():
            time.sleep(5)
            state_exists = os.path.exists(STATE_FILE)
            if state_exists and self._logging_thread and not self._logging_thread.is_alive():
                with self._lock:
                    if self._logging_thread and not self._logging_thread.is_alive():
                        # TODO: Log last 200 lines of Flask debug lines
                        print("[INFO]: Detected crashed logging thread. Terminating logger session and state.")
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