# src/config/config.py

import os

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# MODBUS SETTINGS

MODBUS_PORT = "/dev/serial0"
DEFAULT_SETTINGS = {
    "ACTIVE_METER_MODEL": "wago_879",
    "LOG_INTERVAL": 900,
    "MODBUS_SLAVE_ID": 1,
    "BAUDRATE": 9600,
    "PARITY": 'N',
    "BYTESIZE": 8,
    "STOPBITS": 1,
    "TIMEOUT": 2,
    "ACTIVE_LOG_PARAMETERS": None,
    "LIVE_METRICS": False,
}

# FILE SETTINGS

ROOT = Path(__file__).resolve().parent.parent.parent
DS_DIR = ROOT / "data/"
PL_DIR = ROOT / "plots/"
LOG_DIR = ROOT / "logs/"
STATIC_DIR = ROOT / "static/"
METERS_DIR = ROOT / "src" / "config" / "meters/"
SETTINGS_FILE = DS_DIR / "settings.json"
STATE_FILE = DS_DIR / "logger.state"
DB_FILE = DS_DIR / "database.sqlite"

# READING & LOGGING SETTINGS

USE_MODBUS = True
DEVELOPER_MODE = False
RETRY_INTERVAL = 60
MAX_RETRIES = 10
MAX_METER_VALUE = 1000000

# INFLUXDB SETTINGS

INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = "energy-logger"
INFLUXDB_BUCKET = "energy-logger"
INFLUXDB_TIMEOUT = 30

# REMOTE SYNC SETTINGS

REMOTE_DB_ENABLED = True
SYNC_INTERVAL = 30
SYNC_BATCH_SIZE = 100