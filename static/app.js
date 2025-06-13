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
            } else if (mode === 'visualize') {
                showVisualizationOptions(filename);
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

            // 4. Visualize Data
            if (index === 3) {
                showFileModal('visualize');
            }

            // 5. TODO: Settings
            if (index === 4) {
                alert("Settings feature is not implemented yet.");
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
            modalHeader.textContent = "Analyze Data";
            modalBodyText.textContent = "Select a file to analyze:";
        } else if (mode === 'view') {
            modalHeader.textContent = "View Data";
            modalBodyText.textContent = "Select a file to view:";
        } else if (mode === 'visualize') {
            modalHeader.textContent = "Visualize Data";
            modalBodyText.textContent = "Select a file to visualize:";
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
     * @brief Shows visualization options for the selected file.
     * @filename Shows visualization options for the selected file.
     */

    function showVisualizationOptions(filename) {
        const modalBody = document.querySelector('.modal-body');
        const modalHeader = document.querySelector('.modal-header h2');

        modalHeader.textContent = `Visualize: ${filename}`;

        // Fetch visualization types
        fetch('/api/visualization-types')
            .then(response => response.json())
            .then(types => {
                if (!types || types.length === 0) {
                    modalBody.innerHTML = '<p class="error-message">No visualization types available.</p>';
                    return;
                }

                let html = `
                    <h3>Select Visualization Type</h3>
                    <div class="viz-options">`;

                // Add visualization options
                types.forEach(type => {
                    if (type.name !== 'Custom Selection') {
                        html += `
                            <div class="viz-option" data-viz-type="${type.id}" data-filename="${filename}">
                                <span class="viz-icon">📈</span>
                                <span>${type.name}</span>
                            </div>`;
                    }
                });

                // Add custom option
                html += `
                    <div class="viz-option" data-viz-type="custom" data-filename="${filename}">
                        <span class="viz-icon">✏️</span>
                        <span>Custom Selection</span>
                    </div>
                </div>`;

                modalBody.innerHTML = html;

                // Add event delegation for visualization options
                document.addEventListener('click', handleVizOptionClick);
            })
            .catch(error => {
                console.error('Error loading visualization types:', error);
                modalBody.innerHTML = '<p class="error-message">Error loading visualization types. Please try again.</p>';
            });
    }

    /**
     * @brief Generates a visualization for the selected file and type.
     * @filename The name of the file to visualize. 
     */

    function showCustomSelection(filename) {
        const modalBody = document.querySelector('.modal-body');
        modalBody.innerHTML = '<p class="loading">Loading columns...</p>';
        
        fetch(`/api/columns/${filename}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    modalBody.innerHTML = `<p class="error-message">${data.error}</p>`;
                    return;
                }
                
                const columns = data.columns;
                if (!columns || columns.length === 0) {
                    modalBody.innerHTML = '<p class="error-message">No columns available for visualization.</p>';
                    return;
                }
                
                let html = `
                    <h3>Select Parameters for Custom Visualization</h3>
                    <p>Choose at least one parameter to include in your visualization:</p>
                    <div class="column-selection">`;
                
                columns.forEach(column => {
                    html += `
                        <label class="column-option">
                            <input type="checkbox" name="column" value="${column}">
                            <span>${column}</span>
                        </label>`;
                });
                
                html += `</div>
                    <div class="action-buttons">
                        <button id="generate-custom-viz" class="action-button" data-filename="${filename}">
                            <span class="icon">📊</span> Generate Visualization
                        </button>
                        <button id="back-to-viz-options" class="action-button secondary" data-filename="${filename}">
                            <span class="icon">↩️</span> Back
                        </button>
                    </div>`;
                
                modalBody.innerHTML = html;
                
                // Add handlers
                document.getElementById('generate-custom-viz').addEventListener('click', function() {
                    const selectedColumns = Array.from(
                        document.querySelectorAll('input[name="column"]:checked')
                    ).map(input => input.value);
                    
                    if (selectedColumns.length === 0) {
                        alert('Please select at least one parameter');
                        return;
                    }
                    
                    generateVisualization(filename, 'custom', selectedColumns);
                });
                
                document.getElementById('back-to-viz-options').addEventListener('click', function() {
                    showVisualizationOptions(filename);
                });
            })
            .catch(error => {
                console.error('Error loading columns:', error);
                modalBody.innerHTML = '<p class="error-message">Error loading columns. Please try again.</p>';
            });
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
     * @brief Handles clicks on visualization options.
     * @event The click event that triggered this function. 
     */

    function handleVizOptionClick(event) {
        const vizOption = event.target.closest('.viz-option');
        if (!vizOption) return;

        document.removeEventListener('click', handleVizOptionClick);
        
        const vizType = vizOption.dataset.vizType;
        const filename = vizOption.dataset.filename;
        
        if (vizType === 'custom') {
            showCustomSelection(filename);
        } else {
            generateVisualization(filename, vizType);
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

    /**
     * @brief Generates a visualization for the selected file and type.
     * @filename The name of the file to visualize.
     * @vizType The type of visualization to generate.
     * @columns Optional array of columns for custom visualization.
     */

    function generateVisualization(filename, vizType, columns = null) {
        const modalBody = document.querySelector('.modal-body');
        modalBody.innerHTML = '<div class="loading">Generating visualization...</div>';

        let fetchPromise;

        if (vizType === 'custom' && columns) {
            fetchPromise = fetch(`/api/visualize/custom/${filename}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ columns: columns })
            });
        } else {
            fetchPromise = fetch(`/api/visualize/${filename}/${vizType}`);
        }

        // Process the response for both types
        fetchPromise
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    modalBody.innerHTML = `<p class="error-message">${data.error}</p>`;
                    return;
                }

                const title = vizType === 'custom' ? 'Custom' : '';
                modalBody.innerHTML = `
                    <h3>${title} Visualization Generated</h3>
                    <p>Your visualization has been generated successfully. Download the plots:</p>
                    <div class="download-options">
                        <a href="${data.regular_plot}" class="action-button" download>
                            <span class="icon">📥</span> Download Standard Plot
                        </a>
                        <a href="${data.normalized_plot}" class="action-button" download>
                            <span class="icon">📥</span> Download Normalized Plot
                        </a>
                    </div>
                    <button id="back-to-viz-options" class="action-button secondary spaced" data-filename="${filename}">
                        <span class="icon">↩️</span> Back to Visualization Options
                    </button>`;

                document.getElementById('back-to-viz-options').addEventListener('click', function() {
                    showVisualizationOptions(filename);
                });
            })
            .catch(error => {
                console.error('Error generating visualization:', error);
                modalBody.innerHTML = '<p class="error-message">Error generating visualization. Please try again.</p>';
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
            <p>Select a file to ${modalMode}:</p>
            <div id="file-list"></div>
        `;

        modalMode = '';
        document.removeEventListener('click', handleVizOptionClick);
    }
});