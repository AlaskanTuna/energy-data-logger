# src/config/config.py

import os

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# MODBUS SETTINGS

MODBUS_PORT = "/dev/serial0"
REGISTERS = {    
    # VOLTAGE REGISTERS
    "voltage_l1":               {"address": 0x5002, "number_of_registers": 2, "functioncode": 3, "description": "L1 Voltage (V)"},
    "voltage_l2":               {"address": 0x5004, "number_of_registers": 2, "functioncode": 3, "description": "L2 Voltage (V)"},
    "voltage_l3":               {"address": 0x5006, "number_of_registers": 2, "functioncode": 3, "description": "L3 Voltage (V)"},

    # CURRENT REGISTERS
    "current_l1":               {"address": 0x500C, "number_of_registers": 2, "functioncode": 3, "description": "L1 Current (A)"},
    "current_l2":               {"address": 0x500E, "number_of_registers": 2, "functioncode": 3, "description": "L2 Current (A)"},
    "current_l3":               {"address": 0x5010, "number_of_registers": 2, "functioncode": 3, "description": "L3 Current (A)"},

    # ACTIVE POWER REGISTERS
    "active_power_l1":          {"address": 0x5014, "number_of_registers": 2, "functioncode": 3, "description": "L1 Active Power (kW)"},
    "active_power_l2":          {"address": 0x5016, "number_of_registers": 2, "functioncode": 3, "description": "L2 Active Power (kW)"},
    "active_power_l3":          {"address": 0x5018, "number_of_registers": 2, "functioncode": 3, "description": "L3 Active Power (kW)"},
    "total_active_power":       {"address": 0x5012, "number_of_registers": 2, "functioncode": 3, "description": "Total Active Power (kW)"},

    # REACTIVE POWER REGISTERS
    "reactive_power_l1":        {"address": 0x501C, "number_of_registers": 2, "functioncode": 3, "description": "L1 Reactive Power (kvar)"},
    "reactive_power_l2":        {"address": 0x501E, "number_of_registers": 2, "functioncode": 3, "description": "L2 Reactive Power (kvar)"},
    "reactive_power_l3":        {"address": 0x5020, "number_of_registers": 2, "functioncode": 3, "description": "L3 Reactive Power (kvar)"},
    "total_reactive_power":     {"address": 0x501A, "number_of_registers": 2, "functioncode": 3, "description": "Total Reactive Power (kvar)"},

    # APPARENT POWER REGISTERS
    "apparent_power_l1":        {"address": 0x5024, "number_of_registers": 2, "functioncode": 3, "description": "L1 Apparent Power (kVA)"},
    "apparent_power_l2":        {"address": 0x5026, "number_of_registers": 2, "functioncode": 3, "description": "L2 Apparent Power (kVA)"},
    "apparent_power_l3":        {"address": 0x5028, "number_of_registers": 2, "functioncode": 3, "description": "L3 Apparent Power (kVA)"},
    "total_apparent_power":     {"address": 0x5022, "number_of_registers": 2, "functioncode": 3, "description": "Total Apparent Power (kVA)"},

    # ENERGY REGISTERS
    "total_active_energy":      {"address": 0x6000, "number_of_registers": 2, "functioncode": 3, "description": "Total Active Energy (kWh)"},
    "total_active_energy_l1":   {"address": 0x6006, "number_of_registers": 2, "functioncode": 3, "description": "L1 Total Active Energy (kWh)"},
    "total_active_energy_l2":   {"address": 0x6008, "number_of_registers": 2, "functioncode": 3, "description": "L2 Total Active Energy (kWh)"},
    "total_active_energy_l3":   {"address": 0x600A, "number_of_registers": 2, "functioncode": 3, "description": "L3 Total Active Energy (kWh)"},
    "total_reactive_energy":    {"address": 0x6024, "number_of_registers": 2, "functioncode": 3, "description": "Total Reactive Energy (kvarh)"},

    # ENERGY TARIFF REGISTERS
    "total_active_energy_t1":   {"address": 0x6002, "number_of_registers": 2, "functioncode": 3, "description": "T1 Total Active Energy (kWh)"},
    "total_active_energy_t2":   {"address": 0x6004, "number_of_registers": 2, "functioncode": 3, "description": "T2 Total Active Energy (kWh)"},
    "total_active_energy_t3":   {"address": 0x604B, "number_of_registers": 2, "functioncode": 3, "description": "T3 Total Active Energy (kWh)"},
    "total_active_energy_t4":   {"address": 0x604D, "number_of_registers": 2, "functioncode": 3, "description": "T4 Total Active Energy (kWh)"},
    "import_active_energy":     {"address": 0x600C, "number_of_registers": 2, "functioncode": 3, "description": "Import Active Energy (kWh)"},
    "export_active_energy":     {"address": 0x6018, "number_of_registers": 2, "functioncode": 3, "description": "Export Active Energy (kWh)"},

    # POWER FACTOR REGISTERS
    "power_factor_l1":          {"address": 0x502C, "number_of_registers": 2, "functioncode": 3, "description": "L1 Power Factor"},
    "power_factor_l2":          {"address": 0x502E, "number_of_registers": 2, "functioncode": 3, "description": "L2 Power Factor"},
    "power_factor_l3":          {"address": 0x5030, "number_of_registers": 2, "functioncode": 3, "description": "L3 Power Factor"},
    "power_factor":             {"address": 0x502A, "number_of_registers": 2, "functioncode": 3, "description": "Power Factor"},
}
DEFAULT_SETTINGS = {
    "LOG_INTERVAL": 900,
    "MODBUS_SLAVE_ID": 1,
    "BAUDRATE": 9600,
    "PARITY": 'N',
    "BYTESIZE": 8,
    "STOPBITS": 1,
    "TIMEOUT": 2,
    "ACTIVE_LOG_PARAMETERS": None,
}

# FILE SETTINGS

ROOT = Path(__file__).resolve().parent.parent.parent
DS_HEADER = ["Timestamp"] + [params["description"] for params in REGISTERS.values()]
DS_DIR = ROOT / "data/"
PL_DIR = ROOT / "plots/"
LOG_DIR = ROOT / "logs/"
STATIC_DIR = ROOT / "static/"
SETTINGS_FILE = DS_DIR / "settings.json"
STATE_FILE = DS_DIR / "logger.state"
DB_FILE = DS_DIR / "database.sqlite"

# READING & LOGGING SETTINGS

USE_MODBUS = True
DEVELOPER_MODE = False
RETRY_INTERVAL = 60
MAX_RETRIES = 10

# INFLUXDB SETTINGS

INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = "energy-logger"
INFLUXDB_BUCKET = "energy-logger"
INFLUXDB_TIMEOUT = 30