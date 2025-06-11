// static/app.js

let modalMode = '';

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

    // Add global event delegation for modal handling
    document.addEventListener('click', function(event) {
        // Close button clicked
        if (event.target.classList.contains('close-modal')) {
            closeFileModal();
        }

        // Click outside modal content
        if (event.target.id === 'file-modal') {
            closeFileModal();
        }

        // File item clicked
        if (event.target.closest('.file-item')) {
            const fileItem = event.target.closest('.file-item');
            const filename = fileItem.dataset.filename;
            const mode = fileItem.dataset.mode;
            
            if (mode === 'analyze') {
                showAnalysisOptions(filename);
            } else if (mode === 'view') {
                window.location.href = `/api/files/${filename}`;
                closeFileModal();
            }
        }
    });

    // Initialize event listeners
    menuItems.forEach((item, index) => {
        item.addEventListener('click', function() {
            // 1. Log New Data
            if (index === 0) {
                handleLoggerToggle(this);
            }

            // 2. View Data
            if (index === 1) { 
                showFileModal('view');
            }

            // 3. Analyze Data
            if (index === 2) {
                showFileModal('analyze');
            }

            // TODO: 4. Settings
            if (index === 3) {
                // TODO
            }
        });
    });

    /**
     * @brief Shows the file selection modal with context-specific behavior.
     * @mode Determines which modal to show.
     */

    function showFileModal(mode) {
        modalMode = mode;
        const modal = document.getElementById('file-modal');
        const fileList = document.getElementById('file-list');
        const modalHeader = document.querySelector('.modal-header h2');
        const modalBodyText = document.querySelector('.modal-body p');

        // Context specific modals
        if (mode === 'analyze') {
            modalHeader.textContent = 'Analyze Data';
            modalBodyText.textContent = 'Select a file to analyze:';
        } else if (mode === 'view') {
            modalHeader.textContent = 'View Data';
            modalBodyText.textContent = 'Select a file to view:';
        }

        // Fetch files
        fetch('/api/files')
            .then(response => response.json())
            .then(files => {
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
                    fileItem.dataset.filename = file;
                    fileItem.dataset.mode = mode;
                    fileItem.innerHTML = `
                        <div>
                            <div>${file}</div>
                            <div class="file-item-date">Created: ${dateStr}</div>
                        </div>
                        <span class="${mode === 'analyze' ? 'analysis-icon' : 'download-icon'}">
                            ${mode === 'analyze' ? '📊' : '📥'}
                        </span>
                    `;
                    
                    fileList.appendChild(fileItem);
                });
            })
            .catch(error => {
                console.error('Error fetching files:', error);
                fileList.innerHTML = '<p class="empty-message">Error loading files. Please try again.</p>';
            });

        // Show modal
        modal.style.display = 'flex';
    }

    /**
     * @brief Handles the logger toggle button click.
     * @button The button element that was clicked.
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

                // Stop polling for data
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
        stopDataPolling();
        pollingInterval = setInterval(fetchLatestData, 3000);
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
                    // Update last updated timestamp
                    lastUpdate.textContent = new Date().toLocaleTimeString();

                    // Build HTML table for concurrent readings
                    let html = '<h3>Latest Readings</h3>';
                    html += '<table class="readings-table">';
                    html += '<thead><tr><th>Parameter</th><th>Value</th></tr></thead><tbody>';

                    // Format each reading
                    for (const [key, value] of Object.entries(data)) {
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
     * @brief Shows analysis options after selecting a file.
     * @filename The name of the file to analyze.
     */

    function showAnalysisOptions(filename) {
        const modalBody = document.querySelector('.modal-body');
        const modalHeader = document.querySelector('.modal-header h2');
        
        modalHeader.textContent = `Analyze: ${filename}`;
        modalBody.innerHTML = '<p class="loading">Analyzing data...</p>';
        
        fetch(`/api/analyze/${filename}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    modalBody.innerHTML = `<p class="error-message">${data.error}</p>`;
                    return;
                }

                // Format and display the statistics only
                const formattedAnalysis = data.analysis_text
                    .replace(/\n/g, '<br>')
                    .replace(/=+/g, match => `<hr class="stats-divider">${match}<hr class="stats-divider">`);
                
                // Store the raw text for downloading
                const rawStatsText = data.analysis_text;

                let html = `
                    <h3>Statistics</h3>
                    <div class="statistics-container">
                        <div class="statistics-output">${formattedAnalysis}</div>
                    </div>
                    <button id="download-stats" class="action-button">
                        <span class="icon">📥</span> Download Statistics
                    </button>
                `;

                modalBody.innerHTML = html;
                
                // Add click handler for the download button
                document.getElementById('download-stats').addEventListener('click', () => {
                    downloadStatistics(rawStatsText, filename);
                });
            })
            .catch(error => {
                console.error('Error loading analysis:', error);
                modalBody.innerHTML = '<p class="error-message">Error analyzing data. Please try again.</p>';
            });
    }

    /**
     * @brief Closes the file selection modal.
     */

    function closeFileModal() {
        const modal = document.getElementById('file-modal');
        modal.style.display = 'none';
        const modalBody = document.querySelector('.modal-body');

        // Reset modal structure
        modalBody.innerHTML = `
            <p>Select a file to ${modalMode === 'analyze' ? 'analyze' : 'view'}:</p>
            <div id="file-list"></div>
        `;

        modalMode = '';
    }

    /**
     * @brief Downloads statistics as a text file.
     * @text The statistics text to download.
     * @filename The original CSV filename.
     */

    function downloadStatistics(text, filename) {
        const statsFilename = filename.replace('.csv', '_statistics.txt');
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const downloadLink = document.createElement('a');

        downloadLink.href = url;
        downloadLink.download = statsFilename;
        document.body.appendChild(downloadLink);
        downloadLink.click();

        // Cleanup download link
        setTimeout(() => {
            document.body.removeChild(downloadLink);
            URL.revokeObjectURL(url);
        }, 100);
    }
});