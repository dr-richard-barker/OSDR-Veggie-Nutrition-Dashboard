export async function initGallery() {
    const grid = document.getElementById('image-grid');
    const modal = document.getElementById('lightbox');
    const modalImg = document.getElementById('lightbox-img');
    const modalMeta = document.getElementById('lightbox-meta');
    const closeBtn = document.querySelector('.close-modal');
    
    // Default placeholder images
    let images = Array.from({length: 12}, (_, i) => ({
        filename: `placeholder_${i+1}.jpg`,
        path: `https://picsum.photos/seed/${i+100}/400/300`,
        title: `Veggie Crop Placeholder ${i+1}`,
        mission: i % 3 === 0 ? 'VEG-01A' : (i % 3 === 1 ? 'VEG-01B' : 'VEG-03A'),
        condition: i % 2 === 0 ? 'Flight' : 'Ground',
        description: `Placeholder image representing lettuce growing in Veggie hardware on ISS/Ground.`
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

    // Render
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
                <img src="${img.path}" alt="${img.description}" loading="lazy">
                <div class="gallery-meta">${img.mission} - ${img.condition.toUpperCase()}</div>
            `;
            div.addEventListener('click', () => openModal(img));
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
