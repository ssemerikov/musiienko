# Makefile for compiling Shepilev's PhD dissertation
# Usage:
#   make dissertation  - Compile main dissertation (main.pdf)
#   make clean        - Remove auxiliary files

.PHONY: all dissertation clean clean-all help

# Default target
all: dissertation

# Compile dissertation (build in place)
dissertation: main.pdf

main.pdf: main.tex *.bib chapters/**/*.tex chapters/*.tex figures/*.tex setup.sty
	pdflatex -interaction=nonstopmode -shell-escape main.tex ; \
	biber main && \
	pdflatex -interaction=nonstopmode -shell-escape main.tex && \
	pdflatex -interaction=nonstopmode -shell-escape main.tex

# Clean auxiliary files
clean:
	rm -f *.aux *.bbl *.bcf *.blg *.log *.out *.run.xml *.toc *.fls *.fdb_latexmk

# Clean everything including PDFs
clean-all: clean
	rm -f main.pdf

# Help target
help:
	@echo "Available targets:"
	@echo "  dissertation  - Compile dissertation (main.pdf)"
	@echo "  all          - Same as dissertation"
	@echo "  clean        - Remove auxiliary files"
	@echo "  clean-all    - Remove auxiliary files and PDF"
	@echo "  help         - Show this help message"
