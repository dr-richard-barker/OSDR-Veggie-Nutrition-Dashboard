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

# Renaming map for nutrients
NUTRIENT_RENAME_MAP = {
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
    "ORAC (umol TE/g)": "orac",
    "Microbiology_APC (log10 CFU/g)": "micro_apc",
    "Microbiology_YMC (log10 CFU/g)": "micro_ymc"
}

def curate_single_dataset(raw_dir: Path, suffix: str):
    meta_file = raw_dir / f"synthetic_metadata_{suffix}.csv"
    nut_file = raw_dir / f"synthetic_nutrients_{suffix}.csv"
    
    if not (meta_file.exists() and nut_file.exists()):
        logger.error(f"Missing raw files for {suffix} in {raw_dir}")
        return None, None
        
    df_meta = pd.read_csv(meta_file)
    df_nut = pd.read_csv(nut_file)
    
    df_meta = df_meta.rename(columns={
        "Sample Name": "sample_id",
        "Mission": "mission",
        "Spaceflight/Ground Control": "condition",
        "Plant Number": "plant_number",
        "Harvest Day": "harvest_day",
        "Crop": "crop"
    })
    
    df_nut = df_nut.rename(columns=NUTRIENT_RENAME_MAP)
    df_master = pd.merge(df_meta, df_nut, on="sample_id")
    return df_meta, df_master

def curate_data(raw_dir: Path, processed_dir: Path, docs_data_dir: Path):
    logger.info("Starting meta-analysis data curation...")
    
    # 1. Curate Lettuce (745)
    meta_745, master_745 = curate_single_dataset(raw_dir, "745")
    
    # 2. Curate Mizuna (655)
    meta_655, master_655 = curate_single_dataset(raw_dir, "655")
    
    if master_745 is None or master_655 is None:
        logger.error("Failed to curate individual datasets.")
        return
        
    # Save original Lettuce-only files for backward compatibility
    # Drop microbiology columns so original RF model won't try to use them as elements
    master_745_compat = master_745.drop(columns=["crop", "micro_apc", "micro_ymc"], errors="ignore")
    meta_745_compat = meta_745.drop(columns=["crop"], errors="ignore")
    
    master_745_compat.to_csv(processed_dir / "veggie_nutrition_master.csv", index=False)
    master_745_compat.to_json(processed_dir / "veggie_nutrition_master.json", orient="records", indent=4)
    meta_745_compat.to_csv(processed_dir / "sample_metadata.csv", index=False)
    
    master_745_compat.to_json(docs_data_dir / "nutrition_data.json", orient="records", indent=4)
    meta_745_compat.to_json(docs_data_dir / "sample_metadata.json", orient="records", indent=4)
    logger.info("Saved backward compatibility Lettuce-only datasets.")
    
    # 3. Compile Combined Meta-Analysis Dataset
    df_meta_all = pd.concat([meta_745, meta_655], ignore_index=True)
    df_master_all = pd.concat([master_745, master_655], ignore_index=True)
    
    # Save processed meta-analysis datasets
    meta_csv_path = processed_dir / "veggie_meta_master.csv"
    meta_json_path = processed_dir / "veggie_meta_master.json"
    df_master_all.to_csv(meta_csv_path, index=False)
    df_master_all.to_json(meta_json_path, orient="records", indent=4)
    
    # Save metadata
    metadata_csv_path = processed_dir / "sample_meta_metadata.csv"
    df_meta_all.to_csv(metadata_csv_path, index=False)
    
    logger.info(f"Saved combined master dataset to {meta_csv_path} and {meta_json_path}")
    
    # Save web dashboard data files
    docs_nutrition_json = docs_data_dir / "meta_nutrition_data.json"
    docs_metadata_json = docs_data_dir / "meta_sample_metadata.json"
    
    df_master_all.to_json(docs_nutrition_json, orient="records", indent=4)
    df_meta_all.to_json(docs_metadata_json, orient="records", indent=4)
    
    logger.info(f"Saved web dashboard data to {docs_nutrition_json} and {docs_metadata_json}")
    logger.info("Data curation complete.")

def main():
    parser = argparse.ArgumentParser(description="Curate raw data for lettuce and mizuna meta-analysis.")
    parser.add_argument("--raw_dir", type=str, default="data/raw", help="Directory with raw data")
    parser.add_argument("--processed_dir", type=str, default="data/processed", help="Processed data directory")
    parser.add_argument("--docs_dir", type=str, default="docs/data", help="Dashboard data directory")
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
