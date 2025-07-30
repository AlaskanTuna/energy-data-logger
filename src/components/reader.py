# src/components/reader.py

import random
import time
import minimalmodbus
import logging

from config import config
from services.settings import settings

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
    """
    def __init__(self, use_modbus_flag=config.USE_MODBUS):
        self.instrument = None
        self.use_mock = config.DEVELOPER_MODE
        self.use_modbus = use_modbus_flag

        if self.use_modbus:
            try:
                self.instrument = minimalmodbus.Instrument(
                    port=config.MODBUS_PORT,
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
                raise ConnectionError(f"Failed to initialize Modbus on port '{config.MODBUS_PORT}': {e}", exc_info=True)

    def meter_reading_mock(self):
        """
        Simulate electrical data readings for testing purposes.
        
        @return: Dictionary with mock readings
        """
        readings = {}
        voltage_base = random.uniform(235, 245)
        current_base = random.uniform(2.0, 15.0)
        power_base = voltage_base * current_base / 1000
        energy_base = random.uniform(100, 200)

        for name in config.REGISTERS.keys():
            if 'voltage' in name:
                readings[name] = round(voltage_base * random.uniform(0.99, 1.01), 2)
            elif 'current' in name:
                readings[name] = round(current_base * random.uniform(0.8, 1.2), 2)
            elif 'power' in name and 'total' not in name:
                readings[name] = round(power_base * random.uniform(0.9, 1.1), 3)
            elif name == 'total_power':
                readings[name] = round(power_base * 3 * random.uniform(0.95, 1.05), 3)
            elif 'energy' in name:
                if '_t' in name:
                    readings[name] = round(energy_base * 0.3 * random.uniform(0.95, 1.05), 3)
                elif '_l' in name:
                     readings[name] = round(energy_base / 3 * random.uniform(0.95, 1.05), 3)
                else:
                    readings[name] = round(energy_base * random.uniform(0.98, 1.02), 3)
            else:
                readings[name] = round(random.uniform(0, 1), 3)
        return readings

    def meter_reading_modbus(self):
        """
        Polls electrical data from the power meter registers through Modbus.
        
        @return: Dictionary with Modbus readings or None
        """
        readings = {}
        try:
            for name, params in config.REGISTERS.items():
                value = self.instrument.read_float(
                    registeraddress=params["address"],
                    functioncode=params["functioncode"],
                    number_of_registers=params["number_of_registers"]
                )
                readings[name] = round(value, 3) # Set precision to 3 decimal places
            return readings
        except Exception as e:
            log.error(f"Modbus Error: {e}", exc_info=True)
            return None

    def get_meter_readings(self):
        """
        Get meter readings based on configuration settings.
        
        @return: Dictionary with meter readings or None
        """
        if not self.use_modbus and self.use_mock:
            return self.meter_reading_mock()
        elif self.use_modbus:
            retry_count = 0
            while retry_count < config.MAX_RETRIES:
                readings = self.meter_reading_modbus()
                if readings:
                    return readings
                else:
                    retry_count += 1
                    log.warning(f"Modbus signal lost. Retrying: {retry_count}/{config.MAX_RETRIES}.")
                    time.sleep(config.RETRY_INTERVAL)

            log.error(f"Modbus Error: Failed to get readings after {config.MAX_RETRIES} attempts.")
            return None
        else:
            log.error("No Modbus port detected and is not in developer mode.")
            return None