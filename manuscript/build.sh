#!/bin/bash
# Build script for OSDR Veggie Nutrition Analysis Manuscript

set -e

echo "Building OSDR Veggie Nutrition Analysis PDF..."

# Check if Tectonic is available
if command -v /Users/drb_laptop/.local/bin/tectonic &> /dev/null; then
    COMPILER="/Users/drb_laptop/.local/bin/tectonic"
elif command -v tectonic &> /dev/null; then
    COMPILER="tectonic"
else
    COMPILER="pdflatex"
fi

if [ "$COMPILER" = "pdflatex" ]; then
    echo "Tectonic not found, falling back to pdflatex..."
    pdflatex main.tex
    bibtex main
    pdflatex main.tex
    pdflatex main.tex
    mv main.pdf OSDR_Veggie_Nutrition_Analysis.pdf
else
    echo "Using Tectonic compiler..."
    $COMPILER main.tex
    mv main.pdf OSDR_Veggie_Nutrition_Analysis.pdf
fi

echo "PDF built successfully: OSDR_Veggie_Nutrition_Analysis.pdf"

# Convert to DOCX if pandoc is available
if command -v pandoc &> /dev/null; then
    echo "Building DOCX version..."
    pandoc main.tex -o OSDR_Veggie_Nutrition_Analysis.docx --bibliography=references.bib --citeproc
    echo "DOCX built successfully: OSDR_Veggie_Nutrition_Analysis.docx"
else
    echo "Pandoc not found. Skipping DOCX generation."
fi

echo "Build complete."
