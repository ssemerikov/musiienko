# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NAQA Design Accreditation Scraper - scrapes accreditation records for Ukrainian specialty 022 (Дизайн) from the National Agency for Higher Education Quality Assurance portal at `https://public.naqa.gov.ua`.

## Commands

### Installation
```bash
pip install playwright>=1.57.0 pydantic>=2.0 pydantic-settings>=2.0 aiofiles>=24.0
playwright install chromium
```

### Running the Scraper
```bash
python -m naqa_scraper                                    # Default: specialty 022 Дизайн
python -m naqa_scraper --specialty 022 --degree "Бакалавр"
python -m naqa_scraper --specialty "122 Комп'ютерні науки" --max-cases 5
python -m naqa_scraper --headed                           # Show browser window
python -m naqa_scraper --session-id <id>                  # Resume session
python -m naqa_scraper --list-specialties                 # Show available specialties
python -m naqa_scraper --list-degrees                     # Show degree levels
```

### Post-Processing Utilities
```bash
python naqa_scraper/pdf_extractor.py                      # Extract text from PDFs
python naqa_scraper/ocr_extractor.py                      # OCR scanned PDFs (uses Tesseract)
python reorganize_by_level.py                             # Organize by degree level
python cleanup_duplicates.py                              # Remove duplicate files
```

### Syntax Check
```bash
python -m py_compile naqa_scraper/*.py
```

## Architecture

### Three-Phase Pipeline

1. **URL Collection** (`main.py:collect_case_urls`)
   - Navigate to NAQA portal, apply filters (specialty, degree, status, region)
   - Paginate through results, collect case URLs

2. **Data Extraction** (`main.py:scrape_single_case`)
   - Navigate to each case → Form SE page
   - Extract 16 tabs of form data via `extractor.py`
   - Download all associated files via `downloader.py`

3. **Output Generation** (`storage.py`)
   - Save individual case JSONs to `data/raw/`
   - Generate aggregated outputs to `output/`

### Resume Capability
Checkpoints save after each case to `checkpoints/`. Resume interrupted sessions with `--session-id`.

## Key Modules

| Module | Purpose |
|--------|---------|
| `main.py` | CLI entry point, orchestrates scraping pipeline |
| `config.py` | Settings (Pydantic), filter constants, paths |
| `models.py` | Data models: `AccreditationCase`, `FormSE`, `TabContent`, `EducationalComponent` |
| `browser.py` | Playwright wrapper with anti-detection settings |
| `navigator.py` | NAQA site navigation, filter application, pagination |
| `extractor.py` | Form SE extraction (16 tabs), table parsing |
| `downloader.py` | File downloads, blob URL handling, manifest creation |
| `checkpoint.py` | Progress tracking, atomic saves, resume support |
| `storage.py` | JSON/CSV output generation |

## Form SE Structure

The Form SE document has 16 tabs:
- Tab 0: General info (Загальні відомості)
- Tabs 1-11: Accreditation criteria
- Tab 12: Table 1 - Educational components (curriculum)
- Tab 13: Table 2 - Teachers
- Tab 14: Table 3 - Curriculum-outcome matrix
- Tab 15: Assurance statements

Tab navigation uses `[role="tab"]` selectors. Table 1 components are accessed by clicking Tab 12 first.

## Output Files

| File | Contents |
|------|----------|
| `output/all_programs.json` | Complete session with all cases and Form SE data |
| `output/all_programs.csv` | Flattened program records |
| `output/components_summary.csv` | Educational components from Table 1 |
| `output/tabs_content.json` | Raw tab content |
| `data/downloads/{case_id}/` | Downloaded PDFs organized by case |
| `data/raw/case_{id}.json` | Individual case JSON files |

## Filter System

- **Specialty/Status**: `ng-multiselect-dropdown` components (indices 0, 2)
- **Degree Level**: Standard HTML `<select>` element (not multiselect)
- **Institution/Program**: Text input fields

When standard navigation to Form SE fails, the scraper falls back to direct URL: `/v2/form-se/{case_id}/view`

## Configuration (config.py)

- Rate limiting: 2-5 second delays, 12 requests/minute max
- Retries: 3 attempts with exponential backoff
- Timeouts: Navigation 60s, Download 120s
- Browser: Chromium headless, 1920x1080, locale uk-UA

## Data Organization

After scraping, files can be reorganized by degree level:
```
data/downloads_by_level/
├── Бакалавр/           # Bachelor
├── Магістр/            # Master
└── Доктор_філософії/   # PhD
```
