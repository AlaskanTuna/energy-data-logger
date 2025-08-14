# src/services/database.py

import os
import logging
import sqlalchemy
import pandas as pd

from config import config
from sqlalchemy import create_engine, Table, MetaData, Column, Integer, Float, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# GLOBAL VARIABLES

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
    tableName = Column(String, nullable=True)
    startTime = Column(DateTime, nullable=True)
    endTime = Column(DateTime, nullable=True)
    mode = Column(String, nullable=True)

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

def create_log_table(table_name):
    """ 
    Creates a data log table in the database.

    @table_name: The name of the table
    """
    try:
        metadata = MetaData()
        columns = [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('Timestamp', DateTime, nullable=False),
        ]

        # Iterate parameters to create SQL columns
        for param_name, params in config.REGISTERS.items():
            col_name = params["description"].replace(' ', '_').replace('(', '').replace(')', '')
            columns.append(Column(col_name, Float, nullable=True))

        # Add sync status column
        columns.append(Column('sync_status', String, nullable=False, default='pending'))
        log_table = Table(table_name, metadata, *columns)

        metadata.create_all(ENGINE)
        log.info(f"Successfully created log table '{table_name}' in database.")
        return True
    except Exception as e:
        log.error(f"SQL Creation Error: Failed to create log table '{table_name}' in database: {e}", exc_info=True)
        return False