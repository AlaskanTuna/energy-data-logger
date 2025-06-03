# src/logger.py

import os
import csv
import time

from stats import DataAnalyzer
from datetime import datetime, timezone
from reader import MeterReader
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from config import (
    DS_FILENAME,
    DS_HEADER,
    LOG_INTERVAL,
    INFLUXDB_URL,
    INFLUXDB_TOKEN,
    INFLUXDB_ORG,
    INFLUXDB_BUCKET
)

class DataLogger:
    """
    Handles CSV setup, InfluxDB initialization and continuous data logging. 
    Runs statistics and visualization on termination.
    """
    def __init__(self):
        # Initialize (overwrite) the CSV file with header
        with open(DS_FILENAME, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(DS_HEADER)

        # Initialize MeterReader and DataAnalyzer
        self.reader = MeterReader()
        self.analyzer = DataAnalyzer()

        # Initialize InfluxDB client
        try:
            self.client = InfluxDBClient(
                url=INFLUXDB_URL,
                token=INFLUXDB_TOKEN,
                org=INFLUXDB_ORG
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.influx_enabled = True
            print("InfluxDB connection established successfully.")
        except Exception as e:
            print(f"[INFLUXDB CONNECTION ERROR]: {e}")
            print("Continuing with CSV logging only.")
            self.influx_enabled = False

    def log(self):
        """
        Simultaneously log meter readings to CSV and InfluxDB. 
        Finalize by closing InfluxDB and running statistics + visualization upon KeyboardInterrupt.
        """
        print("\n===== Energy Data Logger: Started Execution =====\n")
        try:
            while True:
                voltage, current, active_energy, reactive_power = self.reader.get_meter_readings()
                timestamp = datetime.now()
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

                # 1) Append to CSV
                try:
                    with open(DS_FILENAME, 'a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow([timestamp_str, voltage, current, active_energy, reactive_power])
                    csv_status = "✓"
                except Exception as e:
                    print(f"[CSV WRITE ERROR]: {e}.")
                    csv_status = "✗"

                # 2) Write to InfluxDB (if enabled)
                influx_status = "-"
                if self.influx_enabled:
                    try:
                        point = (
                            Point("power_measurements")
                            .tag("source", "energy_logger")
                            .tag("location", "main_panel")
                            .field("voltage", voltage)
                            .field("current", current)
                            .field("energy", active_energy)
                            .field("reactive_power", reactive_power)
                            .time(datetime.now(tz=timezone.utc), WritePrecision.S)
                        )
                        self.write_api.write(bucket=INFLUXDB_BUCKET, record=point)
                        influx_status = "✓"
                    except Exception as e:
                        print(f"[INFLUXDB WRITE ERROR]: {e}.")
                        influx_status = "✗"

                # 3) Print statuses
                print(f"[{timestamp_str}] CSV: {csv_status} InfluxDB: {influx_status} | Data logged successfully.")
                time.sleep(LOG_INTERVAL)

        except KeyboardInterrupt:
            # CTRL + C to stop logging.
            print("\nLogging stopped by user. Processing data...")
            if self.influx_enabled:
                self.client.close()
                print("InfluxDB connection closed.")
            df = self.analyzer.calculate_statistics()
            self.analyzer.visualize_data(df)

        except Exception as e:
            if self.influx_enabled:
                self.client.close()

    def start(self):
        """
        Calls log() function.
        """
        try:
            self.log()
            print("\n===== Energy Data Logger: Finished Execution =====")
        except Exception as e:
            print(f"\n[LOG ERROR]: {e}.")