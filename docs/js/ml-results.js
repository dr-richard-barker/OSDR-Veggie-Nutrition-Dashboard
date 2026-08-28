export function initML(data) {
    if (!window.Plotly) return; // Guard

    // 1. PCA Plot (Plotly)
    const traceFlight = {
        x: data.pca.filter(d => d.condition === 'Flight').map(d => d.pc1),
        y: data.pca.filter(d => d.condition === 'Flight').map(d => d.pc2),
        mode: 'markers',
        type: 'scatter',
        name: 'Flight',
        marker: { size: 12, color: '#3B6EA5' }
    };
    const traceGround = {
        x: data.pca.filter(d => d.condition === 'Ground').map(d => d.pc1),
        y: data.pca.filter(d => d.condition === 'Ground').map(d => d.pc2),
        mode: 'markers',
        type: 'scatter',
        name: 'Ground',
        marker: { size: 12, color: '#D4AF37', symbol: 'square' }
    };
    Plotly.newPlot('pca-plot', [traceFlight, traceGround], {
        margin: { t: 10, l: 40, r: 10, b: 40 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: { title: 'Principal Component 1' },
        yaxis: { title: 'Principal Component 2' }
    }, {responsive: true});

    // 2. Feature Importance Chart (Chart.js)
    const ctxFeat = document.getElementById('feature-importance-chart');
    if (ctxFeat) {
        new Chart(ctxFeat, {
            type: 'bar',
            data: {
                labels: data.featureImportance.map(d => d.feature),
                datasets: [{
                    label: 'Importance Score',
                    data: data.featureImportance.map(d => d.importance),
                    backgroundColor: '#54C9BA'
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    // 3. Stats Table
    const tbody = document.querySelector('#stats-table tbody');
    tbody.innerHTML = '';
    data.stats.forEach(s => {
        const isSig = s.pValue < 0.05;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${s.feature}</td>
            <td>${s.pValue.toFixed(3)}</td>
            <td class="${isSig ? 'sig-yes' : 'sig-no'}">${isSig ? 'Significant' : 'Not Sig.'}</td>
        `;
        tbody.appendChild(tr);
    });

    // 4. Metrics
    document.getElementById('metric-acc').textContent = data.metrics.accuracy;
    document.getElementById('metric-prec').textContent = data.metrics.precision;
    document.getElementById('metric-rec').textContent = data.metrics.recall;
    document.getElementById('metric-f1').textContent = data.metrics.f1;
    document.getElementById('metric-orac').textContent = data.metrics.orac_r2;
    document.getElementById('metric-phenolics').textContent = data.metrics.phenolics_r2;
}
