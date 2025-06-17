# src/util.py

import os

import pandas as pd

from datetime import datetime
from logger import DataLogger

def main_menu():
    """
    Display and handle main menu options for CLI mode.
    """
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
        logger = DataLogger()
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
        # TODO: Implement baudrate, parity, CT ratio etc. settings
        pass
    elif choice == '6':
        exit(0)
    else:
        clear_screen()
        return main_menu()

def clear_screen():
    """
    Clear the terminal screen.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def get_filename(file="type"):
    """
    Generate a timestamped CSV filename for data logging.

    @file: Specify file type.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if file == "ds":
        return f"../data/{timestamp}.csv"
    elif file == "pl":
        return f"../plots/{timestamp}.png"

def get_current_filename(file="ds"):
    """
    Get a fresh timestamp-based filename for the current time.
    
    @file: Specify file type (ds=data, pl=plot).
    """
    return get_filename(file)

def list_csv_files(directory="../data/"):
    """
    List all CSV files in the specified directory.
    Returns a list of filenames.
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            return []
        csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
        return sorted(csv_files)
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

def display_csv_file(filename, directory="../data/"):
    """
    Display the content of a CSV file in the terminal.
    Similar to the 'cat' command in Linux.
    """
    try:
        filepath = os.path.join(directory, filename)
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return False
        
        # Read and display the file content
        with open(filepath, 'r') as file:
            print(f"\n===== Content of {filename} =====\n")
            content = file.read()
            print(content)
            return True
    except Exception as e:
        print(f"Error displaying file: {e}")
        return False

def select_csv_file(purpose="action"):
    """
    Display a list of CSV files and let the user select one.
    Returns the selected filename or None if user cancels.

    @purpose: String describing the purpose.
    """
    print(f"\n===== Available CSV Files for {purpose.capitalize()} =====\n")

    csv_files = list_csv_files()
    if not csv_files:
        print("No CSV files found in the data directory.")
        input("\nPress Enter to continue...")
        clear_screen()
        return None
    
    # Display file list with numbers
    print("0. Return to Main Menu")
    for i, file in enumerate(csv_files, 1):
        print(f"{i}. {file}")
    
    # Get user selection
    try:
        selection = int(input(f"\nPlease select a file: ").strip())
        if selection == 0:
            clear_screen()
            return None

        if 1 <= selection <= len(csv_files):
            return csv_files[selection - 1]
    except ValueError:
        print("Invalid selection. Please enter a number.")
        input("\nPress Enter to continue...")
        clear_screen()
        return select_csv_file(purpose)

def view_data():
    """
    Let user select a CSV file and display its content.
    """
    selected_file = select_csv_file("view")
    if selected_file:
        display_csv_file(selected_file)
        input("Press Enter to return...")
        clear_screen()

def analyze_data():
    """
    Let user select a CSV file for data analysis.
    """
    selected_file = select_csv_file("analyze")
    if selected_file:
        filepath = os.path.join("../data/", selected_file)

        try:
            from analyzer import DataAnalyzer
            analyzer = DataAnalyzer()
            analyzer.calculate_statistics(filepath)
            input("\nPress Enter to continue...")
            clear_screen()
        except Exception as e:
            input("\nPress Enter to continue...")
            clear_screen()

def visualize_data():
    """
    Generate visualizaitons for a selected CSV file.
    """
    selected_file = select_csv_file("visualize")
    if selected_file:
        filepath = os.path.join("../data/", selected_file)

        df = pd.read_csv(filepath)

        from analyzer import DataAnalyzer
        analyzer = DataAnalyzer()
        analyzer.visualize_data(df, filepath)

        input("\nPress Enter to continue...")