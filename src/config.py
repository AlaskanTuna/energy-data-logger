# src/config.py

import os
import minimalmodbus

from util import get_filename
from dotenv import load_dotenv
from pathlib import Path

# FILE SETUP 

load_dotenv()

DS_FILEPATH = "../data/"
PL_FILEPATH = "../plots/"
STATIC_FILEPATH = Path(__file__).resolve().parent.parent / "static"
DS_HEADER = [
    "Timestamp", 
    "Voltage L1 (V)", "Voltage L2 (V)", "Voltage L3 (V)",
    "Current L1 (A)", "Current L2 (A)", "Current L3 (A)",
    "Total Active Power (kW)", "Power Factor", 
    "Total Active Energy (kWh)", "Import Active Energy (kWh)", "Export Active Energy (kWh)"
]
DS_FILENAME = get_filename("ds")
PL_FILENAME = get_filename("pl")

# METER & LOGGING 

USE_MODBUS = False # False to use mock data; True to use Modbus
LOG_INTERVAL = 3
RETRY_INTERVAL = 5
MAX_RETRIES = 5

MODBUS_PORT = "/dev/ttyUSB0"
MODBUS_SLAVE_ID = 1
BAUDRATE = 9600
PARITY = minimalmodbus.serial.PARITY_NONE

# INFLUXDB SETTINGS

INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = "energy-logger"
INFLUXDB_BUCKET = "energy-logger"