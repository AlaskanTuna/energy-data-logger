// static/app.js

/**
 * @brief Main JavaScript for the Logger Dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get references to UI elements
    const loggerStatus = document.getElementById('logger-status');
    const lastUpdate = document.getElementById('last-update');
    const latestReadingsDiv = document.getElementById('latest-readings');
    const menuItems = document.querySelectorAll('.menu-item');

    // Tracking variable for logger state
    let isLogging = false;
    let pollingInterval = null;

    // Initialize event listeners
    menuItems.forEach((item, index) => {
        item.addEventListener('click', function() {
            if (index === 0) {  // 1. Log New Data
                handleLoggerToggle(this);
            }
            // TODO: 2. View Data
            // TODO: 3. Analyze Data
            // TODO: 4. Download Data
        });
    });

    /**
     * @brief Handles the logger toggle button click.
     */

    function handleLoggerToggle(button) {
        if (!isLogging) {
            // Start logging
            fetch('/api/start', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                isLogging = true;
                loggerStatus.textContent = 'Active';
                loggerStatus.style.color = 'green';
                lastUpdate.textContent = new Date().toLocaleTimeString();
                button.textContent = '1. Stop Logging';
                button.classList.add('active');
                
                // Start polling for data
                startDataPolling();
            })
            .catch(error => {
                console.error('Error starting logger:', error);
            });
        } else {
            // Stop logging
            fetch('/api/stop', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                isLogging = false;
                loggerStatus.textContent = 'Inactive';
                loggerStatus.style.color = '';
                button.textContent = '1. Log New Data';
                button.classList.remove('active');
                
                // Stop polling
                stopDataPolling();
            })
            .catch(error => {
                console.error('Error stopping logger:', error);
            });
        }
    }
    
    /**
     * @brief Starts polling for the latest data from the server.
     */

    function startDataPolling() {
        // Clear any existing interval
        stopDataPolling();
        
        // Set up new polling interval (every 2 seconds)
        pollingInterval = setInterval(fetchLatestData, 2000);
        
        // Fetch immediately for instant feedback
        fetchLatestData();
    }

    /**
     * @brief Stops the data polling interval.
     */

    function stopDataPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }

    /**
     * @brief Fetches the latest data from the server and updates the UI.
     */

    function fetchLatestData() {
        fetch('/api/latest')
            .then(response => response.json())
            .then(data => {
                if (data && Object.keys(data).length > 0) {
                    // Update last update time
                    lastUpdate.textContent = new Date().toLocaleTimeString();
                    
                    // Build HTML table for readings
                    let html = '<h3>Latest Readings</h3>';
                    html += '<table class="readings-table">';
                    html += '<thead><tr><th>Parameter</th><th>Value</th></tr></thead><tbody>';
                    
                    for (const [key, value] of Object.entries(data)) {
                        // Format numerical values
                        let displayValue = typeof value === 'number' ? 
                            value.toFixed(3) : value;
                        
                        html += `<tr>
                            <td>${key}</td>
                            <td>${displayValue}</td>
                        </tr>`;
                    }
                    
                    html += '</tbody></table>';
                    latestReadingsDiv.innerHTML = html;
                }
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }
});