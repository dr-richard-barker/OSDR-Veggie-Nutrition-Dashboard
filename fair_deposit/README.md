# OSDR Veggie Nutritional Analysis — Zenodo Deposit

This deposit contains the complete analysis pipeline, interactive dashboard, and manuscript for the nutritional composition analysis of lettuce grown aboard the International Space Station.

## Contents

| File | Description |
|------|-------------|
| `veggie_nutrition_master.csv` | Curated dataset: 14 nutritional analytes × ~36 samples |
| `ml_results_summary.json` | Complete ML analysis results (PCA, RF, SHAP, stats) |
| `data_dictionary.json` | Machine-readable column schema |
| `ml_pipeline.py` | Reproducible analysis script |
| `OSDR_Veggie_Nutrition_Analysis.pdf` | Publication manuscript |
| `docs/` | Interactive GitHub Pages dashboard |

## Data Source

NASA Open Science Data Repository (OSDR) study **OSD-745**:
*"Microbiological and Nutritional Analysis of Lettuce Crops Grown on the International Space Station"*

- **DOI:** [10.3389/fpls.2020.00199](https://doi.org/10.3389/fpls.2020.00199)
- **Organism:** *Lactuca sativa* cv. 'Outredgeous' (red romaine lettuce)
- **Hardware:** Veggie plant growth system
- **Missions:** VEG-01A (2014), VEG-01B (2015), VEG-03A (2016)

## License

- **Code:** MIT
- **Text & Figures:** CC-BY-4.0
- **Original data:** NASA public domain
