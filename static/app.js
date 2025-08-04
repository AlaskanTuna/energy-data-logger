// static/app.js

document.addEventListener('DOMContentLoaded', function() {

    // DARK-LIGHT THEME SWITCHER

    const themeSwitcher = document.querySelector('.theme-switcher');
    const themeIcon = document.getElementById('theme-icon');
    const sunIcon = "/static/icons/sun.svg";
    const moonIcon = "/static/icons/moon.svg";

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

    // UI ELEMENTS

    const lastUpdate = document.getElementById('last-update');
    const logButton = document.getElementById('log-button');
    const logButtonText = document.getElementById('log-button-text');
    const menuButtons = {
        log: logButton,
        view: document.getElementById('view-data-button'),
        analyze: document.getElementById('analyze-data-button'),
        visualize: document.getElementById('visualize-data-button'),
        download: document.getElementById('download-logs-button'),
        settings: document.getElementById('settings-button')
    };

    // GLOBAL VARIABLES

    let dataPollingInterval = null;
    let statusPollingInterval = null;

    // STATUS POLLING AND RENDERING

    function startStatusPolling() {
        if (statusPollingInterval) clearInterval(statusPollingInterval);
        fetchStatus();
        statusPollingInterval = setInterval(fetchStatus, 5000);
    }

    function fetchStatus() {
        fetch('/api/schedules/status')
            .then(response => response.json())
            .then(data => {
                updateUIFromStatus(data);
            })
            .catch(error => {
                console.error('Error fetching status:', error);
                document.getElementById('logger-status').textContent = 'Error';
                document.getElementById('logger-status').className = 'error';
            });
    }

    function updateUIFromStatus(data) {
        const modeMap = {
            'none': 'None',
            'default': 'Default',
            'once': 'Scheduled (Once)',
            'recurring': 'Scheduled (Recurring)'
        };
        const statusMap = {
            'idle': 'Idle',
            'scheduled': 'Scheduled',
            'logging': 'Logging'
        };

        document.getElementById('logger-mode').textContent = modeMap[data.mode] || 'Unknown';
        const statusElement = document.getElementById('logger-status');
        statusElement.textContent = statusMap[data.status] || 'Unknown';
        statusElement.className = 'logger-status ' + data.status;

        const lastUpdateElement = document.getElementById('last-update');
        if (data.status === 'logging' && data.lastUpdated) {
            lastUpdateElement.textContent = new Date(data.lastUpdated).toLocaleTimeString();
        } else {
            lastUpdateElement.textContent = 'None';
        }

        if (data.status === 'idle' && data.mode === 'none') {
            logButtonText.textContent = 'Log New Data';
            logButton.onclick = () => showScheduleModal();
            logButton.classList.remove('active');
        } else {
            logButtonText.textContent = 'Stop Logging';
            logButton.onclick = () => clearSchedule();
            logButton.classList.add('active');
        }

        if (data.status === 'logging') {
            if (!dataPollingInterval) startDataPolling();
        } else {
            if (dataPollingInterval) stopDataPolling();
            document.getElementById('latest-readings').innerHTML = '<h2>Latest Readings</h2><p>No data available. Start logging to see real-time measurements.</p>';
        }
    }

    // EVENT LISTENERS

    menuButtons.view.addEventListener('click', () => showFileModal('view'));
    menuButtons.analyze.addEventListener('click', () => showFileModal('analyze'));
    menuButtons.visualize.addEventListener('click', () => showFileModal('visualize'));
    menuButtons.download.addEventListener('click', () => showFileModal('download'));
    menuButtons.settings.addEventListener('click', () => showSettingsModal());

    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('close-modal') || event.target.classList.contains('modal')) {
            const modal = event.target.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
            }
        }
    });

    function handleFileItemClick(event) {
        const fileItem = event.currentTarget;
        const filename = fileItem.dataset.filename;
        const mode = fileItem.dataset.mode;
        
        if (mode === 'analyze') showAnalysisOptions(filename);
        else if (mode === 'view') window.location.href = `/api/files/${filename}`;
        else if (mode === 'download') window.location.href = `/api/logs/${filename}`;
        else if (mode === 'visualize') showVisualizationOptions(filename);
    }

    // LOG NEW DATA MODAL

    function showScheduleModal() {
        const modal = document.getElementById('schedule-modal');
        modal.querySelector('[data-mode="default"]').click();
        modal.querySelector('[data-schedule-type="once"]').click();
        modal.querySelector('#start-time').value = '';
        modal.querySelector('#end-time').value = '';
        modal.querySelector('#day-interval').value = '0';
        modal.style.display = 'flex';
    }

    function clearSchedule() {
        if (!confirm('Do you want to stop the current logging session and clear all log schedules?')) {
            return;
        }
        fetch('/api/schedules/clear', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if(data.status === 'cleared'){
                    fetchStatus();
                } else {
                    alert('Failed to stop logging session and clear schedules.');
                }
            });
    }

    // Add event listeners for the new schedule modal
    const scheduleModal = document.getElementById('schedule-modal');
    const scheduleOptions = document.getElementById('schedule-options');
    const automatedInputs = document.getElementById('automated-schedule-inputs');
    const startTimeInput = document.getElementById('start-time');
    const endTimeInput = document.getElementById('end-time');
    const endTimeLabel = document.getElementById('label[for="end-time"]');
    
    scheduleModal.querySelector('[data-mode="default"]').addEventListener('click', (e) => {
        scheduleOptions.style.display = 'none';
        document.querySelectorAll('[data-mode]').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
    });
    scheduleModal.querySelector('[data-mode="scheduled"]').addEventListener('click', (e) => {
        scheduleOptions.style.display = 'block';
        document.querySelectorAll('[data-mode]').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
    });
    scheduleModal.querySelector('[data-schedule-type="once"]').addEventListener('click', (e) => {
        automatedInputs.style.display = 'none';
        document.querySelectorAll('[data-schedule-type]').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');

        endTimeInput.required = false;
        endTimeLabel.textContent = 'End Time';
    });
    scheduleModal.querySelector('[data-schedule-type="recurring"]').addEventListener('click', (e) => {
        automatedInputs.style.display = 'block';
        document.querySelectorAll('[data-schedule-type]').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');

        endTimeInput.required = true;
        endTimeLabel.textContent = 'End Time';
    });

    document.getElementById('start-schedule-button').addEventListener('click', () => {
        const payload = {};
        const modeButton = scheduleModal.querySelector('.sg-button[data-mode].active');
        const selectedMode = modeButton.dataset.mode;

        if (selectedMode === 'default') {
            payload.mode = 'default';
        } else if (selectedMode === 'scheduled') {
            const typeButton = scheduleModal.querySelector('.sg-button[data-schedule-type].active');
            payload.mode = typeButton.dataset.scheduleType;

            payload.start_time = document.getElementById('start-time').value;
            payload.end_time = document.getElementById('end-time').value;

            if (!payload.start_time) {
                alert("Please provide a start time for the schedule.");
                return;
            }

            if (payload.mode === 'recurring' && !payload.end_time) {
                alert("Please provide an end time for a recurring schedule.");
                return;
            }

            if (payload.mode === 'recurring') {
                payload.day_interval = document.getElementById('day-interval').value;
            }
        } else {
            alert("Invalid logging mode selected.");
            return;
        }
        console.log("Sending schedule payload:", JSON.stringify(payload));

        fetch('/api/schedules/set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).then(res => res.json()).then(data => {
            if (data.error) {
                alert('Error setting schedule: ' + data.error);
            } else {
                scheduleModal.style.display = 'none';
                fetchStatus();
            }
        }).catch(err => {
            console.error('Fetch error:', err);
            alert('An unexpected error occurred while starting the logger.');
        });
    });

    // VIEW DATA MODAL

    function showFileModal(mode) {
        const modal = document.getElementById('file-modal');
        const modalTitle = document.getElementById('file-modal-title');
        const modalBody = document.getElementById('file-modal-body');

        const titles = {
            view: "View Data",
            analyze: "Analyze Data",
            visualize: "Visualize Data",
            download: "Download Application Logs"
        };
        const apiEndpoint = (mode === 'download') ? '/api/logs' : '/api/files';

        modalTitle.textContent = titles[mode];
        modalBody.innerHTML = '<p class="loading">Loading files...</p>';
        modal.style.display = 'flex';

        fetch(apiEndpoint)
            .then(response => response.json())
            .then(files => {
                if (files.length === 0) {
                    modalBody.innerHTML = '<p class="empty-message">No files available.</p>';
                    return;
                }

                let fileListHTML = '<div class="file-list">';
                files.reverse().forEach(file => { // Show latest file on top
                    const namePart = file.split('.')[0];
                    const match = namePart.match(/^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$/);
                    const dateStr = match ? new Date(`${match[1]}-${match[2]}-${match[3]}T${match[4]}:${match[5]}:${match[6]}`).toLocaleString() : "N/A";

                    fileListHTML += `
                        <div class="file-item" data-filename="${file}" data-mode="${mode}">
                            <div>
                                <strong>${file}</strong>
                                <div class="file-item-date">Created: ${dateStr}</div>
                            </div>
                            <img src="/static/icons/chevron-right.svg" class="icon" alt="Select">
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

    // ANALYZE DATA MODAL

    function showAnalysisOptions(filename) {
        const modalTitle = document.getElementById('file-modal-title');
        const modalBody = document.getElementById('file-modal-body');

        modalTitle.textContent = `Analyze: ${filename}`;
        modalBody.innerHTML = `
            <h3>Select Analysis Time Range</h3>
            <div class="segmented-control">
                <button class="sg-button active" data-range-type="full">Full Timeline</button>
                <button class="sg-button" data-range-type="custom">Custom Range</button>
            </div>
            
            <div id="custom-range-inputs" style="display: none;">
                <div class="form-group">
                    <label for="start-date">Start Date & Time</label>
                    <div class="datetime-group">
                        <input type="date" id="start-date" name="start-date" class="time-input">
                        <input type="time" id="start-time" name="start-time" class="time-input" step="1">
                    </div>
                </div>
                <div class="form-group">
                    <label for="end-date">End Date & Time</label>
                    <div class="datetime-group">
                        <input type="date" id="end-date" name="end-date" class="time-input">
                        <input type="time" id="end-time" name="end-time" class="time-input" step="1">
                    </div>
                </div>
            </div>

            <div class="action-buttons">
                <button id="run-analysis-button" class="action-button">Run Analysis</button>
                <button id="back-to-file-list" class="action-button secondary">Back</button>
            </div>
        `;

        const segmentedButtons = document.querySelectorAll('.sg-button');
        const customInputs = document.getElementById('custom-range-inputs');

        segmentedButtons.forEach(button => {
            button.addEventListener('click', () => {
                segmentedButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                const rangeType = button.dataset.rangeType;
                customInputs.style.display = rangeType === 'custom' ? 'block' : 'none';
            });
        });

        document.getElementById('back-to-file-list').addEventListener('click', () => showFileModal('analyze'));
        document.getElementById('run-analysis-button').addEventListener('click', () => {
            const activeRangeButton = document.querySelector('.sg-button.active');
            const rangeType = activeRangeButton ? activeRangeButton.dataset.rangeType : 'full';

            let startTime = null;
            let endTime = null;

            if (rangeType === 'custom') {
                const startDate = document.getElementById('start-date').value;
                const startTimeVal = document.getElementById('start-time').value;
                const endDate = document.getElementById('end-date').value;
                const endTimeVal = document.getElementById('end-time').value;

                if (!startDate || !startTimeVal || !endDate || !endTimeVal) {
                    alert('Please select a valid start datetime and an end datetime.');
                    return;
                }

                // Combine date and time into the required ISO format string
                startTime = `${startDate}T${startTimeVal}`;
                endTime = `${endDate}T${endTimeVal}`;
            }

            runAnalysis(filename, startTime, endTime);
        });
    }

    function runAnalysis(filename, startTime, endTime) {
        const modalBody = document.getElementById('file-modal-body');
        modalBody.innerHTML = '<p class="loading">Analyzing data...</p>';

        const payload = {};
        if (startTime && endTime) {
            payload.start_time = startTime;
            payload.end_time = endTime;
        }

        fetch(`/api/analyze/${filename}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).then(response => response.json()).then(data => {
            if (data.error) { 
                modalBody.innerHTML = `<p class="error-message">${data.error}</p>`; 
                return; 
            }
            const formattedAnalysis = data.analysis_text.replace(/\n/g, '<br>').replace(/=+/g, '<hr>');
            modalBody.innerHTML = `
                <div class="statistics-container"><div class="statistics-output">${formattedAnalysis}</div></div>
                <div class="action-buttons">
                    <button id="download-stats" class="action-button">Download Statistics</button>
                    <button id="back-to-time-range" class="action-button secondary">Back</button>
                </div>`;

            document.getElementById('back-to-time-range').addEventListener('click', () => showAnalysisOptions(filename));
            document.getElementById('download-stats').addEventListener('click', () => downloadStatistics(data.analysis_text, filename));

        }).catch(err => {
            console.error('Analysis fetch error:', err);
            modalBody.innerHTML = '<p class="error-message">Error analyzing data.</p>';
        });
    }

    function downloadStatistics(text, filename) {
        try {
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
        } catch (error) {
            console.error('Download error:', error);
            alert('Failed to download statistics. Please try again.');
        }
    }

    // VISUALIZE DATA MODAL

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
                'Voltage': 'zap',
                'Current': 'activity',
                'Active Power': 'bar-chart-2',
                'Reactive Power': '',
                'Apparent Power': '',
                'Energy': 'battery-charging',
                'Energy Tariff': '',
                'Power Factor': '',
                'Custom Selection': 'edit-3',
                'All Parameters': 'layers',
            };

            types.forEach(type => {
                const iconName = icons[type.name] || 'trending-up';
                html += `
                    <div class="viz-option" data-viz-type="${type.id}" data-filename="${filename}">
                        <img src="/static/icons/${iconName}.svg" class="icon" alt="">
                        <span>${type.name}</span>
                    </div>`;
            });

            // Add custom option separately
            html += `
                <div class="viz-option" data-viz-type="custom" data-filename="${filename}">
                    <img src="/static/icons/edit-3.svg" class="icon" alt="">
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

    // SETTINGS MODAL

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
                            <input type="number" id="log_interval" name="log_interval" value="${data.LOG_INTERVAL}" min="1" required>
                        </div>
                        <div class="form-group">
                            <label for="modbus_slave_id">Modbus Slave ID</label>
                            <input type="number" id="modbus_slave_id" name="modbus_slave_id" value="${data.MODBUS_SLAVE_ID}" min="1" max="247" required>
                        </div>
                        <div class="form-group">
                            <label for="baudrate">Baud Rate</label>
                            <select id="baudrate" name="baudrate">
                                <option value="1200" ${data.BAUDRATE === 1200 ? 'selected' : ''}>1200</option>
                                <option value="2400" ${data.BAUDRATE === 2400 ? 'selected' : ''}>2400</option>
                                <option value="4800" ${data.BAUDRATE === 4800 ? 'selected' : ''}>4800</option>
                                <option value="9600" ${data.BAUDRATE === 9600 ? 'selected' : ''}>9600 (Standard)</option>
                                <option value="19200" ${data.BAUDRATE === 19200 ? 'selected' : ''}>19200</option>
                                <option value="38400" ${data.BAUDRATE === 38400 ? 'selected' : ''}>38400</option>
                                <option value="57600" ${data.BAUDRATE === 57600 ? 'selected' : ''}>57600</option>
                                <option value="115200" ${data.BAUDRATE === 115200 ? 'selected' : ''}>115200</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="parity">Parity</label>
                            <select id="parity" name="parity">
                                <option value='N' ${data.PARITY === 'N' ? 'selected' : ''}>None (Standard)</option>
                                <option value='E' ${data.PARITY === 'E' ? 'selected' : ''}>Even</option>
                                <option value='O' ${data.PARITY === 'O' ? 'selected' : ''}>Odd</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="bytesize">Byte Size</label>
                            <select id="bytesize" name="bytesize">
                                <option value="5" ${data.BYTESIZE === 5 ? 'selected' : ''}>5</option>
                                <option value="6" ${data.BYTESIZE === 6 ? 'selected' : ''}>6</option>
                                <option value="7" ${data.BYTESIZE === 7 ? 'selected' : ''}>7</option>
                                <option value="8" ${data.BYTESIZE === 8 ? 'selected' : ''}>8 (Standard)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="stopbits">Stop Bits</label>
                            <select id="stopbits" name="stopbits">
                                <option value="1" ${data.STOPBITS === 1 ? 'selected' : ''}>1 (Standard)</option>
                                <option value="2" ${data.STOPBITS === 2 ? 'selected' : ''}>2</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="timeout">Timeout (Seconds)</label>
                            <input type="number" id="timeout" name="timeout" value="${data.TIMEOUT}" min="1" required>
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

    // DATA POLLING

    function startDataPolling() {
        if (dataPollingInterval) clearInterval(dataPollingInterval);

        fetch('/api/settings')
            .then(response => response.json())
            .then(settings => {
                const logIntervalSeconds = settings.LOG_INTERVAL || 900;
                const pollingIntervalMS = Math.min(logIntervalSeconds * 1000, 5000); 
                dataPollingInterval = setInterval(fetchLatestData, pollingIntervalMS);
                fetchLatestData();
            })
            .catch(error => {
                console.error("Could not fetch settings to start data polling.", error);
                dataPollingInterval = setInterval(fetchLatestData, 5000);
                fetchLatestData();
            });
    }

    function stopDataPolling() {
        if (dataPollingInterval) {
            clearInterval(dataPollingInterval);
            dataPollingInterval = null;
        }
    }

    function fetchLatestData() {
        fetch('/api/latest').then(r => r.json()).then(data => {
            const readingsDiv = document.getElementById('latest-readings');
            if (data && data.ts) {
                let html = '<h2>Latest Readings</h2><table class="readings-table"><thead><tr><th>Parameter</th><th>Value</th></tr></thead><tbody>';

                const units = {
                    'voltage': 'V', 
                    'current': 'A', 
                    'active_power': 'kW',
                    'reactive_power': 'kvar',
                    'apparent_power': 'kVA',
                    'active_energy': 'kWh',
                    'reactive_energy': 'kvarh',
                    'power_factor': '',
                };
                const order = [
                    'voltage', 
                    'current', 
                    'active_power',
                    'reactive_power',
                    'apparent_power',
                    'active_energy',
                    'reactive_energy',
                    'power_factor',
                ];

                // Sort keys with more specific matching
                const sortedKeys = Object.keys(data).sort((a, b) => {
                    if (a === 'ts' || b === 'ts') return a === 'ts' ? 1 : -1;

                    // Find the most specific match for each key
                    function findBestMatch(key) {
                        let bestMatch = null;
                        let bestLength = 0;
                        
                        for (const param of order) {
                            if (key.includes(param) && param.length > bestLength) {
                                bestMatch = param;
                                bestLength = param.length;
                            }
                        }
                        return bestMatch ? order.indexOf(bestMatch) : 999;
                    }

                    const aIndex = findBestMatch(a);
                    const bIndex = findBestMatch(b);

                    if (aIndex !== 999 && bIndex !== 999) return aIndex - bIndex;
                    return a.localeCompare(b);
                });

                for (const key of sortedKeys) {
                    if (key === 'ts') continue;
                    const value = data[key];
                    const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

                    // Find the most specific unit match
                    let unit = '';
                    let bestMatchLength = 0;
                    
                    for (const paramType in units) {
                        if (key.includes(paramType) && paramType.length > bestMatchLength) {
                            unit = units[paramType];
                            bestMatchLength = paramType.length;
                        }
                    }
                    
                    html += `<tr><td>${formattedKey}</td><td>${Number(value).toFixed(3)} ${unit}</td></tr>`;
                }

                html += '</tbody></table>';
                readingsDiv.innerHTML = html;
            }
        }).catch(err => console.error('Error fetching data:', err));
    }

    // Run initial status check
    startStatusPolling();
});