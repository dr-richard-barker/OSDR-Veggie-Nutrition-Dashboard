import { initCharts } from './charts.js';
import { initGallery } from './gallery.js';
import { initML } from './ml-results.js';

// Demo data fallback for multi-crop meta-analysis
const demoNutritionData = [
    { sample_id: 'Sample_Demo_L1', crop: 'lettuce', mission: 'VEG-01A', condition: 'Flight', plant_number: 1, harvest_day: 33, Fe: 0.18, K: 35.5, Na: 2.1, P: 5.5, S: 2.8, Zn: 0.06, Ca: 12.0, Mg: 4.5, Mn: 0.1, Cu: 0.01, phenolics: 11.2, anthocyanins: 1.1, orac: 420.0, micro_apc: 3.5, micro_ymc: 1.8 },
    { sample_id: 'Sample_Demo_L2', crop: 'lettuce', mission: 'VEG-01A', condition: 'Ground', plant_number: 1, harvest_day: 33, Fe: 0.14, K: 41.2, Na: 1.2, P: 6.2, S: 2.1, Zn: 0.04, Ca: 11.8, Mg: 4.2, Mn: 0.09, Cu: 0.009, phenolics: 8.5, anthocyanins: 1.2, orac: 390.0, micro_apc: 3.2, micro_ymc: 1.4 },
    { sample_id: 'Sample_Demo_M1', crop: 'mizuna', mission: 'VEG-04A', condition: 'Flight', plant_number: 1, harvest_day: 28, Fe: 0.22, K: 45.1, Na: 3.8, P: 7.8, S: 6.2, Zn: 0.08, Ca: 24.5, Mg: 5.8, Mn: 0.15, Cu: 0.014, phenolics: 12.5, anthocyanins: 0.7, orac: 480.0, micro_apc: 4.1, micro_ymc: 2.0 },
    { sample_id: 'Sample_Demo_M2', crop: 'mizuna', mission: 'VEG-04A', condition: 'Ground', plant_number: 1, harvest_day: 28, Fe: 0.17, K: 47.9, Na: 2.5, P: 8.2, S: 5.1, Zn: 0.06, Ca: 21.0, Mg: 5.5, Mn: 0.13, Cu: 0.011, phenolics: 9.8, anthocyanins: 0.8, orac: 430.0, micro_apc: 3.0, micro_ymc: 1.2 }
];

const demoMLData = {
    pca: {
        PC1: [1.2, -1.1, 0.8, -0.9, 2.1, -1.8, 1.6, -1.2],
        PC2: [0.5, 0.8, -0.2, -0.5, 1.1, 1.4, -0.8, -0.9],
        condition: ['Flight', 'Ground', 'Flight', 'Ground', 'Flight', 'Ground', 'Flight', 'Ground'],
        mission: ['VEG-01A', 'VEG-01A', 'VEG-01B', 'VEG-01B', 'VEG-04A', 'VEG-04A', 'VEG-04B', 'VEG-04B'],
        crop: ['lettuce', 'lettuce', 'lettuce', 'lettuce', 'mizuna', 'mizuna', 'mizuna', 'mizuna'],
        sample_id: ['Sample_L1', 'Sample_L2', 'Sample_L3', 'Sample_L4', 'Sample_M1', 'Sample_M2', 'Sample_M3', 'Sample_M4'],
        variance_explained: [0.42, 0.25]
    },
    classification_metrics: {
        random_forest: { accuracy: 0.833, precision: 0.806, recall: 0.861, f1: 0.832 },
        tabpfn: { accuracy: 0.896, precision: 0.882, recall: 0.917, f1: 0.899 },
        feature_importance: {
            Fe: 0.28, K: 0.18, Na: 0.12, P: 0.10, S: 0.09, Zn: 0.06, Ca: 0.05, Mg: 0.04, Mn: 0.02, Cu: 0.01, phenolics: 0.03, anthocyanins: 0.01, orac: 0.01
        }
    },
    statistical_tests: [
        { analyte: 'Fe', p_value: 0.002, p_value_fdr: 0.008, effect_size_d: -0.89 },
        { analyte: 'K', p_value: 0.011, p_value_fdr: 0.025, effect_size_d: -0.65 },
        { analyte: 'Ca', p_value: 0.005, p_value_fdr: 0.015, effect_size_d: 0.75 },
        { analyte: 'S', p_value: 0.009, p_value_fdr: 0.022, effect_size_d: 0.81 }
    ]
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

    try {
        const resNut = await fetch('data/meta_nutrition_data.json');
        if(resNut.ok) nutritionData = await resNut.json();
    } catch(e) { console.log('Using demo nutrition data', e); }

    try {
        const resML = await fetch('data/meta_ml_results.json');
        if(resML.ok) mlData = await resML.json();
    } catch(e) { console.log('Using demo ML data', e); }

    // 4. Initialize Modules
    initCharts(nutritionData);
    initGallery();
    initML(mlData);
});
