(function() {
    const sourceView = document.getElementById('source-view');
    const container = document.getElementById('content');
    
    if (!sourceView || !container) {
        console.error("CSV Viewer: Could not find elements.");
        return;
    }

    container.innerHTML = "<p style='padding: 20px;'>Parsing CSV data...</p>";

    let sortAscending = true;
    let currentSortColumn = null;

    try {
        const rawContent = sourceView.textContent.trim();
        const parsedData = parseCSV(rawContent);
        renderTable(parsedData.data, parsedData.meta.fields);
    } catch (err) {
        container.innerHTML = "<p style='color:red; padding: 20px;'>Error: " + err.message + "</p>";
    }

    function parseCSV(str) {
        const lines = str.trim().split('\n');
        if (lines.length === 0) return { data: [], meta: { fields: [] } };
        
        const headers = lines[0].split(',').map(h => h.trim());
        const data = [];
        for (let i = 1; i < lines.length; i++) {
            if (!lines[i].trim()) continue;
            // Basic split (assumes no commas inside quotes for this simple energy tracker)
            const values = lines[i].split(',');
            const row = {};
            headers.forEach((h, index) => {
                row[h] = values[index] ? values[index].trim() : '';
            });
            data.push(row);
        }
        return { data: data, meta: { fields: headers } };
    }


    function renderTable(data, fields) {
        if (!fields || fields.length === 0) {
            container.innerHTML = '<p style="padding:20px;">Empty CSV or no headers found.</p>';
            return;
        }
        
        let tableHTML = '<table class="csv-table"><thead><tr>';
        fields.forEach((field, i) => {
            let sortIndicator = '';
            if (currentSortColumn === field) {
                sortIndicator = sortAscending ? ' 🔼' : ' 🔽';
            }
            const safeField = field.replace(/'/g, "\\'").replace(/"/g, "&quot;");
            tableHTML += `<th onclick="window.sortTable('${safeField}')">${field}${sortIndicator}</th>`;
        });
        tableHTML += '</tr></thead><tbody>';
        
        data.forEach(row => {
            tableHTML += '<tr>';
            fields.forEach(field => {
                const val = row[field] !== undefined ? row[field] : '';
                const safeVal = String(val)
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
                tableHTML += `<td>${safeVal}</td>`;
            });
            tableHTML += '</tr>';
        });
        
        tableHTML += '</tbody></table>';
        container.innerHTML = tableHTML;
        
        // Expose parsed data globally for sorting
        window.__csvData = data;
        window.__csvFields = fields;
        
        if (window.GenericChartBuilder && !window._chartInitialized) {
            window.GenericChartBuilder.init('chart-view', data, fields);
            window._chartInitialized = true;
        }
    }

    window.sortTable = function(columnName) {
        if (currentSortColumn === columnName) {
            sortAscending = !sortAscending;
        } else {
            currentSortColumn = columnName;
            sortAscending = true;
        }
        
        const data = window.__csvData || [];
        const fields = window.__csvFields || [];
        
        data.sort((a, b) => {
            let valA = a[columnName] || '';
            let valB = b[columnName] || '';
            
            let numA = parseFloat(valA);
            let numB = parseFloat(valB);
            
            if (!isNaN(numA) && !isNaN(numB)) {
                return sortAscending ? numA - numB : numB - numA;
            }
            
            valA = valA.toString().toLowerCase();
            valB = valB.toString().toLowerCase();
            
            if (valA < valB) return sortAscending ? -1 : 1;
            if (valA > valB) return sortAscending ? 1 : -1;
            return 0;
        });
        
        renderTable(data, fields);
    };

    window.toggleView = function() {
        const content = document.getElementById('content');
        const source = document.getElementById('source-view');
        if (window.getComputedStyle(source).display === 'none') {
            source.style.display = 'block';
            content.style.display = 'none';
        } else {
            source.style.display = 'none';
            content.style.display = 'block';
        }
    };
})();
    window.switchView = function(viewName) {
        const content = document.getElementById('content');
        const source = document.getElementById('source-view');
        const chart = document.getElementById('chart-view');
        
        content.style.display = viewName === 'table' ? 'block' : 'none';
        chart.style.display = viewName === 'chart' ? 'block' : 'none';
        source.style.display = viewName === 'source' ? 'block' : 'none';
    };

    // Replace old toggleView with switchView logic for backwards compat
    window.toggleView = function() {
        if (document.getElementById('content').style.display !== 'none') {
            window.switchView('source');
        } else {
            window.switchView('table');
        }
    };
