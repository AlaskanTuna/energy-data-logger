# src/logger_wrapper.py

import threading
from logger import DataLogger

class LoggerService:
    """
    Wrapper around DataLogger.
    Exposes start/stop/latest helpers for the web layer.
    """
    def __init__(self):
        self._dl = None
        self._thread = None
        self._latest_data = None

    # INTERNAL WORKER

    def _bg_loop(self):
        if not self._dl:
            self._dl = DataLogger()
        self._dl.log()

    # PUBLIC API

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        # Reset any previous instance
        if self._dl:
            del self._dl
            self._dl = None

        self._thread = threading.Thread(target=self._bg_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        if self._dl:
            self._dl.stop()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        return True

    def latest(self):
        """
        Returns {'ts': datetime, <all meter fields>} or None.
        """
        return self._dl.latest if self._dl else None

# Global instance for the web layer
logger_service = LoggerService()