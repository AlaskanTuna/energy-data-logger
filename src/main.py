# src/main.py

# NOTE: To access CLI implementation, make sure `DEVELOPER_MODE` is set to True 
#       in src/settings.py file. Then run this script from the CLI: `python src/main.py`. 
#       This is only for development and testing purposes.

from components.util import main_menu, clear_screen

if __name__ == "__main__":
    while True:
        clear_screen()
        main_menu()