# src/reader.py

import random
import time
import minimalmodbus
import logging

from settings import settings
from config import (
    REGISTERS,
    USE_MODBUS,
    MODBUS_PORT,
    DEVELOPER_MODE,
    RETRY_INTERVAL,
    MAX_RETRIES
)

# CONSTANTS

PARITY_MAP = {
    'N': minimalmodbus.serial.PARITY_NONE,
    'E': minimalmodbus.serial.PARITY_EVEN,
    'O': minimalmodbus.serial.PARITY_ODD,
}
log = logging.getLogger(__name__)

class MeterReader:
    """
    Encapsulates the logic for reading from a power meter.
    
    @use_modbus_flag: If True, uses Modbus to read data; otherwise, uses mock data.
    """
    def __init__(self, use_modbus_flag=USE_MODBUS):
        self.instrument = None
        self.use_mock = DEVELOPER_MODE
        self.use_modbus = use_modbus_flag

        if self.use_modbus:
            try:
                self.instrument = minimalmodbus.Instrument(
                    port=MODBUS_PORT,
                    slaveaddress=settings.get("MODBUS_SLAVE_ID")
                )
                parity_str = settings.get("PARITY")
                self.instrument.serial.parity = PARITY_MAP.get(parity_str, minimalmodbus.serial.PARITY_NONE)
                self.instrument.serial.baudrate = settings.get("BAUDRATE")
                self.instrument.serial.bytesize = settings.get("BYTESIZE")
                self.instrument.serial.stopbits = settings.get("STOPBITS")
                self.instrument.serial.timeout = settings.get("TIMEOUT")
                self.instrument.mode = minimalmodbus.MODE_RTU
                log.info("Modbus instrument initialized for real readings.")
            except Exception as e:
                raise ConnectionError(f"Failed to initialize Modbus on port {MODBUS_PORT}. {e}")

    def meter_reading_mock(self):
        """
        Simulate electrical data readings for testing purposes.
        """
        readings = {}
        voltage_base = random.uniform(215, 240)
        current_base = random.uniform(1.5, 15.0)
        power_base = voltage_base * current_base / 1000
        energy_base = random.uniform(500, 10000)

        for name in REGISTERS.keys():
            if 'voltage' in name:
                readings[name] = round(voltage_base * random.uniform(0.98, 1.02), 2)
            elif 'current' in name:
                readings[name] = round(current_base * random.uniform(0.95, 1.05), 2)
            elif 'power' in name and 'total' not in name:
                readings[name] = round(power_base * random.uniform(0.9, 1.1), 3)
            elif name == 'total_power':
                readings[name] = round(power_base * 3 * random.uniform(0.95, 1.05), 3)
            elif 'energy' in name:
                if '_t' in name:
                    readings[name] = round(energy_base * 0.4 * random.uniform(0.9, 1.1), 3)
                elif '_l' in name:
                     readings[name] = round(energy_base / 3 * random.uniform(0.9, 1.1), 3)
                else:
                    readings[name] = round(energy_base * random.uniform(0.98, 1.02), 3)
            else:
                readings[name] = round(random.uniform(0, 1), 3)
        return readings

    def meter_reading_modbus(self):
        """
        Polls electrical data from the power meter registers through Modbus.
        """
        readings = {}
        try:
            for name, params in REGISTERS.items():
                value = self.instrument.read_float(
                    registeraddress=params["address"],
                    functioncode=params["functioncode"],
                    number_of_registers=params["number_of_registers"]
                )
                readings[name] = round(value, 3) # Set precision to 3 decimal places
            return readings
        except Exception as e:
            log.error(f"Modbus Error: {e}")
            return None

    def get_meter_readings(self):
        """
        Get meter readings either using mock values or Modbus polling.
        Returns a dictionary of readings.
        """
        if not self.use_modbus and self.use_mock:
            return self.meter_reading_mock()
        elif self.use_modbus:
            retry_count = 0
            while retry_count < MAX_RETRIES:
                readings = self.meter_reading_modbus()
                if readings:
                    return readings
                else:
                    retry_count += 1
                    log.warning(f"Modbus signal lost. Retrying: {retry_count}/{MAX_RETRIES}.")
                    time.sleep(RETRY_INTERVAL)

            log.error(f"Modbus Error: Failed to get readings after {MAX_RETRIES} attempts.")
            return None
        else:
            log.error("No Modbus port detected and is not in developer mode.")
            return None