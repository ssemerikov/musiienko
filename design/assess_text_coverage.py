#!/usr/bin/env python3
"""
Assess text extraction coverage across all cases.
Compares manifest files (expected) vs actual text files (extracted).
"""

import json
from pathlib import Path
from collections import defaultdict


def count_text_files(text_dir: Path) -> int:
    """Count all .txt files in a directory tree."""
    if not text_dir.exists():
        return 0
    return len(list(text_dir.rglob("*.txt")))


def get_manifest_count(manifest_path: Path) -> int:
    """Get expected file count from manifest."""
    if not manifest_path.exists():
        return 0
    with open(manifest_path) as f:
        data = json.load(f)
    return data.get("successful", 0)


def main():
    pdf_base = Path("data/downloads_by_level")
    text_base = Path("data/text_by_level")

    levels = ["Бакалавр", "Магістр", "Доктор_філософії"]

    total_stats = {
        "cases": 0,
        "manifest_total": 0,
        "text_total": 0,
        "cases_with_loss": 0,
        "total_missing": 0
    }

    issues = []

    for level in levels:
        pdf_level = pdf_base / level
        text_level = text_base / level

        if not pdf_level.exists():
            continue

        print(f"\n=== {level} ===")

        level_manifest = 0
        level_text = 0

        for case_dir in sorted(pdf_level.iterdir()):
            if not case_dir.is_dir():
                continue

            case_id = case_dir.name
            manifest_path = case_dir / "manifest.json"
            text_dir = text_level / case_id

            manifest_count = get_manifest_count(manifest_path)
            text_count = count_text_files(text_dir)

            total_stats["cases"] += 1
            level_manifest += manifest_count
            level_text += text_count
            total_stats["manifest_total"] += manifest_count
            total_stats["text_total"] += text_count

            if text_count < manifest_count:
                missing = manifest_count - text_count
                total_stats["cases_with_loss"] += 1
                total_stats["total_missing"] += missing
                loss_pct = (missing / manifest_count * 100) if manifest_count > 0 else 0

                if loss_pct > 20:  # Report cases with >20% loss
                    issues.append({
                        "case_id": case_id,
                        "level": level,
                        "manifest": manifest_count,
                        "text": text_count,
                        "missing": missing,
                        "loss_pct": loss_pct
                    })
                    print(f"  {case_id}: {text_count}/{manifest_count} text files ({loss_pct:.1f}% loss)")

        coverage = (level_text / level_manifest * 100) if level_manifest > 0 else 0
        print(f"\n  Level Total: {level_text}/{level_manifest} text files ({coverage:.1f}% coverage)")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nTotal cases: {total_stats['cases']}")
    print(f"Expected syllabi (from manifests): {total_stats['manifest_total']}")
    print(f"Extracted text files: {total_stats['text_total']}")
    coverage = (total_stats['text_total'] / total_stats['manifest_total'] * 100) if total_stats['manifest_total'] > 0 else 0
    print(f"Overall coverage: {coverage:.1f}%")
    print(f"\nCases with data loss: {total_stats['cases_with_loss']}")
    print(f"Total missing text files: {total_stats['total_missing']}")

    if issues:
        print(f"\nCases with >20% loss ({len(issues)}):")
        for i in sorted(issues, key=lambda x: x['loss_pct'], reverse=True)[:15]:
            print(f"  {i['case_id']}: {i['text']}/{i['manifest']} ({i['loss_pct']:.1f}% loss)")


if __name__ == "__main__":
    main()
