# src/logger_wrapper.py

import threading
import os
import json
from datetime import datetime
from logger import DataLogger
from util import get_current_filename

STATE_FILE = "../data/logger.state"

class LoggerService:
    """
    Wrapper around DataLogger.
    Manages persistent logging via a state file to support long unattended logging sessions.
    """
    def __init__(self):
        self._dl = None
        self._thread = None
        self._state = self._read_state()

        # Auto-start logging if the state file indicates it should be running
        if self.is_running():
            print("[INFO]: Logger state is 'running'. Auto-starting logging thread from initialization.")
            self.start(from_init=True)

    def _read_state(self):
        """
        Safely reads and decodes the state file if it exists.
        """
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                print(f"[ERROR]: Could not read or decode state file: {e}. Clearing.")
                self._clear_state()
                return None
        return None

    def _write_state(self, data):
        """
        Writes the current state to the state file.
        """
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError:
            print(f"[ERROR]: Could not write to state file: {STATE_FILE}")

    def _clear_state(self):
        """
        Removes the state file.
        """
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

    def _bg_loop(self, filename):
        """
        The background worker thread target.
        """
        if not self._dl:
            self._dl = DataLogger(filename=filename)
        self._dl.log()

    # PUBLIC API

    def start(self, from_init=False):
        """
        Starts a logging session. If not from_init, it's a new session.
        """
        if self._thread and self._thread.is_alive():
            return {"status": "already_running", "state": self._state}

        # New session initialization
        if not from_init:
            csv_filepath = get_current_filename("ds")
            self._state = {
                "status": "running",
                "startTime": datetime.now().isoformat(),
                "csvFile": csv_filepath
            }
            self._write_state(self._state)
            print(f"[INFO]: New logging session started. State file created.")

        # Use filename from the state object.
        target_filename = self._state.get("csvFile")
        if not target_filename:
            print("[ERROR] Cannot start logger: no CSV filename in state.")
            self._clear_state()
            return {"status": "error", "message": "State file was corrupt or missing."}

        self._thread = threading.Thread(target=self._bg_loop, args=(target_filename,), daemon=True)
        self._thread.start()
        return {"status": "started", "state": self._state}

    def stop(self):
        """
        Stops the current logging session and cleans up.
        """
        if self._dl:
            self._dl.stop()  # Sets the internal _running flag to False
        
        if self._thread:
            self._thread.join(timeout=5)  # Wait for the thread to finish cleanly
        
        self._clear_state()
        self._state = None
        self._thread = None
        self._dl = None
        print("[INFO] Logging session stopped. State file cleared.")
        return {"status": "stopped"}

    def latest(self):
        """
        Returns the most recent reading.
        """
        return self._dl.latest if self._dl else None
    
    def get_status(self):
        """
        Returns the current state of the logger for the UI.
        """
        return self._state if self.is_running() else {"status": "inactive"}

    def is_running(self):
        """
        Checks if the logger should be running based on the state.
        """
        return self._state is not None and self._state.get("status") == "running"

# Global instance for the web layer.
logger_service = LoggerService()