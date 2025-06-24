// static/app.js

document.addEventListener('DOMContentLoaded', function() {

    // THEME SWITCHER

    const themeSwitcher = document.querySelector('.theme-switcher');
    const themeIcon = document.getElementById('theme-icon');
    const sunIcon = "https://raw.githubusercontent.com/feathericons/feather/master/icons/sun.svg";
    const moonIcon = "https://raw.githubusercontent.com/feathericons/feather/master/icons/moon.svg";

    const setTheme = (isDark) => {
        document.body.classList.toggle('dark-mode', isDark);
        themeIcon.src = isDark ? sunIcon : moonIcon;
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    };

    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDarkMode = savedTheme ? savedTheme === 'dark' : prefersDark;
    setTheme(isDarkMode);

    themeSwitcher.addEventListener('click', () => {
        setTheme(!document.body.classList.contains('dark-mode'));
    });

    // APPLICATION LOGIC

    const loggerStatus = document.getElementById('logger-status');
    const lastUpdate = document.getElementById('last-update');
    const latestReadingsDiv = document.getElementById('latest-readings');
    const logButton = document.getElementById('log-button');
    const logButtonText = document.getElementById('log-button-text');
    
    const menuButtons = {
        log: logButton,
        view: document.getElementById('view-data-button'),
        analyze: document.getElementById('analyze-data-button'),
        visualize: document.getElementById('visualize-data-button'),
        settings: document.getElementById('settings-button')
    };

    let isLogging = false;
    let pollingInterval = null;

    function checkInitialStatus() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                updateLoggerUI(data.status === 'running');
                if (data.status === 'running') {
                    startDataPolling();
                }
            })
            .catch(error => {
                console.error('Error fetching initial status:', error);
                loggerStatus.textContent = 'Unknown';
                loggerStatus.style.color = 'orange';
            });
    }

    function updateLoggerUI(loggingStatus) {
        isLogging = loggingStatus;
        if (isLogging) {
            loggerStatus.textContent = 'Active';
            loggerStatus.classList.add('active');
            logButton.classList.add('active');
            logButtonText.textContent = 'Stop Logging';
        } else {
            loggerStatus.textContent = 'Inactive';
            loggerStatus.classList.remove('active');
            logButton.classList.remove('active');
            logButtonText.textContent = 'Log New Data';
        }
    }

    // Event listeners for menu buttons
    menuButtons.log.addEventListener('click', () => handleLoggerToggle());
    menuButtons.view.addEventListener('click', () => showFileModal('view'));
    menuButtons.analyze.addEventListener('click', () => showFileModal('analyze'));
    menuButtons.visualize.addEventListener('click', () => showFileModal('visualize'));
    menuButtons.settings.addEventListener('click', () => showSettingsModal());

    // Modal close event listener
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('close-modal') || event.target.classList.contains('modal')) {
            const modal = event.target.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
            }
        }
    });

    function showFileModal(mode) {
        const modal = document.getElementById('file-modal');
        const modalTitle = document.getElementById('file-modal-title');
        const modalBody = document.getElementById('file-modal-body');

        const titles = {
            view: "View Data",
            analyze: "Analyze Data",
            visualize: "Visualize Data"
        };
        modalTitle.textContent = titles[mode];
        modalBody.innerHTML = '<p class="loading">Loading files...</p>';
        modal.style.display = 'flex';

        fetch('/api/files')
            .then(response => response.json())
            .then(files => {
                if (files.length === 0) {
                    modalBody.innerHTML = '<p class="empty-message">No data files available.</p>';
                    return;
                }
                
                let fileListHTML = '<div class="file-list">';
                files.reverse().forEach(file => { // Show newest first
                    const match = file.match(/^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})\.csv$/);
                    const dateStr = match ? new Date(`${match[1]}-${match[2]}-${match[3]}T${match[4]}:${match[5]}:${match[6]}`).toLocaleString() : "N/A";

                    fileListHTML += `
                        <div class="file-item" data-filename="${file}" data-mode="${mode}">
                            <div>
                                <strong>${file}</strong>
                                <div class="file-item-date">Created: ${dateStr}</div>
                            </div>
                            <img src="https://raw.githubusercontent.com/feathericons/feather/master/icons/chevron-right.svg" class="icon" alt="Select">
                        </div>
                    `;
                });
                fileListHTML += '</div>';
                modalBody.innerHTML = fileListHTML;

                document.querySelectorAll('.file-item').forEach(item => {
                    item.addEventListener('click', handleFileItemClick);
                });
            })
            .catch(error => {
                console.error('Error fetching files:', error);
                modalBody.innerHTML = '<p class="error-message">Error loading files. Please try again.</p>';
            });
    }
    
    function handleFileItemClick(event) {
        const fileItem = event.currentTarget;
        const filename = fileItem.dataset.filename;
        const mode = fileItem.dataset.mode;
        
        if (mode === 'analyze') showAnalysisOptions(filename);
        else if (mode === 'view') window.location.href = `/api/files/${filename}`;
        else if (mode === 'visualize') showVisualizationOptions(filename);
    }

    function showAnalysisOptions(filename) {
        const modalBody = document.getElementById('file-modal-body');
        document.getElementById('file-modal-title').textContent = `Analyze: ${filename}`;
        modalBody.innerHTML = '<p class="loading">Analyzing data...</p>';

        fetch(`/api/analyze/${filename}`).then(response => response.json()).then(data => {
            if (data.error) { modalBody.innerHTML = `<p class="error-message">${data.error}</p>`; return; }
            const formattedAnalysis = data.analysis_text.replace(/\n/g, '<br>').replace(/=+/g, '<hr>');
            modalBody.innerHTML = `
                <div class="statistics-container"><div class="statistics-output">${formattedAnalysis}</div></div>
                <button id="download-stats" class="action-button"><img src="https://raw.githubusercontent.com/feathericons/feather/master/icons/download.svg" class="icon" style="filter:invert(100%)">Download Statistics</button>`;
            document.getElementById('download-stats').addEventListener('click', () => downloadStatistics(data.analysis_text, filename));
        }).catch(err => modalBody.innerHTML = '<p class="error-message">Error analyzing data.</p>');
    }

    function showVisualizationOptions(filename) {
        const modalBody = document.getElementById('file-modal-body');
        document.getElementById('file-modal-title').textContent = `Visualize: ${filename}`;
        modalBody.innerHTML = '<p class="loading">Loading visualization types...</p>';

        fetch('/api/visualization-types').then(r => r.json()).then(types => {
            if (!types || !types.length) {
                modalBody.innerHTML = '<p class="error-message">No visualization types available.</p>';
                return;
            }

            let html = '<h3>Select Visualization Type</h3><div class="viz-options">';
            const icons = {
                'Voltage Comparison': 'zap',
                'Current Comparison': 'activity',
                'Power Analysis': 'bar-chart-2',
                'Energy Consumption': 'battery-charging',
                'All Parameters': 'layers',
                'Custom Selection': 'edit-3'
            };

            types.forEach(type => {
                const iconName = icons[type.name] || 'trending-up';
                html += `
                    <div class="viz-option" data-viz-type="${type.id}" data-filename="${filename}">
                        <img src="https://raw.githubusercontent.com/feathericons/feather/master/icons/${iconName}.svg" class="icon" alt="">
                        <span>${type.name}</span>
                    </div>`;
            });

            // Add custom option separately to ensure it's always last
            html += `
                <div class="viz-option" data-viz-type="custom" data-filename="${filename}">
                    <img src="https://raw.githubusercontent.com/feathericons/feather/master/icons/edit-3.svg" class="icon" alt="">
                    <span>Custom Selection</span>
                </div>`;

            html += '</div>';
            modalBody.innerHTML = html;

            document.querySelectorAll('.viz-option').forEach(item => {
                item.addEventListener('click', e => {
                    const el = e.currentTarget;
                    if (el.dataset.vizType === 'custom') {
                        showCustomSelection(el.dataset.filename);
                    } else {
                        generateVisualization(el.dataset.filename, el.dataset.vizType);
                    }
                });
            });
        }).catch(err => modalBody.innerHTML = '<p class="error-message">Error loading types.</p>');
    }

    function showCustomSelection(filename) {
        const modalBody = document.getElementById('file-modal-body');
        modalBody.innerHTML = '<p class="loading">Loading columns...</p>';

        fetch(`/api/columns/${filename}`).then(r => r.json()).then(data => {
            if (data.error) { modalBody.innerHTML = `<p class="error-message">${data.error}</p>`; return; }
            let html = `<h3>Select Parameters</h3><div class="column-selection">`;
            data.columns.forEach(column => {
                html += `<label class="column-option"><input type="checkbox" name="column" value="${column}"><span>${column}</span></label>`;
            });
            html += `</div><div class="action-buttons">
                <button id="generate-custom-viz" class="action-button">Generate</button>
                <button id="back-to-viz-options" class="action-button secondary">Back</button>
                </div>`;
            modalBody.innerHTML = html;
            document.getElementById('generate-custom-viz').addEventListener('click', () => {
                const selected = Array.from(document.querySelectorAll('input[name="column"]:checked')).map(cb => cb.value);
                if (selected.length > 0) generateVisualization(filename, 'custom', selected);
                else alert('Please select at least one parameter.');
            });
            document.getElementById('back-to-viz-options').addEventListener('click', () => showVisualizationOptions(filename));
        }).catch(err => modalBody.innerHTML = '<p class="error-message">Error loading columns.</p>');
    }
    
    function generateVisualization(filename, vizType, columns = null) {
        const modalBody = document.getElementById('file-modal-body');
        modalBody.innerHTML = '<div class="loading">Generating visualization...</div>';

        const fetchPromise = vizType === 'custom' && columns
            ? fetch(`/api/visualize/custom/${filename}`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({columns}) })
            : fetch(`/api/visualize/${filename}/${vizType}`);
            
        fetchPromise.then(r => r.json()).then(data => {
            if (data.error) { modalBody.innerHTML = `<p class="error-message">${data.error}</p>`; return; }
            modalBody.innerHTML = `
                <h3>Visualization Generated</h3>
                <p>Download the generated plot images:</p>
                <div class="download-options">
                    <a href="${data.regular_plot}" class="action-button" download style="text-decoration: none;">Download Standard Plot</a>
                    <a href="${data.normalized_plot}" class="action-button" download style="text-decoration: none;">Download Normalized Plot</a>
                </div>
                <button id="back-to-viz-options" class="action-button secondary" style="margin-top: 1rem;">Back</button>`;
            document.getElementById('back-to-viz-options').addEventListener('click', () => showVisualizationOptions(filename));
        }).catch(err => modalBody.innerHTML = '<p class="error-message">Error generating visualization.</p>');
    }

    function handleLoggerToggle() {
        const action = isLogging ? '/api/stop' : '/api/start';

        // Disable the button to prevent double-clicks
        logButton.disabled = true;

        fetch(action, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                const isNowLogging = data.status === 'started' || data.status === 'already_running';
                updateLoggerUI(isNowLogging);
                
                if (isNowLogging) {
                    startDataPolling();
                } else {
                    stopDataPolling();
                    const readingsDiv = document.getElementById('latest-readings');
                    readingsDiv.innerHTML = '<h2>Latest Readings</h2><p>No data available. Start logging to see real-time measurements.</p>';
                    lastUpdate.textContent = 'Never';
                }

                if (data.status === 'error') {
                    alert('An error occurred: ' + (data.message || 'Unknown error'));
                }
            })
            .catch(error => { 
                console.error('Error toggling logger:', error); 
                alert('Failed to communicate with the server.'); 
            })
            .finally(() => {
                logButton.disabled = false;
            });
    }

    function startDataPolling() {
        if (pollingInterval) clearInterval(pollingInterval);
        pollingInterval = setInterval(fetchLatestData, 3000);
        fetchLatestData();
    }

    function stopDataPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }

    function fetchLatestData() {
        fetch('/api/latest').then(r => r.json()).then(data => {
            const readingsDiv = document.getElementById('latest-readings');
            const lastUpdateSpan = document.getElementById('last-update');

            if (data && data.ts) {
                lastUpdateSpan.textContent = new Date().toLocaleTimeString();
                let html = '<h2>Latest Readings</h2><table class="readings-table"><thead><tr><th>Parameter</th><th>Value</th></tr></thead><tbody>';

                const order = ['voltage', 'current', 'power', 'energy'];
                const sortedKeys = Object.keys(data).sort((a, b) => {
                    if(a === 'ts' || b === 'ts') return a === 'ts' ? 1 : -1;
                    const aIndex = order.findIndex(p => a.includes(p));
                    const bIndex = order.findIndex(p => b.includes(p));
                    if(aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
                    return a.localeCompare(b);
                });

                for (const key of sortedKeys) {
                    if(key === 'ts') continue;
                    const value = data[key];
                    const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    html += `<tr><td>${formattedKey}</td><td>${Number(value).toFixed(3)}</td></tr>`;
                }
                html += '</tbody></table>';
                readingsDiv.innerHTML = html;
            }
        }).catch(err => console.error('Error fetching data:', err));
    }

    function showSettingsModal() {
        const modal = document.getElementById('settings-modal');
        const body = document.getElementById('settings-body');
        modal.style.display = 'flex';
        body.innerHTML = '<p class="loading">Loading settings...</p>';

        fetch('/api/settings')
            .then(response => response.json())
            .then(data => {
                body.innerHTML = `
                    <form id="settings-form">
                        <div class="form-group">
                            <label for="log_interval">Logging Interval (Seconds)</label>
                            <input type="number" id="log_interval" name="log_interval" value="${data.log_interval}" min="1" required>
                        </div>
                        <div class="form-group">
                            <label for="modbus_slave_id">Modbus Slave ID</label>
                            <input type="number" id="modbus_slave_id" name="modbus_slave_id" value="${data.modbus_slave_id}" min="1" max="247" required>
                        </div>
                        <div class="form-group">
                            <label for="baudrate">Baud Rate</label>
                            <select id="baudrate" name="baudrate">
                                <option value="1200" ${data.baudrate === 1200 ? 'selected' : ''}>1200</option>
                                <option value="2400" ${data.baudrate === 2400 ? 'selected' : ''}>2400</option>
                                <option value="4800" ${data.baudrate === 4800 ? 'selected' : ''}>4800</option>
                                <option value="9600" ${data.baudrate === 9600 ? 'selected' : ''}>9600 (Standard)</option>
                                <option value="19200" ${data.baudrate === 19200 ? 'selected' : ''}>19200</option>
                                <option value="38400" ${data.baudrate === 38400 ? 'selected' : ''}>38400</option>
                                <option value="57600" ${data.baudrate === 57600 ? 'selected' : ''}>57600</option>
                                <option value="115200" ${data.baudrate === 115200 ? 'selected' : ''}>115200</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="parity">Parity</label>
                            <select id="parity" name="parity">
                                <option value='N' ${data.parity === 'N' ? 'selected' : ''}>None (Standard)</option>
                                <option value='E' ${data.parity === 'E' ? 'selected' : ''}>Even</option>
                                <option value='O' ${data.parity === 'O' ? 'selected' : ''}>Odd</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="bytesize">Byte Size</label>
                            <select id="bytesize" name="bytesize">
                                <option value="5" ${data.bytesize === 5 ? 'selected' : ''}>5</option>
                                <option value="6" ${data.bytesize === 6 ? 'selected' : ''}>6</option>
                                <option value="7" ${data.bytesize === 7 ? 'selected' : ''}>7</option>
                                <option value="8" ${data.bytesize === 8 ? 'selected' : ''}>8 (Standard)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="stopbits">Stop Bits</label>
                            <select id="stopbits" name="stopbits">
                                <option value="1" ${data.stopbits === 1 ? 'selected' : ''}>1 (Standard)</option>
                                <option value="2" ${data.stopbits === 2 ? 'selected' : ''}>2</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="timeout">Timeout (Seconds)</label>
                            <input type="number" id="timeout" name="timeout" value="${data.timeout}" min="1" required>
                        </div>
                        <div class="action-buttons">
                            <button type="submit" class="action-button">Save Settings</button>
                        </div>
                    </form>
                `;

                document.getElementById('settings-form').addEventListener('submit', handleSaveSettings);
            })
            .catch(error => {
                body.innerHTML = '<p class="error-message">Could not load settings.</p>';
            });
    }

    function handleSaveSettings(event) {
        event.preventDefault();
        const form = event.target;
        const button = form.querySelector('button[type="submit"]');
        button.textContent = 'Saving...';
        button.disabled = true;

        const newSettings = {
            LOG_INTERVAL: parseInt(form.log_interval.value, 10),
            MODBUS_SLAVE_ID: parseInt(form.modbus_slave_id.value, 10),
            BAUDRATE: parseInt(form.baudrate.value, 10),
            PARITY: form.parity.value,
            BYTESIZE: parseInt(form.bytesize.value, 10),
            STOPBITS: parseInt(form.stopbits.value, 10),
            TIMEOUT: parseInt(form.timeout.value, 10)
        };

        fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newSettings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Settings saved. If a session was active, it has been stopped. Please start a new session for changes to take effect.');
                document.getElementById('settings-modal').style.display = 'none';
                // Re-check the main status since stopping the logger is a side effect
                checkInitialStatus(); 
            } else {
                alert('Error saving settings: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => alert('Failed to save settings.'))
        .finally(() => {
            button.textContent = 'Save Settings';
            button.disabled = false;
        });
    }

    function downloadStatistics(text, filename) {
        const statsFilename = filename.replace('.csv', '_statistics.txt');
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = statsFilename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    // INITIAL CHECK

    checkInitialStatus();
});