.PHONY: all pdf docx clean

all: pdf docx

pdf:
	./build.sh

docx:
	pandoc main.tex -o OSDR_Veggie_Nutrition_Analysis.docx --bibliography=references.bib --citeproc

clean:
	rm -f *.aux *.log *.out *.toc *.lof *.lot *.bbl *.blg *.fls *.fdb_latexmk
	rm -f chapters/*.aux
	rm -f OSDR_Veggie_Nutrition_Analysis.pdf
	rm -f OSDR_Veggie_Nutrition_Analysis.docx
