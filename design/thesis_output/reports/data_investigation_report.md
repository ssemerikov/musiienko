# Data Investigation Report: Missing Sequence Numbers

**Date:** 2026-01-31
**Issue:** Case 9997 and others have missing directory sequence numbers

## Executive Summary

The "missing sequence numbers" issue was investigated and determined to be a result of data cleanup operations, not a scraping or download error. The cleanup removed duplicate PDF directories, leaving gaps in sequential numbering.

## Findings

### Root Cause
1. PDFs were originally downloaded with sequential directory names (000, 001, 002...)
2. During cleanup, duplicate PDFs (identical content across multiple components) were identified
3. Duplicate directories were removed
4. Empty directories were deleted
5. This left gaps in the sequence (e.g., 001, 003, 006... missing 000, 002, 004, 005, 009)

### Case 9997 Specific Analysis
From the manifest.json:
- Component 000 (Фізичне виховання) - removed as empty
- Component 002 (Підготовка кваліфікаційної роботи) - same PDF as component 001
- Component 004 (Виробнича практика) - same PDF as component 003
- Component 005 (Безпека життєдіяльності) - removed during cleanup
- Component 009 (Основи формоутворення) - removed during cleanup

The text files were preserved in `data/text_by_level/` for all 30 components, so no content loss occurred for analysis purposes.

### Scale of Issue
- **43 cases** had missing sequence numbers
- **226 total directories** were affected
- Most cases had 1-5 gaps; a few had 20+ gaps

### Cases with Actual Data Loss
Some cases had genuine data loss (PDFs never downloaded or removed incorrectly):

**Master level (100% loss):**
- 12786: 14 files
- 12787: 14 files
- 13008: 12 files
- 15168: 12 files
- 5365: 10 files

**Bachelor level (>50% loss):**
- 8588: 91.3% loss
- 3363: 79.5% loss
- 5160: 73.3% loss
- 3362: 69.2% loss
- 5159: 50.0% loss

## Actions Taken

### 1. Assessment Scripts Created
- `assess_missing_components.py` - Identifies directory sequence gaps
- `assess_text_coverage.py` - Compares manifest expectations vs actual text files
- `generate_data_report.py` - Comprehensive data status report

### 2. Re-downloads Completed
**Round 1:** Bachelor cases with 100% loss (completed)
- 8855: 31/31 files ✓
- 8856: 44/44 files ✓
- 8857: 62/62 files ✓
- 14140: 34/34 files ✓

**Round 2:** Remaining cases (in progress)
- 5 Master cases with 100% loss
- 5 Bachelor cases with >50% loss

### 3. Text Extraction
- 171 new text files extracted from Round 1 downloads
- Automatic text extraction included in Round 2 script

## Final Data Status

After Round 1 fixes:
- **Bachelor:** 74 cases, 2,214 PDFs, 57.6M characters
- **Master:** 43 cases, 479 PDFs, 12.8M characters
- **PhD:** 5 cases, 44 PDFs, 0.8M characters
- **Total:** 122 cases, 2,737 PDFs, 71.2M characters
- **Coverage:** 100% text extraction for existing PDFs

## Recommendations

1. **For analysis:** Current data (90.9% of expected) is sufficient for thesis
2. **After Round 2:** Coverage will improve to ~95-98%
3. **Future scraping:** Implement checksum-based duplicate detection instead of filename-based removal

## Files Created

1. `thesis_output/reports/missing_components.json` - Detailed gap analysis
2. `thesis_output/reports/data_status.json` - Current data statistics
3. `assess_missing_components.py` - Gap detection script
4. `assess_text_coverage.py` - Coverage assessment script
5. `redownload_cases.py` - Round 1 re-download script
6. `redownload_remaining.py` - Round 2 re-download script
7. `extract_new_text.py` - Text extraction for new downloads
8. `generate_data_report.py` - Data report generator
