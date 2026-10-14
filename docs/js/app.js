import { initCharts } from './charts.js';
import { initGallery } from './gallery.js';
import { initML, resizeMLPlots } from './ml-results.js';

// No demo or placeholder data: if a data file fails to load, the page says so
// and leaves those charts empty rather than drawing invented numbers.
function showDataError(files) {
    const banner = document.createElement('div');
    banner.className = 'card';
    banner.setAttribute('role', 'alert');
    banner.style.borderLeft = '4px solid #C2483F';
    const title = document.createElement('strong');
    title.textContent = 'Data failed to load. ';
    banner.appendChild(title);
    banner.appendChild(document.createTextNode(
        `Charts that depend on ${files.join(' and ')} are not shown. No placeholder values are substituted.`));
    (document.querySelector('main') || document.body).prepend(banner);
}

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Tab Navigation
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            const targetPanel = document.getElementById(btn.dataset.target);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }

            if (btn.dataset.target === 'panel-ml') {
                setTimeout(() => {
                    resizeMLPlots();
                }, 50);
            }
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
            if (mlData) {
                initML(mlData);
            }
        });
    }

    // 3. Load Data
    let nutritionData = null;
    let mlData = null;
    const failed = [];

    try {
        const resNut = await fetch('data/meta_nutrition_data.json');
        if (!resNut.ok) throw new Error(`HTTP ${resNut.status}`);
        nutritionData = await resNut.json();
    } catch (e) { failed.push(`data/meta_nutrition_data.json (${e.message})`); }

    try {
        const resML = await fetch('data/meta_ml_results.json');
        if (!resML.ok) throw new Error(`HTTP ${resML.status}`);
        mlData = await resML.json();
    } catch (e) { failed.push(`data/meta_ml_results.json (${e.message})`); }

    if (failed.length) showDataError(failed);

    // 4. Initialize Modules
    if (nutritionData) initCharts(nutritionData);
    initGallery();
    if (mlData) initML(mlData);
});
