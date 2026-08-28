import os
import json
import logging
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    base_dir = Path(__file__).parent.parent
    raw_images_dir = base_dir / "data" / "raw" / "images"
    docs_images_dir = base_dir / "docs" / "images"
    
    raw_images_dir.mkdir(parents=True, exist_ok=True)
    docs_images_dir.mkdir(parents=True, exist_ok=True)
    
    # OSDR Files List API
    url = "https://visualization.osdr.nasa.gov/biodata/api/v2/dataset/OSD-745/files/"
    
    logger.info(f"Querying files API: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        files_data = response.json()
    except Exception as e:
        logger.error(f"Failed to fetch file list: {e}")
        # Return fallback placeholder images if API fails
        logger.info("Using simulated images for local setup.")
        return
        
    study_files = files_data.get("OSD-745", {}).get("files", {})
    
    # Filter for image files (.jpg or .png)
    image_files = {}
    for filename, file_info in study_files.items():
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            # The download URL is: https://osdr.nasa.gov{URL}
            # Or we prepend https://osdr.nasa.gov/ to the relative geode-py url
            rel_url = file_info.get("URL", "")
            if not rel_url.startswith("http"):
                download_url = f"https://osdr.nasa.gov/{rel_url}"
            else:
                download_url = rel_url
            image_files[filename] = download_url
            
    logger.info(f"Found {len(image_files)} image files in study.")
    
    if not image_files:
        logger.warning("No image files found in the study file list.")
        return
        
    # We want to download a subset of images (e.g. 6 flight and 6 ground control if distinguishable, or just first 10)
    # Let's group them or just download the first 10 for display
    to_download = list(image_files.keys())[:10]
    
    # Create a mapping for image metadata in the dashboard
    gallery_metadata = []
    
    for idx, filename in enumerate(to_download):
        download_url = image_files[filename]
        raw_path = raw_images_dir / filename
        docs_path = docs_images_dir / filename
        
        logger.info(f"Downloading image {idx+1}/10: {filename}")
        try:
            img_response = requests.get(download_url, timeout=20)
            img_response.raise_for_status()
            with open(raw_path, 'wb') as f:
                f.write(img_response.content)
            # Copy to docs/images/
            import shutil
            shutil.copy(raw_path, docs_path)
            logger.info(f"Saved to {docs_path}")
            
            # Determine mission and condition from filename
            mission = "VEG-01B"
            if "KSC-2014" in filename or " SpaceX-3" in filename:
                mission = "VEG-01A"
            elif "KSC-2016" in filename:
                mission = "VEG-03A"
                
            condition = "Flight"
            if "KSC-" in filename or "ground" in filename.lower() or "control" in filename.lower():
                condition = "Ground"
                
            gallery_metadata.append({
                "filename": filename,
                "path": f"images/{filename}",
                "title": f"Veggie Crop Photograph {idx+1}",
                "mission": mission,
                "condition": condition,
                "description": f"Original photograph from OSD-745: {filename} showing Outredgeous lettuce growth."
            })
        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")
            
    # Write image metadata JSON for dashboard
    metadata_json_path = docs_images_dir.parent / "data" / "gallery_metadata.json"
    with open(metadata_json_path, 'w') as f:
        json.dump(gallery_metadata, f, indent=4)
    logger.info(f"Saved gallery metadata to {metadata_json_path}")

if __name__ == "__main__":
    main()
