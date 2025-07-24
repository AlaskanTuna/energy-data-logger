# src/services/database.py

import os
import logging
import sqlalchemy
import pandas as pd

from config import config
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# CONSTANTS

ENGINE = create_engine(f"sqlite:///{config.DB_FILE}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)
Base = declarative_base()
log = logging.getLogger(__name__)

# SERVICES

class Setting(Base):
    """ 
    Represents the logger settings in the database.
    """
    __tablename__ = "settings"
    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)

class LoggerState(Base):
    """
    Represents the state of the logger in the database.
    """
    __tablename__ = "logger_state"
    id = Column(Integer, primary_key=True, default=1)
    status = Column(String, nullable=False)
    csvFile = Column(String, nullable=True)
    startTime = Column(DateTime, nullable=True)

# FUNCTIONS

def init_db():
    """
    Initializes the database and creates relevant tables.
    """
    try:
        if not os.path.exists(config.DS_DIR):
            os.makedirs(config.DS_DIR, exist_ok=True)
        Base.metadata.create_all(bind=ENGINE)
        log.info("Database initialized successfully.")
    except Exception as e:
        log.error(f"Database Initialization Error: {e}", exc_info=True)

def archive_csv_to_db(filepath):
    """ 
    Archives CSV data to the database with proper timestamp objects.
    
    @filepath: Path to the CSV file to archive
    """
    if not os.path.exists(filepath):
        log.error(f"DB Archive Error. CSV file not found at {filepath}.")
        return

    try:
        # Read CSV and parse dates
        df = pd.read_csv(filepath, parse_dates=['Timestamp'])
        df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.floor('s')

        # Create table name
        table_name = os.path.splitext(os.path.basename(filepath))[0]
        safe_table_name = "".join(c for c in table_name if c.isalnum() or c == '_')

        # Write to SQL with proper datetime dtype
        df.to_sql(
            safe_table_name, 
            con=ENGINE, 
            if_exists='replace', 
            index=False,
            dtype={'Timestamp': sqlalchemy.types.DateTime()}
        )

        log.info(f"Archived CSV data to table '{safe_table_name}' from {filepath} successfully.")
    except Exception as e:
        log.error(f"DB Archive Error: {e}", exc_info=True)