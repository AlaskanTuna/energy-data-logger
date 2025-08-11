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

    def meter_reading_mock(self, active_parameters=None):
        """
        Simulate electrical data readings for testing purposes.
        
        @active_parameters: List of specific parameters to generate mock readings for
        @return: Dictionary with mock readings
        """
        readings = {}
        params_to_log = active_parameters if active_parameters else config.REGISTERS.keys()

        # Base simulation values
        voltage_base = random.uniform(235, 245)
        current_base = random.uniform(2.0, 15.0)
        active_power_base = voltage_base * current_base * 0.9 / 1000
        power_factor_base = random.uniform(0.85, 0.98)
        apparent_power_base = active_power_base / power_factor_base
        reactive_power_base = (apparent_power_base**2 - active_power_base**2)**0.5
        energy_base = random.uniform(200, 1000)

        # Generate values for each register type
        for name in params_to_log:
            if 'voltage' in name:
                readings[name] = round(voltage_base * random.uniform(0.98, 1.02), 2)
            elif 'current' in name:
                readings[name] = round(current_base * random.uniform(0.7, 1.3), 2)
            elif 'active_power' in name:
                if 'total' in name:
                    readings[name] = round(active_power_base * 3 * random.uniform(0.95, 1.05), 3)
                else:
                    readings[name] = round(active_power_base * random.uniform(0.8, 1.2), 3)
            elif 'reactive_power' in name:
                if 'total' in name:
                    readings[name] = round(reactive_power_base * 3 * random.uniform(0.95, 1.05), 3)
                else:
                    readings[name] = round(reactive_power_base * random.uniform(0.8, 1.2), 3)
            elif 'apparent_power' in name:
                if 'total' in name:
                    readings[name] = round(apparent_power_base * 3 * random.uniform(0.95, 1.05), 3)
                else:
                    readings[name] = round(apparent_power_base * random.uniform(0.8, 1.2), 3)
            elif 'energy' in name:
                if 'active' in name:
                    if '_t' in name:
                        tariff_num = int(name.split('_t')[1][0])
                        portion = 0.4 if tariff_num == 1 else 0.3 if tariff_num == 2 else 0.2 if tariff_num == 3 else 0.1
                        readings[name] = round(energy_base * portion * random.uniform(0.95, 1.05), 3)
                    elif '_l' in name:
                        readings[name] = round(energy_base / 3 * random.uniform(0.9, 1.1), 3)
                    elif 'import' in name:
                        readings[name] = round(energy_base * 0.95 * random.uniform(0.98, 1.02), 3)
                    elif 'export' in name:
                        readings[name] = round(energy_base * 0.05 * random.uniform(0.9, 1.1), 3)
                    else:
                        readings[name] = round(energy_base * random.uniform(0.98, 1.02), 3)
                elif 'reactive' in name:
                    readings[name] = round(energy_base * 0.4 * random.uniform(0.95, 1.05), 3)
            elif 'power_factor' in name:
                if 'l1' in name or 'l2' in name or 'l3' in name:
                    readings[name] = round(power_factor_base * random.uniform(0.97, 1.03), 3)
                else:
                    readings[name] = round(power_factor_base, 3)
        return readings

    def meter_reading_modbus(self, active_parameters=None):
        """
        Polls electrical data from the power meter registers through Modbus.
        
        @active_parameters: List of specific parameters to read from Modbus
        @return: Dictionary with Modbus readings or None
        """
        readings = {}
        try:
            params_to_log = active_parameters if active_parameters else config.REGISTERS.keys()
            for name in params_to_log:
                if name in config.REGISTERS:
                    params = config.REGISTERS[name]
                    value = self.instrument.read_float(
                        registeraddress=params["address"],
                        functioncode=params["functioncode"],
                        number_of_registers=params["number_of_registers"],
                    )
                    readings[name] = round(value, 3) # Set precision to 3 decimal places
            return readings
        except Exception as e:
            log.error(f"Modbus Error: {e}", exc_info=True)
            return None

    def get_meter_readings(self, active_parameters=None):
        """
        Get meter readings based on configuration settings.
        
        @active_parameters: List of specific parameters to read
        @return: Dictionary with meter readings or None
        """
        if not self.use_modbus and self.use_mock:
            return self.meter_reading_mock(active_parameters=active_parameters)
        elif self.use_modbus:
            retry_count = 0
            while retry_count < config.MAX_RETRIES:
                readings = self.meter_reading_modbus(active_parameters=active_parameters)
                if readings:
                    return readings
                else:
                    retry_count += 1
                    log.warning(f"Modbus signal lost. Retrying: {retry_count}/{config.MAX_RETRIES}.")
                    time.sleep(config.RETRY_INTERVAL)

            log.error(f"Modbus Read Error: Failed to get readings after {config.MAX_RETRIES} attempts.")
            return None
        else:
            log.error("Modbus Error: No Modbus port detected and is not in developer mode.")
            return None