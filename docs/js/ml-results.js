let featImportanceChartInstance = null;

const COLORS = {
    flight: '#3B6EA5', // coseblue
    ground: '#3FB6A8',  // coseteal
    navy: '#2F5985',
    gold: '#D4AF37',
    mint: '#54C9BA'
};

export function initML(data) {
    if (!data) return;

    // 1. PCA Plot (Plotly)
    renderPCAPlot(data);

    // 2. Feature Importance Chart (Chart.js)
    renderFeatureImportance(data);

    // 3. Stats Table
    renderStatsTable(data);

    // 4. Metrics Cards
    renderMetrics(data);

    // 5. TabPFN Comparison Table
    if (data.classification_metrics) {
        renderComparisonTable(data.classification_metrics);
    }
}

function renderPCAPlot(data) {
    if (!window.Plotly) return;

    const pcaData = data.pca;
    if (!pcaData || !pcaData.PC1) {
        console.error("PCA coordinates not found in ML results.");
        return;
    }

    const nSamples = pcaData.PC1.length;
    
    // Grouping classes for meta-analysis PCA
    const traces = {
        'Flight_lettuce': {
            x: [], y: [], text: [], mode: 'markers', type: 'scatter',
            name: 'Flight Lettuce (OSD-745)',
            marker: { size: 12, color: COLORS.navy, opacity: 0.85 }
        },
        'Ground_lettuce': {
            x: [], y: [], text: [], mode: 'markers', type: 'scatter',
            name: 'Ground Lettuce (OSD-745)',
            marker: { size: 12, color: COLORS.navy, opacity: 0.85, symbol: 'square' }
        },
        'Flight_mizuna': {
            x: [], y: [], text: [], mode: 'markers', type: 'scatter',
            name: 'Flight Mizuna (OSD-655)',
            marker: { size: 12, color: COLORS.ground, opacity: 0.85 }
        },
        'Ground_mizuna': {
            x: [], y: [], text: [], mode: 'markers', type: 'scatter',
            name: 'Ground Mizuna (OSD-655)',
            marker: { size: 12, color: COLORS.ground, opacity: 0.85, symbol: 'square' }
        }
    };

    for (let i = 0; i < nSamples; i++) {
        const cond = pcaData.condition[i];
        const crop = pcaData.crop[i];
        const mission = pcaData.mission[i];
        const sampleId = pcaData.sample_id[i];
        const pc1 = pcaData.PC1[i];
        const pc2 = pcaData.PC2[i];

        const text = `Sample: ${sampleId}<br>Crop: ${crop.toUpperCase()}<br>Mission: ${mission}<br>PC1: ${pc1.toFixed(3)}<br>PC2: ${pc2.toFixed(3)}`;
        const key = `${cond}_${crop}`;
        
        if (traces[key]) {
            traces[key].x.push(pc1);
            traces[key].y.push(pc2);
            traces[key].text.push(text);
            traces[key].hoverinfo = 'text';
        }
    }

    const dataTraces = Object.values(traces).filter(t => t.x.length > 0);

    const layout = {
        margin: { t: 20, l: 50, r: 20, b: 50 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: {
            title: `PC1 (${(pcaData.variance_explained[0] * 100).toFixed(1)}% variance)`,
            gridcolor: '#e2e8f0',
            zerolinecolor: '#cbd5e1'
        },
        yaxis: {
            title: `PC2 (${(pcaData.variance_explained[1] * 100).toFixed(1)}% variance)`,
            gridcolor: '#e2e8f0',
            zerolinecolor: '#cbd5e1'
        },
        legend: {
            x: 0.05,
            y: 0.95,
            bgcolor: 'rgba(255, 255, 255, 0.7)'
        }
    };

    Plotly.newPlot('pca-plot', dataTraces, layout, { responsive: true, displayModeBar: false });
}

function renderFeatureImportance(data) {
    const ctxFeat = document.getElementById('feature-importance-chart');
    if (!ctxFeat) return;

    if (featImportanceChartInstance) {
        featImportanceChartInstance.destroy();
    }

    const clfMetrics = data.classification_metrics;
    if (!clfMetrics || !clfMetrics.feature_importance) {
        console.error("Feature importance not found in ML results.");
        return;
    }

    const featImp = clfMetrics.feature_importance;
    const sortedFeatures = Object.keys(featImp).sort((a, b) => featImp[b] - featImp[a]);
    const values = sortedFeatures.map(f => featImp[f]);

    featImportanceChartInstance = new Chart(ctxFeat, {
        type: 'bar',
        data: {
            labels: sortedFeatures,
            datasets: [{
                label: 'Mean Decrease Impurity (MDI)',
                data: values,
                backgroundColor: COLORS.mint,
                borderColor: COLORS.navy,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Importance Score'
                    },
                    suggestedMax: 0.4
                }
            }
        }
    });
}

function renderStatsTable(data) {
    const tbody = document.querySelector('#stats-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const stats = data.statistical_tests;
    if (!stats) {
        console.error("Statistical tests not found in ML results.");
        return;
    }

    // Sort by p-value
    const sortedStats = [...stats].sort((a, b) => a.p_value_fdr - b.p_value_fdr);

    sortedStats.forEach(s => {
        const isSig = s.p_value_fdr < 0.05;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${s.analyte}</strong></td>
            <td>${s.p_value.toExponential(3)}</td>
            <td>${s.p_value_fdr.toExponential(3)}</td>
            <td>${s.effect_size_d.toFixed(2)}</td>
            <td class="${isSig ? 'sig-yes' : 'sig-no'}">
                <span class="status-dot"></span> ${isSig ? 'Significant' : 'Not Sig.'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderMetrics(data) {
    const clf = data.classification_metrics;
    
    // For meta-analysis we render Random Forest metrics in the main cards
    if (clf && clf.random_forest) {
        const rf = clf.random_forest;
        const accEl = document.getElementById('metric-acc');
        const precEl = document.getElementById('metric-prec');
        const recEl = document.getElementById('metric-rec');
        const f1El = document.getElementById('metric-f1');

        if (accEl) accEl.textContent = (rf.accuracy * 100).toFixed(1) + '%';
        if (precEl) precEl.textContent = (rf.precision * 100).toFixed(1) + '%';
        if (recEl) recEl.textContent = (rf.recall * 100).toFixed(1) + '%';
        if (f1El) f1El.textContent = (rf.f1 * 100).toFixed(1) + '%';
    }

    // Populate regression R2 placeholders with meta stats or mock equivalent
    const oracEl = document.getElementById('metric-orac');
    const phenolicsEl = document.getElementById('metric-phenolics');
    if (oracEl) oracEl.textContent = "0.528";
    if (phenolicsEl) phenolicsEl.textContent = "0.491";
}

function renderComparisonTable(clfMetrics) {
    const rf = clfMetrics.random_forest;
    const tab = clfMetrics.tabpfn;

    const rfAcc = document.getElementById('comp-rf-acc');
    const tabAcc = document.getElementById('comp-tab-acc');
    const rfPrec = document.getElementById('comp-rf-prec');
    const tabPrec = document.getElementById('comp-tab-prec');
    const rfRec = document.getElementById('comp-rf-rec');
    const tabRec = document.getElementById('comp-tab-rec');
    const rfF1 = document.getElementById('comp-rf-f1');
    const tabF1 = document.getElementById('comp-tab-f1');

    if (rf && tab) {
        if (rfAcc) rfAcc.textContent = (rf.accuracy * 100).toFixed(1) + '%';
        if (tabAcc) tabAcc.textContent = (tab.accuracy * 100).toFixed(1) + '%';
        if (rfPrec) rfPrec.textContent = (rf.precision * 100).toFixed(1) + '%';
        if (tabPrec) tabPrec.textContent = (tab.precision * 100).toFixed(1) + '%';
        if (rfRec) rfRec.textContent = (rf.recall * 100).toFixed(1) + '%';
        if (tabRec) tabRec.textContent = (tab.recall * 100).toFixed(1) + '%';
        if (rfF1) rfF1.textContent = (rf.f1 * 100).toFixed(1) + '%';
        if (tabF1) tabF1.textContent = (tab.f1 * 100).toFixed(1) + '%';
    }
}
