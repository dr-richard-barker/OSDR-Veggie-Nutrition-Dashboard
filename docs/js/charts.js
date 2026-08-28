let barChartInstance = null;
let radarChartInstance = null;

const COLORS = {
    flight: '#3B6EA5', // coseblue
    ground: '#3FB6A8',  // coseteal
    navy: '#2F5985',
    gold: '#D4AF37',
    mint: '#54C9BA'
};

const ELEMENTS = ['Fe', 'K', 'Na', 'P', 'S', 'Zn', 'Ca', 'Mg', 'Mn', 'Cu'];
const SIGNIFICANT_ELEMENTS = ['Fe', 'K', 'Na', 'S', 'Ca'];
const BIOCHEMICALS = ['phenolics', 'anthocyanins', 'orac'];

export function initCharts(data) {
    if (!data) return;

    const cropSelect = document.getElementById('crop-select');
    const missionFilter = document.getElementById('mission-filter');
    const viewSelect = document.getElementById('element-view-select');

    // Sync Mission options based on selected Crop
    function syncMissions() {
        const crop = cropSelect ? cropSelect.value : 'all';
        const missionVal = missionFilter ? missionFilter.value : 'all';
        
        if (!missionFilter) return;

        // Save selection
        const prevSelected = missionFilter.value;
        missionFilter.innerHTML = '<option value="all">All Missions</option>';

        if (crop === 'all' || crop === 'lettuce') {
            missionFilter.innerHTML += `
                <option value="VEG-01A">VEG-01A (Lettuce)</option>
                <option value="VEG-01B">VEG-01B (Lettuce)</option>
                <option value="VEG-03A">VEG-03A (Lettuce)</option>
            `;
        }
        if (crop === 'all' || crop === 'mizuna') {
            missionFilter.innerHTML += `
                <option value="VEG-04A">VEG-04A (Mizuna)</option>
                <option value="VEG-04B">VEG-04B (Mizuna)</option>
            `;
        }

        // Try to restore previous selection
        missionFilter.value = prevSelected;
        if (missionFilter.value === '') {
            missionFilter.value = 'all';
        }
    }

    function updateVisualizations() {
        const crop = cropSelect ? cropSelect.value : 'all';
        const mission = missionFilter ? missionFilter.value : 'all';
        const view = viewSelect ? viewSelect.value : 'all';

        // Filter Data
        let filtered = data;
        if (crop !== 'all') {
            filtered = filtered.filter(d => d.crop === crop);
        }
        if (mission !== 'all') {
            filtered = filtered.filter(d => d.mission === mission);
        }

        // Render charts & tables
        renderBarChart(filtered, view);
        renderRadarChart(filtered, view);
        renderTable(filtered);
    }

    if (cropSelect) {
        cropSelect.addEventListener('change', () => {
            syncMissions();
            updateVisualizations();
        });
    }

    if (missionFilter) {
        missionFilter.addEventListener('change', updateVisualizations);
    }

    if (viewSelect) {
        viewSelect.addEventListener('change', updateVisualizations);
    }

    syncMissions();
    updateVisualizations();
}

function getAverage(array, key) {
    if (array.length === 0) return 0;
    const sum = array.reduce((acc, curr) => acc + (curr[key] || 0), 0);
    return sum / array.length;
}

function renderBarChart(filteredData, view) {
    const ctx = document.getElementById('bar-chart');
    if (!ctx) return;

    if (barChartInstance) {
        barChartInstance.destroy();
    }

    // Determine features
    let features = ELEMENTS;
    if (view === 'significant') {
        features = SIGNIFICANT_ELEMENTS;
    } else if (view === 'biochemicals') {
        features = BIOCHEMICALS;
    }

    const flightSamples = filteredData.filter(d => d.condition === 'Flight');
    const groundSamples = filteredData.filter(d => d.condition === 'Ground');

    const labels = [];
    const normalizedFlight = [];
    const normalizedGround = [];
    const rawFlightVals = [];
    const rawGroundVals = [];

    features.forEach(f => {
        const fMean = getAverage(flightSamples, f);
        const gMean = getAverage(groundSamples, f);

        labels.push(f);
        rawFlightVals.push(fMean);
        rawGroundVals.push(gMean);

        // Normalize relative to Ground (100%)
        if (gMean === 0) {
            normalizedGround.push(100);
            normalizedFlight.push(0);
        } else {
            normalizedGround.push(100);
            normalizedFlight.push((fMean / gMean) * 100);
        }
    });

    barChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Ground Control (KSC = 100%)',
                    data: normalizedGround,
                    backgroundColor: COLORS.ground,
                    borderColor: COLORS.navy,
                    borderWidth: 1
                },
                {
                    label: 'Flight (ISS)',
                    data: normalizedFlight,
                    backgroundColor: COLORS.flight,
                    borderColor: COLORS.navy,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Relative Concentration (% of Ground)'
                    },
                    suggestedMax: 150
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const index = context.dataIndex;
                            const featureName = labels[index];
                            const datasetIndex = context.datasetIndex;
                            const isFlight = datasetIndex === 1;

                            const val = isFlight ? rawFlightVals[index] : rawGroundVals[index];
                            const percent = isFlight ? normalizedFlight[index] : 100;
                            
                            let unit = 'mg/g';
                            if (featureName === 'phenolics') unit = 'GAE mg/g';
                            if (featureName === 'orac') unit = 'µmol TE/g';
                            if (featureName === 'micro_apc' || featureName === 'micro_ymc') unit = 'log10 CFU/g';

                            return `${context.dataset.label}: ${val.toFixed(3)} ${unit} (${percent.toFixed(1)}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderRadarChart(filteredData, view) {
    const ctx = document.getElementById('radar-chart');
    if (!ctx) return;

    if (radarChartInstance) {
        radarChartInstance.destroy();
    }

    let features = ELEMENTS;
    if (view === 'significant') {
        features = SIGNIFICANT_ELEMENTS;
    } else if (view === 'biochemicals') {
        features = BIOCHEMICALS;
    }

    const flightSamples = filteredData.filter(d => d.condition === 'Flight');
    const groundSamples = filteredData.filter(d => d.condition === 'Ground');

    const flightAves = features.map(f => getAverage(flightSamples, f));
    const groundAves = features.map(f => getAverage(groundSamples, f));

    // Radar chart scales elements to fit nicely together (Z-scaling averages across all loaded data)
    const maxVals = features.map(f => {
        const vals = filteredData.map(d => d[f] || 0);
        return Math.max(...vals, 1);
    });

    const scaledFlight = flightAves.map((v, i) => (v / maxVals[i]) * 100);
    const scaledGround = groundAves.map((v, i) => (v / maxVals[i]) * 100);

    radarChartInstance = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: features,
            datasets: [
                {
                    label: 'Flight (ISS)',
                    data: scaledFlight,
                    fill: true,
                    backgroundColor: 'rgba(59, 110, 165, 0.2)',
                    borderColor: COLORS.flight,
                    pointBackgroundColor: COLORS.flight,
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: COLORS.flight
                },
                {
                    label: 'Ground Control (KSC)',
                    data: scaledGround,
                    fill: true,
                    backgroundColor: 'rgba(63, 182, 168, 0.2)',
                    borderColor: COLORS.ground,
                    pointBackgroundColor: COLORS.ground,
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: COLORS.ground
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
                    suggestedMax: 100,
                    ticks: { display: false }
                }
            }
        }
    });
}

function renderTable(filteredData) {
    const tbody = document.querySelector('#data-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    filteredData.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${row.sample_id}</strong></td>
            <td><span class="crop-badge crop-${row.crop}">${row.crop.toUpperCase()}</span></td>
            <td>${row.mission}</td>
            <td><span class="cond-badge cond-${row.condition.toLowerCase()}">${row.condition.toUpperCase()}</span></td>
            <td>${(row.Fe || 0).toFixed(3)}</td>
            <td>${(row.K || 0).toFixed(1)}</td>
            <td>${(row.Na || 0).toFixed(2)}</td>
            <td>${(row.P || 0).toFixed(2)}</td>
            <td>${(row.S || 0).toFixed(2)}</td>
            <td>${(row.Zn || 0).toFixed(4)}</td>
            <td>${(row.Ca || 0).toFixed(1)}</td>
            <td>${(row.Mg || 0).toFixed(2)}</td>
            <td>${(row.phenolics || 0).toFixed(1)}</td>
            <td>${(row.orac || 0).toFixed(0)}</td>
        `;
        tbody.appendChild(tr);
    });
}
