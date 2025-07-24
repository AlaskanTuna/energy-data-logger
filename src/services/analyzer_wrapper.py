# src/services/analyzer_wrapper.py

import os
import sys
import logging
import pandas as pd

from components.analyzer import DataAnalyzer
from services.database import ENGINE
from io import StringIO
from datetime import datetime, timedelta

# CONSTANTS

VISUALIZATION_TYPES = {
    '1': {'name': 'Voltage Comparison', 'filter': 'Voltage'},
    '2': {'name': 'Current Comparison', 'filter': 'Current'},
    '3': {'name': 'Power Analysis', 'filter': 'Power'},
    '4': {'name': 'Energy Consumption', 'filter': 'Energy'},
    '5': {'name': 'All Parameters', 'columns': []}
}
log = logging.getLogger(__name__)

# SERVICES

class AnalyzerService:
    """
    Wrapper around DataAnalyzer. 
    Exposes robust helpers for the web layer.
    """
    def __init__(self):
        self._analyzer = DataAnalyzer()
        self._cache = {}

    def _get_data_from_db(self, filename, start_time=None, end_time=None):
        """ 
        Gets data from the database for a logged data file.
        
        @filename: CSV file to query
        @start_time: Optional start time for filtering
        @end_time: Optional end time for filtering
        @return: DataFrame with queried data
        """
        table_name = os.path.splitext(os.path.basename(filename))[0]
        safe_table_name = "".join(c for c in table_name if c.isalnum() or c == '_')
        query = f'SELECT * FROM "{safe_table_name}"'
        params = {}
        conditions = []

        if start_time:
            conditions.append("Timestamp >= :start")
            params["start"] = datetime.fromisoformat(start_time)
        if end_time:
            end_time_dt = datetime.fromisoformat(end_time)
            stepped_end_time_dt = end_time_dt + timedelta(seconds=1) # Offset by 1s
            conditions.append("Timestamp < :end")
            params["end"] = stepped_end_time_dt
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        try:
            df = pd.read_sql(query, ENGINE, params=params, parse_dates=['Timestamp'])
            return df
        except Exception as e:
            log.error(f"DB Query Error: {e}", exc_info=True)
            return None

    # PUBLIC API

    def analyze_file(self, filename, start_time=None, end_time=None):
        """
        Analyze a file and return the statistics for a given time range.
        
        @filename: CSV file to analyze
        @start_time: Optional start time for the time range (ISO format string)
        @end_time: Optional end time for the time range (ISO format string)
        @return: Dictionary with analysis text and status
        """
        df = self._get_data_from_db(filename, start_time, end_time)

        if df is None:
            return {"error": "Unable to retrieve data from database."}

        try:
            old_stdout = sys.stdout
            captured_output = StringIO()
            sys.stdout = captured_output

            self._analyzer.calculate_statistics(df)
            self._analyzer.calculate_session_consumption(df)

            # Capture the output
            sys.stdout = old_stdout
            analysis_text = captured_output.getvalue()

            result = {
                "filename": filename,
                "analysis_text": analysis_text
            }
            return result
        except Exception as e:
            log.error(f"Analysis Error: {e}", exc_info=True)
            if sys.stdout != old_stdout:
                sys.stdout = old_stdout
            return {"error": "An internal error occurred during analysis."}

    def visualize_file(self, filename, plot_type, custom_columns=None):
        """
        Generates visualizations.
        
        @filename: CSV file to visualize
        @plot_type: Type of visualization to generate
        @custom_columns: List of custom columns for 'custom' plot type
        @return: Dictionary with paths to generated plots
        """
        try:
            filename = os.path.basename(filename)
            filepath = os.path.join("../data/", filename)
            if not os.path.exists(filepath): return {"error": "File not found"}

            df = pd.read_csv(filepath)
            if 'Timestamp' in df.columns:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            
            available_cols = [col for col in df.columns if col != 'Timestamp']
            columns_to_plot = []
            title = "Untitled"

            if plot_type == "custom" and custom_columns:
                title = "Custom Selection"
                columns_to_plot = [col for col in custom_columns if col in available_cols]
            elif plot_type in VISUALIZATION_TYPES:
                viz_config = VISUALIZATION_TYPES[plot_type]
                title = viz_config['name']
                
                if 'filter' in viz_config:
                    columns_to_plot = [col for col in available_cols if viz_config['filter'] in col]
                else:
                    columns_to_plot = available_cols
            else:
                return {"error": "Invalid visualization type"}

            if not columns_to_plot:
                return {"error": f"No data available for the '{title}' plot in this file."}

            self._analyzer._generate_plot(df, title, columns_to_plot, filepath)
            
            csv_base_name = os.path.splitext(filename)[0]
            safe_suffix = title.replace(' ', '_').lower()
            regular_filename = f"{csv_base_name}_{safe_suffix}.png"
            normalized_filename = f"{csv_base_name}_{safe_suffix}_normalized.png"

            return {
                "regular_plot": f"/plots/{regular_filename}",
                "normalized_plot": f"/plots/{normalized_filename}"
            }
        except Exception as e:
            log.error(f"Visualization Error: {e}", exc_info=True)
            return {"error": "An internal error occurred during visualization."}

    def get_columns(self, filename):
        """
        Get available columns from a file for custom visualization.
        
        @filename: CSV file to analyze
        @return: Dictionary with filename and list of columns
        """
        try:
            filename = os.path.basename(filename)
            filepath = os.path.join("../data/", filename)
            
            if not os.path.exists(filepath):
                return {"error": "File not found"}

            # Extract columns from the CSV file
            df = pd.read_csv(filepath, nrows=1)
            columns = [col for col in df.columns if col != 'Timestamp']
            
            return {
                "filename": filename,
                "columns": columns
            }
            
        except Exception as e:
            return {"error": "An internal error occurred during visualization."}

# GLOBAL INSTANCE

analyzer_service = AnalyzerService()