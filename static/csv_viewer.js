(function() {
    const sourceView = document.getElementById('source-view');
    const container = document.getElementById('content');
    
    if (!sourceView || !container) {
        console.error("CSV Viewer: Could not find #source-view or #content elements.");
        return;
    }

    if (typeof Papa === 'undefined') {
        container.innerHTML = '<p style="color:red; padding:20px;">Error: PapaParse library not loaded. Check internet connection or ad blockers.</p>';
        console.error("PapaParse is not defined.");
        return;
    }

    // Use textContent to get the browser-unescaped CSV text
    const rawContent = sourceView.textContent.trim();
    
    // Parse CSV using PapaParse
    const parsedData = Papa.parse(rawContent, {
        header: true,
        skipEmptyLines: true
    });
    
    if (parsedData.errors.length > 0 && parsedData.data.length === 0) {
        container.innerHTML = '<p style="color:red; padding:20px;">Error parsing CSV data.</p>';
        console.error("PapaParse errors:", parsedData.errors);
    } else {
        renderTable(parsedData.data, parsedData.meta.fields);
    }
    
    let sortAscending = true;
    let currentSortColumn = null;

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
            // Escape field for use in HTML string
            const safeField = field.replace(/'/g, "\\'").replace(/"/g, "&quot;");
            tableHTML += `<th onclick="window.sortTable('${safeField}')">${field}${sortIndicator}</th>`;
        });
        tableHTML += '</tr></thead><tbody>';
        
        data.forEach(row => {
            tableHTML += '<tr>';
            fields.forEach(field => {
                // Escape value for use in HTML
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
    }

    // Expose functions to window for inline onclick handlers
    window.sortTable = function(columnName) {
        if (currentSortColumn === columnName) {
            sortAscending = !sortAscending;
        } else {
            currentSortColumn = columnName;
            sortAscending = true;
        }
        
        parsedData.data.sort((a, b) => {
            let valA = a[columnName] || '';
            let valB = b[columnName] || '';
            
            // Try numeric sort first
            let numA = parseFloat(valA);
            let numB = parseFloat(valB);
            
            if (!isNaN(numA) && !isNaN(numB)) {
                return sortAscending ? numA - numB : numB - numA;
            }
            
            // Fallback to string sort
            valA = valA.toString().toLowerCase();
            valB = valB.toString().toLowerCase();
            
            if (valA < valB) return sortAscending ? -1 : 1;
            if (valA > valB) return sortAscending ? 1 : -1;
            return 0;
        });
        
        renderTable(parsedData.data, parsedData.meta.fields);
    };

    window.toggleView = function() {
        const content = document.getElementById('content');
        const source = document.getElementById('source-view');
        // The CSS initially hides source-view via display:none
        if (window.getComputedStyle(source).display === 'none') {
            source.style.display = 'block';
            content.style.display = 'none';
        } else {
            source.style.display = 'none';
            content.style.display = 'block';
        }
    };
})();