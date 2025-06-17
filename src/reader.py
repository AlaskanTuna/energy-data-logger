# src/reader.py

import random
import time
import minimalmodbus

from config import (
    USE_MODBUS,
    RETRY_INTERVAL,
    MAX_RETRIES,
    MODBUS_PORT,
    MODBUS_SLAVE_ID,
    BAUDRATE,
    PARITY,
    BYTESIZE,
    STOPBITS,
    TIMEOUT,
    REGISTERS
)

class MeterReader:
    """
    Encapsulates the logic for reading from a power meter.
    """
    def __init__(self, use_modbus_flag=USE_MODBUS):
        self.use_modbus = use_modbus_flag
        self.instrument = None
        if self.use_modbus:
            try:
                self.instrument = minimalmodbus.Instrument(
                    port=MODBUS_PORT,
                    slaveaddress=MODBUS_SLAVE_ID
                )
                self.instrument.serial.baudrate = BAUDRATE
                self.instrument.serial.parity = PARITY
                self.instrument.serial.bytesize = BYTESIZE
                self.instrument.serial.stopbits = STOPBITS
                self.instrument.serial.timeout = TIMEOUT
                self.instrument.mode = minimalmodbus.MODE_RTU
                print("[INFO]: Modbus instrument initialized for real readings.")
            except Exception as e:
                raise ConnectionError(f"[MODBUS ERROR]: Failed to initialize Modbus on port {MODBUS_PORT}: {e}")
        else:
            print("[INFO]: Mock data initialized for mock readings.")

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
            print(f"[MODBUS READ ERROR]: {e}")
            return None

    def get_meter_readings(self):
        """
        Get meter readings either using mock values or Modbus polling.
        Returns a dictionary of readings.
        """
        if not self.use_modbus:
            return self.meter_reading_mock()

        retry_count = 0
        while retry_count < MAX_RETRIES:
            readings = self.meter_reading_modbus()
            if readings:
                return readings
            else:
                retry_count += 1
                print(f"[MODBUS ERROR]: Attempting to reestablish connection. {retry_count}/{MAX_RETRIES}.")
                time.sleep(RETRY_INTERVAL)

        print(f"[MODBUS ERROR]: Failed to get readings after {MAX_RETRIES} attempts.")
        return None