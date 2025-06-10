# src/main.py

from util import clear_screen, view_data, analyze_data
from logger import DataLogger

def main_menu():
    """
    Display and handle main menu options.
    """
    print("===== Main Menu =====")
    print("1. Log New Data")
    print("2. View Data")
    print("3. Analyze Data")
    print("4. Exit")

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
        exit(0)
    else:
        clear_screen()
        return main_menu()

if __name__ == "__main__":
    while True:
        clear_screen()
        main_menu()