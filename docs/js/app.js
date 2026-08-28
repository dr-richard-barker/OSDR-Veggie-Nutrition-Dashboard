import { initCharts } from './charts.js';
import { initGallery } from './gallery.js';
import { initML } from './ml-results.js';

// Demo data fallback
const demoNutritionData = [
    { sample_id: 'Sample_Demo_1', mission: 'VEG-01A', condition: 'Flight', plant_number: 1, harvest_day: 33, Fe: 0.18, K: 35.5, Na: 2.1, P: 5.5, S: 2.8, Zn: 0.06, Ca: 12.0, Mg: 4.5, Mn: 0.1, Cu: 0.01, phenolics: 11.2, anthocyanins: 1.1, orac: 420.0 },
    { sample_id: 'Sample_Demo_2', mission: 'VEG-01A', condition: 'Ground', plant_number: 1, harvest_day: 33, Fe: 0.14, K: 41.2, Na: 1.2, P: 6.2, S: 2.1, Zn: 0.04, Ca: 11.8, Mg: 4.2, Mn: 0.09, Cu: 0.009, phenolics: 8.5, anthocyanins: 1.2, orac: 390.0 }
];

const demoMLData = {
    pca: {
        pca_coordinates: {
            PC1: [1.2, -1.1, 0.8, -0.9],
            PC2: [0.5, 0.8, -0.2, -0.5],
            condition: ['Flight', 'Ground', 'Flight', 'Ground'],
            mission: ['VEG-01A', 'VEG-01A', 'VEG-01B', 'VEG-01B'],
            sample_id: ['Sample_1', 'Sample_2', 'Sample_3', 'Sample_4']
        },
        pca_variance_explained: [0.45, 0.22]
    },
    classification_metrics: {
        accuracy: 0.833,
        precision: 0.806,
        recall: 0.861,
        f1: 0.832,
        feature_importance: {
            Fe: 0.32, K: 0.22, Na: 0.15, P: 0.11, S: 0.08, Zn: 0.05, Ca: 0.03, Mg: 0.02, Mn: 0.01, Cu: 0.01
        }
    },
    regression_metrics: {
        orac: { r2: 0.45, rmse: 35.2 },
        phenolics: { r2: 0.38, rmse: 1.1 }
    },
    statistical_tests: [
        { analyte: 'Fe', p_value: 0.004, p_value_fdr: 0.012, effect_size_d: -0.85 },
        { analyte: 'K', p_value: 0.015, p_value_fdr: 0.035, effect_size_d: -0.62 },
        { analyte: 'Na', p_value: 0.045, p_value_fdr: 0.080, effect_size_d: 0.45 }
    ]
};

const demoTabPFNData = {
    RandomForest: { accuracy: 0.833, precision: 0.806, recall: 0.861, f1: 0.832 },
    TabPFN: { accuracy: 0.878, precision: 0.856, recall: 0.905, f1: 0.880 }
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

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
        });
    }

    // 3. Load Data
    let nutritionData = demoNutritionData;
    let mlData = demoMLData;
    let tabpfnData = demoTabPFNData;

    try {
        const resNut = await fetch('data/nutrition_data.json');
        if(resNut.ok) nutritionData = await resNut.json();
    } catch(e) { console.log('Using demo nutrition data', e); }

    try {
        const resML = await fetch('data/ml_results.json');
        if(resML.ok) mlData = await resML.json();
    } catch(e) { console.log('Using demo ML data', e); }

    try {
        const resTab = await fetch('data/tabpfn_comparison.json');
        if(resTab.ok) tabpfnData = await resTab.json();
    } catch(e) { console.log('Using demo TabPFN data', e); }

    // 4. Initialize Modules
    initCharts(nutritionData);
    initGallery();
    initML(mlData, tabpfnData);
});
