## Connecting to the Raspberry Pi via SSH

### Network Setup

1. Boot Raspberry Pi up, wait about a minute for WiFi to activate
2. Connect to the Pi’s configured WLAN

### Finding the Pi’s IP Address (Windows)

1. Make sure the local machine is on the same WLAN as the Pi, then open a terminal
2. Run:

   ```
   ipconfig
   ```

   and note the first three octets of your IPv4 address (network ID)
3. Run:

   ```
   nmap -sn <NETWORK_ID>.1/24
   ```

   to scan for devices
4. Look for “Raspberry Pi” in the results and note its IP address

### Establishing SSH Connection

* **Option 1**: Use PuTTY (GUI)
* **Option 2**: Command line:

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
   git clone https://github.com/AlaskanTuna/Energy-Data-Logger.git
   cd Energy-Data-Logger
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
4. **Create the `data/` directory at the project root**, which will hold the CSV and plot files:

   ```bash
   mkdir data
   ```
5. Run the script from the project root:

   ```bash
   python src/main.py
   ```
6. To stop logging, press **Ctrl +C**.

---

## Retrieving Data from the Pi

1. Connect to the Pi via SSH.
2. Navigate to the repository folder:

   ```bash
   cd Energy-Data-Logger
   ```
3. If you haven’t already created a local directory for plots and CSV files, do so:

   ```bash
   mkdir -p data
   ```
4. Download the generated files from the Pi. For example:

   ```bash
   scp admin@<Pi_IP>:~/Energy-Data-Logger/data/energy_data.csv ./data/
   scp admin@<Pi_IP>:~/Energy-Data-Logger/data/*.png ./data/
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

## Environment Variables for InfluxDB (Optional)

If you wish to enable InfluxDB logging instead of CSV-only, create a `.env` file at the project root with:

```
INFLUXDB_URL=<your-influxdb-url>
INFLUXDB_TOKEN=<your-influxdb-token>
```

The code will attempt to connect to InfluxDB; if it fails (e.g., missing or invalid credentials), it will continue logging to CSV only.