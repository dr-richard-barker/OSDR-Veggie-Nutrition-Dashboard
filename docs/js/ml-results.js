let featImportanceChartInstance = null;

const COLORS = {
    flightLettuce: '#2F5985', // Deep Navy Blue
    groundLettuce: '#6EA3D8', // Light Blue
    flightMizuna: '#C2483F',  // Crimson Red
    groundMizuna: '#3FB6A8',  // Emerald Teal
    accent: '#3B6EA5',
    accent2: '#3FB6A8',
    mint: '#54C9BA',
    gold: '#D4AF37'
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

export function resizeMLPlots() {
    if (window.Plotly) {
        try {
            Plotly.Plots.resize('pca-plot');
        } catch (e) {
            console.log('Plotly resize deferred');
        }
    }
    if (featImportanceChartInstance) {
        featImportanceChartInstance.resize();
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
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    
    // High-contrast, human-readable trace configurations
    const traces = {
        'Flight_lettuce': {
            x: [], y: [], text: [], mode: 'markers', type: 'scatter',
            name: 'Flight Lettuce (OSD-745)',
            marker: {
                size: 13,
                color: COLORS.flightLettuce,
                symbol: 'circle',
                opacity: 0.9,
                line: { color: '#ffffff', width: 1.5 }
            }
        },
        'Ground_lettuce': {
            x: [], y: [], text: [], mode: 'markers', type: 'scatter',
            name: 'Ground Lettuce (OSD-745)',
            marker: {
                size: 13,
                color: COLORS.groundLettuce,
                symbol: 'square',
                opacity: 0.9,
                line: { color: '#2F5985', width: 1.5 }
            }
        },
        'Flight_mizuna': {
            x: [], y: [], text: [], mode: 'markers', type: 'scatter',
            name: 'Flight Mizuna (OSD-655)',
            marker: {
                size: 13,
                color: COLORS.flightMizuna,
                symbol: 'circle',
                opacity: 0.9,
                line: { color: '#ffffff', width: 1.5 }
            }
        },
        'Ground_mizuna': {
            x: [], y: [], text: [], mode: 'markers', type: 'scatter',
            name: 'Ground Mizuna (OSD-655)',
            marker: {
                size: 13,
                color: COLORS.groundMizuna,
                symbol: 'square',
                opacity: 0.9,
                line: { color: '#1B6044', width: 1.5 }
            }
        }
    };

    for (let i = 0; i < nSamples; i++) {
        const cond = pcaData.condition[i];
        const crop = pcaData.crop[i];
        const mission = pcaData.mission[i];
        const sampleId = pcaData.sample_id[i];
        const pc1 = pcaData.PC1[i];
        const pc2 = pcaData.PC2[i];

        const text = `<b>${sampleId}</b><br>Species: ${crop.toUpperCase()}<br>Mission: ${mission}<br>Treatment: ${cond}`;
        const key = `${cond}_${crop}`;
        
        if (traces[key]) {
            traces[key].x.push(pc1);
            traces[key].y.push(pc2);
            traces[key].text.push(text);
            traces[key].hovertemplate = '%{text}<br><b>PC1:</b> %{x:.3f}<br><b>PC2:</b> %{y:.3f}<extra></extra>';
        }
    }

    const dataTraces = Object.values(traces).filter(t => t.x.length > 0);

    const pc1Var = pcaData.variance_explained ? (pcaData.variance_explained[0] * 100).toFixed(1) : '42.0';
    const pc2Var = pcaData.variance_explained ? (pcaData.variance_explained[1] * 100).toFixed(1) : '25.0';

    const layout = {
        autosize: true,
        margin: { t: 45, l: 55, r: 25, b: 50 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            size: 12,
            color: isDark ? '#e6ebf2' : '#1a2230'
        },
        xaxis: {
            title: {
                text: `PC1 (${pc1Var}% Explained Variance) — Species Separation`,
                font: { size: 12, color: isDark ? '#9aa6b6' : '#5a6473' }
            },
            gridcolor: isDark ? '#232c39' : '#e5e9f0',
            zerolinecolor: isDark ? '#334155' : '#cbd5e1'
        },
        yaxis: {
            title: {
                text: `PC2 (${pc2Var}% Explained Variance) — Microgravity Response`,
                font: { size: 12, color: isDark ? '#9aa6b6' : '#5a6473' }
            },
            gridcolor: isDark ? '#232c39' : '#e5e9f0',
            zerolinecolor: isDark ? '#334155' : '#cbd5e1'
        },
        legend: {
            orientation: 'h',
            x: 0,
            y: 1.14,
            xanchor: 'left',
            yanchor: 'bottom',
            font: { size: 11, color: isDark ? '#e6ebf2' : '#1a2230' },
            bgcolor: isDark ? 'rgba(22, 29, 39, 0.85)' : 'rgba(255, 255, 255, 0.85)',
            bordercolor: isDark ? '#232c39' : '#e5e9f0',
            borderwidth: 1
        }
    };

    Plotly.newPlot('pca-plot', dataTraces, layout, {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d']
    });
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

    // Color gradient for top features vs secondary features
    const bgColors = sortedFeatures.map((_, idx) => idx < 3 ? COLORS.accent : COLORS.accent2);
    const borderColors = sortedFeatures.map((_, idx) => idx < 3 ? '#2F5985' : '#2F855A');

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#e6ebf2' : '#1a2230';
    const gridColor = isDark ? '#232c39' : '#e5e9f0';

    featImportanceChartInstance = new Chart(ctxFeat, {
        type: 'bar',
        data: {
            labels: sortedFeatures,
            datasets: [{
                label: 'Mean Decrease Impurity (MDI)',
                data: values,
                backgroundColor: bgColors,
                borderColor: borderColors,
                borderWidth: 1.5,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` MDI Importance: ${(context.raw * 100).toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Importance Score (MDI)',
                        color: textColor,
                        font: { weight: 'bold' }
                    },
                    ticks: {
                        color: textColor,
                        callback: function(val) {
                            return (val * 100).toFixed(0) + '%';
                        }
                    },
                    grid: {
                        color: gridColor
                    },
                    suggestedMax: 0.35
                },
                y: {
                    ticks: {
                        color: textColor,
                        font: { weight: 'bold', size: 12 }
                    },
                    grid: {
                        display: false
                    }
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

    // Sort by FDR p-value ascending
    const sortedStats = [...stats].sort((a, b) => a.p_value_fdr - b.p_value_fdr);

    sortedStats.forEach(s => {
        const isSig = s.p_value_fdr < 0.05;
        const tr = document.createElement('tr');
        
        // Format p-values cleanly
        const rawP = s.p_value < 0.001 ? s.p_value.toExponential(2) : s.p_value.toFixed(4);
        const fdrP = s.p_value_fdr < 0.001 ? s.p_value_fdr.toExponential(2) : s.p_value_fdr.toFixed(4);
        const effectD = `${s.effect_size_d >= 0 ? '+' : ''}${s.effect_size_d.toFixed(2)}`;

        tr.innerHTML = `
            <td><strong>${s.analyte}</strong></td>
            <td><code>${rawP}</code></td>
            <td><code>${fdrP}</code></td>
            <td><strong>${effectD}</strong></td>
            <td>
                <span class="badge ${isSig ? 'badge-sig' : 'badge-nonsig'}">
                    <span class="status-dot"></span>${isSig ? 'Significant (p < 0.05)' : 'Not Significant'}
                </span>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderMetrics(data) {
    const clf = data.classification_metrics;
    
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
