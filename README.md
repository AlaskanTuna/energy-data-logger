# Energy Data Logger Notes

## Connecting to the Raspberry Pi via SSH

### Network Setup
1. Boot Raspberry Pi up, wait about a minute for WiFi to activate.

2. Connect to the Pi's wireless network:
    - SSID: `T01⁰N9`
    - Password: `TolonglahAku`
    
    > *Note: These are the default WLAN settings configured during flash and may change in the future.*

### Finding the Pi's IP Address (Windows)
1. Open a command prompt
2. Run `ipconfig` and note the first 3 octets of your IPv4 address (network ID)
3. Run `nmap -sn <NETWORK_ID>.1/24` to scan for devices
4. Look for "Raspberry Pi" in the results and note its IP address

### Establishing SSH Connection
- Option 1: Use PuTTY (GUI)
- Option 2: Command line: `ssh <username>@<ip-address>`

## Managing Scripts on the Pi

### Copying Scripts to the Pi
```bash
scp energy_logger.py admin@192.168.85.193:~/
```

### Running Scripts
1. Connect to the Pi via SSH
2. Run the script with: `python3 energy_logger.py`
3. Stop the script with: `CTRL+C`

## Testing: Retrieving Data from the Pi

### Setup
1. Connect to the Pi via SSH
2. Create a plots directory (if needed): `mkdir -p ~/plots`
3. Run your script to generate plots

### Downloading Plots to Local Machine
1. Exit the Pi SSH session: `exit`
2. Create a local plots directory: `mkdir -p plots`
3. Download the plots:
```bash
scp admin@192.168.85.193:~/plots/* ./plots/
```