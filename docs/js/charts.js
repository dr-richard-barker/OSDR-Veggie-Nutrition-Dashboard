export function initCharts(data) {
    const coseColors = {
        flight: '#3B6EA5', // coseblue
        ground: '#D4AF37'  // cosegold
    };

    // 1. Populate Table
    const tbody = document.querySelector('#data-table tbody');
    tbody.innerHTML = '';
    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.id}</td>
            <td>${row.mission}</td>
            <td>${row.condition}</td>
            <td>${row.element}</td>
            <td>${row.value}</td>
            <td>${row.unit}</td>
        `;
        tbody.appendChild(tr);
    });

    // Process data for charts
    const flightFe = data.find(d => d.condition === 'Flight' && d.element === 'Fe')?.value || 0;
    const groundFe = data.find(d => d.condition === 'Ground' && d.element === 'Fe')?.value || 0;
    const flightK = data.find(d => d.condition === 'Flight' && d.element === 'K')?.value || 0;
    const groundK = data.find(d => d.condition === 'Ground' && d.element === 'K')?.value || 0;

    // 2. Bar Chart
    const ctxBar = document.getElementById('bar-chart');
    if (ctxBar) {
        new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: ['Fe (ppm)', 'K (ppm/100)'],
                datasets: [
                    {
                        label: 'Flight',
                        data: [flightFe, flightK / 100],
                        backgroundColor: coseColors.flight
                    },
                    {
                        label: 'Ground',
                        data: [groundFe, groundK / 100],
                        backgroundColor: coseColors.ground
                    }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    // 3. Radar Chart
    const ctxRadar = document.getElementById('radar-chart');
    if (ctxRadar) {
        new Chart(ctxRadar, {
            type: 'radar',
            data: {
                labels: ['Fe', 'K', 'Ca', 'Mg', 'ORAC'],
                datasets: [
                    {
                        label: 'Flight',
                        data: [80, 90, 70, 85, 95],
                        borderColor: coseColors.flight,
                        backgroundColor: 'rgba(59, 110, 165, 0.2)'
                    },
                    {
                        label: 'Ground',
                        data: [75, 85, 75, 80, 80],
                        borderColor: coseColors.ground,
                        backgroundColor: 'rgba(212, 175, 55, 0.2)'
                    }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
}
