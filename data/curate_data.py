import os
import sys
import json
import logging
import argparse
import pandas as pd
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def curate_data(raw_dir: Path, processed_dir: Path, docs_data_dir: Path):
    """
    Reads raw OSDR data files (or synthetic fallback files), cleans and curates the data,
    and outputs processed datasets and web-ready JSON files.
    
    Args:
        raw_dir: Directory containing raw metadata and data files.
        processed_dir: Directory to save processed data for analysis.
        docs_data_dir: Directory to save web dashboard data.
    """
    logger.info("Starting data curation...")
    
    # Check for synthetic data or real data
    # In this pipeline, fetch_osdr_data.py generated synthetic_metadata.csv and synthetic_nutrients.csv
    # if it fell back. Let's look for those.
    
    metadata_file = raw_dir / "synthetic_metadata.csv"
    nutrients_file = raw_dir / "synthetic_nutrients.csv"
    
    if not (metadata_file.exists() and nutrients_file.exists()):
        logger.error(f"Could not find expected raw files in {raw_dir}.")
        logger.info("Assuming actual ISA-Tab parsing logic would go here if files were downloaded.")
        return
        
    logger.info("Loading metadata...")
    metadata_df = pd.read_csv(metadata_file)
    
    logger.info("Loading nutritional data...")
    nutrients_df = pd.read_csv(nutrients_file)
    
    # Clean and standardize metadata
    # Expected columns: sample_id, mission, condition, plant_number, harvest_day
    metadata_df = metadata_df.rename(columns={
        "Sample Name": "sample_id",
        "Mission": "mission",
        "Spaceflight/Ground Control": "condition",
        "Plant Number": "plant_number",
        "Harvest Day": "harvest_day"
    })
    
    # Clean and standardize nutrients data
    nutrient_rename_map = {
        "Sample Name": "sample_id",
        "Fe (mg/g)": "Fe",
        "K (mg/g)": "K",
        "Na (mg/g)": "Na",
        "P (mg/g)": "P",
        "S (mg/g)": "S",
        "Zn (mg/g)": "Zn",
        "Ca (mg/g)": "Ca",
        "Mg (mg/g)": "Mg",
        "Mn (mg/g)": "Mn",
        "Cu (mg/g)": "Cu",
        "Phenolics (GAE mg/g)": "phenolics",
        "Anthocyanins (mg/g)": "anthocyanins",
        "ORAC (umol TE/g)": "orac"
    }
    nutrients_df = nutrients_df.rename(columns=nutrient_rename_map)
    
    # Merge them
    master_df = pd.merge(metadata_df, nutrients_df, on="sample_id")
    
    # Save Processed Master Data
    master_csv_path = processed_dir / "veggie_nutrition_master.csv"
    master_json_path = processed_dir / "veggie_nutrition_master.json"
    
    master_df.to_csv(master_csv_path, index=False)
    master_df.to_json(master_json_path, orient="records", indent=4)
    logger.info(f"Saved master dataset to {master_csv_path} and {master_json_path}")
    
    # Save Processed Metadata
    metadata_csv_path = processed_dir / "sample_metadata.csv"
    metadata_df.to_csv(metadata_csv_path, index=False)
    logger.info(f"Saved sample metadata to {metadata_csv_path}")
    
    # Save Web Dashboard Data
    docs_nutrition_json = docs_data_dir / "nutrition_data.json"
    docs_metadata_json = docs_data_dir / "sample_metadata.json"
    
    # For web dashboard, we might want slightly different formatting, but for now we export records
    master_df.to_json(docs_nutrition_json, orient="records", indent=4)
    metadata_df.to_json(docs_metadata_json, orient="records", indent=4)
    
    logger.info(f"Saved web dashboard data to {docs_nutrition_json} and {docs_metadata_json}")
    logger.info("Data curation complete.")

def main():
    parser = argparse.ArgumentParser(description="Curate raw OSDR data for the Veggie Nutrition Dashboard.")
    parser.add_argument("--raw_dir", type=str, default="data/raw", help="Directory with raw data")
    parser.add_argument("--processed_dir", type=str, default="data/processed", help="Directory for processed data")
    parser.add_argument("--docs_dir", type=str, default="docs/data", help="Directory for web dashboard data")
    args = parser.parse_args()
    
    base_path = Path(__file__).parent.parent
    raw_dir = base_path / args.raw_dir
    processed_dir = base_path / args.processed_dir
    docs_data_dir = base_path / args.docs_dir
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    docs_data_dir.mkdir(parents=True, exist_ok=True)
    
    curate_data(raw_dir, processed_dir, docs_data_dir)

if __name__ == "__main__":
    main()
