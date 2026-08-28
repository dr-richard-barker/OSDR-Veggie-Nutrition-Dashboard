import { initCharts } from './charts.js';
import { initGallery } from './gallery.js';
import { initML } from './ml-results.js';

// Demo data fallback
const demoNutritionData = [
    { id: 'S1', mission: 'VEG-01A', condition: 'Flight', element: 'Fe', value: 45.2, unit: 'ppm' },
    { id: 'S2', mission: 'VEG-01A', condition: 'Ground', element: 'Fe', value: 38.1, unit: 'ppm' },
    { id: 'S3', mission: 'VEG-01B', condition: 'Flight', element: 'K', value: 4100, unit: 'ppm' },
    { id: 'S4', mission: 'VEG-01B', condition: 'Ground', element: 'K', value: 3900, unit: 'ppm' },
    { id: 'S5', mission: 'VEG-03A', condition: 'Flight', element: 'ORAC', value: 120, unit: 'TE/g' },
    { id: 'S6', mission: 'VEG-03A', condition: 'Ground', element: 'ORAC', value: 110, unit: 'TE/g' }
];

const demoMLData = {
    pca: [
        { pc1: 2.1, pc2: 0.5, condition: 'Flight', mission: 'VEG-01A' },
        { pc1: -1.2, pc2: 1.1, condition: 'Ground', mission: 'VEG-01A' },
        { pc1: 1.8, pc2: -0.2, condition: 'Flight', mission: 'VEG-01B' },
        { pc1: -1.5, pc2: -0.5, condition: 'Ground', mission: 'VEG-01B' }
    ],
    featureImportance: [
        { feature: 'Fe', importance: 0.35 },
        { feature: 'K', importance: 0.25 },
        { feature: 'ORAC', importance: 0.20 },
        { feature: 'Phenolics', importance: 0.15 }
    ],
    stats: [
        { feature: 'Fe', pValue: 0.042 },
        { feature: 'K', pValue: 0.150 },
        { feature: 'ORAC', pValue: 0.035 }
    ],
    metrics: { accuracy: '85%', precision: '83%', recall: '88%', f1: '85%', orac_r2: '0.72', phenolics_r2: '0.68' }
};

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Tab Navigation
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.add('active');
        });
    });

    // 2. Theme Toggle
    const themeBtn = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);

    themeBtn.addEventListener('click', () => {
        const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    });

    // 3. Load Data
    let nutritionData = demoNutritionData;
    let mlData = demoMLData;

    try {
        const resNut = await fetch('data/nutrition_data.json');
        if(resNut.ok) nutritionData = await resNut.json();
    } catch(e) { console.log('Using demo nutrition data'); }

    try {
        const resML = await fetch('data/ml_results.json');
        if(resML.ok) mlData = await resML.json();
    } catch(e) { console.log('Using demo ML data'); }

    // 4. Initialize Modules
    initCharts(nutritionData);
    initGallery();
    initML(mlData);
});
