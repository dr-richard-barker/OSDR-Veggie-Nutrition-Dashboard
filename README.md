# 🥬 OSDR Veggie Nutritional Analysis Dashboard & ML Pipeline

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.XXXXXXX-blue)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![License: MIT](https://img.shields.io/badge/Code-MIT-green.svg)](LICENSE)
[![License: CC BY 4.0](https://img.shields.io/badge/Docs-CC_BY_4.0-lightgrey.svg)](LICENSE-CC-BY-4.0)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://www.python.org/)
[![Data: NASA OSDR](https://img.shields.io/badge/Data-NASA_OSDR_OSD--745-orange.svg)](https://osdr.nasa.gov/bio/repo/data/studies/OSD-745)

**Interactive dashboard, machine learning analysis, and FAIR-compliant research repository for the nutritional composition of lettuce crops grown aboard the International Space Station using the Veggie plant growth hardware.**

> **Author:** Richard Barker · NASA GeneLab / OSDR  
> **Target Journal:** *Frontiers in Plant Science* / *npj Microgravity*  
> **Data Source:** [NASA OSDR OSD-745](https://osdr.nasa.gov/bio/repo/data/studies/OSD-745)  
> **Reference Publication:** Khodadad et al. (2020) [DOI: 10.3389/fpls.2020.00199](https://doi.org/10.3389/fpls.2020.00199)

---

## 🔬 Key Outputs

- 🌐 **[Interactive Dashboard](https://dr-richard-barker.github.io/OSDR-Veggie-Nutrition-Dashboard/)** — Explore nutritional data, ISS images, and ML results
- 📊 **ML Analysis** — PCA, Random Forest classification, SHAP feature importance, statistical testing
- 📄 **LaTeX Manuscript** — Publication-ready PDF and DOCX with all figures

---

## 🧪 Scientific Context

*Lactuca sativa* cv. **'Outredgeous'** (red romaine lettuce) was grown aboard the ISS in the **Veggie** plant growth hardware across three independent missions:

| Mission | ISS Period | SpaceX Flight | Growth Duration |
|---------|-----------|---------------|-----------------|
| VEG-01A | May – Jun 2014 | SpaceX-3 | 33 days |
| VEG-01B | Jul – Aug 2015 | SpaceX-8 | 33 days |
| VEG-03A | Oct – Dec 2016 | SpaceX-8 | 33–56 days (sequential harvest) |

Parallel ground controls were grown at Kennedy Space Center (KSC) in controlled environment chambers replicating ISS conditions with a 24–72 h delay.

### Nutritional Assays

Harvested leaves were analyzed for:

- **Elemental composition** (ICP-OES): Fe, K, Na, P, S, Zn, Ca, Mg, Mn, Cu — reported in mg/g dry weight
- **Total phenolic content** (Folin–Ciocalteu): gallic acid equivalents (GAE mg/g DW)
- **Anthocyanin content** (pH differential): cyanidin-3-glucoside equivalents (mg/g DW)
- **Antioxidant capacity** (ORAC): μmol Trolox equivalents/g DW

Key findings from Khodadad et al. (2020):
- Significant differences in **Fe, K, Na, P, S, Zn** between flight and ground
- **No significant differences** in anthocyanins or ORAC
- Space-grown lettuce was **safe for consumption** with comparable nutritional quality

### Machine Learning Analysis

This repository extends the original descriptive analysis with multivariate ML methods:

$$\mathbf{X} \in \mathbb{R}^{n \times p}, \quad n \approx 36 \text{ samples}, \quad p = 14 \text{ nutritional features}$$

- **PCA** dimensionality reduction to visualize sample clustering
- **Random Forest** classification (flight vs. ground) with leave-one-mission-out CV
- **SHAP** (SHapley Additive exPlanations) for interpretable feature importance
- **Multi-target regression** predicting biochemical properties from elemental profiles
- **Statistical testing** with multiple comparison correction (FDR, Bonferroni)

---

## 🚀 Quickstart

```bash
# Clone the repository
git clone https://github.com/dr-richard-barker/OSDR-Veggie-Nutrition-Dashboard.git
cd OSDR-Veggie-Nutrition-Dashboard

# Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r analysis/requirements.txt

# Fetch data from OSDR (with fallback to synthetic data)
python data/fetch_osdr_data.py
python data/curate_data.py

# Run ML analysis
python analysis/ml_pipeline.py

# View the interactive dashboard
open docs/index.html
# or serve locally:
python3 -m http.server 8080 -d docs

# Build the manuscript (requires Tectonic or pdflatex)
cd manuscript && bash build.sh
```

---

## 📁 Repository Architecture

```
OSDR-Veggie-Nutrition-Dashboard/
├── README.md                          # This file
├── CITATION.cff                       # CFF v1.2.0 citation metadata
├── LICENSE                            # MIT (code)
├── LICENSE-CC-BY-4.0                  # CC-BY-4.0 (text & figures)
├── .gitignore
├── .github/workflows/pages.yml        # GitHub Pages deployment
│
├── data/                              # Data acquisition & curation
│   ├── fetch_osdr_data.py            # OSDR API download script
│   ├── curate_data.py                # Data harmonization pipeline
│   ├── raw/                          # Unmodified OSDR downloads
│   ├── processed/                    # Analysis-ready datasets
│   │   ├── veggie_nutrition_master.csv
│   │   └── data_dictionary.json
│   └── images/                       # ISS Veggie photographs
│
├── analysis/                          # Machine learning pipeline
│   ├── ml_pipeline.py                # Complete ML analysis script
│   ├── requirements.txt              # Python dependencies
│   ├── figures/                      # Generated plots (PNG, 300 DPI)
│   ├── results/                      # JSON results for dashboard
│   └── models/                       # Saved sklearn models (joblib)
│
├── docs/                              # GitHub Pages dashboard
│   ├── index.html                    # 5-panel interactive dashboard
│   ├── css/style.css                 # CoSE design system
│   ├── js/                           # Modular ES6 visualization code
│   └── data/                         # Dashboard JSON data
│
├── manuscript/                        # LaTeX publication
│   ├── main.tex                      # Master document
│   ├── cose-style.sty                # CoSE design system package
│   ├── chapters/                     # Modular chapter files
│   ├── figures/                      # Manuscript figures
│   ├── build.sh                      # Tectonic build script
│   └── Makefile                      # pdf / docx / clean targets
│
└── fair_deposit/                      # Zenodo & RO-Crate metadata
    ├── zenodo.json
    ├── CITATION.cff
    ├── data_dictionary.json
    ├── ro-crate-metadata.json
    └── README.md
```

---

## 📖 Citation

```bibtex
@software{barker2026veggie,
  author    = {Barker, Richard},
  title     = {{OSDR Veggie Nutritional Analysis Dashboard \& ML Pipeline}},
  year      = {2026},
  publisher = {GitHub / Zenodo},
  url       = {https://github.com/dr-richard-barker/OSDR-Veggie-Nutrition-Dashboard},
  doi       = {10.5281/zenodo.XXXXXXX}
}
```

**Original data publication:**
```bibtex
@article{khodadad2020microbiological,
  title     = {Microbiological and Nutritional Analysis of Lettuce Crops Grown
               on the International Space Station},
  author    = {Khodadad, Christina L. M. and Hummerick, Mary E. and Spencer,
               LaShelle E. and Dixit, Anirudha R. and Richards, Jeffrey T. and
               Romeyn, Matthew W. and Smith, Trent M. and Wheeler, Raymond M.
               and Massa, Gioia D.},
  journal   = {Frontiers in Plant Science},
  volume    = {11},
  pages     = {199},
  year      = {2020},
  doi       = {10.3389/fpls.2020.00199}
}
```

---

## ⚖️ Licensing

| Component | License |
|-----------|---------|
| Code & scripts | [MIT](LICENSE) |
| Manuscript, figures & documentation | [CC-BY-4.0](LICENSE-CC-BY-4.0) |
| Original OSDR data | NASA Open Data (public domain) |
