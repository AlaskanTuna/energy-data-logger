# src/webapp.py

# NOTE: Make sure `DEVELOPER_MODE` and `USE_MODBUS` are set to False and True respectively
#       in src/settings.py file. Then run this script from the CLI: `python src/webapp.py`.
#       This is the main application for the data logger.

import os
import logging
import datetime
import atexit

from flask import Flask, request, jsonify, send_from_directory
from config import config
from services.database import init_db; init_db()
from components.util import list_files
from services.settings import settings
from services.logger_wrapper import logger_service
from services.analyzer_wrapper import analyzer_service
from services.analyzer_wrapper import VISUALIZATION_TYPES
from services.remote_syncer import remote_syncer_service
from datetime import datetime, time, timedelta

# GLOBAL VARIABLES

app = Flask(__name__, static_folder=str(config.STATIC_DIR))
log = logging.getLogger(__name__)

# REMOTE DB SYNCER SERVICE

if config.REMOTE_DB_ENABLED:
    log.info(f"Remote DB is enabled. Sync service will run every {config.SYNC_INTERVAL}s.")
    remote_syncer_service.start()
    atexit.register(remote_syncer_service.stop)
else:
    log.info("Remote DB is disabled. Sync service will not run.")

# HELPER FUNCTIONS

def start_logging_job(**kwargs):
    return logger_service.start()

def stop_logging_job(**kwargs):
    if logger_service.is_running():
        return logger_service.stop()
    return {"status": "not_running"}

# FLASK GET ROUTES

@app.get("/")
def index():
    """ 
    Get the main index page of the web application.
    
    @return: HTML content of the index page
    """
    return send_from_directory(app.static_folder, "index.html")

@app.get("/api/latest")
def latest():
    """ 
    Get the latest logged data.
    
    @return: JSON object with latest data or empty if no data
    """
    data = logger_service.latest()
    return jsonify(data if data else {})

@app.get("/api/status")
def get_logger_status():
    """ 
    Get the current status of the logger service.
    
    @return: JSON object with logger status
    """
    return get_scheduler_status()

@app.get("/api/schedules/status")
def get_scheduler_status():
    """ 
    Gets the current status of the scheduler service.
    
    @return: JSON object with scheduler status
    """
    # Indicators
    logger_state = logger_service.get_status()
    jobs = logger_service._scheduler.get_jobs()
    latest_data = logger_service.latest()
    sync_status = remote_syncer_service._get_status()
    internet_connected = remote_syncer_service._check_internet()

    response = {
        "mode": "none",
        "status": "idle",
        "activeCSVFile": logger_state.get("csvFile"),
        "lastUpdated": latest_data.get("ts").isoformat() if latest_data and latest_data.get("ts") else None,
        "liveMetricsEnabled": settings.get("LIVE_METRICS"),
        "syncStatus": sync_status,
        "internetStatus": internet_connected,
    }

    if logger_state.get("status") == "running":
        response["status"] = "logging"
        response["mode"] = logger_state.get("mode", "default")
    else:
        start_job = next((j for j in jobs if j.id == "start_job"), None)
        if start_job:
            response["status"] = "scheduled"
            response["mode"] = start_job.kwargs.get('schedule_mode', 'none')
    return jsonify(response)

@app.get("/api/settings")
def get_settings():
    """ 
    Get the current application settings.
    
    @return: JSON object with all settings
    """
    return jsonify(settings.get_all())

@app.get("/api/files")
def list_data_files():
    """
    Get a list of data files.
    
    @return: JSON list of data file names
    """
    files = list_files("ds")
    return jsonify(files)

@app.get("/api/files/<filename>")
def get_data_file(filename):
    """ 
    Get the specified CSV file for download.
    
    @filename: Name of the file to download
    @return: File download response
    """
    filename = os.path.basename(filename)
    return send_from_directory(
        config.DS_DIR,
        filename,
        as_attachment=True,
        download_name=filename
    )

@app.get("/api/logs")
def list_log_files():
    """ 
    Get a list of log files.
    
    @return: JSON list of log file names
    """
    files = list_files("log")
    return jsonify(files)

@app.get("/api/logs/<filename>")
def get_log_file(filename):
    """ 
    Get the specified CSV file for download.
    
    @filename: Name of the file to download
    @return: File download response
    """
    filename = os.path.basename(filename)
    return send_from_directory(
        config.LOG_DIR,
        filename,
        as_attachment=True,
        download_name=filename
    )

@app.get("/api/visualization-types")
def get_visualization_types():
    """ 
    Get the list of available visualization types.
    
    @return: JSON list of visualization types with IDs and names
    """
    viz_types = []
    for key, config in VISUALIZATION_TYPES.items():
        viz_types.append({
            "id": key,
            "name": config['name'],
        })
    return jsonify(viz_types)

@app.get("/api/columns/<filename>")
def get_columns(filename):
    """ 
    Get available columns for custom visualization from a file.
    
    @filename: Name of the file to analyze
    @return: JSON object with filename and list of columns
    """
    result = analyzer_service.get_columns(filename)
    return jsonify(result)

@app.get("/api/columns/all")
def get_all_columns():
    """
    Get all available columns for logging.
    
    @return: JSON list of all available parameters
    """
    all_params = [
        {"name": name, "description": params["description"]}
        for name, params in config.REGISTERS.items()
    ]
    return jsonify({"columns": all_params})

@app.get("/api/visualize/<filename>/<plot_type>")
def generate_visualization(filename, plot_type):
    """ 
    Get a visualization for a specified file and plot type.
    
    @filename: Name of the file to visualize
    @plot_type: Type of visualization to generate
    @return: JSON object with paths to generated plots
    """
    result = analyzer_service.visualize_file(filename, plot_type)
    return jsonify(result)

@app.get("/plots/<path:filename>")
def serve_plot(filename):
    """ 
    Get a generated plot file for download.
    
    @filename: Name of the plot file to download
    @return: File download response
    """
    return send_from_directory(
        "../plots", 
        filename,
        as_attachment=True
    )

# FLASK POST ROUTES

@app.post("/api/schedules/set")
def set_schedule():
    """ 
    Sets the logging action based on the provided mode.
    
    @return: JSON object with status of the start operation
    """
    from services.schedule_runner import start_logging_job, stop_logging_job

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    mode = data.get("mode")
    logger_service._scheduler.remove_all_jobs()

    if mode == "default":
        result = logger_service.start() 
        return jsonify(result)

    try:
        if mode == "once":
            start_t_str = data.get("start_time")
            end_t_str = data.get("end_time")

            if not start_t_str:
                return jsonify({"error": "Start time is required for Scheduled Logging."}), 400

            start_t = time.fromisoformat(start_t_str)
            now = datetime.now()
            start_dt = now.replace(hour=start_t.hour, minute=start_t.minute, second=start_t.second, microsecond=0)
            if start_dt < now:
                start_dt += timedelta(days=1)

            if not end_t_str:
                end_dt = datetime(2099, 12, 31, 23, 59, 59)
            else:
                end_t = time.fromisoformat(end_t_str)
                end_dt = now.replace(hour=end_t.hour, minute=end_t.minute, second=end_t.second, microsecond=0)
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)

            logger_service._scheduler.add_job(
                start_logging_job, 
                "date", 
                run_date=start_dt, 
                id="start_job", 
                kwargs={'end_time': end_dt, 'schedule_mode': 'once'}
            )
            logger_service._scheduler.add_job(
                stop_logging_job, 
                "date", 
                run_date=end_dt, 
                id="stop_job", 
                kwargs={'schedule_mode': 'once'}
            )
            return jsonify({"status": "scheduled", "mode": "once"})

        elif mode == "recurring":
            start_t_str = data.get("start_time")
            end_t_str = data.get("end_time")

            if not start_t_str or not end_t_str:
                return jsonify({"error": "Both start and end times are required for recurring schedules."}), 400

            start_t = time.fromisoformat(start_t_str)
            end_t = time.fromisoformat(end_t_str)
            day_interval = int(data.get("day_interval", 0))

            if day_interval > 0:
                start_dt = datetime.now().replace(hour=start_t.hour, minute=start_t.minute, second=0, microsecond=0)
                if start_dt < datetime.now():
                    start_dt += timedelta(days=1)

                logger_service._scheduler.add_job(
                    start_logging_job, 
                    "interval", 
                    days=day_interval,
                    start_date=start_dt,
                    id="start_job", 
                    kwargs={'schedule_mode': 'recurring'}
                )

                end_dt = datetime.now().replace(hour=end_t.hour, minute=end_t.minute, second=end_t.second, microsecond=0)
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)

                logger_service._scheduler.add_job(
                    stop_logging_job, 
                    "interval", 
                    days=day_interval,
                    start_date=end_dt,
                    id="stop_job", 
                    kwargs={'schedule_mode': 'recurring'}
                )
            else:
                logger_service._scheduler.add_job(
                    start_logging_job, 
                    "cron", 
                    hour=start_t.hour, 
                    minute=start_t.minute,
                    second=start_t.second,
                    id="start_job", 
                    kwargs={'schedule_mode': 'recurring'}
                )
                logger_service._scheduler.add_job(
                    stop_logging_job, 
                    "cron", 
                    hour=end_t.hour, 
                    minute=end_t.minute,
                    second=end_t.second,
                    id="stop_job", 
                    kwargs={'schedule_mode': 'recurring'}
                )
            return jsonify({"status": "scheduled", "mode": "recurring"})
        else:
            return jsonify({"error": "Invalid mode specified."}), 400
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid time format: {e}"}), 400

@app.post("/api/schedules/clear")
def clear_schedule():
    """ 
    Stops the logger and clears all scheduled jobs.
    """
    logger_service.stop()
    logger_service._scheduler.remove_all_jobs()
    return jsonify({"status": "cleared"})

@app.post("/api/analyze/<filename>")
def analyze_file(filename):
    """ 
    Get the analysis results for a specified CSV file.
    
    @filename: Name of the file to analyze
    @return: JSON object with analysis results
    """
    data = request.get_json() or {}
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    result = analyzer_service.analyze_file(filename, start_time, end_time)
    return jsonify(result if result else {"error": "Analysis failed"})

@app.post("/api/settings")
def save_settings():
    """ 
    Post request to update and save application settings.
    
    @return: JSON object with status of the settings update
    """
    new_settings = request.get_json()
    if not new_settings:
        return jsonify({"error": "Invalid data"}), 400

    # Stop logger
    is_param_update_only = list(new_settings.keys()) == ["ACTIVE_LOG_PARAMETERS"]
    if not is_param_update_only and logger_service.is_running():
        logger_service.stop()

    # Update and save new settings.
    if settings.update(new_settings):
        return jsonify({"status": "success", "settings": settings.get_all()})
    else:
        return jsonify({"error": "Failed to save settings"}), 500

@app.post("/api/visualize/custom/<filename>")
def generate_custom_visualization(filename):
    """ 
    Post request to generate a custom visualization for a file.
    
    @filename: Name of the file to visualize
    @return: JSON object with paths to generated plotss
    """
    data = request.get_json()
    if not data or "columns" not in data:
        return jsonify({"error": "No columns specified"}), 400

    result = analyzer_service.visualize_file(filename, "custom", data['columns'])
    return jsonify(result)

# RUN FLASK

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)