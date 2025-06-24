## Connecting to the Raspberry Pi via SSH

### Network Setup

1. Boot Raspberry Pi up, wait about a minute for WiFi to activate
2. Connect to the Pi’s configured WLAN

### Finding the Pi’s IP Address (Windows)

1. Make sure the local machine is on the same WLAN as the Pi, then open a terminal.

2. Run the following command and note the first three octets of your IPv4 address (network ID):

   ```
   ipconfig
   ```

3. Run the following command to scan for devices on the network:

   ```
   nmap -sn <NETWORK_ID>.1/24
   ```

4. Look for “Raspberry Pi” in the results and note its IP address.

### Establishing SSH Connection

* **Option 1**: Use PuTTY (GUI)
* **Option 2**: Any UNIX Shell

* **Command:**
  ```
  ssh <username>@<ip-address>
  ```

---

## Post‐flash Configurations

### Install Necessary Resources

1. Update the OS and install Python on the Pi:

   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   sudo apt install python3 python3-pip python3-venv -y
   ```

2. Install Git on the Pi:

   ```bash
   sudo apt-get install git
   ```

3. Make the following configuration changes in `raspi-config`:

   ```bash
   sudo raspi-config
   ```

   * Using your arrow keys, choose **System Options → Boot/Auto Login → Console/AutoLogin**.
   * Next choose **Interface Options → Serial Port → No → Yes**.
   * Finally, choose **Interface Options → RPi Connect → Yes**. Follow any on‐screen instructions.
   * Choose **Finish → Yes** to reboot.
   * Once rebooted, reconnect to the Pi and update the system again:

     ```bash
     sudo apt-get update
     sudo apt-get upgrade
     ```

---

## Cloning Repository and Setting Up the Environment

1. With Git installed, clone the project and navigate into it:

   ```bash
   git clone https://github.com/AlaskanTuna/energy-data-logger.git
   cd energy-data-logger/
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

4. Before running either scripts, locate to the `src/` directory first.

   ```bash
   cd src/
   ```

---

## Retrieving Data from the Pi

1. Connect to the Pi via SSH.

2. Navigate to the repository folder:

   ```bash
   cd energy-data-logger/
   ```

3. If you haven’t already created a local directory for plots and CSV files, do so:

   ```bash
   mkdir -p data
   ```

4. Download the generated files from the Pi. For example:

   ```bash
   scp admin@<Pi_IP>:~/energy-data-logger/data/energy_data.csv ./data/
   scp admin@<Pi_IP>:~/energy-data-logger/data/*.png ./data/
   ```

---

## Installing InfluxDB 2.x OSS (Ubuntu & Debian ARM 64-bit) on the Pi

   ```bash
   curl --silent --location -O \
   https://repos.influxdata.com/influxdata-archive.key
   echo "943666881a1b8d9b849b74caebf02d3465d6beb716510d86a39f6c8e8dac7515  influxdata-archive.key" \
   | sha256sum --check - && cat influxdata-archive.key \
   | gpg --dearmor \
   | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive.gpg > /dev/null \
   && echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive.gpg] https://repos.influxdata.com/debian stable main' \
   | sudo tee /etc/apt/sources.list.d/influxdata.list

   sudo apt-get update && sudo apt-get install influxdb2

   # Followed by:
   sudo service influxdb start
   sudo service influxdb status --no-pager -l
   ```

---

## Installing Grafana OSS (Ubuntu & Debian) on the Pi

   ```bash
   sudo apt-get install -y apt-transport-https software-properties-common wget
   sudo mkdir -p /etc/apt/keyrings/
   wget -q -O - https://apt.grafana.com/gpg.key \
   | gpg --dearmor \
   | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
   echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" \
   | sudo tee -a /etc/apt/sources.list.d/grafana.list
   sudo apt-get update && sudo apt-get install grafana

   # Followed by:
   sudo systemctl daemon-reload
   sudo systemctl enable grafana-server
   sudo systemctl start grafana-server
   sudo systemctl status grafana-server --no-pager -l
   ```

---

## Environment Variables for InfluxDB/Grafana (Optional)

If you wish to enable InfluxDB/Grafana logging instead of CSV-only, create a `.env` file at the project root with:

```
INFLUXDB_URL=<your-influxdb-url>
INFLUXDB_TOKEN=<your-influxdb-token>
GRAFANA_URL=<your-grafana-url>
GRAFANA_VIEW_TOKEN=<your-influxdb-token>
```

The program will attempt to connect to InfluxDB/Grafana. If it fails (e.g. missing or invalid credentials), the program will continue logging to CSV only.

---

## OTG Usage: Pi and LAN Connected Devices

### Hardware Requirements

1. RJ45-to-USB Type-C adapter
2. RJ45 LAN cable
3. LAN device that supports ethernet

### Setting Up Pi as the LAN Server

*Note: For RPi Debian Bookworm OS, the default network stack is NetworkManager, which network profiles are stored under `/etc/NetworkManager/system-connections/` and ignores `dhcpcd.conf`*

1. Create a connection profile for the eth0 network interface:

   ```bash
   sudo nmcli connection add \
     type ethernet \
     ifname eth0 \
     con-name eth0 \
     ipv4.method manual \
     ipv4.addresses <ENTER STATIC IP ADDRESS>/24 \
     ipv4.gateway "" \
     ipv4.dns ""

   # Make sure eth0 autoconnects upon boot
   sudo nmcli connection modify eth0 connection.autoconnect yes
   ```

2. Bring up the connection profile:

   ```bash
   sudo ip link set eth0 up
   sudo nmcli connection up eth0
   ```

3. Install DHCP/DNS service on the Pi:

   ```bash
   sudo apt-get update
   sudo apt-get install dnsmasq
   ```

4. Create the DHCP config using the `sudo nano /etc/dnsmasq.d/eth0-dhcp.conf` command:

   ```bash
   interface=eth0
   bind-dynamic

   # StartIP,EndIP,SubnetMask,LeaseDuration
   dhcp-range=192.168.69.2,192.168.69.254,255.255.255.0,12h
   ```

5. Restart the service:

   ```bash
   sudo systemctl restart dnsmasq
   sudo systemctl enable dnsmasq
   sudo systemctl status dnsmasq --no-pager -l
   ```

6. Connect the OTG adapter to a LAN device (client), the DHCP service on the Pi will allocate an IP address to the it automatically.

### Setting Up Systemd for eth0 Interface

*For some reason, the eth0 static IP won't be up unless there is a carrier or is manually configured. Therefore, we create a temporary solution for this.*

1. Create the systemd unit file:

   ```bash
   sudo nano /etc/systemd/system/configure-eth0.service
   ```

2. Fill the content of the systemd unit file:
*Note: This configuration will restart the eth0 service every X seconds/minutes to ensure the interface always have static IP regardless of crashes.*

   ```bash
   [Unit]
   Description=Configure eth0 interface
   After=NetworkManager.service
   Wants=NetworkManager.service
   Before=energy-web.service dnsmasq.service

   [Service]
   Type=simple
   ExecStart=/bin/bash -c 'while true; do /usr/bin/nmcli connection up eth0 || true; ip addr show eth0 || true; echo "Rechecking eth0 in 10 minutes."; sleep 600; done'
   Restart=on-failure
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:

   ```bash
   sudo chmod 644 /etc/systemd/system/configure-eth0.service
   sudo systemctl daemon-reload
   sudo systemctl enable configure-eth0.service
   sudo systemctl restart configure-eth0.service

   # Check service "active (running)":
   sudo systemctl status configure-eth0.service --no-pager -l
   ```

### Setting Up Systemd (Gunicorn) for Energy Data Logger Webapp

1. Create the systemd unit file:

   ```bash
   sudo nano /etc/systemd/system/energy-web.service
   ```

2. Fill the content of the systemd unit file:

   ```bash
   [Unit]
   Description=Energy Logger Web App

   # MAKE SURE NETWORKMANAGER IS ONLINE
   After=network-online.target dnsmasq.service
   Wants=network-online.target dnsmasq.service

   # MAKE SURE DNSMASQ IS ONLINE
   Requires=dnsmasq.service

   [Service]
   # CODE DIR
   WorkingDirectory=/home/admin/energy-data-logger/src

   # ENVIRONMENT
   User=admin
   Group=admin
   Environment="PATH=/home/admin/energy-data-logger/venv/bin"

   # AUTHORITY
   AmbientCapabilities=CAP_NET_BIND_SERVICE

   # COMMAND
   ExecStart=/home/admin/energy-data-logger/venv/bin/gunicorn \
            -b 192.168.69.1:80 webapp:app

   # RELIABILITY
   Restart=on-failure
   RestartSec=3

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now energy-web

   # Check service “active (running)”:
   sudo systemctl status energy-web --no-pager -l
   ```

4. Try performing sanity check to confirm whether the service is up or not:

   ```bash
   curl -I http://192.168.69.1 # Should return HTTP/1.1 200 OK
   ```

5. Reboot the Pi and access webapp on browser by Pi's static IP address instantly.

---

## Test Modbus RTU Polling


### Serial Port Configuration

1. Have the RS485 cable wires connected accordingly to the energy meter and the Pi's CAN HAT.
*Note: Make sure to have serial port hardware enabled in `raspi-config` already.*

2. Use the following command to check for available serial ports. There should be at least one port (e.g. `/dev/serial -> ttyS0`) being displayed.
   
   ```bash
   ls -l /dev/serial*
   ```

3. Install dependencies (modpoll to be specific) in `/energy-data-logger/requirements.txt`.

4. Run the following command to see if there are responses from the Modbus RTU.

   ```bash
   mbpoll -m rtu -a 1 -b 9600 -P none -t 4:float -r 20482 -c 2 -l 1000 /dev/serial0
   ```

---

## Setting Up Watchdog

1. Install the Watchdog package:

   ```bash
   sudo apt-get update
   sudo apt install watchdog
   ```

2. Enable hardware Watchdog by editing the boot config file:

   ```bash
   sudo nano /boot/firmware/config.txt
   
   # Followed by adding this line under the `[all]` section:
   dtparam=watchdog=on
   ```

3. Create pre-reboot logging script and a directory to store log files:

   ```bash
   # Create directory for logs
   sudo mkdir -p /var/log/watchdog

   # Create the script
   sudo nano /usr/local/bin/watchdog-pre-reboot-log.sh

   # Add the following content
   #!/bin/bash
   # Script to capture system logs before watchdog reboot

   TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
   LOG_DIR="/var/log/watchdog"

   # Create log files with timestamp
   JOURNAL_LOG="${LOG_DIR}/pre-reboot-journal_${TIMESTAMP}.log"
   KERNEL_LOG="${LOG_DIR}/pre-reboot-kernel_${TIMESTAMP}.log"

   # Log last 200 journal entries
   journalctl -n 200 > "${JOURNAL_LOG}"

   # Log last 50 kernel messages
   dmesg | tail -n 50 > "${KERNEL_LOG}"

   # Add permissions
   chmod 644 "${JOURNAL_LOG}" "${KERNEL_LOG}"
   ```

4. Make the script executable:

   ```bash
   sudo chmod +x /usr/local/bin/watchdog-pre-reboot-log.sh
   ```

5. Configure Watchdog service:

   ```bash
   # Edit watchdog configuration
   sudo nano /etc/watchdog.conf

   # Uncomment or add these lines
   watchdog-device = /dev/watchdog
   watchdog-timeout = 15
   interval = 3
   log-dir = /var/log/watchdog
   repair-binary = /usr/local/bin/watchdog-pre-reboot-log.sh
   repair-timeout = 60
   temperature-sensor = /sys/devices/virtual/thermal/thermal_zone0/temp
   max-temperature = 80000
   #test-binary = /bin/false
   ```

6. Enable and start Watchdog service, then reboot:

   ```bash
   sudo systemctl enable watchdog
   sudo systemctl start watchdog
   sudo systemctl status watchdog --no-pager -l
   sudo reboot
   ```

---