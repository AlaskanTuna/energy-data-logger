# Energy Data Logger Notes

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

## Managing Scripts on the Pi

### Install Python

```bash
sudo apt update
sudo apt install python3 python3-pip -y
```

### Copying Scripts to the Pi

```bash
scp energy_logger.py admin@192.168.85.193:~/
```

### Running Scripts

1. Connect to the Pi via SSH
2. Run the script with: `python3 energy_logger.py`
3. Stop the script with: `CTRL+C`

## Testing: Retrieving Data from the Pi

### Setup and Downloading Plots to Local Machine

1. Connect to the Pi via SSH
2. Run the script to generate logged files
3. Exit the Pi SSH session: `exit`
4. Create directory to fetch files in, for example: `mkdir -p plots`
5. Download the plots with `scp admin@192.168.85.193:~/plots/* ./plots/`