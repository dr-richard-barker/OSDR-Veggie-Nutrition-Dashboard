export function initGallery() {
    const grid = document.getElementById('image-grid');
    const modal = document.getElementById('lightbox');
    const modalImg = document.getElementById('lightbox-img');
    const modalMeta = document.getElementById('lightbox-meta');
    const closeBtn = document.querySelector('.close-modal');
    
    // Generate 12 dummy images
    const images = Array.from({length: 12}, (_, i) => ({
        id: i,
        src: `https://picsum.photos/seed/${i+100}/400/300`, // Placeholder
        mission: i % 3 === 0 ? 'VEG-01A' : (i % 3 === 1 ? 'VEG-01B' : 'VEG-03A'),
        condition: i % 2 === 0 ? 'flight' : 'ground',
        desc: `Plant sample image from ${i % 2 === 0 ? 'ISS' : 'Ground Control'}`
    }));

    // Render
    function renderImages(filter = 'all') {
        grid.innerHTML = '';
        images.forEach(img => {
            if (filter !== 'all' && filter !== img.condition && filter !== img.mission.toLowerCase()) return;
            
            const div = document.createElement('div');
            div.className = 'gallery-item';
            div.innerHTML = `
                <img src="${img.src}" alt="${img.desc}" loading="lazy">
                <div class="gallery-meta">${img.mission} - ${img.condition.toUpperCase()}</div>
            `;
            div.addEventListener('click', () => openModal(img));
            grid.appendChild(div);
        });
    }

    // Modal logic
    function openModal(img) {
        modalImg.src = img.src;
        modalMeta.innerHTML = `<strong>Mission:</strong> ${img.mission}<br><strong>Condition:</strong> ${img.condition.toUpperCase()}<br><strong>Description:</strong> ${img.desc}`;
        modal.style.display = 'block';
    }

    closeBtn.onclick = () => modal.style.display = 'none';
    window.onclick = (e) => { if(e.target === modal) modal.style.display = 'none'; };
    document.addEventListener('keydown', (e) => {
        if(e.key === 'Escape') modal.style.display = 'none';
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
