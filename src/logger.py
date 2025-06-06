# src/logger.py

import os
import csv
import time

from analyzer import DataAnalyzer
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
        self.influx_enabled = False
        if INFLUXDB_URL and INFLUXDB_TOKEN:
            try:
                self.client = InfluxDBClient(
                    url=INFLUXDB_URL,
                    token=INFLUXDB_TOKEN,
                    org=INFLUXDB_ORG,
                    timeout=3000  # 3 seconds timeout
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

    def log(self):
        """
        Simultaneously log meter readings to CSV and InfluxDB. 
        Finalize by closing InfluxDB and running statistics + visualization upon KeyboardInterrupt.
        """
        print("\n===== Energy Data Logger: Started Execution =====\n")
        try:
            while True:
                readings = self.reader.get_meter_readings()
                timestamp = datetime.now()
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

                # 1) Append to CSV
                try:
                    with open(DS_FILENAME, 'a', newline='') as file:
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

                # 3) Print status with summary of key values
                avg_voltage = round((readings["voltage_L1"] + readings["voltage_L2"] + readings["voltage_L3"]) / 3, 1)
                avg_current = round((readings["current_L1"] + readings["current_L2"] + readings["current_L3"]) / 3, 1)
                
                print(
                    f"[{timestamp_str}] CSV: {csv_status} InfluxDB: {influx_status} | " +
                    f"V={avg_voltage}V | I={avg_current}A | P={readings['total_active_power']}kW | " +
                    f"PF={readings['power_factor']} | E={readings['total_active_energy']}kWh"
                    )
                
                time.sleep(LOG_INTERVAL)

        # CTRL + C to stop logging.
        except KeyboardInterrupt:
            print("\nLogging stopped by user. Processing data...")
            if self.influx_enabled:
                self.client.close()
                print("InfluxDB connection closed.")

            # Run statistics and visualization
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
            print(f"\n[LOG ERROR]: {e}")

# TODO: Selection prompt in CLI - 1. Log New Data 2. View Data 3. Analyze Data 4. Exit
# TODO: Save logged data CSV file as timestamped file