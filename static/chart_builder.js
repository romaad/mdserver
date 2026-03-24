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
            <div class="chart-controls" style="margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 15px; align-items: flex-end;">
                <div>
                    <label style="display:block; margin-bottom:5px; font-weight:600;">X-Axis</label>
                    <select id="cb-x-axis" style="padding: 6px; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-color); color: var(--text-color);"></select>
                </div>
                <div>
                    <label style="display:block; margin-bottom:5px; font-weight:600;">Y-Axis</label>
                    <select id="cb-y-axis" style="padding: 6px; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-color); color: var(--text-color);"></select>
                </div>
                <div>
                    <label style="display:block; margin-bottom:5px; font-weight:600;">Breakdown (opt)</label>
                    <select id="cb-breakdown" style="padding: 6px; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-color); color: var(--text-color);">
                        <option value="">-- None --</option>
                    </select>
                </div>
                <div>
                    <label style="display:block; margin-bottom:5px; font-weight:600;">Chart Type</label>
                    <select id="cb-type" style="padding: 6px; border-radius: 4px; border: 1px solid var(--border-color); background: var(--bg-color); color: var(--text-color);">
                        <option value="line">Line Chart</option>
                        <option value="bar">Bar Chart</option>
                    </select>
                </div>
                <div>
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
            // usually the first column is a date/time/label
            xSel.selectedIndex = 0;
            // and the next numerical column is Y
            ySel.selectedIndex = 1;
        }

        // Auto-render initial
        if (typeof Chart !== 'undefined') {
            this.render();
        }
    },

    render: function() {
        if (typeof Chart === 'undefined') {
            alert("Chart.js library is still loading or failed to load. Please try again in a moment.");
            return;
        }

        const xAxis = document.getElementById('cb-x-axis').value;
        const yAxis = document.getElementById('cb-y-axis').value;
        const breakdown = document.getElementById('cb-breakdown').value;
        const chartType = document.getElementById('cb-type').value;

        if (!xAxis || !yAxis) return;

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
            'rgba(255, 159, 64, 0.7)'   // Orange
        ];
        const borderColors = colors.map(c => c.replace('0.7', '1'));

        if (!breakdown) {
            // No breakdown, single dataset aggregating by X
            let dataPoints = labels.map(l => {
                let rows = this.data.filter(r => r[xAxis] === l);
                // Try summing numeric values, otherwise count them if non-numeric?
                // Assuming numeric for standard metrics:
                let sum = rows.reduce((acc, r) => acc + (parseFloat(r[yAxis]) || 0), 0);
                return sum;
            });

            datasets.push({
                label: yAxis,
                data: dataPoints,
                backgroundColor: colors[0],
                borderColor: borderColors[0],
                borderWidth: 2,
                fill: chartType === 'line' ? false : true,
                tension: 0.1
            });
        } else {
            // Group by breakdown field
            const bSet = new Set();
            this.data.forEach(row => { 
                if (row[breakdown] !== undefined && row[breakdown] !== '') {
                    bSet.add(row[breakdown]);
                }
            });
            const bGroups = Array.from(bSet).sort();

            bGroups.forEach((group, idx) => {
                let dataPoints = labels.map(l => {
                    let rows = this.data.filter(r => r[xAxis] === l && r[breakdown] === group);
                    return rows.reduce((acc, r) => acc + (parseFloat(r[yAxis]) || 0), 0);
                });

                datasets.push({
                    label: `${group} (${yAxis})`,
                    data: dataPoints,
                    backgroundColor: colors[idx % colors.length],
                    borderColor: borderColors[idx % borderColors.length],
                    borderWidth: 2,
                    fill: chartType === 'line' ? false : true,
                    tension: 0.1
                });
            });
        }

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