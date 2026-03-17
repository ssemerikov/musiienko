# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PhD thesis workspace for **Musiienko Oleksandr** (Kryvyi Rih State Pedagogical University). Research topic: "Formation of information-communicative competence in the professional training of future designers." Supervisor: Prof. Osadcha K.P.

The core argument is that the shift from classical design to AI-related design necessitates changes in professional training. The thesis must follow Ukrainian dissertation regulations: https://zakon.rada.gov.ua/laws/show/z0155-17#Text

**Key methodological note**: No formative pedagogical experiment was conducted. Instead, the thesis uses a **data-driven curriculum transformation** approach — analyzing existing programs, surveys, and accreditation data to propose how each design course should change to incorporate AI/ICT competencies.

## Language

All thesis content, chapter text, and academic writing must be in **Ukrainian**. BibTeX entries may be in their original language. Code comments and tooling are in English or Ukrainian as appropriate.

## Directory Structure

| Directory | Contents |
|-----------|----------|
| `thesis/` | **Active working thesis** — the assembled LaTeX dissertation with chapters, bibliography, analysis scripts, and generated figures. This is the primary work directory. |
| `articles/` | Two published papers by Musiienko (LaTeX sources + Scopus/WoS .bib files). Article IDs: `13_1093` and `13_1112`. Can be fully reused in the thesis. |
| `template_example/` | **Reference LaTeX template** — a completed thesis (Shepilev) to follow for structure, formatting, and narrative style. |
| `materials/` | Early unfinished thesis drafts (DOCX), presentations, an article draft. |
| `experiment/` | Real experimental data: surveys (Анкетування), educational programs (ОПП), stakeholder reviews, practice agreements, curricula for three design programs (Графічний дизайн, Дизайн одягу, Дизайн середовища). |
| `design/` | NAQA accreditation scraper + analysis of all Design (022) educational programs accredited in Ukraine. Has its own CLAUDE.md. |

## LaTeX Build System

The thesis uses pdflatex + biber with GOST-numeric bibliography style.

```bash
# Build the thesis (from thesis/)
cd thesis && make dissertation

# Manual build
pdflatex -interaction=nonstopmode -shell-escape main.tex
biber main
pdflatex -interaction=nonstopmode -shell-escape main.tex
pdflatex -interaction=nonstopmode -shell-escape main.tex

# Clean
make clean        # aux files only
make clean-all    # aux + PDF
```

### Build articles
```bash
# From articles/13_1093_Musiienko/source/ or articles/13_1112_Musiienko/source/
make
```

## LaTeX Formatting Conventions (ДСТУ 3008:2015)

Formatting is encoded in `thesis/setup.sty` (copied from `template_example/setup.sty`):

- **Document class**: `extarticle` with 14pt font, A4 paper, Tempora font (Times-like with Cyrillic)
- **Margins**: left 3cm, right 1.5cm, top/bottom 2cm
- **Line spacing**: 1.25 (`\linespread{1.25}`, equivalent to Word 1.5)
- **Page numbers**: top-right corner (fancyhdr)
- **Section headings**: `РОЗДІЛ N` centered bold, subsections from paragraph indent
- **Figures**: `Рисунок 1.1 – Назва` (centered, italic, endash separator)
- **Tables**: `Таблиця 1.1 – Назва` (left-aligned above table, endash separator)
- **Paragraph indent**: 1.25cm
- **Bibliography**: biblatex with `gost-numeric` style, custom `abyrvalg` sorting, biber backend
- **Citation command**: Custom `\citet{key}` produces "Author [N]" inline format
- **TikZ diagrams**: use `dia/` prefixed styles defined in `setup.sty` (e.g., `dia/header`, `dia/box`, `dia/arrow`)
- **Draft markers**: `\draft{text}` for yellow-highlighted draft notes

## Thesis Structure (in `thesis/chapters/`)

```
title-page.tex          — Title page
summary.tex             — Annotation (Ukrainian + English)
umovni_poznachennya.tex — Abbreviations
vstup.tex               — Introduction (ВСТУП)
chap1/                  — Розділ 1: Теоретичні засади формування ІКК майбутніх дизайнерів
chap2/                  — Розділ 2: Аналіз стану формування ІКК у дизайн-освіті України
chap3/                  — Розділ 3: Модель трансформації навчальних програм для формування ІКК
vysnovky.tex            — General conclusions (ВИСНОВКИ)
appendix.tex            — Appendices
```

Each chapter has sections in files like `chapter1.1.tex`, `chapter1.2.tex`, etc. Chapter conclusions go in `chapter1.X.tex` (the `X` suffix).

## Thesis Analysis Pipeline (thesis/analysis/)

Python scripts that process experimental data and generate figures/tables for the thesis. Install dependencies with `pip install -r thesis/analysis/requirements.txt`.

| Script | Purpose |
|--------|---------|
| `survey_parser.py` | Parse graduate/employer survey data from `experiment/Анкетування/` → CSV summaries and comparison figures |
| `syllabus_analyzer.py` | Analyze curricula for ICT/AI relevance → heatmaps of IKK coverage per program |
| `stakeholder_analyzer.py` | Process stakeholder reviews and expert evaluations |
| `bibliography_merger.py` | Merge and deduplicate .bib files from articles and other sources into `references.bib` |
| `run_topic_modeling.py` | BERTopic-based topic modeling of educational components across programs |
| `run_semantic_clustering.py` | Sentence-transformer clustering of syllabi for cross-program comparison |

Generated outputs go to `thesis/analysis/output/` (CSVs, JSONs) and `thesis/figures/` (PDF plots).

## Key Data Files

- `experiment/Анкетування/` — Survey results from graduates and employers for three design programs (TXT extracts + PDF originals)
- `experiment/ОСВІТНІ ПРОГРАМИ/` — Educational programs 2017-2019
- `experiment/ОПП матеріали/` — OPP (educational-professional program) accreditation materials
- `design/data/` — Scraped NAQA accreditation data for specialty 022
- `design/thesis_output/` — Generated analysis reports, figures, LaTeX fragments

## NAQA Design Scraper (design/)

Python-based Playwright scraper for Ukrainian accreditation data. See `design/CLAUDE.md` for full details.

```bash
pip install playwright>=1.57.0 pydantic>=2.0 pydantic-settings>=2.0 aiofiles>=24.0
playwright install chromium
python -m naqa_scraper
```

## MCP and External Tools

The task.md instructs active use of MCP servers for academic search, web search, etc. Available MCPs include academic search, PubMed, Consensus, arXiv, and Playwright for web scraping.
