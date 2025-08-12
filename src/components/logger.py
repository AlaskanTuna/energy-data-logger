# src/components/logger.py

import os
import csv
import time
import logging

from config import config
from services.settings import settings
from services.database import ENGINE
from components.reader import MeterReader
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from sqlalchemy import text

# CONSTANTS

log = logging.getLogger(__name__)

class DataLogger:
    """
    Handles CSV and InfluxDB logging of energy meter readings.
    """
    def __init__(self, filename, table_name, end_time=None, on_failure_callback=None):
        self.ds_dir = config.DS_DIR
        if not os.path.exists(self.ds_dir):
            os.makedirs(self.ds_dir, exist_ok=True)

        self.ds_filename = filename
        self.tb_name = table_name
        self.end_time = end_time
        self.on_failure_callback = on_failure_callback

        # Get active parameters from settings or use default
        self.active_params = settings.get("ACTIVE_LOG_PARAMETERS")
        if not self.active_params:
            self.active_params = list(config.REGISTERS.keys())

        # Create dynamic CSV header
        self.ds_header = ["Timestamp"]
        self.sql_columns = ["Timestamp"]
        
        for p in self.active_params:
            if p in config.REGISTERS:
                desc = config.REGISTERS[p]["description"]
                self.ds_header.append(desc)
                col_name = f'"{desc.replace(" ", "_").replace("(", "").replace(")", "")}"'
                self.sql_columns.append(col_name)

        self.sql_columns.append('"sync_status"')

        # If the file is new or empty, write the header row; otherwise, leave it unchanged
        is_new_file = not os.path.exists(self.ds_filename) or os.path.getsize(self.ds_filename) == 0
        with open(self.ds_filename, 'a', newline='') as file:
            if is_new_file:
                writer = csv.writer(file)
                writer.writerow(self.ds_header)
        log.info(f"Data logging initialized to CSV file '{self.ds_filename}'.")
        log.info(f"SQL logging initialized to database table '{self.tb_name}'.")

        # NOTE: Since the serial port on Pi is enabled, the Modbus port (/dev/serial0) is always available.
        #       Modbus could appear available even without a connection to the meter.
        #       To truly ensure Modbus availability, we attempt to test polling the meter.

        self.reader = None
        try:
            self.reader = MeterReader(use_modbus_flag=config.USE_MODBUS)
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
        if not (config.INFLUXDB_URL and config.INFLUXDB_TOKEN):
            log.info("InfluxDB config not provided. Continuing with CSV logging only.")
            return

        try:
            self.client = InfluxDBClient(
                url=config.INFLUXDB_URL,
                token=config.INFLUXDB_TOKEN,
                org=config.INFLUXDB_ORG,
                timeout=config.INFLUXDB_TIMEOUT
            )

            # Verify connection with ping
            if self.client.ping():
                self.write_api = self.client.write_api(
                    write_options=SYNCHRONOUS,
                    timeout=config.INFLUXDB_TIMEOUT
                )
                self.influx_enabled = True
                log.info(f"InfluxDB ping successful. Ready to log.")
            else:
                log.error("InfluxDB ping failed. Please check token and organization settings.")
        except Exception as e:
            log.error(f"InfluxDB Connection Error: {e}", exc_info=True)
            log.warning("Could not connect to InfluxDB. Continuing with CSV logging only.")
            self.client = None

    def log(self):
        """
        Simultaneously log meter readings to CSV and InfluxDB.
        """
        try:
            while self._running and (self.end_time is None or datetime.now() < self.end_time):
                readings = self.reader.get_meter_readings(active_parameters=self.active_params)
                if not readings:
                    log.error("Data Logger Error: Could not retrieve readings after max retries. Shutting down logger.")
                    if self.on_failure_callback:
                        self.on_failure_callback()
                    self.stop()
                    return

                timestamp = datetime.now()
                self.latest = {"ts": timestamp, **readings}
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

                # CSV WRITING
                csv_status = "FAIL"
                try:
                    row_data = [timestamp_str] + [readings.get(key) for key in self.active_params]
                    with open(self.ds_filename, 'a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(row_data)
                    csv_status = "OK"
                except Exception as e:
                    log.error(f"CSV Write Error: {e}", exc_info=True)

                # INFLUXDB WRITING
                influx_status = "FAIL" if (config.INFLUXDB_URL and config.INFLUXDB_TOKEN) else "-"
                if self.influx_enabled:
                    try:
                        point = Point("meter_measurements").tag("source", "wago_meter")
                        for key, value in readings.items():
                            if value is not None:
                                point.field(key, value)
                        point.time(datetime.now(tz=timezone.utc), WritePrecision.S)
                        self.write_api.write(bucket=config.INFLUXDB_BUCKET, record=point)
                        influx_status = "OK"
                    except Exception as e:
                        log.error(f"InfluxDB Write Error: {e}", exc_info=True)
                        influx_status = "FAIL"

                # SQLITE WRITING
                sqlite_status = "FAIL"
                try:
                    sql_values = [timestamp] + [readings.get(key) for key in self.active_params]
                    sql_values.append('pending')
                    
                    # Construct SQL statement
                    columns_str = ", ".join(self.sql_columns)
                    placeholders = ", ".join([f":param_{i}" for i in range(len(sql_values))])
                    stmt = text(f'INSERT INTO "{self.tb_name}" ({columns_str}) VALUES ({placeholders})')
                    params_dict = {f"param_{i}": val for i, val in enumerate(sql_values)}

                    with ENGINE.connect() as connection:
                        with connection.begin():
                            connection.execute(stmt, params_dict)
                    sqlite_status = "OK"
                except Exception as e:
                    log.error(f"SQLite Write Error: {e}", exc_info=True)

                log.info(f"Data logged successfully! | CSV: {csv_status} | InfluxDB: {influx_status} | SQLite: {sqlite_status} |")
                time.sleep(settings.get("LOG_INTERVAL"))
        except KeyboardInterrupt:
            log.info("Data logging stopped by user.")
        finally:
            self.stop()

    def start(self):
        """ 
        Starts the data logging procecss.
        """
        from util import clear_screen
        try:
            print("\n===== Energy Data Logger: Started Execution =====\n")
            self.log()
            print("\n===== Energy Data Logger: Finished Execution =====")
            input("\nPress Enter to continue...")
            clear_screen()
        except Exception as e:
            log.error(f"Log Error: {e}", exc_info=True)

    def stop(self):
        """ 
        Stops the data logging process.
        """
        self._running = False
        if self.influx_enabled and self.client:
            self.client.close()
            log.info("InfluxDB connection closed.")