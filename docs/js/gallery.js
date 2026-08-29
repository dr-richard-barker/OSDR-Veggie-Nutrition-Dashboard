export async function initGallery() {
    const grid = document.getElementById('image-grid');
    const modal = document.getElementById('lightbox');
    const modalImg = document.getElementById('lightbox-img');
    const modalMeta = document.getElementById('lightbox-meta');
    const closeBtn = document.querySelector('.close-modal');
    const compareModeCheckbox = document.getElementById('compare-mode');
    const compareView = document.getElementById('compare-view');
    const compareLeftContent = document.querySelector('#compare-left .compare-content');
    const compareRightContent = document.querySelector('#compare-right .compare-content');

    let isCompareMode = false;
    let selectedFlight = null;
    let selectedGround = null;
    
    // Default placeholder images
    let images = Array.from({length: 12}, (_, i) => ({
        filename: `placeholder_${i+1}.jpg`,
        path: `https://picsum.photos/seed/${i+100}/400/300`,
        title: `Veggie Crop Photograph ${i+1}`,
        mission: i % 3 === 0 ? 'VEG-01A' : (i % 3 === 1 ? 'VEG-01B' : 'VEG-03A'),
        condition: i % 2 === 0 ? 'Flight' : 'Ground',
        description: `Photograph representing space-grown crop canopy under Veggie illumination.`
    }));

    try {
        const res = await fetch('data/gallery_metadata.json');
        if (res.ok) {
            const actualImages = await res.json();
            if (actualImages && actualImages.length > 0) {
                images = actualImages;
            }
        }
    } catch(e) {
        console.log('Using default gallery fallback images:', e);
    }

    // Set initial compare selections
    selectedFlight = images.find(img => img.condition.toLowerCase() === 'flight') || images[0];
    selectedGround = images.find(img => img.condition.toLowerCase() === 'ground') || images[1];

    function updateCompareBoxes() {
        if (compareLeftContent && selectedFlight) {
            compareLeftContent.innerHTML = `
                <img src="${selectedFlight.path}" alt="${selectedFlight.title}" style="max-height: 220px; width: auto; max-width: 100%; border-radius: 6px; object-fit: contain; margin-top: 8px;" onerror="this.src='https://picsum.photos/seed/veggie1/400/300';">
                <div style="font-size: 0.82rem; margin-top: 6px; font-weight: 600;">${selectedFlight.mission} (Flight)</div>
                <div style="font-size: 0.75rem; color: var(--muted);">${selectedFlight.title}</div>
            `;
        }
        if (compareRightContent && selectedGround) {
            compareRightContent.innerHTML = `
                <img src="${selectedGround.path}" alt="${selectedGround.title}" style="max-height: 220px; width: auto; max-width: 100%; border-radius: 6px; object-fit: contain; margin-top: 8px;" onerror="this.src='https://picsum.photos/seed/veggie2/400/300';">
                <div style="font-size: 0.82rem; margin-top: 6px; font-weight: 600;">${selectedGround.mission} (Ground Control)</div>
                <div style="font-size: 0.75rem; color: var(--muted);">${selectedGround.title}</div>
            `;
        }
    }

    // Compare Mode Toggle
    if (compareModeCheckbox && compareView) {
        compareModeCheckbox.addEventListener('change', (e) => {
            isCompareMode = e.target.checked;
            if (isCompareMode) {
                compareView.classList.remove('hidden');
                updateCompareBoxes();
            } else {
                compareView.classList.add('hidden');
            }
        });
    }

    // Render Grid
    function renderImages(filter = 'all') {
        if (!grid) return;
        grid.innerHTML = '';
        
        images.forEach(img => {
            const condLower = img.condition.toLowerCase();
            const missLower = img.mission.toLowerCase();
            
            if (filter !== 'all' && filter !== condLower && filter !== missLower) return;
            
            const div = document.createElement('div');
            div.className = 'gallery-item';
            div.innerHTML = `
                <img src="${img.path}" alt="${img.description}" loading="lazy" onerror="this.src='https://picsum.photos/seed/veggie/400/300';">
                <div class="gallery-meta">${img.mission} - ${img.condition.toUpperCase()}</div>
            `;
            div.addEventListener('click', () => {
                if (isCompareMode) {
                    if (img.condition.toLowerCase() === 'flight') {
                        selectedFlight = img;
                    } else {
                        selectedGround = img;
                    }
                    updateCompareBoxes();
                } else {
                    openModal(img);
                }
            });
            grid.appendChild(div);
        });
    }

    // Modal logic
    function openModal(img) {
        if (!modalImg || !modalMeta || !modal) return;
        modalImg.src = img.path;
        modalMeta.innerHTML = `
            <h3>${img.title || img.filename}</h3>
            <strong>Mission:</strong> ${img.mission}<br>
            <strong>Condition:</strong> ${img.condition.toUpperCase()}<br>
            <strong>Description:</strong> ${img.description}
        `;
        modal.style.display = 'block';
    }

    if (closeBtn) {
        closeBtn.onclick = () => modal.style.display = 'none';
    }
    
    window.onclick = (e) => { 
        if (e.target === modal) modal.style.display = 'none'; 
    };
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal) modal.style.display = 'none';
    });

    // Filters
    document.querySelectorAll('#gallery-filters .btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('#gallery-filters .btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            renderImages(e.target.dataset.filter);
        });
    });

    renderImages();
}
