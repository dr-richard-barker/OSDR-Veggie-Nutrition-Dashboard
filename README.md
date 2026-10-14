# 🥬 OSDR Multi-Crop Space Agriculture Meta-Analysis: Dashboard & ML Pipeline

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.XXXXXXX-blue)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![License: MIT](https://img.shields.io/badge/Code-MIT-green.svg)](LICENSE)
[![License: CC BY 4.0](https://img.shields.io/badge/Docs-CC_BY_4.0-lightgrey.svg)](LICENSE-CC-BY-4.0)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://www.python.org/)
[![Data: NASA OSDR](https://img.shields.io/badge/Data-NASA_OSDR_OSD--745_%7C_655_%7C_780-orange.svg)](https://osdr.nasa.gov/)

**Interactive dashboard, machine learning analysis, and FAIR-compliant research repository for the comparative nutritional and microbiological meta-analysis of space-grown crops (Lettuce and Mizuna Mustard) cultivated aboard the International Space Station using the Veggie plant growth hardware.**

> **Author:** Richard Barker · NASA GeneLab / OSDR  
> **Target Journal:** *Frontiers in Plant Science* / *npj Microgravity*  
> **Data Sources:** [NASA OSDR OSD-745](https://osdr.nasa.gov/bio/repo/data/studies/OSD-745), [OSD-655](https://osdr.nasa.gov/bio/repo/data/studies/OSD-655), [OSD-780](https://osdr.nasa.gov/bio/repo/data/studies/OSD-780)  
> **Reference Publications:** 
> - Khodadad et al. (2020) *Front. Plant Sci.* [DOI: 10.3389/fpls.2020.00199](https://doi.org/10.3389/fpls.2020.00199)
> - Bunchek et al. (2024) *J. Plant Interact.* [DOI: 10.1080/17429145.2023.2292220](https://doi.org/10.1080/17429145.2023.2292220)
> - Hollmann et al. (2025) *Nature* [DOI: 10.1038/s41586-024-08328-6](https://doi.org/10.1038/s41586-024-08328-6)

---

## 🔬 Key Outputs

- 🌐 **[Interactive CoSE Dashboard](https://dr-richard-barker.github.io/OSDR-Veggie-Nutrition-Dashboard/)** — Multi-crop data explorer, ISS photography gallery, food safety microbiology, and ML benchmarking
- 📊 **Meta-Analysis ML Pipeline** — Joint PCA, Leave-One-Mission-Out CV, a benchmark model (written for TabPFN; without a license token it falls back to Gradient Boosting, and every reported benchmark result is that fallback), and Gini feature importance (SHAP is computed only in the lettuce-only `analysis/ml_pipeline.py`). *(Leave-One-Crop-Out CV was previously listed here and has been withdrawn: no crop-based split is implemented — every `LeaveOneGroupOut` in `analysis/` groups on mission. On the real OSDR data, cross-crop transfer performs below a stratified-dummy baseline.)*
- 📄 **LaTeX Manuscript** — Publication-ready PDF ([OSDR_Veggie_Nutrition_Analysis.pdf](manuscript/OSDR_Veggie_Nutrition_Analysis.pdf)) styled with the CoSE (Collaborative Science Environment) design system

---

## 🧪 Scientific Context

Two leafy green crops were evaluated aboard the ISS across 5 independent spaceflight missions:

| Crop Species | Cultivar | Mission | ISS Period | Harvest Strategy | Study IDs |
|--------------|----------|---------|------------|------------------|-----------|
| *Lactuca sativa* | 'Outredgeous' (Red Romaine) | VEG-01A | May – Jun 2014 | Terminal harvest (33 d) | OSD-745 |
| *Lactuca sativa* | 'Outredgeous' (Red Romaine) | VEG-01B | Jul – Aug 2015 | Terminal harvest (33 d) | OSD-745 |
| *Lactuca sativa* | 'Outredgeous' (Red Romaine) | VEG-03A | Oct – Dec 2016 | Cut-and-come-again (33–56 d) | OSD-745 |
| *Brassica rapa* | Mizuna (var. *japonica*) | VEG-04A | Jun – Jul 2019 | Single terminal harvest (35 d) | OSD-655, OSD-780 |
| *Brassica rapa* | Mizuna (var. *japonica*) | VEG-04B | Oct – Nov 2019 | Repeated harvests (29, 43 and 58 d) | OSD-655, OSD-780 |

Parallel ground controls were grown at Kennedy Space Center (KSC) in controlled environment chambers replicating ISS telemetry (temperature, relative humidity, $\text{CO}_2$) with a 24–72 h delay.

### Multi-Crop Findings & Data Provenance
- **Translational Countermeasures & Astronaut Health:** Crop elemental mineral yields ($\text{K}^+$, $\text{Ca}^{2+}$, $\text{Mg}^{2+}$, $\text{Fe}^{2+}$, $\text{Zn}^{2+}$) could contribute to dietary countermeasures for the spaceflight mineral-pathway changes studied in astronaut crews. See companion repository [**astronaut-mineral-final**](https://github.com/dr-richard-barker/astronaut-mineral-final) for Inspiration4 multi-omics mineral pathway regulation and NHANES population comparisons.
- **Open Science Data, read from the archive:** 24 lettuce samples (OSD-745; 11 flight, 13 ground) and 36 mizuna (OSD-655; 18, 18), plus one mizuna sample with a phenolic measurement but no elemental data, across 5 missions (VEG-01A, VEG-01B, VEG-03A, VEG-04A, VEG-04B). Downloaded by `data/fetch_osdr_data.py`; checksums and unit provenance in `data/raw/osdr_fetch_provenance.json`.

> **⚠️ Correction, 13 October 2026.** Earlier versions of this repository
> reported figures that did not come from NASA OSDR. `data/fetch_osdr_data.py`
> returned values written as literals in its own source — first produced by
> `numpy.random.normal()`, later replaced by hand-typed numbers that still did
> not match the archive (36 lettuce samples against the archive's 24, calcium
> about 3× the measured value, a copper column for a study that never measured
> copper). The data layer now downloads and uses the archive and has no
> synthetic fallback, and all derived results have been regenerated.
>
> **What changed:** classification accuracy fell from 83.3%/89.6% to 0.490/0.572
> (at or below chance); the elemental→antioxidant regression, scored out-of-fold
> rather than in-sample, gives R² of −0.90 and −2.16 (worse than predicting the
> mean); of five analytes previously reported significant, only potassium and
> sulfur survive FDR correction; and the cross-species (LOCOCV) claim is
> withdrawn — no crop-based split was ever implemented. Full detail in
> [CORRECTION_NOTE_2_ANTIOXIDANTS.md](https://github.com/dr-richard-barker/SpaceMineralAtlas/blob/main/veggie_correction/CORRECTION_NOTE_2_ANTIOXIDANTS.md).
- **Nutrition and food safety:** Only potassium and sulfur differ between flight and ground after FDR correction, both higher in flight, in a pooled test not blocked by crop or mission; equivalence was not formally tested. Flight mizuna leaf carries a substantially higher microbial load than ground controls (OSD-780).
- **Machine Learning Cross-Validation:** Under Leave-One-Mission-Out Cross-Validation, neither the Random Forest (accuracy 0.490) nor the Gradient Boosting benchmark (0.572) separates flight from ground.

---

## 🚀 Quickstart

```bash
# Clone the repository
git clone https://github.com/dr-richard-barker/OSDR-Veggie-Nutrition-Dashboard.git
cd OSDR-Veggie-Nutrition-Dashboard

# Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r analysis/requirements.txt

# Fetch authentic metadata and curate datasets
python data/fetch_osdr_data.py
python data/curate_data.py

# Run Meta-Analysis ML pipeline
python analysis/meta_ml_pipeline.py
python analysis/tabpfn_pipeline.py

# View the interactive dashboard locally:
python3 -m http.server 8080 -d docs
```

---

## 📁 Repository Architecture

```
OSDR-Veggie-Nutrition-Dashboard/
├── README.md                          # Repository overview & metadata
├── CITATION.cff                       # CFF v1.2.0 citation metadata
├── LICENSE                            # MIT (code)
├── LICENSE-CC-BY-4.0                  # CC-BY-4.0 (text & figures)
├── .github/workflows/pages.yml        # Automated GitHub Pages CI/CD
│
├── data/                              # Data acquisition & curation
│   ├── fetch_osdr_data.py            # OSDR API multi-study fetch script
│   ├── curate_data.py                # Data harmonization pipeline
│   ├── raw/                          # Unmodified OSDR downloads
│   ├── processed/                    # Analysis-ready datasets
│   │   ├── veggie_meta_master.csv    # Merged master dataset (61 rows; 60 with elemental data)
│   │   └── veggie_nutrition_master.csv
│   └── images/                       # ISS Veggie photographs
│
├── analysis/                          # Machine learning pipeline
│   ├── meta_ml_pipeline.py           # Joint PCA, RF, TabPFN; LOMOCV only (groups on mission)
│   ├── requirements.txt              # Python dependencies
│   ├── figures/                      # High-res publication plots (300 DPI)
│   ├── results/                      # JSON summaries for dashboard
│   └── models/                       # Saved trained models (joblib)
│
├── docs/                              # CoSE Interactive Dashboard
│   ├── index.html                    # 5-panel CoSE sidebar web application
│   ├── css/style.css                 # Shared CoSE design system
│   ├── js/                           # Modular ES6 visualization code
│   └── data/                         # Precomputed JSON data matrices
│
├── manuscript/                        # LaTeX publication
│   ├── main.tex                      # Master document
│   ├── cose-style.sty                # CoSE design system LaTeX package
│   ├── chapters/                     # Modular chapter files (01-05)
│   ├── figures/                      # Manuscript figures
│   ├── references.bib                # BibTeX references
│   └── build.sh                      # Tectonic compiler script
│
└── fair_deposit/                      # Zenodo & RO-Crate metadata
    ├── zenodo.json
    ├── CITATION.cff
    ├── data_dictionary.json
    ├── ro-crate-metadata.json
    └── OSDR_Veggie_Nutrition_Analysis.pdf
```

---

## 📖 Citations

```bibtex
@article{khodadad2020microbiological,
  title     = {Microbiological and Nutritional Analysis of Lettuce Crops Grown on the International Space Station},
  author    = {Khodadad, Christina L. M. and Hummerick, Mary E. and Spencer, LaShelle E. and Dixit, Anirudha R. and Richards, Jeffrey T. and Romeyn, Matthew W. and Smith, Trent M. and Wheeler, Raymond M. and Massa, Gioia D.},
  journal   = {Frontiers in Plant Science},
  volume    = {11},
  pages     = {199},
  year      = {2020},
  doi       = {10.3389/fpls.2020.00199}
}

@article{bunchek2024pick,
  title     = {Pick-and-eat space crop production flight testing on the International Space Station},
  author    = {Bunchek, Jess M. and Hummerick, Mary E. and Spencer, LaShelle E. and Romeyn, Matthew W. and Young, Millennia and Morrow, Robert C. and Mitchell, Cary A. and Douglas, Grace L. and Wheeler, Raymond M. and Massa, Gioia D.},
  journal   = {Journal of Plant Interactions},
  volume    = {19},
  number    = {1},
  pages     = {2292220},
  year      = {2024},
  doi       = {10.1080/17429145.2023.2292220}
}

@article{hollmann2025accurate,
  title     = {Accurate predictions on small data with a tabular foundation model},
  author    = {Hollmann, Noah and M{\"u}ller, Samuel and Purucker, Lennart and Krishnakumar, Arjun and K{\"o}rfer, Max and Hoo, Shi Bin and Schirrmeister, Robin Tibor and Hutter, Frank},
  journal   = {Nature},
  volume    = {637},
  pages     = {319--326},
  year      = {2025},
  doi       = {10.1038/s41586-024-08328-6}
}
```

---

## ⚖️ Licensing

| Component | License |
|-----------|---------|
| Code & scripts | [MIT](LICENSE) |
| Manuscript, figures & documentation | [CC-BY-4.0](LICENSE-CC-BY-4.0) |
| Original OSDR data | NASA Open Data (public domain) |
