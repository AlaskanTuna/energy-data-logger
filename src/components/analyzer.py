# src/components/analyzer.py

import os
import pandas as pd
import logging
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from config import config

# GLOBAL VARIABLES

log = logging.getLogger(__name__)
EXCLUDE_COLUMNS = ["id", "sync_status"]

class DataAnalyzer:
    """
    Computes statistics and generates plots for the logged CSV data.
    """
    def __init__(self):
        self.plot_dir = config.PL_DIR
        os.makedirs(self.plot_dir, exist_ok=True)

    # DATA ANALYSIS

    def calculate_statistics(self, df, description_to_group_map):
        """
        Compute statistics for the given DataFrame.
        
        @df: DataFrame to analyze
        @description_to_group_map: Dictionary mapping column names to relevant groups
        @return: DataFrame with statistics or None if error
        """
        try:
            param_groups = {}
            analysis_columns = [col for col in df.columns if col not in EXCLUDE_COLUMNS + ["Timestamp"]]
            for column in analysis_columns:
                if column == "Timestamp":
                    continue
                group = description_to_group_map.get(column, "Parameter Readings Summary")
                if group not in param_groups:
                    param_groups[group] = []
                param_groups[group].append(column)

            print("\n===== Power Meter Statistics =====")
            if df.empty:
                print("No data available for the selected time range.")
                return df

            for group_name, columns in param_groups.items():
                if not columns: 
                    print(f"\n{group_name}: Not enough data for statistics calculation.")
                    continue

                print(f"\n{group_name}:")
                for column in columns:
                    if column in df.columns:
                        unit = ""
                        if '(' in column and ')' in column:
                            unit = column.split('(')[-1].split(')')[0]
                        print(f"\n  {column}:")
                        stats = df[column].describe()
                        print(f"    min:    {stats.get('min', 0):.2f} {unit}")
                        print(f"    max:    {stats.get('max', 0):.2f} {unit}")
                        print(f"    mean:   {stats.get('mean', 0):.2f} {unit}")
                        print(f"    std:    {stats.get('std', 0):.2f} {unit}")

            return df
        except Exception as e:
            log.error(f"Statistics Error: {e}", exc_info=True)
            return None

    def calculate_session_consumption(self, df):
        """ 
        Compute total consumption for cumulative columns from a DataFrame.
        
        @df: DataFrame to analyze
        @return: Dictionary with total consumption or None if error
        """
        try:
            consumption_results = {}
            columns = [col for col in df.columns if "total" in col.lower()]
            if not columns:
                log.warning("No cumulative columns found for consumption calculation.")
                return {}
            
            if df.empty:
                print("\nNo data available for consumption calculation in the selected time range.")
                return {}

            print("\n===== Session Consumption Analysis =====\n")
            for column in columns:
                series = df[column].dropna()
                if len(series) < 2:
                    print(f"  {column}: Not enough data for consumption calculation.")
                    continue

                first_val = series.iloc[0]
                last_val = series.iloc[-1]

                if last_val < first_val:
                    # Meter rollover calculation
                    consumption = (config.MAX_METER_VALUE - first_val) + last_val
                else:
                    # Normal calculation
                    consumption = last_val - first_val

                # Extract the unit from the column name
                unit = ""
                if '(' in column and ')' in column:
                    unit = column.split('(')[-1].split(')')[0]
                print(f"  {column}: {consumption:.3f} {unit}")
                consumption_results[column] = consumption

            return consumption_results
        except Exception as e:
            log.error(f"Consumption Analysis Error: {e}", exc_info=True)
            return None

    # TIME SERIES PLOTTING

    def visualize_data(self, df, source=None):
        """
        Interactive CLI visualization.
        
        @df: DataFrame containing the logged data
        @source: Optional source filename for generating plots
        """
        if df is None or len(df) < 2:
            log.warning("Not enough data for visualization.")
            return

        if 'Timestamp' not in df.columns:
            log.error("Plot Error: Timestamp column not found. Cannot create time-series plots.")
            return
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        available_cols = [col for col in df.columns if col not in EXCLUDE_COLUMNS + ["Timestamp"]]

        categories = {
            '0': {'name': 'Exit', 'columns': []},
            '1': {'name': 'Voltage', 'columns': [c for c in available_cols if 'Voltage' in c]},
            '2': {'name': 'Current', 'columns': [c for c in available_cols if 'Current' in c]},
            '3': {'name': 'Active Power', 'columns': [c for c in available_cols if 'Active Power' in c]},
            '4': {'name': 'Reactive Power', 'columns': [c for c in available_cols if 'Reactive Power' in c]},
            '5': {'name': 'Apparent Power', 'columns': [c for c in available_cols if 'Apparent Power' in c]},
            '6': {'name': 'Energy', 'columns': [c for c in available_cols if "Energy" in c and 
                                                not ((c.startswith("T") and c[1].isdigit()) or 
                                                    c.startswith("Import") or 
                                                    c.startswith("Export"))]},
            '7': {'name': 'Energy Tariff', 'columns': [c for c in available_cols if "Energy" in c and 
                                                    ((c.startswith("T") and c[1].isdigit()) or 
                                                    c.startswith("Import") or 
                                                    c.startswith("Export"))]},
            '8': {'name': 'Power Factor', 'columns': [c for c in available_cols if 'Power Factor' in c]},
            '9': {'name': 'Custom Selection', 'columns': []},
            '10': {'name': 'All Parameters', 'columns': available_cols},
        }

        while True:
            print("\nSelect visualization to generate:")
            for key, value in categories.items():
                if value.get('columns') or key in ['0', '10']:
                    print(f"{key}. {value['name']}")
            choice = input("\nEnter your choice: ").strip()

            if choice == '0':
                print("Exiting visualization menu.")
                return
            elif choice == '9':
                all_columns = [col for col in df.columns if col != 'Timestamp']
                print("\nAvailable parameters:")
                for i, col in enumerate(all_columns, 1):
                    print(f"{i}. {col}")

                selection = input("\nEnter parameter numbers separated by commas: ")
                selected_indices = [int(idx.strip()) - 1 for idx in selection.split(',') if idx.strip().isdigit()]
                selected_columns = [all_columns[idx] for idx in selected_indices if 0 <= idx < len(all_columns)]

                if selected_columns:
                    self._generate_plot(df, "Custom Selection", selected_columns, source)
                    return
                else:
                    log.warning("No valid parameters selected.")
                return
            elif choice in categories and categories[choice]['columns']:
                self._generate_plot(df, categories[choice]['name'], categories[choice]['columns'], source)
                return
            else:
                log.warning("Invalid choice or no data available for that option.")

    def _generate_plot(self, df, title, columns_to_plot, source=None):
        """
        Helper method to generate and save a plot.
        
        @df: DataFrame containing the logged data
        @title: Title for the plot
        @columns_to_plot: List of columns to include in the plot
        @source: Optional source filename for generating plots
        """
        columns = [col for col in columns_to_plot if col in df.columns]

        if not columns:
            log.warning(f"None of the requested columns for '{title}' plot exist in the data. Skipping plot.")
            return

        base_filename = "visualization"
        if source and os.path.isfile(source):
            base_filename = os.path.splitext(os.path.basename(source))[0]

        # Create standard version of the plot
        plt.figure(figsize=(12, 8))
        for column in columns:
            plt.plot(df['Timestamp'], df[column], marker='o', markersize=3, linewidth=1.5, label=column)
        
        plt.title(f"{title} - Time Series")
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Create standard plot filename
        safe_suffix = title.replace(' ', '_').lower()
        filename = os.path.join(config.PL_DIR, f"{base_filename}_{safe_suffix}.png")
        plt.savefig(filename)
        plt.close()
        log.info(f"Plot saved as: '{filename}'.")

        # Create normalized version of the plot for comparison
        if len(columns) > 1:
            plt.figure(figsize=(12, 8))
            for column in columns:
                if column in df.columns:
                    series = df[column]
                    if series.max() > series.min():
                        normalized = (series - series.min()) / (series.max() - series.min())
                        plt.plot(df['Timestamp'], normalized, marker='.', markersize=4, label=column)

            plt.title(f"{title} - Normalized Comparison")
            plt.xlabel('Time')
            plt.ylabel('Normalized Value (0-1)')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Create normalized plot filename
            norm_filename = os.path.join(config.PL_DIR, f"{base_filename}_{safe_suffix}_normalized.png")
            plt.savefig(norm_filename)
            plt.close()
            log.info(f"Normalized plot saved as: '{norm_filename}'.")