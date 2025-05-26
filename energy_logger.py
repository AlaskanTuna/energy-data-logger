# THIS IS A MOCK SCRIPT FOR TESTING PURPOSES

import csv
import random
import time
from datetime import datetime

# Definitions
DS_FILENAME = "energy_data.csv"
DS_HEADER = ["Timestamp", "Voltage (V)", "Current (A)", "Energy (kW)", "Reactive Power (LVA)"]

try:
    with open(DS_FILENAME, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(DS_HEADER)
except FileExistsError:
    pass

# Functions
def meter_reading():
    """
    Simulate electrical signals from a power meter
    """
    # Generate mock values in realistic ranges
    voltage = round(random.uniform(215, 240), 2)
    current = round(random.uniform(1.5, 15.0), 2)
    energy = round(random.uniform(0.2, 2.5), 3)
    reactive_power = round(random.uniform(0.1, 1.2), 3)
    return voltage, current, energy, reactive_power

# Simulate energy data logging
while True:
    voltage, current, energy, reactive_power = meter_reading()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Log data to file
    with open(DS_FILENAME, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, voltage, current, energy, reactive_power])
        
    print(f"[{timestamp}] Logged: V={voltage}V | I={current}A | E={energy}kW | RP={reactive_power}LVA")

    time.sleep(5) # Interval between readings