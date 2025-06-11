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
            // 1. Log New Data
            if (index === 0) {
                handleLoggerToggle(this);
            }

            // 2. View Data
            if (index === 1) { 
                showFileSelectionModal();
            }

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

    /**
     * @brief Shows the file selection modal to view/download data files.
     */

    function showFileSelectionModal() {
        const modal = document.getElementById('file-modal');
        const closeBtn = document.querySelector('.close-modal');
        const fileList = document.getElementById('file-list');

        fetch('/api/files')
            .then(response => response.json())
            .then(files => {
                // Clear existing list
                fileList.innerHTML = '';
                if (files.length === 0) {
                    fileList.innerHTML = '<p class="empty-message">No data files available.</p>';
                    return;
                }

                // Add each file to the list
                files.forEach(file => {
                    let dateStr = "N/A";
                    const match = file.match(/^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})\.csv$/);
                    if (match) {
                        const [_, year, month, day, hour, minute, second] = match;
                        const date = new Date(year, month-1, day, hour, minute, second);
                        dateStr = date.toLocaleString();
                    }

                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    fileItem.innerHTML = `
                        <div>
                            <div>${file}</div>
                            <div class="file-item-date">Created: ${dateStr}</div>
                        </div>
                        <span class="download-icon">📥</span>
                    `;

                    // Add click handler to download file
                    fileItem.addEventListener('click', () => {
                        window.location.href = `/api/files/${file}`;
                        closeFileModal();
                    });
                    
                    fileList.appendChild(fileItem);
                });
            })
            .catch(error => {
                console.error('Error fetching files:', error);
                fileList.innerHTML = '<p class="empty-message">Error loading files. Please try again.</p>';
            });

        // Show modal
        modal.style.display = 'flex';

        // Close when clicking X
        closeBtn.addEventListener('click', closeFileModal);

        // Close when clicking outside the modal
        modal.addEventListener('click', event => {
            if (event.target === modal) {
                closeFileModal();
            }
        });
    }

    /**
     * @brief Closes the file selection modal.
     */

    function closeFileModal() {
        const modal = document.getElementById('file-modal');
        modal.style.display = 'none';
    }
});