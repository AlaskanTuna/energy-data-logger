# THIS IS A MOCK SCRIPT FOR TESTING PURPOSES

import csv
import random
import time
import os
import msvcrt
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Config
DS_FILENAME = "energy_data.csv"
DS_HEADER = ["Timestamp", "Voltage (V)", "Current (A)", "Energy (kW)", "Reactive Power (LVA)"]

# Create new CSV file if it doesn't exist
if not os.path.exists(DS_FILENAME):
    with open(DS_FILENAME, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(DS_HEADER)

# Functions
def meter_reading():
    """
    Simulate electrical signals from a power meter.
    """
    # Generate mock values in realistic ranges
    voltage = round(random.uniform(215, 240), 2)
    current = round(random.uniform(1.5, 15.0), 2)
    energy = round(random.uniform(0.2, 2.5), 3)
    reactive_power = round(random.uniform(0.1, 1.2), 3)
    return voltage, current, energy, reactive_power

def calculate_statistics():
    """
    Calculate statistics based on the logged data.
    """
    df = pd.read_csv(DS_FILENAME)
    
    # Calculate statistics for each column
    stats = {}
    for column in df.columns[1:]:  # Skip timestamp column
        stats[column] = {
            'min': df[column].min(),
            'max': df[column].max(),
            'mean': df[column].mean(),
            'median': df[column].median(),
            'std': df[column].std()
        }
    
    # Print statistics
    print("\n===== Power Meter Statistics =====")
    for column, values in stats.items():
        print(f"\n{column}:")
        for stat_name, stat_value in values.items():
            print(f"  {stat_name}: {stat_value:.2f}")
    
    return df

def visualize_data(df):
    """
    Visualize the logged data with enhanced time series charts.
    """
    # Convert timestamp to datetime for better plotting
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # Create figure with shared x-axis for better time comparison
    fig, axs = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
    
    # Format the date/time display on x-axis
    from matplotlib.dates import DateFormatter
    date_format = DateFormatter('%H:%M:%S')
    
    # Plot voltage with markers and grid
    axs[0, 0].plot(df['Timestamp'], df['Voltage (V)'], 'b-', linewidth=1.5, marker='o', markersize=3)
    axs[0, 0].set_title('Voltage Over Time')
    axs[0, 0].set_ylabel('Voltage (V)')
    axs[0, 0].grid(True, linestyle='--', alpha=0.7)
    
    # Plot current
    axs[0, 1].plot(df['Timestamp'], df['Current (A)'], 'r-', linewidth=1.5, marker='o', markersize=3)
    axs[0, 1].set_title('Current Over Time')
    axs[0, 1].set_ylabel('Current (A)')
    axs[0, 1].grid(True, linestyle='--', alpha=0.7)
    
    # Plot energy
    axs[1, 0].plot(df['Timestamp'], df['Energy (kW)'], 'g-', linewidth=1.5, marker='o', markersize=3)
    axs[1, 0].set_title('Energy Over Time')
    axs[1, 0].set_ylabel('Energy (kW)')
    axs[1, 0].set_xlabel('Time')
    axs[1, 0].grid(True, linestyle='--', alpha=0.7)
    
    # Plot reactive power
    axs[1, 1].plot(df['Timestamp'], df['Reactive Power (LVA)'], 'm-', linewidth=1.5, marker='o', markersize=3)
    axs[1, 1].set_title('Reactive Power Over Time')
    axs[1, 1].set_ylabel('Reactive Power (LVA)')
    axs[1, 1].set_xlabel('Time')
    axs[1, 1].grid(True, linestyle='--', alpha=0.7)
    
    # Apply the formatter to all x-axes
    for ax in axs.flat:
        ax.xaxis.set_major_formatter(date_format)
    
    # Add rolling averages if enough data points
    if len(df) > 5:
        window = min(5, len(df) // 2)  # Use sensible window size
        axs[0, 0].plot(df['Timestamp'], df['Voltage (V)'].rolling(window=window).mean(), 
            'k--', alpha=0.7, linewidth=1, label='Trend (Rolling Avg)')
        axs[0, 1].plot(df['Timestamp'], df['Current (A)'].rolling(window=window).mean(), 
            'k--', alpha=0.7, linewidth=1, label='Trend (Rolling Avg)')
        axs[1, 0].plot(df['Timestamp'], df['Energy (kW)'].rolling(window=window).mean(), 
            'k--', alpha=0.7, linewidth=1, label='Trend (Rolling Avg)')
        axs[1, 1].plot(df['Timestamp'], df['Reactive Power (LVA)'].rolling(window=window).mean(), 
            'k--', alpha=0.7, linewidth=1, label='Trend (Rolling Avg)')
        
        # Add legends
        for ax in axs.flat:
            ax.legend()
    
    # Rotate x-axis labels
    plt.setp(axs[1, 0].get_xticklabels(), rotation=45, ha='right')
    plt.setp(axs[1, 1].get_xticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Add a combined normalized time series plot
    plt.figure(figsize=(14, 6))
    
    # Normalize each series to 0-1 range for comparison
    for column in df.columns[1:]:
        series = df[column]
        normalized = (series - series.min()) / (series.max() - series.min())
        plt.plot(df['Timestamp'], normalized, marker='.', markersize=4, label=column)
    
    plt.title('Normalized Values Comparison')
    plt.xlabel('Time')
    plt.ylabel('Normalized Value (0-1)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save both figures
    fig.savefig('energy_data_visualization.png')
    plt.savefig('energy_data_normalized.png')

    print("\nVisualizations saved as:")
    print("'energy_data_visualization.png'")
    print("'energy_data_normalized.png'")

def simulate():
    """
    Simulate energy data logging.
    """
    try:
        while True:
            voltage, current, energy, reactive_power = meter_reading()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Log data to file
            with open(DS_FILENAME, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, voltage, current, energy, reactive_power])
                
            print(f"[{timestamp}] Logged: V={voltage}V | I={current}A | E={energy}kW | RP={reactive_power}LVA")

            for _ in range(30):
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode().lower()
                    if key == 'c':
                        raise KeyboardInterrupt
                time.sleep(0.1)
    except KeyboardInterrupt:
        # Visualize data on exit
        df = calculate_statistics()
        visualize_data(df)

if __name__ == "__main__":
    simulate()
    print("\nEnergy data logging completed.")