# src/services/remote_syncer.py

import logging
import socket
import psycopg2

from config import config
from services.database import ENGINE
from sqlalchemy import text

# CONSTANTS

log = logging.getLogger(__name__)

# SERVICES

class RemoteDBSyncer:
    """
    Handles the synchronization of local SQLite data from multiple log tables
    into a single remote PostgreSQL table.
    """
    def __init__(self):
        self.remote_db_config = config.REMOTE_DB_CONFIG
        self.remote_table_name = config.REMOTE_DB_TABLE
        self.batch_size = 100 # Number of rows to sync per cycle

    def _check_internet(self):
        """
        Checks for active Internet connection.
        """
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            log.info("Internet connection detected. Preparing sync cycle.")
            return True
        except OSError:
            log.info("Internet connection not detected. Skipping sync cycle.")
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

    def run_sync_cycle(self):
        """
        Executes a single synchronization cycle.
        """
        if not config.REMOTE_DB_ENABLED:
            log.info("Remote database sync is disabled. Skipping sync cycle.")
            return

        if not self._check_internet():
            return

        target_table = self._get_target_table()
        if not target_table:
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
            cursor = remote_conn.cursor()

            for row in rows_to_sync:
                # Get the data from the local row excluding internal metadata
                row_data = dict(row)
                row_id = row_data.pop('id')
                row_data.pop('sync_status', None)

                # Prepare the INSERT statement
                columns_to_insert = row_data.keys()
                values_to_insert = [row_data[col] for col in columns_to_insert]
                
                # Build the INSERT statement
                column_names_str = ", ".join(f'"{c}"' for c in columns_to_insert)
                value_placeholders_str = ", ".join(["%s"] * len(values_to_insert))
                insert_stmt = f'INSERT INTO "{self.remote_table_name}" ({column_names_str}) VALUES ({value_placeholders_str})'

                try:
                    cursor.execute(insert_stmt, values_to_insert)
                    successful_ids.append(row_id)
                except Exception as e:
                    log.error(f"Remote Sync Error: Failed to insert row ID {row_id} from '{target_table}': {e}")

            # Commit the entire batch transaction to the remote DB.
            remote_conn.commit()
            cursor.close()

        except Exception as e:
            log.error(f"Remote Sync Error: {e}", exc_info=True)
        finally:
            if remote_conn:
                remote_conn.close()

        if successful_ids:
            with ENGINE.connect() as local_conn:
                with local_conn.begin():
                    update_stmt = text(f'UPDATE "{target_table}" SET sync_status = :status WHERE id IN :ids')
                    local_conn.execute(update_stmt, {"status": "synced", "ids": tuple(successful_ids)})
            log.info(f"Successfully synced and updated {len(successful_ids)} rows from table '{target_table}'.")

# GLOBAL INSTANCE

remote_syncer_service = RemoteDBSyncer()