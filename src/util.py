# src/util.py

import os
import config

from analyzer import DataAnalyzer

# HELPER FUNCTIONS

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

# UTILITY FUNCTIONS

def clear_screen():
    """
    Clear the terminal screen.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

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
    Let user select a CSV file for data analysis and visualization.
    """
    selected_file = select_csv_file("analyze")
    if selected_file:
        filepath = os.path.join("../data/", selected_file)

        # Create analyzer and run analysis
        analyzer = DataAnalyzer()
        df = analyzer.calculate_statistics(filepath)
        analyzer.visualize_data(df)

        input("\nPress Enter to continue...")
        clear_screen()