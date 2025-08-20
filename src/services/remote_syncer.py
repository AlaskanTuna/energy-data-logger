# src/services/remote_syncer.py

import logging
import socket
import psycopg2
import threading
import time

from config import config
from components.database import ENGINE
from sqlalchemy import text, bindparam
from datetime import datetime

# GLOBAL VARIABLES

log = logging.getLogger(__name__)

# SERVICES

class RemoteDBSyncer:
    """
    Handles synchronization of local database tables with a remote database.
    """
    def __init__(self):
        self.remote_db_config = config.REMOTE_DB_CONFIG
        self.remote_table_name = config.REMOTE_DB_TABLE
        self.batch_size = config.SYNC_BATCH_SIZE
        self._thread = None
        self._status = "idle"
        self._stop_event = threading.Event()

    def _run(self):
        """ 
        The main loop for the background thread. 
        """
        log.info("RemoteDBSyncer thread has started.")
        while not self._stop_event.is_set():
            try:
                self.run_sync_cycle()
            except Exception as e:
                log.error(f"RemoteDBSyncer Thread Error: {e}", exc_info=True)
            self._stop_event.wait(config.SYNC_INTERVAL)
        log.info("RemoteDBSyncer thread has stopped.")

    def start(self):
        """ 
        Starts the background thread. 
        """
        if self._thread is not None and self._thread.is_alive():
            log.warning("RemoteDBSyncer thread is already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """ 
        Signals the background thread to stop. 
        """
        if self._thread is None or not self._thread.is_alive():
            log.info("RemoteDBSyncer thread is not running.")
            return

        self._stop_event.set()
        self._thread.join(timeout=5)
        if self._thread.is_alive():
            log.warning("RemoteDBSyncer thread did not stop in time.")
        self._thread = None

    def _check_internet(self):
        """
        Checks for active Internet connection.
        """
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            log.info("Internet disconnected. Skipping sync cycle.")
            return False

    def _get_target_table(self):
        """
        Finds tables with pending rows to sync.
        """
        with ENGINE.connect() as connection:
            statement = text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '20%' ORDER BY name ASC")
            result = connection.execute(statement)
            sorted_tables = [row[0] for row in result]

            for table_name in sorted_tables:
                check_statement = text(f'SELECT id FROM "{table_name}" WHERE sync_status = :status LIMIT 1')
                pending_row = connection.execute(check_statement, {"status": "pending"}).first()
                if pending_row:
                    log.info(f"Found pending work at '{table_name}' to sync.")
                    return table_name

        log.info("No pending work found in any table to sync.")
        return None

    def _get_status(self):
        return self._status

    def run_sync_cycle(self):
        """
        Executes a single synchronization cycle.
        """
        if not config.REMOTE_DB_ENABLED:
            return

        if self._check_internet():
            self._status = "active"
        else:
            self._status = "idle"
            return

        target_table = self._get_target_table()
        if not target_table:
            self._status = "idle"
            return

        rows_to_sync = []
        with ENGINE.connect() as local_conn:
            select_statement = text(f'SELECT * FROM "{target_table}" WHERE sync_status = :status ORDER BY id ASC LIMIT :limit')
            rows_to_sync = local_conn.execute(select_statement, {"status": "pending", "limit": self.batch_size}).mappings().all()

        if not rows_to_sync:
            return
        log.info(f"Attempting to sync {len(rows_to_sync)} rows from local table '{target_table}'.")

        successful_ids = []
        remote_conn = None
        try:
            remote_conn = psycopg2.connect(**self.remote_db_config)
            for row in rows_to_sync:
                with remote_conn.cursor() as cursor:
                    # Prepare the row data for insertion
                    row_data = dict(row)
                    row_id = row_data.pop('id')
                    row_data.pop('sync_status', None)

                    # Prepare the columns and values for insertion
                    columns_to_insert = row_data.keys()
                    values_to_insert = []
                    for col in columns_to_insert:
                        val = row_data[col]
                        if isinstance(val, datetime):
                            values_to_insert.append(val.strftime('%Y-%m-%d %H:%M:%S'))
                        else:
                            values_to_insert.append(val)

                    # Construct the SQL insert statement
                    column_names_str = ", ".join(f'"{c}"' for c in columns_to_insert)
                    value_placeholders_str = ", ".join(["%s"] * len(values_to_insert))
                    insert_statement = (
                        f'INSERT INTO "{self.remote_table_name}" ({column_names_str}) '
                        f'VALUES ({value_placeholders_str}) '
                        f'ON CONFLICT ("Timestamp") DO NOTHING'
                    )

                    try:
                        cursor.execute(insert_statement, values_to_insert)
                        remote_conn.commit()
                        successful_ids.append(row_id)
                    except Exception as e:
                        log.error(f"Remote Sync Error: Failed to insert row ID {row_id} from '{target_table}'. Skipping row. Error: {e}")
                        remote_conn.rollback()
        except Exception as e:
            log.error(f"Remote Sync Connection Error: {e}", exc_info=True)
        finally:
            if remote_conn:
                remote_conn.close()
            self._status = "idle"

        if successful_ids:
            try:
                with ENGINE.connect() as local_conn:
                    with local_conn.begin():
                        update_statement = text(f'UPDATE "{target_table}" SET sync_status = :status WHERE id IN :ids').bindparams(
                            bindparam('ids', expanding=True)
                        )
                        local_conn.execute(update_statement, {"status": "synced", "ids": tuple(successful_ids)})
                log.info(f"Synced and updated {len(successful_ids)} rows from table '{target_table}' successfully.")
            except Exception as e:
                log.error(f"Failed to update local sync status for table '{target_table}': {e}", exc_info=True)

# GLOBAL INSTANCE
remote_syncer_service = RemoteDBSyncer()