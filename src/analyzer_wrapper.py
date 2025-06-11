# src/analyzer_wrapper.py

import os
import sys
import pandas as pd

from analyzer import DataAnalyzer
from io import StringIO
from util import get_current_filename

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

class AnalyzerService:
    """
    Wrapper around DataAnalyzer.
    Exposes analyze/visualize helpers for the web layer.
    """
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

# Global instance for the web layer
analyzer_service = AnalyzerService()