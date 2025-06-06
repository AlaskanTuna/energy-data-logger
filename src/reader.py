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
        # Create realistic mock values
        voltage_base = random.uniform(215, 240)
        current_base = random.uniform(1.5, 15.0)
        
        # Per-phase values with realistic variation
        voltage_L1 = round(voltage_base * random.uniform(0.98, 1.02), 2)
        voltage_L2 = round(voltage_base * random.uniform(0.98, 1.02), 2)
        voltage_L3 = round(voltage_base * random.uniform(0.98, 1.02), 2)
        
        current_L1 = round(current_base * random.uniform(0.95, 1.05), 2)
        current_L2 = round(current_base * random.uniform(0.95, 1.05), 2)
        current_L3 = round(current_base * random.uniform(0.95, 1.05), 2)
        
        total_active_power = round(((voltage_L1 + voltage_L2 + voltage_L3) / 3) * 
                                ((current_L1 + current_L2 + current_L3) / 3) * 
                                random.uniform(0.85, 0.95) / 1000, 3)
        
        power_factor = round(random.uniform(0.8, 0.98), 2)
        
        total_active_energy = round(random.uniform(0.2, 2.5), 3)
        import_active_energy = round(total_active_energy * random.uniform(0.95, 1.0), 3)
        export_active_energy = round(total_active_energy * random.uniform(0, 0.05), 3)
        
        return {
            "voltage_L1": voltage_L1,
            "voltage_L2": voltage_L2,
            "voltage_L3": voltage_L3,
            "current_L1": current_L1,
            "current_L2": current_L2,
            "current_L3": current_L3,
            "total_active_power": total_active_power,
            "power_factor": power_factor,
            "total_active_energy": total_active_energy,
            "import_active_energy": import_active_energy,
            "export_active_energy": export_active_energy
        }

    def meter_reading_modbus(self):
        """
        Poll electrical data from the power meter via Modbus.
        The register values are returned as FLOAT32 (ABCD).
        """
        try:
            # Read per-phase voltages (recommended parameters)
            voltage_L1 = self.instrument.read_float(0x5002, functioncode=3, number_of_registers=2)
            voltage_L2 = self.instrument.read_float(0x5004, functioncode=3, number_of_registers=2)
            voltage_L3 = self.instrument.read_float(0x5006, functioncode=3, number_of_registers=2)
            
            # Read per-phase currents
            current_L1 = self.instrument.read_float(0x500C, functioncode=3, number_of_registers=2)
            current_L2 = self.instrument.read_float(0x500E, functioncode=3, number_of_registers=2)
            current_L3 = self.instrument.read_float(0x5010, functioncode=3, number_of_registers=2)
            
            # Read power measurements
            total_active_power = self.instrument.read_float(0x5012, functioncode=3, number_of_registers=2)
            power_factor = self.instrument.read_float(0x502A, functioncode=3, number_of_registers=2)
            
            # Read energy measurements
            total_active_energy = self.instrument.read_float(0x6000, functioncode=3, number_of_registers=2)
            import_active_energy = self.instrument.read_float(0x600C, functioncode=3, number_of_registers=2)
            export_active_energy = self.instrument.read_float(0x6018, functioncode=3, number_of_registers=2)
            
            # Return all values in a dictionary
            return {
                "voltage_L1": round(voltage_L1, 2),
                "voltage_L2": round(voltage_L2, 2),
                "voltage_L3": round(voltage_L3, 2),
                "current_L1": round(current_L1, 2),
                "current_L2": round(current_L2, 2),
                "current_L3": round(current_L3, 2),
                "total_active_power": round(total_active_power, 3),
                "power_factor": round(power_factor, 2),
                "total_active_energy": round(total_active_energy, 3),
                "import_active_energy": round(import_active_energy, 3),
                "export_active_energy": round(export_active_energy, 3)
            }
        except Exception as e:
            print(f"[MODBUS ERROR]: {e}.")
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
                print(f"[MODBUS ERROR] Attempting to reestablish connection: {retry_count}/{MAX_RETRIES}.")
                time.sleep(RETRY_INTERVAL)

        raise Exception(f"Failed to get MODBUS readings after {MAX_RETRIES} attempts.")