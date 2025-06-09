# src/logger_service.py

import threading
from logger import DataLogger

class LoggerService:
    """
    Thin wrapper that runs DataLogger in its own thread and
    exposes start/stop/latest helpers for the web layer.
    """
    def __init__(self):
        self._dl = DataLogger()
        self._thread = None

    # INTERNAL WORKER

    def _bg_loop(self):
        self._dl.log()

    # PUBLIC API

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._bg_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._dl.stop()
        if self._thread:
            self._thread.join()

    def latest(self):
        """
        Returns {'ts': datetime, <all meter fields>} or None.
        """
        return self._dl.latest

# Global instance for the web layer
service = LoggerService()