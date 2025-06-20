# src/logger.py

import os
import csv
import time

from settings import settings
from reader import MeterReader
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from config import (
    REGISTERS,
    USE_MODBUS,
    DS_HEADER,
    DS_FILEPATH,
    INFLUXDB_URL,
    INFLUXDB_TOKEN,
    INFLUXDB_ORG,
    INFLUXDB_BUCKET,
    INFLUXDB_TIMEOUT
)

class DataLogger:
    """
    Handles CSV setup, InfluxDB initialization and continuous data logging.
    """
    def __init__(self, filename):
        self.ds_dir = DS_FILEPATH
        if not os.path.exists(self.ds_dir):
            os.makedirs(self.ds_dir, exist_ok=True)

        self.ds_filename = filename
        self.ds_header = DS_HEADER

        # If the file is new or empty, write the header row; otherwise, leave it unchanged
        is_new_file = not os.path.exists(self.ds_filename) or os.path.getsize(self.ds_filename) == 0
        with open(self.ds_filename, 'a', newline='') as file:
            if is_new_file:
                writer = csv.writer(file)
                writer.writerow(self.ds_header)
        
        print(f"[INFO]: Data logging initialized. CSV file: {self.ds_filename}")

        self.reader = None

        # Test if Modbus is actually available
        try:
            self.reader = MeterReader(use_modbus_flag=USE_MODBUS)
            test_readings = self.reader.get_meter_readings()

            if not test_readings:
                raise ConnectionError
        except ConnectionError:
            self.reader = MeterReader(use_modbus_flag=False)

        self._initialize_influxdb()
        self._running = True
        self.latest = None

    def _initialize_influxdb(self):
        """
        Initializes and tests the InfluxDB client connection.
        """
        self.influx_enabled = False
        if not (INFLUXDB_URL and INFLUXDB_TOKEN):
            print("[INFO]: InfluxDB config not provided. Continuing with CSV logging only.")
            return

        try:
            self.client = InfluxDBClient(
                url=INFLUXDB_URL,
                token=INFLUXDB_TOKEN,
                org=INFLUXDB_ORG,
                timeout=INFLUXDB_TIMEOUT
            )
            if self.client.ping():
                self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
                self.influx_enabled = True
                print("[INFO]: InfluxDB connection established successfully.")
            else:
                print("[ERROR]: InfluxDB ping failed. Please check token and organization settings.")
        except Exception as e:
            print(f"[INFLUXDB CONNECTION ERROR]: {e}")
            print("[WARNING]: Could not connect to InfluxDB. Continuing with CSV logging only.")
            self.client = None

    def log(self):
        """
        Simultaneously log meter readings to CSV and InfluxDB.
        """
        try:
            while self._running:
                readings = self.reader.get_meter_readings()
                if not readings:
                    print("\n[WARNING]: Could not retrieve readings. Terminating logger session.")
                    self.stop()
                    continue

                timestamp = datetime.now()
                self.latest = {"ts": timestamp, **readings}
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

                # DYNAMIC CSV WRITING

                csv_status = "✗"
                try:
                    row_data = [timestamp_str] + [readings.get(key) for key in REGISTERS.keys()]
                    with open(self.ds_filename, 'a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(row_data)
                    csv_status = "✓"
                except Exception as e:
                    print(f"[CSV WRITE ERROR]: {e}")

                # DYNAMIC INFLUXDB WRITING

                influx_status = "-"
                if self.influx_enabled:
                    try:
                        point = Point("power_measurements").tag("source", "wago_meter")

                        # Loop through all readings and add them as fields
                        for key, value in readings.items():
                            if value is not None:
                                point.field(key, value)
                        point.time(datetime.now(tz=timezone.utc), WritePrecision.S)
                        
                        self.write_api.write(bucket=INFLUXDB_BUCKET, record=point)
                        influx_status = "✓"
                    except Exception as e:
                        print(f"[INFLUXDB WRITE ERROR]: {e}")
                        influx_status = "✗"
                else:
                    influx_status = "✗" if (INFLUXDB_URL and INFLUXDB_TOKEN) else "-"

                print(f"[{timestamp_str}] Logged successfully | CSV: {csv_status} | InfluxDB: {influx_status}")
                time.sleep(settings.get("LOG_INTERVAL"))
        except KeyboardInterrupt:
            print("\n[INFO]: Logging stopped by user.")
        finally:
            self.stop()

    def start(self):
        from util import clear_screen
        try:
            print("\n===== Energy Data Logger: Started Execution =====\n")
            self.log()
            print("\n===== Energy Data Logger: Finished Execution =====")
            input("\nPress Enter to continue...")
            clear_screen()
        except Exception as e:
            print(f"\n[LOG ERROR]: {e}")

    def stop(self):
        self._running = False
        if self.influx_enabled and self.client:
            self.client.close()
            print("[INFO]: InfluxDB connection closed.")