# src/services/schedule_runner.py

import logging

# CONSTANTS

log = logging.getLogger(__name__)

# SERVICES

def start_logging_job(**kwargs):
    from services.logger_wrapper import logger_service

    return logger_service.start()

def stop_logging_job(**kwargs):
    from services.logger_wrapper import logger_service

    if logger_service.is_running():
        return logger_service.stop()
    return {"status": "not_running"}
