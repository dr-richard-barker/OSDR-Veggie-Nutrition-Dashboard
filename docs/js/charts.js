let barChartInstance = null;
let radarChartInstance = null;
let rawData = [];

// Element groupings
const GROUPS = {
    all: ['Fe', 'K', 'Na', 'P', 'S', 'Zn', 'Ca', 'Mg', 'Mn', 'Cu'],
    significant: ['Fe', 'K', 'Na', 'P', 'S', 'Zn', 'phenolics'],
    biochemicals: ['phenolics', 'anthocyanins', 'orac']
};

const UNITS = {
    Fe: 'mg/g', K: 'mg/g', Na: 'mg/g', P: 'mg/g', S: 'mg/g', Zn: 'mg/g',
    Ca: 'mg/g', Mg: 'mg/g', Mn: 'mg/g', Cu: 'mg/g',
    phenolics: 'GAE mg/g', anthocyanins: 'mg/g', orac: 'µmol TE/g'
};

const COLORS = {
    flight: '#3B6EA5', // coseblue
    ground: '#3FB6A8',  // coseteal
    navy: '#2F5985',
    gold: '#D4AF37'
};

export function initCharts(data) {
    rawData = data;

    // Attach event listeners for filters
    const elementSelect = document.getElementById('element-view-select');
    const missionFilter = document.getElementById('mission-filter');

    if (elementSelect) {
        elementSelect.addEventListener('change', updateDashboard);
    }
    if (missionFilter) {
        missionFilter.addEventListener('change', updateDashboard);
    }

    // Initial render
    updateDashboard();
}

function updateDashboard() {
    const view = document.getElementById('element-view-select')?.value || 'all';
    const mission = document.getElementById('mission-filter')?.value || 'all';

    // 1. Filter Data
    let filteredData = rawData;
    if (mission !== 'all') {
        filteredData = rawData.filter(d => d.mission === mission);
    }

    // 2. Render Table
    renderTable(filteredData, view);

    // 3. Render Charts
    renderBarChart(filteredData, view);
    renderRadarChart(filteredData);
}

function renderTable(data, view) {
    const tbody = document.querySelector('#data-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const selectedFeatures = GROUPS[view];

    data.forEach(row => {
        selectedFeatures.forEach(feature => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${row.sample_id}</strong></td>
                <td><span class="badge badge-mission">${row.mission}</span></td>
                <td><span class="badge badge-${row.condition.toLowerCase()}">${row.condition}</span></td>
                <td>${feature}</td>
                <td>${row[feature] !== undefined ? row[feature].toFixed(4) : 'N/A'}</td>
                <td><small>${UNITS[feature] || ''}</small></td>
            `;
            tbody.appendChild(tr);
        });
    });
}

function renderBarChart(data, view) {
    const ctxBar = document.getElementById('bar-chart');
    if (!ctxBar) return;

    if (barChartInstance) {
        barChartInstance.destroy();
    }

    const features = GROUPS[view];
    
    // Calculate means for Flight and Ground
    const flightData = data.filter(d => d.condition === 'Flight');
    const groundData = data.filter(d => d.condition === 'Ground');

    const flightMeans = [];
    const groundMeans = [];

    features.forEach(f => {
        const fVals = flightData.map(d => d[f] || 0);
        const gVals = groundData.map(d => d[f] || 0);
        
        const fMean = fVals.length ? fVals.reduce((a, b) => a + b, 0) / fVals.length : 0;
        const gMean = gVals.length ? gVals.reduce((a, b) => a + b, 0) / gVals.length : 0;
        
        flightMeans.push(fMean);
        groundMeans.push(gMean);
    });

    // To make different scales visible side-by-side, we can normalize relative to Ground mean (Ground = 100%)
    // But we'll display raw values in the tooltips
    const normalizedFlight = [];
    const normalizedGround = [];

    features.forEach((f, idx) => {
        const gMean = groundMeans[idx];
        const fMean = flightMeans[idx];
        
        if (gMean === 0) {
            normalizedGround.push(100);
            normalizedFlight.push(0);
        } else {
            normalizedGround.push(100);
            normalizedFlight.push((fMean / gMean) * 100);
        }
    });

    barChartInstance = new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: features,
            datasets: [
                {
                    label: 'Flight (% of Ground)',
                    data: normalizedFlight,
                    backgroundColor: COLORS.flight,
                    borderColor: COLORS.navy,
                    borderWidth: 1,
                    rawValues: flightMeans // custom field for tooltips
                },
                {
                    label: 'Ground Control (100%)',
                    data: normalizedGround,
                    backgroundColor: COLORS.ground,
                    borderColor: '#2e8b57',
                    borderWidth: 1,
                    rawValues: groundMeans // custom field for tooltips
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const dataset = context.dataset;
                            const idx = context.dataIndex;
                            const label = dataset.label.split(' ')[0]; // Flight or Ground
                            const rawVal = dataset.rawValues[idx].toFixed(4);
                            const percent = context.raw.toFixed(1);
                            const element = context.label;
                            const unit = UNITS[element];
                            return `${label}: ${rawVal} ${unit} (${percent}%)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Relative Concentration (% of Ground Control)'
                    },
                    suggestedMax: 150
                }
            }
        }
    });
}

function renderRadarChart(data) {
    const ctxRadar = document.getElementById('radar-chart');
    if (!ctxRadar) return;

    if (radarChartInstance) {
        radarChartInstance.destroy();
    }

    // Pick 5 representative elements/biochemicals of different scales
    const radarFeatures = ['Fe', 'K', 'Ca', 'Mg', 'orac'];
    
    // Scale max values to 100
    const maxVals = {};
    radarFeatures.forEach(f => {
        maxVals[f] = Math.max(...rawData.map(d => d[f] || 1));
    });

    const flightData = data.filter(d => d.condition === 'Flight');
    const groundData = data.filter(d => d.condition === 'Ground');

    const flightMeans = radarFeatures.map(f => {
        const vals = flightData.map(d => d[f] || 0);
        const mean = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
        return (mean / maxVals[f]) * 100;
    });

    const groundMeans = radarFeatures.map(f => {
        const vals = groundData.map(d => d[f] || 0);
        const mean = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
        return (mean / maxVals[f]) * 100;
    });

    radarChartInstance = new Chart(ctxRadar, {
        type: 'radar',
        data: {
            labels: radarFeatures.map(f => `${f} (scaled)`),
            datasets: [
                {
                    label: 'Flight',
                    data: flightMeans,
                    borderColor: COLORS.flight,
                    backgroundColor: 'rgba(59, 110, 165, 0.2)',
                    pointBackgroundColor: COLORS.flight
                },
                {
                    label: 'Ground Control',
                    data: groundMeans,
                    borderColor: COLORS.ground,
                    backgroundColor: 'rgba(63, 182, 168, 0.2)',
                    pointBackgroundColor: COLORS.ground
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { display: true },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            }
        }
    });
}
