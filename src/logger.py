# src/logger.py

import os
import csv
import time

from util import clear_screen, get_current_filename
from datetime import datetime, timezone
from reader import MeterReader
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from config import (
    DS_FILEPATH,
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
        # Initialize data directory
        self.ds_dir = DS_FILEPATH
        if not os.path.exists(self.ds_dir):
            try:
                os.makedirs(self.ds_dir)
            except Exception as e:
                print(f"[DIRECTORY CREATION ERROR]: {e}")

        # Initialize the CSV file with header
        self.ds_filename = get_current_filename("ds")
        self.ds_header = DS_HEADER
        with open(self.ds_filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.ds_header)

        # Initialize MeterReader and DataAnalyzer
        self.reader = MeterReader()

        # Initialize InfluxDB client
        self.influx_enabled = False
        if INFLUXDB_URL and INFLUXDB_TOKEN:
            try:
                self.client = InfluxDBClient(
                    url=INFLUXDB_URL,
                    token=INFLUXDB_TOKEN,
                    org=INFLUXDB_ORG,
                    timeout=3000
                )

                # Test write capability with a small test point
                write_api = self.client.write_api(write_options=SYNCHRONOUS)
                test_point = Point("connection_test").field("value", 1)
                write_api.write(bucket=INFLUXDB_BUCKET, record=test_point)

                self.write_api = write_api
                self.influx_enabled = True
                print("InfluxDB connection established successfully.")
            except Exception as e:
                self.client = None
                print(f"[INFLUXDB CONNECTION ERROR]: {e}")
                print("InfluxDB connection established unsuccessfully. Continuing with CSV logging only.")
        else:
            print("[INFLUXDB CONFIG ERROR]: InfluxDB URL or token not provided.")
            print("InfluxDB connection established unsuccessfully. Continuing with CSV logging only.")

        self._running = True
        self.latest = None

    def log(self):
        """
        Simultaneously log meter readings to CSV and InfluxDB. 
        """
        try:
            while self._running:
                readings = self.reader.get_meter_readings()
                timestamp = datetime.now()
                self.latest = {"ts": timestamp, **readings}
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

                # 1) Append to CSV
                try:
                    with open(self.ds_filename, 'a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow([
                            timestamp_str, 
                            readings["voltage_L1"], readings["voltage_L2"], readings["voltage_L3"],
                            readings["current_L1"], readings["current_L2"], readings["current_L3"],
                            readings["total_active_power"], readings["power_factor"],
                            readings["total_active_energy"], readings["import_active_energy"], readings["export_active_energy"]
                        ])
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
                            # Voltage measurements
                            .field("voltage_L1", readings["voltage_L1"])
                            .field("voltage_L2", readings["voltage_L2"])
                            .field("voltage_L3", readings["voltage_L3"])
                            # Current measurements
                            .field("current_L1", readings["current_L1"])
                            .field("current_L2", readings["current_L2"])
                            .field("current_L3", readings["current_L3"])
                            # Power measurements
                            .field("total_active_power", readings["total_active_power"])
                            .field("power_factor", readings["power_factor"])
                            # Energy measurements
                            .field("total_active_energy", readings["total_active_energy"])
                            .field("import_active_energy", readings["import_active_energy"])
                            .field("export_active_energy", readings["export_active_energy"])
                            .time(datetime.now(tz=timezone.utc), WritePrecision.S)
                        )
                        self.write_api.write(bucket=INFLUXDB_BUCKET, record=point)
                        influx_status = "✓"
                    except Exception as e:
                        print(f"[INFLUXDB WRITE ERROR]: {e}.")
                        influx_status = "✗"
                else:
                    influx_status = "✗"

                print(f"[{timestamp_str}] CSV: {csv_status} InfluxDB: {influx_status} | Logged successfully.")
                time.sleep(LOG_INTERVAL)

        # CTRL + C to stop logging.
        except KeyboardInterrupt:
            print("\nLogging stopped by user. Processing data...")
            if self.influx_enabled:
                self.client.close()
                print("InfluxDB connection closed.")

        except Exception as e:
            if self.influx_enabled:
                self.client.close()

    def start(self):
        """
        Calls log() function.
        """
        try:
            print("\n===== Energy Data Logger: Started Execution =====\n")
            self.log()
            print("\n===== Energy Data Logger: Finished Execution =====")
            input("\nPress Enter to continue...")
            clear_screen()
        except Exception as e:
            print(f"\n[LOG ERROR]: {e}")

    def stop(self):
        """
        Tell the logging loop to exit on the next iteration.
        """
        self._running = False