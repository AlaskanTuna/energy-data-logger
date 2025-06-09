# src/webapp.py

from flask import Flask, jsonify, send_from_directory
from logger_service import service
from config import STATIC_FILEPATH

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

# CONVENIENT CLI

if __name__ == "__main__":
    # cd src/ => python webapp.py
    app.run(host="192.168.69.1", port=8000, debug=True)