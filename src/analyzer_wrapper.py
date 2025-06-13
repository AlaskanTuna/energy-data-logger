# src/analyzer_wrapper.py

import os
import sys
import pandas as pd

from analyzer import DataAnalyzer
from io import StringIO
from util import get_current_filename

class AnalyzerService:
    """
    Wrapper around DataAnalyzer.
    Exposes analyze/visualize helpers for the web layer.
    """
    VISUALIZATION_TYPES = {
        '1': {'name': 'Voltage Comparison', 'filter': 'Voltage'},
        '2': {'name': 'Current Comparison', 'filter': 'Current'},
        '3': {'name': 'Power Analysis', 'columns': ['Total Active Power (kW)', 'Power Factor']},
        '4': {'name': 'Energy Consumption', 'filter': 'Energy'},
        '5': {'name': 'Phase Balance', 'columns': [
            'Voltage L1 (V)', 'Voltage L2 (V)', 'Voltage L3 (V)',
            'Current L1 (A)', 'Current L2 (A)', 'Current L3 (A)'
        ]},
        '6': {'name': 'Power Quality', 'columns': ['Power Factor', 'Total Reactive Power (kvar)']},
        '7': {'name': 'Custom Selection', 'columns': []},
        '8': {'name': 'All Parameters', 'columns': []}
    }

    def __init__(self):
        self._analyzer = DataAnalyzer()
        self._cache = {} # Cache to store analysis results

    def analyze_file(self, filename):
        """
        Analyze a file and return the statistics.
        
        @filename: CSV file to analyze
        @return: Dictionary with analysis text and status
        """
        # Check cache first
        cache_key = f"stats_{filename}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        filename = os.path.basename(filename)
        filepath = os.path.join("../data/", filename)

        if not os.path.exists(filepath):
            return {"error": "File not found"}

        try:
            old_stdout = sys.stdout
            captured_output = StringIO()
            sys.stdout = captured_output

            # Use existing analyzer to calculate statistics
            df = self._analyzer.calculate_statistics(filepath)

            # Restore stdout
            sys.stdout = old_stdout
            analysis_text = captured_output.getvalue()

            # Cache and return the result (without visualization options)
            result = {
                "filename": filename,
                "analysis_text": analysis_text
            }
            self._cache[cache_key] = result
            return result
        except Exception as e:
            if sys.stdout != old_stdout:
                sys.stdout = old_stdout
            return {"error": str(e)}

    def visualize_file(self, filename, plot_type, custom_columns=None):
        """
        Generate visualizations for a file and return paths for web display.
        
        @filename: CSV file to visualize.
        @plot_type: Type of visualization.
        @custom_columns: List of column names for custom visualization.
        @return: Dictionary with plot paths.
        """
        try:
            filename = os.path.basename(filename)
            filepath = os.path.join("../data/", filename)

            if not os.path.exists(filepath):
                return {"error": "File not found"}

            # Load the data
            df = pd.read_csv(filepath)

            # Convert timestamp to datetime if present
            if 'Timestamp' in df.columns:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                
            # Determine which columns to plot based on visualization type
            if plot_type == "custom" and custom_columns:
                title = "Custom Selection"
                columns = custom_columns
            elif plot_type in self.VISUALIZATION_TYPES:
                viz_config = self.VISUALIZATION_TYPES[plot_type]
                title = viz_config['name']
                
                if 'columns' in viz_config and viz_config['columns']:
                    columns = [col for col in viz_config['columns'] if col in df.columns]
                elif 'filter' in viz_config:
                    columns = [col for col in df.columns if viz_config['filter'] in col]
                else:
                    columns = [col for col in df.columns if col != 'Timestamp']
            else:
                return {"error": "Invalid visualization type"}

            # Use the source filename directly
            csv_base_name = os.path.splitext(filename)[0]

            # Generate plots using the source filename
            self._analyzer._generate_plot(df, title, columns, filepath)
            safe_suffix = title.replace(' ', '_').lower()
            regular_filename = f"{csv_base_name}_{safe_suffix}.png"
            normalized_filename = f"{csv_base_name}_{safe_suffix}_normalized.png"

            # Return paths for the webapp to use
            return {
                "regular_plot": f"/plots/{regular_filename}",
                "normalized_plot": f"/plots/{normalized_filename}"
            }

        except Exception as e:
            print(f"Error in visualization: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {"error": str(e)}

    def get_columns(self, filename):
        """
        Get available columns from a file for custom visualization.
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
            return {"error": str(e)}

# Global instance for the web layer
analyzer_service = AnalyzerService()