window.GenericChartBuilder = {
    chartInstance: null,
    data: [],
    fields: [],

    init: function(containerId, data, fields) {
        const container = document.getElementById(containerId);
        if (!container) return;

        this.data = data;
        this.fields = fields;

        // Build UI
        let html = `
            <div class="chart-controls" style="margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 15px; align-items: flex-start;">
                <div>
                    <label style="display:block; margin-bottom:5px; font-weight:600;">X-Axis</label>
                    <select id="cb-x-axis" style="padding: 6px; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-color); color: var(--text-color); min-width: 150px;"></select>
                </div>
                <div>
                    <label style="display:block; margin-bottom:5px; font-weight:600;">Y-Axis (Multi)</label>
                    <select id="cb-y-axis" multiple size="4" style="padding: 6px; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-color); color: var(--text-color); min-width: 150px;"></select>
                    <div style="font-size: 11px; color: #888; margin-top: 3px;">Ctrl/Cmd+Click (or tap) to select multiple</div>
                </div>
                <div>
                    <label style="display:block; margin-bottom:5px; font-weight:600;">Breakdown (Multi)</label>
                    <select id="cb-breakdown" multiple size="4" style="padding: 6px; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-color); color: var(--text-color); min-width: 150px;">
                    </select>
                </div>
                <div>
                    <label style="display:block; margin-bottom:5px; font-weight:600;">Chart Type</label>
                    <select id="cb-type" style="padding: 6px; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-color); color: var(--text-color);">
                        <option value="line">Line Chart</option>
                        <option value="bar">Bar Chart</option>
                    </select>
                </div>
                <div style="align-self: flex-end; margin-bottom: 16px;">
                    <button class="btn" onclick="window.GenericChartBuilder.render()" style="padding: 7px 15px; cursor: pointer; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-color); color: var(--text-color); font-weight:bold;">Draw Chart</button>
                </div>
            </div>
            <div style="position: relative; height: 55vh; width: 100%;">
                <canvas id="cb-canvas"></canvas>
            </div>
        `;
        container.innerHTML = html;

        const xSel = document.getElementById('cb-x-axis');
        const ySel = document.getElementById('cb-y-axis');
        const bSel = document.getElementById('cb-breakdown');

        fields.forEach(f => {
            xSel.add(new Option(f, f));
            ySel.add(new Option(f, f));
            bSel.add(new Option(f, f));
        });

        // Smart defaults if possible
        if (fields.length >= 2) {
            xSel.selectedIndex = 0;
            ySel.options[1].selected = true;
        } else if (fields.length === 1) {
            xSel.selectedIndex = 0;
            ySel.options[0].selected = true;
        }

        // Auto-render initial
        if (typeof Chart !== 'undefined') {
            this.render();
        }
    },

    getSelectValues: function(select) {
        let result = [];
        let options = select && select.options;
        let opt;
        for (let i=0, iLen=options.length; i<iLen; i++) {
            opt = options[i];
            if (opt.selected && opt.value) {
                result.push(opt.value);
            }
        }
        return result;
    },

    render: function() {
        if (typeof Chart === 'undefined') {
            alert("Chart.js library is still loading or failed to load. Please try again in a moment.");
            return;
        }

        const xAxis = document.getElementById('cb-x-axis').value;
        const yAxes = this.getSelectValues(document.getElementById('cb-y-axis'));
        const breakdowns = this.getSelectValues(document.getElementById('cb-breakdown'));
        const chartType = document.getElementById('cb-type').value;

        if (!xAxis || yAxes.length === 0) {
            alert("Please select an X-Axis and at least one Y-Axis.");
            return;
        }

        const ctx = document.getElementById('cb-canvas').getContext('2d');
        
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        let datasets = [];
        let labels = [];

        // Extract unique X values and sort them
        const xSet = new Set();
        this.data.forEach(row => {
            if (row[xAxis] !== undefined && row[xAxis] !== '') {
                xSet.add(row[xAxis]);
            }
        });
        labels = Array.from(xSet).sort();

        // Helper color palette
        const colors = [
            'rgba(54, 162, 235, 0.7)',  // Blue
            'rgba(255, 99, 132, 0.7)',  // Red
            'rgba(75, 192, 192, 0.7)',  // Green
            'rgba(255, 206, 86, 0.7)',  // Yellow
            'rgba(153, 102, 255, 0.7)', // Purple
            'rgba(255, 159, 64, 0.7)',  // Orange
            'rgba(199, 199, 199, 0.7)', // Grey
            'rgba(83, 102, 255, 0.7)',  // Indigo
            'rgba(255, 99, 255, 0.7)'   // Pink
        ];
        const borderColors = colors.map(c => c.replace('0.7', '1'));

        let colorIdx = 0;

        // Determine all unique breakdown combinations present in the data
        let groupKeys = ["No Breakdown"];
        if (breakdowns.length > 0) {
            const bSet = new Set();
            this.data.forEach(row => {
                let keyParts = [];
                let hasValidBreakdown = false;
                breakdowns.forEach(b => {
                    if (row[b] !== undefined && row[b] !== '') {
                        keyParts.push(row[b]);
                        hasValidBreakdown = true;
                    } else {
                        keyParts.push("Unknown");
                    }
                });
                if (hasValidBreakdown) {
                    bSet.add(keyParts.join(" | "));
                }
            });
            groupKeys = Array.from(bSet).sort();
        }

        yAxes.forEach(yAxis => {
            groupKeys.forEach(group => {
                let dataPoints = labels.map(l => {
                    let rows = this.data.filter(r => {
                        let matchX = r[xAxis] === l;
                        if (!matchX) return false;
                        
                        if (breakdowns.length > 0) {
                            let keyParts = breakdowns.map(b => (r[b] !== undefined && r[b] !== '') ? r[b] : "Unknown");
                            return keyParts.join(" | ") === group;
                        }
                        return true;
                    });
                    return rows.reduce((acc, r) => acc + (parseFloat(r[yAxis]) || 0), 0);
                });

                let label = yAxis;
                if (breakdowns.length > 0) {
                    label = `${group} (${yAxis})`;
                } else if (yAxes.length > 1) {
                    label = yAxis;
                }

                datasets.push({
                    label: label,
                    data: dataPoints,
                    backgroundColor: colors[colorIdx % colors.length],
                    borderColor: borderColors[colorIdx % borderColors.length],
                    borderWidth: 2,
                    fill: chartType === 'line' ? false : true,
                    tension: 0.1
                });
                colorIdx++;
            });
        });

        Chart.defaults.color = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? '#d4d4d4' : '#666';

        this.chartInstance = new Chart(ctx, {
            type: chartType,
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { color: 'rgba(128, 128, 128, 0.2)' }
                    },
                    y: { 
                        beginAtZero: true,
                        grid: { color: 'rgba(128, 128, 128, 0.2)' }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { boxWidth: 12 }
                    }
                }
            }
        });
    }
};