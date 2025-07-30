# src/services/schedule_runner.py

import logging

# CONSTANTS

log = logging.getLogger(__name__)

# SERVICES

def start_logging_job(end_time=None, schedule_mode=None, **kwargs):
    """ 
    Wrapper function to start the logging job from the scheduler.
    """
    from services.logger_wrapper import logger_service

    log.info(f"APScheduler: Starting scheduled job on '{schedule_mode}' mode.")
    if schedule_mode == 'recurring':
        log.info("APScheduler: Detected 'recurring' mode. Calculating next stop time.")
        scheduler = logger_service._scheduler
        try:
            stop_job = scheduler.get_job('stop_job')
            if stop_job:
                end_time = stop_job.next_run_time
            else:
                log.warning("APScheduler: Recurring job started but no corresponding stop_job found. Running indefinitely.")
                end_time = None
        except Exception as e:
            log.error(f"APScheduler Error: Failed to get recurring stop_job's next run time: {e}", exc_info=True)
            end_time = None

    log.info(f"APScheduler: Passing control to LoggerService with End Time at '{end_time}'.")
    return logger_service.start(end_time=end_time)

def stop_logging_job(**kwargs):
    """ 
    Wrapper function to stop the logging job from the scheduler.
    """
    from services.logger_wrapper import logger_service

    if logger_service.is_running():
        log.info(f"APScheduler: Stopping scheduled job.")
        return logger_service.stop()
    return {"status": "not_running"}
