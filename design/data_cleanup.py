#!/usr/bin/env python3
"""
Data cleanup and repair script for thesis analysis.

1. Removes empty duplicate directories
2. Identifies missing PDFs vs manifest
3. Re-extracts text from existing PDFs
4. Reports statistics
"""

import os
import re
import json
import shutil
import subprocess
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from tqdm import tqdm


# Paths
DATA_DIR = Path("data")
DOWNLOADS_DIR = DATA_DIR / "downloads_by_level"
TEXT_DIR = DATA_DIR / "text_by_level"
RAW_DIR = DATA_DIR / "raw"


def find_empty_dirs(base_path: Path) -> List[Path]:
    """Find all empty directories."""
    empty_dirs = []
    for dirpath, dirnames, filenames in os.walk(base_path):
        if not dirnames and not filenames:
            empty_dirs.append(Path(dirpath))
    return empty_dirs


def find_duplicate_dirs(case_dir: Path) -> Dict[str, List[Path]]:
    """Find directories with same name (different prefix) in components folder."""
    components_dir = case_dir / "components"
    if not components_dir.exists():
        return {}

    # Group by name (without numeric prefix)
    name_to_dirs = defaultdict(list)
    pattern = re.compile(r"^\d+_(.+)$")

    for item in components_dir.iterdir():
        if item.is_dir():
            match = pattern.match(item.name)
            if match:
                base_name = match.group(1)
                name_to_dirs[base_name].append(item)

    # Return only duplicates
    return {name: dirs for name, dirs in name_to_dirs.items() if len(dirs) > 1}


def remove_empty_duplicates(base_path: Path, dry_run: bool = False) -> Tuple[int, int]:
    """Remove empty duplicate directories, keeping the one with content."""
    removed = 0
    kept = 0

    for level_dir in base_path.iterdir():
        if not level_dir.is_dir():
            continue

        for case_dir in tqdm(list(level_dir.iterdir()), desc=f"Processing {level_dir.name}"):
            if not case_dir.is_dir():
                continue

            duplicates = find_duplicate_dirs(case_dir)

            for name, dirs in duplicates.items():
                # Check which have content
                with_content = []
                without_content = []

                for d in dirs:
                    files = list(d.glob("*"))
                    if files:
                        with_content.append(d)
                    else:
                        without_content.append(d)

                # Remove empty duplicates
                for empty_dir in without_content:
                    if dry_run:
                        print(f"Would remove: {empty_dir}")
                    else:
                        shutil.rmtree(empty_dir)
                    removed += 1

                if with_content:
                    kept += len(with_content)

    return removed, kept


def check_pdfs_vs_manifest(case_dir: Path) -> Tuple[Set[str], Set[str]]:
    """Check which PDFs exist vs what manifest says should exist."""
    manifest_path = case_dir / "manifest.json"
    if not manifest_path.exists():
        return set(), set()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Get expected files from manifest
    expected = set()
    for item in manifest.get("files", []):
        filename = item.get("saved_as") or item.get("filename", "")
        if filename:
            expected.add(filename)

    # Get actual PDFs
    actual = set()
    for pdf in case_dir.rglob("*.pdf"):
        actual.add(pdf.name)

    missing = expected - actual
    extra = actual - expected

    return missing, extra


def extract_text_from_pdf(pdf_path: Path, output_path: Path) -> bool:
    """Extract text from PDF using pdftotext."""
    try:
        # Try pdftotext first
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), str(output_path)],
            capture_output=True,
            timeout=60,
        )
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: try with python libraries
    try:
        import PyPDF2
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""

        if text.strip():
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            return True
    except Exception:
        pass

    return False


def extract_all_text(downloads_dir: Path, text_dir: Path, force: bool = False) -> Dict[str, int]:
    """Extract text from all PDFs."""
    stats = {"success": 0, "failed": 0, "skipped": 0}

    for level_dir in downloads_dir.iterdir():
        if not level_dir.is_dir():
            continue

        level_name = level_dir.name
        text_level_dir = text_dir / level_name
        text_level_dir.mkdir(parents=True, exist_ok=True)

        for case_dir in tqdm(list(level_dir.iterdir()), desc=f"Extracting {level_name}"):
            if not case_dir.is_dir():
                continue

            case_id = case_dir.name
            text_case_dir = text_level_dir / case_id / "components"
            text_case_dir.mkdir(parents=True, exist_ok=True)

            # Find all PDFs
            for pdf_path in case_dir.rglob("*.pdf"):
                # Create output path
                rel_path = pdf_path.relative_to(case_dir)
                output_path = text_level_dir / case_id / rel_path.with_suffix(".txt")
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Skip if already exists
                if output_path.exists() and output_path.stat().st_size > 0 and not force:
                    stats["skipped"] += 1
                    continue

                # Extract
                if extract_text_from_pdf(pdf_path, output_path):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1

    return stats


def generate_report(downloads_dir: Path, text_dir: Path) -> str:
    """Generate comprehensive data status report."""
    report = []
    report.append("=" * 60)
    report.append("DATA STATUS REPORT")
    report.append("=" * 60)

    total_cases = 0
    total_pdfs = 0
    total_texts = 0
    empty_component_dirs = 0
    total_missing_pdfs = 0

    by_level = {}

    for level_dir in downloads_dir.iterdir():
        if not level_dir.is_dir():
            continue

        level_name = level_dir.name
        level_stats = {
            "cases": 0,
            "pdfs": 0,
            "texts": 0,
            "empty_dirs": 0,
            "missing_pdfs": 0,
        }

        for case_dir in level_dir.iterdir():
            if not case_dir.is_dir():
                continue

            level_stats["cases"] += 1
            total_cases += 1

            # Count PDFs
            pdfs = list(case_dir.rglob("*.pdf"))
            level_stats["pdfs"] += len(pdfs)
            total_pdfs += len(pdfs)

            # Count empty component dirs
            components_dir = case_dir / "components"
            if components_dir.exists():
                for comp_dir in components_dir.iterdir():
                    if comp_dir.is_dir() and not list(comp_dir.glob("*")):
                        level_stats["empty_dirs"] += 1
                        empty_component_dirs += 1

            # Check manifest
            missing, _ = check_pdfs_vs_manifest(case_dir)
            level_stats["missing_pdfs"] += len(missing)
            total_missing_pdfs += len(missing)

        # Count texts
        text_level_dir = text_dir / level_name
        if text_level_dir.exists():
            texts = list(text_level_dir.rglob("*.txt"))
            level_stats["texts"] = len(texts)
            total_texts += len(texts)

        by_level[level_name] = level_stats

    report.append(f"\nTotal cases: {total_cases}")
    report.append(f"Total PDFs: {total_pdfs}")
    report.append(f"Total text files: {total_texts}")
    report.append(f"Empty component dirs: {empty_component_dirs}")
    report.append(f"Missing PDFs (vs manifest): {total_missing_pdfs}")

    report.append("\n" + "-" * 40)
    report.append("BY LEVEL:")
    for level, stats in by_level.items():
        report.append(f"\n{level}:")
        report.append(f"  Cases: {stats['cases']}")
        report.append(f"  PDFs: {stats['pdfs']}")
        report.append(f"  Text files: {stats['texts']}")
        report.append(f"  Empty dirs: {stats['empty_dirs']}")
        report.append(f"  Missing PDFs: {stats['missing_pdfs']}")

    report.append("\n" + "=" * 60)

    return "\n".join(report)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Data cleanup and repair")
    parser.add_argument("--report", action="store_true", help="Generate status report")
    parser.add_argument("--clean", action="store_true", help="Remove empty duplicates")
    parser.add_argument("--extract", action="store_true", help="Extract text from PDFs")
    parser.add_argument("--force", action="store_true", help="Force re-extraction of text")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--all", action="store_true", help="Run all operations")

    args = parser.parse_args()

    if args.report or args.all:
        print(generate_report(DOWNLOADS_DIR, TEXT_DIR))

    if args.clean or args.all:
        print("\n--- Removing empty duplicates ---")
        removed, kept = remove_empty_duplicates(DOWNLOADS_DIR, dry_run=args.dry_run)
        print(f"Removed: {removed}, Kept with content: {kept}")

    if args.extract or args.all:
        print("\n--- Extracting text from PDFs ---")
        stats = extract_all_text(DOWNLOADS_DIR, TEXT_DIR, force=args.force)
        print(f"Success: {stats['success']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")

    if not any([args.report, args.clean, args.extract, args.all]):
        parser.print_help()


if __name__ == "__main__":
    main()
