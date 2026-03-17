#!/usr/bin/env python3
"""
Generate comprehensive data status report for thesis.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def count_files(directory: Path, extension: str) -> int:
    """Count files with given extension."""
    if not directory.exists():
        return 0
    return len(list(directory.rglob(f"*{extension}")))


def get_total_size(directory: Path, extension: str) -> int:
    """Get total size of files with given extension."""
    if not directory.exists():
        return 0
    total = 0
    for f in directory.rglob(f"*{extension}"):
        total += f.stat().st_size
    return total


def get_total_characters(directory: Path) -> int:
    """Get total character count from text files."""
    if not directory.exists():
        return 0
    total = 0
    for f in directory.rglob("*.txt"):
        try:
            total += len(f.read_text(encoding="utf-8"))
        except Exception:
            pass
    return total


def main():
    report = {
        "generated_at": datetime.now().isoformat(),
        "levels": {},
        "totals": {}
    }

    levels = {
        "Бакалавр": "Bachelor",
        "Магістр": "Master",
        "Доктор_філософії": "PhD"
    }

    total_cases = 0
    total_pdfs = 0
    total_texts = 0
    total_pdf_size = 0
    total_chars = 0

    for ukr_level, eng_level in levels.items():
        pdf_dir = Path(f"data/downloads_by_level/{ukr_level}")
        text_dir = Path(f"data/text_by_level/{ukr_level}")

        if not pdf_dir.exists():
            continue

        cases = [d for d in pdf_dir.iterdir() if d.is_dir()]
        pdf_count = count_files(pdf_dir, ".pdf")
        txt_count = count_files(text_dir, ".txt")
        pdf_size = get_total_size(pdf_dir, ".pdf")
        char_count = get_total_characters(text_dir)

        report["levels"][eng_level] = {
            "cases": len(cases),
            "pdf_files": pdf_count,
            "text_files": txt_count,
            "pdf_size_mb": round(pdf_size / 1024 / 1024, 1),
            "text_characters": char_count,
            "text_characters_millions": round(char_count / 1_000_000, 2),
            "coverage_pct": round(txt_count / pdf_count * 100, 1) if pdf_count > 0 else 0
        }

        total_cases += len(cases)
        total_pdfs += pdf_count
        total_texts += txt_count
        total_pdf_size += pdf_size
        total_chars += char_count

    report["totals"] = {
        "cases": total_cases,
        "pdf_files": total_pdfs,
        "text_files": total_texts,
        "pdf_size_mb": round(total_pdf_size / 1024 / 1024, 1),
        "text_characters": total_chars,
        "text_characters_millions": round(total_chars / 1_000_000, 2),
        "coverage_pct": round(total_texts / total_pdfs * 100, 1) if total_pdfs > 0 else 0
    }

    # Save JSON report
    output_dir = Path("thesis_output/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "data_status.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print human-readable summary
    print("=" * 60)
    print("DESIGN EDUCATION DATA STATUS REPORT")
    print("=" * 60)
    print(f"\nGenerated: {report['generated_at'][:19]}")

    print("\n" + "-" * 60)
    print("BY DEGREE LEVEL")
    print("-" * 60)

    for level, stats in report["levels"].items():
        print(f"\n{level}:")
        print(f"  Cases: {stats['cases']}")
        print(f"  PDFs: {stats['pdf_files']} ({stats['pdf_size_mb']} MB)")
        print(f"  Text files: {stats['text_files']} ({stats['coverage_pct']}% coverage)")
        print(f"  Text content: {stats['text_characters_millions']}M characters")

    print("\n" + "-" * 60)
    print("TOTALS")
    print("-" * 60)
    t = report["totals"]
    print(f"\n  Total cases: {t['cases']}")
    print(f"  Total PDFs: {t['pdf_files']} ({t['pdf_size_mb']} MB)")
    print(f"  Total text files: {t['text_files']} ({t['coverage_pct']}% coverage)")
    print(f"  Total text content: {t['text_characters_millions']}M characters")

    print("\n" + "=" * 60)
    print(f"Report saved to: {output_dir / 'data_status.json'}")


if __name__ == "__main__":
    main()
