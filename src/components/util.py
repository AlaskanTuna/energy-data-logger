# src/components/util.py

import os
import logging
import pandas as pd

from config import config
from components.logger import DataLogger
from components.analyzer import DataAnalyzer
from services.settings import settings
from datetime import datetime

# CONSTANTS

log = logging.getLogger(__name__)

def main_menu():
    """
    Display and handle main menu options for CLI mode.
    """
    if config.DEVELOPER_MODE:
        print("===== Main Menu =====")
        print("1. Log New Data")
        print("2. View Data")
        print("3. Analyze Data")
        print("4. Visualize Data")
        print("5. Settings")
        print("6. Exit")

        choice = input("\nEnter your choice: ").strip()

        if choice == '1':
            clear_screen()
            logger = DataLogger(filename=get_current_filename("ds"))
            logger.start()
        elif choice == '2':
            clear_screen()
            view_data()
        elif choice == '3':
            clear_screen()
            analyze_data()
        elif choice == '4':
            clear_screen()
            visualize_data()
        elif choice == '5':
            clear_screen()
            settings_menu()
        elif choice == '6':
            exit(0)
        else:
            clear_screen()
            return main_menu()
    else:
        log.info("Developer mode is disabled.")
        exit(0)

def clear_screen():
    """
    Clear the terminal screen.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def get_filename(file="type"):
    """
    Generate a timestamped CSV filename for data logging.

    @file: Specify file type
    @return: Timestamped filename for data or plot
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if file == "ds":
        return f"../data/{timestamp}.csv"
    elif file == "pl":
        return f"../plots/{timestamp}.png"
    elif file == "log":
        return f"../logs/{timestamp}.log.gz"

def get_current_filename(file):
    """
    Get the current filename
    
    @file: Specify file type
    @return: Filename based on the type
    """
    return get_filename(file)

def list_files(file="type"):
    """ 
    List all files of a specific type.
    
    @file: Specify file type
    """
    if file == "ds":
        directory = config.DS_DIR
        extension = ".csv"
    elif file == "pl":
        directory = config.PL_DIR
        extension = ".png"
    elif file == "log":
        directory = config.LOG_DIR
        extension = ".log.gz"
    else:
        log.warning(f"Unknown file type: '{file}'.")
        return []

    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            return []

        files = [f for f in os.listdir(directory) if f.endswith(extension)]
        return sorted(files)
    except Exception as e:
        log.error(f"File Listing Error: {e}", exc_info=True)

def display_csv_file(filename, directory=config.DS_DIR):
    """
    Display the content of a CSV file in the terminal.
    
    @filename: Name of the CSV file
    @directory: Directory where the file is located
    """
    try:
        filepath = os.path.join(directory, filename)
        if not os.path.exists(filepath):
            print(f"File not found: '{filepath}'.")
            return False

        # Read and display the file content
        with open(filepath, 'r') as file:
            print(f"\n===== Content of {filename} =====\n")
            content = file.read()
            print(content)
            return True
    except Exception as e:
        log.error(f"Display File Error: {e}", exc_info=True)
        return False

def select_file(purpose="action", file="type"):
    """
    Display a list of files and let user select one.

    @purpose: String describing the purpose
    @file: Specify file type
    @return: Selected filename or None
    """
    file_type_name = "CSV" if file == "ds" else "PNG" if file == "pl" else "LOG" if file == "log" else "Unknown"
    print(f"\n===== Available {file_type_name} Files for {purpose.capitalize()} =====\n")

    files = list_files(file)
    if not files:
        print(f"No {file_type_name} files found in the directory.")
        input("\nPress Enter to continue...")
        clear_screen()
        return None

    print("0. Return to Main Menu")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")

    try:
        selection = int(input(f"\nPlease select a file: ").strip())
        if selection == 0:
            clear_screen()
            return None

        if 1 <= selection <= len(files):
            return files[selection - 1]
    except ValueError:
        input("Invalid selection. Please enter a number. \n\nPress Enter to continue...")
        clear_screen()
        return select_file(purpose, file)

def view_data():
    """
    Let user select a CSV file and display its content.
    """
    selected_file = select_file("view", "ds")
    if selected_file:
        display_csv_file(selected_file)
        input("Press Enter to return...")
        clear_screen()

def analyze_data():
    """
    Let user select a CSV file for data analysis.
    """
    selected_file = select_file("analyze", "ds")
    if selected_file:
        filepath = os.path.join(config.DS_DIR, selected_file)

        try:
            if not os.path.exists(filepath):
                log.error(f"File not found at '{filepath}'.")
                input("\nPress Enter to continue...")
                clear_screen()
                return

            df = pd.read_csv(filepath)
            analyzer = DataAnalyzer()

            analyzer.calculate_statistics(df)
            analyzer.calculate_session_consumption(df)
        except Exception as e:
            log.error(f"Analysis Error: {e}", exc_info=True)
        finally:
            input("\nPress Enter to continue...")
            clear_screen()

def visualize_data():
    """
    Generate visualizaitons for a selected CSV file.
    """
    selected_file = select_file("visualize", "ds")
    if selected_file:
        filepath = os.path.join(config.DS_DIR, selected_file)
        df = pd.read_csv(filepath)
        analyzer = DataAnalyzer()

        analyzer.visualize_data(df, filepath)
        input("\nPress Enter to continue...")

def settings_menu():
    """
    Display and handle settings configuration for the CLI.
    """
    while True:
        clear_screen()
        current_settings = settings.get_all()
        parity_map = {'N': 'None', 'E': 'Even', 'O': 'Odd'}

        print("===== Settings Menu =====")
        print("0. Return to Main Menu")
        print(f"1. Logging Interval: {current_settings.get('LOG_INTERVAL')} seconds")
        print(f"2. Modbus Slave ID: {current_settings.get('MODBUS_SLAVE_ID')}")
        print(f"3. Baud Rate: {current_settings.get('BAUDRATE')}")
        print(f"4. Parity: {parity_map.get(current_settings.get('PARITY'))}")
        print(f"5. Byte Size: {current_settings.get('BYTESIZE')}")
        print(f"6. Stop Bits: {current_settings.get('STOPBITS')}")
        print(f"7. Timeout: {current_settings.get('TIMEOUT')} seconds")
        choice = input("\nEnter your choice to change current settings: ").strip()

        if choice == '0':
            clear_screen()
            return None
        elif choice == '1':
            new_val = input("Enter new Logging Interval: ").strip()
            if new_val.isdigit():
                settings.update({"LOG_INTERVAL": int(new_val)})
            else:
                input("Invalid input. \n\nPress Enter to continue...")
        elif choice == '2':
            new_val = input("Enter new Modbus Slave ID: ").strip()
            if new_val.isdigit() and 1 <= int(new_val) <= 247:
                settings.update({"MODBUS_SLAVE_ID": int(new_val)})
            else:
                input("Invalid input. \n\nPress Enter to continue...")
        elif choice == '3':
            new_val = input("Enter new Baud Rate: ").strip()
            if new_val.isdigit():
                settings.update({"BAUDRATE": int(new_val)})
            else:
                input("Invalid input. \n\nPress Enter to continue...")
        elif choice == '4':
            parity_choice = input("Select Parity (1=None, 2=Even, 3=Odd): ").strip()
            parity_map_save = {'1': 'N', '2': 'E', '3': 'O'}
            if parity_choice in parity_map_save:
                settings.update({"PARITY": parity_map_save[parity_choice]})
            else:
                input("Invalid selection. \n\nPress Enter to continue...")
        elif choice == '5':
            new_val = input("Enter new Byte Size").strip()
            if new_val.isdigit() and 5 <= int(new_val) <= 8:
                settings.update({"BYTESIZE": int(new_val)})
            else:
                input("Invalid input. \n\nPress Enter to continue...")
        elif choice == '6':
            new_val = input("Enter new Stop Bits: ").strip()
            if new_val.isdigit() and int(new_val) in [1, 2]:
                settings.update({"STOPBITS": int(new_val)})
            else:
                input("Invalid input. \n\nPress Enter to continue...")
        elif choice == '7':
            new_val = input("Enter new Timeout: ").strip()
            if new_val.isdigit() and int(new_val) > 0:
                settings.update({"TIMEOUT": int(new_val)})
            else:
                input("Invalid input. \n\nPress Enter to continue...")
        else:
            return settings_menu()