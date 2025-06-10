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

3. Make the following configuration changes:

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

4. Run the script from the project root:

   ```bash
   cd src/
   python main.py
   ```

5. To stop logging, press **Ctrl +C**.

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
wget -q https://repos.influxdata.com/influxdata-archive_compat.key
echo '393e8779c89ac8d958f81f942f9ad7fb82a25e133faddaf92e15b16e6ac9ce4c influxdata-archive_compat.key' \
  | sha256sum -c && \
  cat influxdata-archive_compat.key | gpg --dearmor \
  | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null

echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] \
  https://repos.influxdata.com/debian stable main' \
  | sudo tee /etc/apt/sources.list.d/influxdata.list

sudo apt-get update && sudo apt-get install influxdb2
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
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com beta main" \
  | sudo tee -a /etc/apt/sources.list.d/grafana.list

sudo apt-get update && sudo apt-get install grafana
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
     ipv4.addresses <static-ip-address>/24 \
     ipv4.gateway "" \
     ipv4.dns ""
   ```

2. Make sure it autoconnects:

   ```bash
   sudo nmcli connection modify eth0 connection.autoconnect yes
   ```

3. Bring up the connection profile:

   ```bash
   sudo nmcli connection up eth0
   ```

4. Install DHCP/DNS service on the Pi:

   ```bash
   sudo apt update
   sudo apt install dnsmasq
   ```

5. Create the DHCP config:

   ```bash
   interface=eth0
   bind-dynamic

   # StartIP,EndIP,SubnetMask,LeaseDuration
   dhcp-range=192.168.69.2,192.168.69.254,255.255.255.0,12h
   ```

6. Restart the service:

   ```bash
   sudo systemctl restart dnsmasq
   sudo systemctl enable dnsmasq
   ```

7. Connect the OTG adapter to a LAN device (client), the DHCP service on the Pi will allocate an IP address to the it. Then, SSH into the Pi using Termux and the Pi's static IP address.

### Setting Up Systemd for Energy Data Logger Webapp

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
   systemctl status energy-web --no-pager -l
   ```

4. Try performing sanity check to confirm whether the service is up or not:

   ```bash
   curl -I http://192.168.69.1   # Should return HTTP/1.1 200 OK
   ```

5. Reboot the Pi and access webapp on browser by Pi's static IP address instantly.

---

## Troubleshooting Commands