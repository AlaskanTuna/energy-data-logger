# src/services/database.py

import os
import logging

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
    except Exception as e:
        log.error(f"{e}", exc_info=True)