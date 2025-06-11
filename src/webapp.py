# src/webapp.py

import os

from util import list_csv_files
from logger_wrapper import logger_service
from analyzer_wrapper import analyzer_service
from config import STATIC_FILEPATH
from flask import Flask, jsonify, send_from_directory

# INITIALIZE FLASK

app = Flask(__name__, static_folder=str(STATIC_FILEPATH))

# GET ROUTES
@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/api/latest")
def latest():
    data = logger_service.latest()
    return jsonify(data if data else {})

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

# POST ROUTES

@app.post("/api/start")
def start_logging():
    logger_service.start()
    return {"status": "started"}

@app.post("/api/stop")
def stop_logging():
    logger_service.stop()
    return {"status": "stopped"}

# CONVENIENT CLI

if __name__ == "__main__":
    # cd src/ => python webapp.py
    app.run(host="0.0.0.0", port=8000, debug=True)