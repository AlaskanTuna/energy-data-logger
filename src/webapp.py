# src/webapp.py

import os

from util import list_csv_files
from logger_service import service
from config import STATIC_FILEPATH
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder=str(STATIC_FILEPATH))

# ROUTES

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.post("/api/start")
def start_logging():
    service.start()
    return {"status": "started"}

@app.post("/api/stop")
def stop_logging():
    service.stop()
    return {"status": "stopped"}

@app.get("/api/latest")
def latest():
    data = service.latest()
    return jsonify(data if data else {})

@app.get("/api/files")
def list_files():
    """
    Returns a list of aavailable CSV files in the data directory.
    """
    files = list_csv_files()
    return jsonify(files)

@app.get("/api/files/<filename>")
def get_file(filename):
    """
    Returns the specific CSV file for download.
    """
    filename = os.path.basename(filename)
    return send_from_directory(
        "../data",
        filename,
        as_attachment=True,
        download_name=filename
    )

# CONVENIENT CLI

if __name__ == "__main__":
    # cd src/ => python webapp.py
    app.run(host="0.0.0.0", port=8000, debug=True)