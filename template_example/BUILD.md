# Build Instructions — Shepilev PhD Thesis

## Prerequisites
- TeX Live 2021+ with pdflatex, biber
- Packages: tempora, biblatex, gost-numeric, totcount, pgfplots, tikz, etc.

## Build

```bash
cd thesis_final
make dissertation
```

Or manually:
```bash
pdflatex -shell-escape main.tex
biber main
pdflatex -shell-escape main.tex
pdflatex -shell-escape main.tex
```

## Clean
```bash
make clean      # remove aux files
make clean-all  # remove aux + PDF
```

## Structure
```
main.tex              — main document
setup.sty             — formatting (margins, fonts, sections)
mybibfile.bib         — general bibliography
mypaper.bib           — Shepilev's publications + template refs
chapters/
  title-page.tex      — title page
  summary.tex         — annotation (UKR + ENG)
  umovni_poznachennya.tex — abbreviations
  vstup.tex           — introduction (ВСТУП)
  chap1/              — Chapter 1: Theoretical foundations
  chap2/              — Chapter 2: Organizational-pedagogical foundations
  chap3/              — Chapter 3: Experimental research
  vysnovky.tex        — general conclusions
  appendix.tex        — appendices
images/media/         — figures from Word conversion
converted_sources/    — pandoc output (reference only)
```

## Known Issues
- Citation markers `\hl{[X-N]}` from Word conversion are rendered as plain text
  (need to be resolved to `\cite{bibkey}` entries)
- Font shape warnings for Tempora (cosmetic, does not affect output)
