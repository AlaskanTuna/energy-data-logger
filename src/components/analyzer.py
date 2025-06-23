# src/components/analyzer.py

import os
import pandas as pd
import logging
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from config import config

# CONSTANTS

log = logging.getLogger(__name__)

class DataAnalyzer:
    """
    Computes statistics and generates plots for the logged CSV data.
    """
    def __init__(self):
        self.plot_dir = config.PL_DIR
        os.makedirs(self.plot_dir, exist_ok=True)

    def calculate_statistics(self, filepath):
        """
        Compute statistics for each column, organized by parameter groups.
        """
        try:
            df = pd.read_csv(filepath)

            param_groups = {
                "Voltage Parameters": [col for col in df.columns if "Voltage" in col],
                "Current Parameters": [col for col in df.columns if "Current" in col],
                "Power Parameters":   [col for col in df.columns if "Power" in col],
                "Energy Parameters":  [col for col in df.columns if "Energy" in col],
            }

            print("\n===== Power Meter Statistics =====")
            for group_name, columns in param_groups.items():
                if not columns: continue

                print(f"\n{group_name}:")
                for column in columns:
                    if column in df.columns:
                        print(f"\n  {column}:")
                        stats = df[column].describe()
                        print(f"    min:    {stats.get('min', 0):.2f}")
                        print(f"    max:    {stats.get('max', 0):.2f}")
                        print(f"    mean:   {stats.get('mean', 0):.2f}")
                        print(f"    std:    {stats.get('std', 0):.2f}")

            return df
        except Exception as e:
            log.error(f"Statistics Error: {e}", exc_info=True)
            return None

    def visualize_data(self, df, source=None):
        """
        Interactive CLI visualization.
        
        @df: DataFrame containing the logged data.
        @source: Optional source filename for generating plots.
        """
        if df is None or len(df) < 2:
            log.warning("Not enough data for visualization.")
            return

        if 'Timestamp' not in df.columns:
            log.error("Plot Error: Timestamp column not found. Cannot create time-series plots.")
            return
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        available_cols = [col for col in df.columns if col != 'Timestamp']

        categories = {
            '1': {'name': 'Voltage Comparison', 'columns': [c for c in available_cols if 'Voltage' in c]},
            '2': {'name': 'Current Comparison', 'columns': [c for c in available_cols if 'Current' in c]},
            '3': {'name': 'Power Analysis', 'columns': [c for c in available_cols if 'Power' in c]},
            '4': {'name': 'Energy Consumption', 'columns': [c for c in available_cols if 'Energy' in c]},
            '5': {'name': 'Custom Selection', 'columns': []},
            '6': {'name': 'All Parameters', 'columns': available_cols},
            '0': {'name': 'Exit', 'columns': []}
        }

        while True:
            print("\nSelect visualization to generate:")
            for key, value in categories.items():
                if value.get('columns') or key in ['5', '0']:
                    print(f"{key}. {value['name']}")
            choice = input("\nEnter your choice: ").strip()

            if choice == '0':
                print("Exiting visualization menu.")
                return
            elif choice == '5':
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
        log.info(f"Plot saved as: {filename}")

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
            log.info(f"Normalized plot saved as: {norm_filename}")