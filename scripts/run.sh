#!/bin/bash
# sample script for manually compiling, comparing diffs, and cleaning up aux files
latexmk -pdf -jobname="pdflatex_compiled" main.tex
latexmk -xelatex -jobname="xelatex_compiled" main.tex
latexmk -lualatex -jobname="lualatex_compiled" main.tex
diff-pdf --output-diff='xe_pdf_diff.pdf' -smg --dpi=100 --per-page-pixel-tolerance=3000 xelatex_compiled.pdf pdflatex_compiled.pdf
diff-pdf --output-diff='xe_lua_diff.pdf' -smg --dpi=100 --per-page-pixel-tolerance=3000 xelatex_compiled.pdf lualatex_compiled.pdf
rm *.aux *.fls *.fdb_latexmk *.dvi *.xdv
