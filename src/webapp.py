# src/webapp.py

# NOTE: Make sure `DEVELOPER_MODE` and `USE_MODBUS` are set to False and True respectively
#       in src/settings.py file. Then run this script from the CLI: `python src/webapp.py`.
#       This is the main application for the data logger.

import os

from flask import Flask, request, jsonify, send_from_directory
from components.util import list_csv_files
from services.logger_wrapper import logger_service
from services.analyzer_wrapper import analyzer_service
from services.settings import settings
from config import config

# CONSTANTS

app = Flask(__name__, static_folder=str(config.STATIC_DIR))

# GET ROUTES

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/api/latest")
def latest():
    data = logger_service.latest()
    return jsonify(data if data else {})

@app.get("/api/status")
def get_logger_status():
    return jsonify(logger_service.get_status())

@app.get("/api/settings")
def get_settings():
    return jsonify(settings.get_all())

@app.get("/api/files")
def list_files():
    files = list_csv_files()
    return jsonify(files)

@app.get("/api/files/<filename>")
def get_file(filename):
    filename = os.path.basename(filename)
    return send_from_directory(
        "../data",
        filename,
        as_attachment=True,
        download_name=filename
    )

@app.get("/api/analyze/<filename>")
def analyze_file(filename):
    result = analyzer_service.analyze_file(filename)
    return jsonify(result if result else {"error": "Analysis failed"})

@app.get("/api/visualization-types")
def get_visualization_types():
    viz_types = []
    for key, config in analyzer_service.VISUALIZATION_TYPES.items():
        viz_types.append({
            "id": key,
            "name": config['name'],
        })
    return jsonify(viz_types)

@app.get("/api/columns/<filename>")
def get_columns(filename):
    result = analyzer_service.get_columns(filename)
    return jsonify(result)

@app.get("/api/visualize/<filename>/<plot_type>")
def generate_visualization(filename, plot_type):
    result = analyzer_service.visualize_file(filename, plot_type)
    return jsonify(result)

@app.get("/plots/<path:filename>")
def serve_plot(filename):
    return send_from_directory(
        "../plots", 
        filename,
        as_attachment=True
    )

# POST ROUTES

@app.post("/api/start")
def start_logging():
    result = logger_service.start()
    return jsonify(result)

@app.post("/api/stop")
def stop_logging():
    result = logger_service.stop()
    return jsonify(result)

@app.post("/api/settings")
def save_settings():
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
    data = request.get_json()
    if not data or 'columns' not in data:
        return jsonify({"error": "No columns specified"}), 400

    result = analyzer_service.visualize_file(filename, "custom", data['columns'])
    return jsonify(result)

# RUN FLASK APP

if __name__ == "__main__":
    # cd src/ => python webapp.py
    app.run(host="0.0.0.0", port=8000, debug=True)