# src/config.py

import os
import minimalmodbus

from datetime import datetime
from dotenv import load_dotenv

# HELPER FUNCTIONS

def get_filename(file="type"):
    """
    Generate a timestamped CSV filename for data logging.

    @file: Specify file type.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if file == "ds":
        return f"../data/{timestamp}.csv"
    elif file == "pl":
        return f"../plots/{timestamp}.png"

# FILE SETUP 

load_dotenv()

DS_FILEPATH = "../data/"
PL_FILEPATH = "../plots/"
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