# src/webapp.py

# NOTE: Make sure `DEVELOPER_MODE` and `USE_MODBUS` are set to False and True respectively
#       in src/settings.py file. Then run this script from the CLI: `python src/webapp.py`.
#       This is the main application for the data logger.

import os

from flask import Flask, request, jsonify, send_from_directory
from components.util import list_files
from services.logger_wrapper import logger_service
from services.analyzer_wrapper import analyzer_service
from services.analyzer_wrapper import VISUALIZATION_TYPES
from services.settings import settings
from config import config

# CONSTANTS

app = Flask(__name__, static_folder=str(config.STATIC_DIR))

# GET ROUTES

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
    return jsonify(logger_service.get_status())

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

@app.get("/api/analyze/<filename>")
def analyze_file(filename):
    """ 
    Get the analysis results for a specified CSV file.
    
    @filename: Name of the file to analyze
    @return: JSON object with analysis results
    """
    result = analyzer_service.analyze_file(filename)
    return jsonify(result if result else {"error": "Analysis failed"})

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

# POST ROUTES

@app.post("/api/start")
def start_logging():
    """ 
    Post request to start the data logging service.
    
    @return: JSON object with status of the logging service
    """
    result = logger_service.start()
    return jsonify(result)

@app.post("/api/stop")
def stop_logging():
    """ 
    Post request to stop the data logging service.
    
    @return: JSON object with status of the logging service
    """
    result = logger_service.stop()
    return jsonify(result)

@app.post("/api/settings")
def save_settings():
    """ 
    Post request to update and save application settings.
    
    @return: JSON object with status of the settings update
    """
    new_settings = request.get_json()
    if not new_settings:
        return jsonify({"error": "Invalid data"}), 400

    # Stop logger before new settings
    if logger_service.is_running():
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
    if not data or 'columns' not in data:
        return jsonify({"error": "No columns specified"}), 400

    result = analyzer_service.visualize_file(filename, "custom", data['columns'])
    return jsonify(result)

# RUN FLASK APP

if __name__ == "__main__":
    # cd src/ => python webapp.py
    app.run(host="0.0.0.0", port=8000, debug=True)