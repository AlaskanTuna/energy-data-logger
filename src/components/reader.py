# src/components/reader.py

import random
import time
import minimalmodbus
import logging

from config import config
from components.settings import settings

# GLOBAL VARIABLES

log = logging.getLogger(__name__)
PARITY_MAP = {
    'N': minimalmodbus.serial.PARITY_NONE,
    'E': minimalmodbus.serial.PARITY_EVEN,
    'O': minimalmodbus.serial.PARITY_ODD,
}

class MeterReader:
    """
    Encapsulates the logic for reading from a power meter.
    """
    def __init__(self, use_modbus_flag=config.USE_MODBUS, register_map=None):
        self.instrument = None
        self.use_mock = config.DEVELOPER_MODE
        self.use_modbus = use_modbus_flag
        self.register_map = register_map

        if self.use_modbus:
            if not self.register_map:
                raise ValueError("Unable to find register map for Modbus communication.")
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
                log.info("Modbus instrument initialized for meter readings.")
            except Exception as e:
                raise ConnectionError(f"Failed to initialize Modbus on port '{config.MODBUS_PORT}': {e}", exc_info=True)

    def meter_reading_mock(self, active_parameters=None):
        """
        Simulate electrical data readings for testing purposes.
        
        @active_parameters: List of specific parameters to generate mock readings for
        @return: Dictionary with mock readings
        """
        readings = {}
        params_to_log = active_parameters if active_parameters else self.register_map.keys()

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
            elif 'active_power' in name or 'real_power' in name or ('real' in name and 'power' in name):
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
                if 'active' in name or 'real' in name:
                    if '_t' in name:
                        tariff_num = int(name.split('_t')[1][0])
                        portion = 0.4 if tariff_num == 1 else 0.3 if tariff_num == 2 else 0.2 if tariff_num == 3 else 0.1
                        readings[name] = round(energy_base * portion * random.uniform(0.95, 1.05), 3)
                    elif '_l' in name:
                        readings[name] = round(energy_base / 3 * random.uniform(0.9, 1.1), 3)
                    elif 'import' in name or 'positive' in name:
                        readings[name] = round(energy_base * 0.95 * random.uniform(0.98, 1.02), 3)
                    elif 'export' in name or 'negative' in name:
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
            params_to_log = active_parameters if active_parameters else self.register_map.keys()
            for name in params_to_log:
                if name in self.register_map:
                    params = self.register_map[name]
                    data_type = params.get("data_type")
                    scale_factor = params.get("scale_factor", 1)
                    raw_value = 0

                    if data_type == "float":
                        raw_value = self.instrument.read_float(
                            registeraddress=params["address"],
                            functioncode=params["functioncode"],
                            number_of_registers=params.get("number_of_registers", 2),
                        )
                    elif data_type in ["dword", "int"]:
                        is_signed = (data_type == "int")
                        raw_value = self.instrument.read_long(
                            registeraddress=params["address"],
                            functioncode=params["functioncode"],
                            number_of_registers=params.get("number_of_registers", 2),
                            signed=is_signed,
                        )
                    elif data_type == "word":
                        raw_value = self.instrument.read_register(
                            registeraddress=params["address"],
                            functioncode=params["functioncode"],
                        )
                    else:
                        log.warning(f"Unsupported data type '{data_type}' for parameter '{name}'.")
                        continue

                    # Process register reading
                    final_value = raw_value * scale_factor
                    readings[name] = round(final_value, 3) # Set precision to 3 decimal places
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
                    log.warning(f"Modbus communication failed. Retrying: {retry_count}/{config.MAX_RETRIES}.")
                    time.sleep(config.RETRY_INTERVAL)

            log.error(f"Modbus Read Error: Failed to get readings after {config.MAX_RETRIES} attempts.")
            return None
        else:
            log.error("Modbus Read Error: No Modbus port detected and is not in developer mode.")
            return None