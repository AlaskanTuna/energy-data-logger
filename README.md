## Connecting to the Raspberry Pi via SSH

### Network Setup

1. Boot Raspberry Pi up, wait about a minute for WiFi to activate
2. Connect to the Pi's configured WLAN

### Finding the Pi's IP Address (Windows)

1. Make sure the local machine is on the same WLAN as the Pi, then open a terminal
2. Run `ipconfig` and note the first 3 octets of your IPv4 address (network ID)
3. Run `nmap -sn <NETWORK_ID>.1/24` to scan for devices
4. Look for "Raspberry Pi" in the results and note its IP address

### Establishing SSH Connection

- Option 1: Use PuTTY (GUI)
- Option 2: Command line: `ssh <username>@<ip-address>`

## Post-flash Configurations

### Install Necessary Resources

1. Update the OS and Install Python on the Pi:

```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt install python3 python3-pip python3-venv -y
````

2. Install Git on the Pi:

```bash
sudo apt-get install git
```

3. Make Following Configuration Changes:

   * Using your arrow keys, choose System Options -> Boot/Auto Login -> Console/AutoLogin.
   * Next choose Interface Options -> Serial Port -> No -> Yes.
   * Finally, choose Interface Options -> RPi Connect -> Yes. Follow any on-screen instructions.
   * Choose Finish -> Yes to reboot.
   * Once rebooted, reconnect to the Pi and update the system again.

### Cloning Repository and Setting Up the Environment

1. With Git installed, clone the project and navigate to the repository:

```bash
git clone https://github.com/AlaskanTuna/Energy-Data-Logger.git
cd energy-data-logger
```

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the required Python packages:

```bash
pip install -r requirements.txt
```

4. Run the script:

```bash
python energy_logger.py
```

5. Stop the script with: `CTRL+C`

## Retrieving Data from the Pi

1. Connect to the Pi via SSH
2. Navigate to the repository (`cd energy-data-logger`) and run the script to create script-generated files
3. In the local machine, create directory to fetch files in if haven't already, for example: `mkdir -p plots`
4. Download the files from the Pi, for example: `scp admin@ipaddress:~/plots/* ./plots/`