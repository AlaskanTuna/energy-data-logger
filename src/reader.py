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
    PARITY
)

class MeterReader:
    """
    Encapsulates the logic for reading from a power meter.
    """
    def __init__(self):
        self.use_modbus = USE_MODBUS
        if self.use_modbus:
            # Initialize a minimalmodbus.Instrument for real Modbus reads
            self.instrument = minimalmodbus.Instrument(MODBUS_PORT, MODBUS_SLAVE_ID)
            self.instrument.serial.baudrate = BAUDRATE
            self.instrument.serial.parity = PARITY
            self.instrument.serial.bytesize = 8
            self.instrument.serial.stopbits = 1
            self.instrument.serial.timeout = 1

    def meter_reading_mock(self):
        """
        Simulate meter readings with mock values.
        """
        voltage = round(random.uniform(215, 240), 2)
        current = round(random.uniform(1.5, 15.0), 2)
        active_energy_total = round(random.uniform(0.2, 2.5), 3)
        reactive_power_total = round(random.uniform(0.1, 1.2), 3)
        return voltage, current, active_energy_total, reactive_power_total

    def meter_reading_modbus(self):
        """
        Poll electrical data from the power meter via Modbus.
        The register values are returned as FLOAT32 (ABCD).
        """
        try:
            # Read total measurements
            voltage = self.instrument.read_float(0x5000, functioncode=3, number_of_registers=2)
            current = self.instrument.read_float(0x500A, functioncode=3, number_of_registers=2)
            active_energy_total = self.instrument.read_float(0x6000, functioncode=3, number_of_registers=2)
            reactive_power_total = self.instrument.read_float(0x501A, functioncode=3, number_of_registers=2)

            # Round them to match original precision
            return (
                round(voltage, 2),
                round(current, 2),
                round(active_energy_total, 3),
                round(reactive_power_total, 3),
            )
        except Exception as e:
            print(f"[MODBUS ERROR]: {e}.")
            return None

    def get_meter_readings(self):
        """
        Get meter readings either using mock values or Modbus polling.
        Modbus returns a tuple.
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
                print(f"[MODBUS ERROR] Attempting to reestablish connection: {retry_count}/{MAX_RETRIES}.")
                time.sleep(RETRY_INTERVAL)

        raise Exception(f"Failed to get MODBUS readings after {MAX_RETRIES} attempts.")
