# src/config.py

import os

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# MODBUS SETTINGS

# For other configurable parameters, refer to settings.py
MODBUS_PORT = "/dev/serial0"
REGISTERS = {
    "voltage_l1":      {"address": 0x5002, "number_of_registers": 2, "functioncode": 3, "description": "Voltage L1 (V)"},
    "voltage_l2":      {"address": 0x5004, "number_of_registers": 2, "functioncode": 3, "description": "Voltage L2 (V)"},
    "voltage_l3":      {"address": 0x5006, "number_of_registers": 2, "functioncode": 3, "description": "Voltage L3 (V)"},
    "current_l1":      {"address": 0x500C, "number_of_registers": 2, "functioncode": 3, "description": "Current L1 (A)"},
    "current_l2":      {"address": 0x500E, "number_of_registers": 2, "functioncode": 3, "description": "Current L2 (A)"},
    "current_l3":      {"address": 0x5010, "number_of_registers": 2, "functioncode": 3, "description": "Current L3 (A)"},
    "power_l1":        {"address": 0x5014, "number_of_registers": 2, "functioncode": 3, "description": "Power L1 (kW)"},
    "power_l2":        {"address": 0x5016, "number_of_registers": 2, "functioncode": 3, "description": "Power L2 (kW)"},
    "power_l3":        {"address": 0x5018, "number_of_registers": 2, "functioncode": 3, "description": "Power L3 (kW)"},
    "total_power":     {"address": 0x5012, "number_of_registers": 2, "functioncode": 3, "description": "Total Active Power (kW)"},
    "total_energy":    {"address": 0x6000, "number_of_registers": 2, "functioncode": 3, "description": "Total Active Energy (kWh)"},
    "total_energy_l1": {"address": 0x6006, "number_of_registers": 2, "functioncode": 3, "description": "Total Energy L1 (kWh)"},
    "total_energy_l2": {"address": 0x6008, "number_of_registers": 2, "functioncode": 3, "description": "Total Energy L2 (kWh)"},
    "total_energy_l3": {"address": 0x600A, "number_of_registers": 2, "functioncode": 3, "description": "Total Energy L3 (kWh)"},
    "total_energy_t1": {"address": 0x6002, "number_of_registers": 2, "functioncode": 3, "description": "Total Energy T1 (kWh)"},
    "total_energy_t2": {"address": 0x6004, "number_of_registers": 2, "functioncode": 3, "description": "Total Energy T2 (kWh)"},
    "total_energy_t3": {"address": 0x604B, "number_of_registers": 2, "functioncode": 3, "description": "Total Energy T3 (kWh)"},
    "total_energy_t4": {"address": 0x604D, "number_of_registers": 2, "functioncode": 3, "description": "Total Energy T4 (kWh)"},
}

# FILE SETTINGS

DS_HEADER = ["Timestamp"] + [params["description"] for params in REGISTERS.values()]
DS_DIR = "../data/"
PL_DIR = "../plots/"
LOG_DIR = "../logs/"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
STATE_FILE = "../data/logger.state"

# READING & LOGGING SETTINGS

USE_MODBUS = True
DEVELOPER_MODE = False
RETRY_INTERVAL = 5
MAX_RETRIES = 10

# INFLUXDB SETTINGS

INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = "energy-logger"
INFLUXDB_BUCKET = "energy-logger"
INFLUXDB_TIMEOUT = 5