# src/statistics.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from matplotlib.dates import DateFormatter
from config import DS_FILENAME, PLOT1_FILENAME, PLOT2_FILENAME

class DataAnalyzer:
    """
    Computes statistics and generates plots for the logged CSV data.
    """

    def calculate_statistics(self):
        """
        Compute min/max/mean/median/std for each column, print and return the DataFrame.
        """
        try:
            df = pd.read_csv(DS_FILENAME)
            stats = {}
            for column in df.columns[1:]:  # Skip timestamp
                stats[column] = {
                    'min': df[column].min(),
                    'max': df[column].max(),
                    'mean': df[column].mean(),
                    'median': df[column].median(),
                    'std': df[column].std()
                }

            print("\n===== Power Meter Statistics =====")
            for column, values in stats.items():
                print(f"\n{column}:")
                for stat_name, stat_value in values.items():
                    print(f"  {stat_name}: {stat_value:.2f}")

            return df
        except Exception as e:
            print(f"[STATISTICS ERROR]: {e}")
            return None

    def visualize_data(self, df):
        """
        Generate a 2×2 grid showing time-series data.
        Generate a single plot comparing normalized values.
        """
        if df is None or len(df) < 2:
            print("\nNot enough data for visualization.")
            return

        try:
            # Convert timestamp to datetime
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])

            # First figure: 2×2 subplots
            fig, axs = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
            date_format = DateFormatter('%H:%M:%S')

            # Voltage
            axs[0, 0].plot(df['Timestamp'], df['Voltage (V)'], 'b-', linewidth=1.5, marker='o', markersize=3)
            axs[0, 0].set_title('Voltage Over Time')
            axs[0, 0].set_ylabel('Voltage (V)')
            axs[0, 0].grid(True, linestyle='--', alpha=0.7)

            # Current
            axs[0, 1].plot(df['Timestamp'], df['Current (A)'], 'r-', linewidth=1.5, marker='o', markersize=3)
            axs[0, 1].set_title('Current Over Time')
            axs[0, 1].set_ylabel('Current (A)')
            axs[0, 1].grid(True, linestyle='--', alpha=0.7)

            # Total Active Energy
            axs[1, 0].plot(df['Timestamp'], df['Total Active Energy (kWh)'], 'g-', linewidth=1.5, marker='o', markersize=3)
            axs[1, 0].set_title('Total Active Energy Over Time')
            axs[1, 0].set_ylabel('Total Active Energy (kWh)')
            axs[1, 0].set_xlabel('Time')
            axs[1, 0].grid(True, linestyle='--', alpha=0.7)

            # Reactive Power
            axs[1, 1].plot(df['Timestamp'], df['Total Reactive Power (kvar)'], 'm-', linewidth=1.5, marker='o', markersize=3)
            axs[1, 1].set_title('Total Reactive Power Over Time')
            axs[1, 1].set_ylabel('Total Reactive Power (kvar)')
            axs[1, 1].set_xlabel('Time')
            axs[1, 1].grid(True, linestyle='--', alpha=0.7)

            for ax in axs.flat:
                ax.xaxis.set_major_formatter(date_format)

            # Add rolling‐average trend lines if enough data
            if len(df) > 5:
                window = min(5, len(df) // 2)
                axs[0, 0].plot(
                    df['Timestamp'],
                    df['Voltage (V)'].rolling(window=window).mean(),
                    'k--', alpha=0.7, linewidth=1, label='Trend (Rolling Avg)'
                )
                axs[0, 1].plot(
                    df['Timestamp'],
                    df['Current (A)'].rolling(window=window).mean(),
                    'k--', alpha=0.7, linewidth=1, label='Trend (Rolling Avg)'
                )
                axs[1, 0].plot(
                    df['Timestamp'],
                    df['Total Active Energy (kWh)'].rolling(window=window).mean(),
                    'k--', alpha=0.7, linewidth=1, label='Trend (Rolling Avg)'
                )
                axs[1, 1].plot(
                    df['Timestamp'],
                    df['Total Reactive Power (kvar)'].rolling(window=window).mean(),
                    'k--', alpha=0.7, linewidth=1, label='Trend (Rolling Avg)'
                )
                for ax in axs.flat:
                    ax.legend()

            plt.setp(axs[1, 0].get_xticklabels(), rotation=45, ha='right')
            plt.setp(axs[1, 1].get_xticklabels(), rotation=45, ha='right')
            plt.tight_layout()

            fig.savefig(PLOT1_FILENAME)

            # Second figure: normalized comparison
            plt.figure(figsize=(14, 6))
            for column in df.columns[1:]:
                series = df[column]
                normalized = (series - series.min()) / (series.max() - series.min())
                plt.plot(df['Timestamp'], normalized, marker='.', markersize=4, label=column)

            plt.title('Normalized Values Comparison')
            plt.xlabel('Time')
            plt.ylabel('Normalized Value (0–1)')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(PLOT2_FILENAME)

            print("\nVisualization successfully saved as plots.")

        except Exception as e:
            print(f"[PLOTTING ERROR]: {e}.")