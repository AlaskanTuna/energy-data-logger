# src/statistics.py

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from config import (
    PL_FILEPATH,
    PL_FILENAME
)

class DataAnalyzer:
    """
    Computes statistics and generates plots for the logged CSV data.
    """
    def __init__(self):
        """
        Initialize the DataAnalyzer.
        """
        # Initialize plot directory
        self.plot_dir = PL_FILEPATH
        if not os.path.exists(self.plot_dir):
            try:
                os.makedirs(self.plot_dir)
            except Exception as e:
                print(f"[DIRECTORY CREATION ERROR]: {e}")

    def calculate_statistics(self, filepath):
        """
        Compute min/max/mean/median/std for each column, organized by parameter groups.

        @filepath: Path to the CSV file containing logged data.
        """
        try:
            df = pd.read_csv(filepath)

            # Define parameter groups for better organization
            param_groups = {
                "Voltage Parameters": [col for col in df.columns if "Voltage" in col],
                "Current Parameters": [col for col in df.columns if "Current" in col],
                "Power Parameters": [col for col in df.columns if "Power" in col or "Factor" in col],
                "Energy Parameters": [col for col in df.columns if "Energy" in col]
            }

            print("\n===== Power Meter Statistics =====")

            # Process each parameter group
            for group_name, columns in param_groups.items():
                print(f"\n{group_name}:")

                # Get system-wide averages where applicable
                if "Voltage" in group_name or "Current" in group_name:
                    group_cols = [c for c in columns if any(f"L{i}" in c for i in range(1, 4))]
                    if group_cols:
                        system_avg = df[group_cols].mean(axis=1).mean()
                        system_min = df[group_cols].mean(axis=1).min()
                        system_max = df[group_cols].mean(axis=1).max()
                        print(f"  System Average: {system_avg:.2f}")
                        print(f"  System Min: {system_min:.2f}")
                        print(f"  System Max: {system_max:.2f}")

                        # Calculate phase imbalance (max deviation from average)
                        if len(group_cols) > 1:
                            imbalance_pct = ((df[group_cols].max(axis=1) - df[group_cols].min(axis=1)) / 
                                            df[group_cols].mean(axis=1) * 100).mean()
                            print(f"  Average Phase Imbalance: {imbalance_pct:.2f}%")

                # Calculate stats for each column in this group
                for column in columns:
                    print(f"\n  {column}:")
                    stats = {
                        'min': df[column].min(),
                        'max': df[column].max(),
                        'mean': df[column].mean(),
                        'median': df[column].median(),
                        'std': df[column].std()
                    }

                    for stat_name, stat_value in stats.items():
                        print(f"    {stat_name}: {stat_value:.2f}")

            # Calculate energy consumption rate (kWh per hour)
            if len(df) > 1 and 'Timestamp' in df.columns and any('Energy' in col for col in df.columns):
                try:
                    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                    total_hours = (df['Timestamp'].max() - df['Timestamp'].min()).total_seconds() / 3600
                    
                    if 'Total Active Energy (kWh)' in df.columns and total_hours > 0:
                        energy_rate = (df['Total Active Energy (kWh)'].max() - df['Total Active Energy (kWh)'].min()) / total_hours
                        print(f"\nEnergy Consumption Rate: {energy_rate:.3f} kWh/hour")
                except:
                    pass

            return df
        except Exception as e:
            print(f"[STATISTICS ERROR]: {e}")
            return None

    def visualize_data(self, df):
        """
        Interactive visualization with CLI-based parameter selection.

        @df: DataFrame containing the logged data.
        """
        if df is None or len(df) < 2:
            print("\nNot enough data for visualization.")
            return

        try:
            # Convert timestamp to datetime
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            
            # Define visualization categories
            categories = {
                '1': {'name': 'Voltage Comparison', 'columns': [col for col in df.columns if 'Voltage' in col]},
                '2': {'name': 'Current Comparison', 'columns': [col for col in df.columns if 'Current' in col]},
                '3': {'name': 'Power Analysis', 'columns': ['Total Active Power (kW)', 'Power Factor']},
                '4': {'name': 'Energy Consumption', 'columns': [col for col in df.columns if 'Energy' in col]},
                '5': {'name': 'Phase Balance', 'columns': [
                    'Voltage L1 (V)', 'Voltage L2 (V)', 'Voltage L3 (V)',
                    'Current L1 (A)', 'Current L2 (A)', 'Current L3 (A)'
                    ]},
                '6': {'name': 'Power Quality', 'columns': ['Power Factor', 'Total Reactive Power (kvar)']},
                '7': {'name': 'Custom Selection', 'columns': []},
                '8': {'name': 'All Parameters', 'columns': []},
                '0': {'name': 'Exit', 'columns': []}
            }

            # Menu loop
            while True:
                # Display menu
                print("\nSelect visualization to generate:")
                for key, value in categories.items():
                    print(f"{key}. {value['name']}")
                choice = input("\nEnter your choice: ").strip()

                if choice in categories:
                    if choice == '0':
                        print("Exiting visualization menu.")
                        return
                    if choice == '7':
                        # Custom selection
                        all_columns = [col for col in df.columns if col != 'Timestamp']
                        print("\nAvailable parameters:")
                        for i, col in enumerate(all_columns, 1):
                            print(f"{i}. {col}")
                        
                        selection = input("\nEnter parameter numbers separated by commas: ")
                        selected_indices = [int(idx.strip()) - 1 for idx in selection.split(',') if idx.strip().isdigit()]
                        selected_columns = [all_columns[idx] for idx in selected_indices if 0 <= idx < len(all_columns)]
                        
                        if selected_columns:
                            self._generate_plot(df, "Custom Selection", selected_columns)
                            return
                        else:
                            print("No valid parameters selected.")
                            return
                    elif choice == '8':
                        all_columns = [col for col in df.columns if col != 'Timestamp']
                        self._generate_plot(df, "All Parameters", all_columns)
                        return
                    else:
                        # Generate selected visualization
                        category = categories[choice]
                        self._generate_plot(df, category['name'], category['columns'])
                        return
                else:
                    print("Invalid choice. Please select a valid option.")
        except Exception as e:
            print(f"[PLOTTING ERROR]: {e}")

    def _generate_plot(self, df, title, columns):
        """
        Helper method to generate and save a plot with the specified columns.
        """
        if not columns:
            print(f"No data columns available for {title}")
            return

        base_filename = os.path.basename(PL_FILENAME)
        base_filename = os.path.splitext(base_filename)[0]

        plt.figure(figsize=(12, 8))

        # Plot each column
        for column in columns:
            if column in df.columns:
                plt.plot(df['Timestamp'], df[column], marker='o', markersize=3, linewidth=1.5, label=column)
        
        plt.title(f"{title} - Time Series")
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Create safe suffix from title
        safe_suffix = title.replace(' ', '_').lower()
        
        # Create full filename with timestamp prefix
        filename = os.path.join(PL_FILEPATH, f"{base_filename}_{safe_suffix}.png")
        plt.savefig(filename)
        print(f"Plot saved as: {filename}")
        
        # Create normalized version for comparison
        if len(columns) > 1:
            plt.figure(figsize=(12, 8))
            for column in columns:
                if column in df.columns:
                    series = df[column]
                    if series.max() > series.min():  # Avoid division by zero
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
            norm_filename = os.path.join(PL_FILEPATH, f"{base_filename}_{safe_suffix}_normalized.png")
            plt.savefig(norm_filename)
            print(f"Normalized plot saved as: {norm_filename}")