# src/config/config.py

import os

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# MODBUS SETTINGS

# For other configurable parameters, refer to settings.py
MODBUS_PORT = "/dev/serial0"
REGISTERS = {
    "voltage_l1":               {"address": 0x5002, "number_of_registers": 2, "functioncode": 3, "description": "L1 Voltage (V)"},
    "voltage_l2":               {"address": 0x5004, "number_of_registers": 2, "functioncode": 3, "description": "L2 Voltage (V)"},
    "voltage_l3":               {"address": 0x5006, "number_of_registers": 2, "functioncode": 3, "description": "L3 Voltage (V)"},
    "current_l1":               {"address": 0x500C, "number_of_registers": 2, "functioncode": 3, "description": "L1 Current (A)"},
    "current_l2":               {"address": 0x500E, "number_of_registers": 2, "functioncode": 3, "description": "L2 Current (A)"},
    "current_l3":               {"address": 0x5010, "number_of_registers": 2, "functioncode": 3, "description": "L3 Current (A)"},
    "active_power_l1":          {"address": 0x5014, "number_of_registers": 2, "functioncode": 3, "description": "L1 Active Power (kW)"},
    "active_power_l2":          {"address": 0x5016, "number_of_registers": 2, "functioncode": 3, "description": "L2 Active Power (kW)"},
    "active_power_l3":          {"address": 0x5018, "number_of_registers": 2, "functioncode": 3, "description": "L3 Active Power (kW)"},
    "total_active_power":       {"address": 0x5012, "number_of_registers": 2, "functioncode": 3, "description": "Total Active Power (kW)"},
    "total_active_energy":      {"address": 0x6000, "number_of_registers": 2, "functioncode": 3, "description": "Total Active Energy (kWh)"},
    "total_active_energy_l1":   {"address": 0x6006, "number_of_registers": 2, "functioncode": 3, "description": "L1 Total Active Energy (kWh)"},
    "total_active_energy_l2":   {"address": 0x6008, "number_of_registers": 2, "functioncode": 3, "description": "L2 Total Active Energy (kWh)"},
    "total_active_energy_l3":   {"address": 0x600A, "number_of_registers": 2, "functioncode": 3, "description": "L3 Total Active Energy (kWh)"},
    "total_active_energy_t1":   {"address": 0x6002, "number_of_registers": 2, "functioncode": 3, "description": "T1 Total Active Energy (kWh)"},
    "total_active_energy_t2":   {"address": 0x6004, "number_of_registers": 2, "functioncode": 3, "description": "T2 Total Active Energy (kWh)"},
    "total_active_energy_t3":   {"address": 0x604B, "number_of_registers": 2, "functioncode": 3, "description": "T3 Total Active Energy (kWh)"},
    "total_active_energy_t4":   {"address": 0x604D, "number_of_registers": 2, "functioncode": 3, "description": "T4 Total Active Energy (kWh)"},
}

# FILE SETTINGS

ROOT = Path(__file__).resolve().parent.parent.parent
DS_HEADER = ["Timestamp"] + [params["description"] for params in REGISTERS.values()]
DS_DIR = ROOT / "data/"
PL_DIR = ROOT / "plots/"
LOG_DIR = ROOT / "logs/"
STATIC_DIR = ROOT / "static/"
STATE_FILE = DS_DIR / "logger.state"

# READING & LOGGING SETTINGS

USE_MODBUS = False
DEVELOPER_MODE = True
RETRY_INTERVAL = 5
MAX_RETRIES = 10

# INFLUXDB SETTINGS

INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = "energy-logger"
INFLUXDB_BUCKET = "energy-logger"
INFLUXDB_TIMEOUT = 5