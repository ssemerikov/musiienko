#!/usr/bin/env python3
"""
Assess missing component numbers across all cases.
Identifies cases where component directory sequences have gaps.
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def analyze_case_components(case_dir: Path) -> dict:
    """Analyze component directories for a single case."""
    components_dir = case_dir / "components"

    if not components_dir.exists():
        return {"status": "no_components_dir"}

    # Get all component directories
    component_dirs = sorted([
        d.name for d in components_dir.iterdir()
        if d.is_dir()
    ])

    if not component_dirs:
        return {"status": "empty"}

    # Extract numbers from directory names
    numbers = []
    for dirname in component_dirs:
        match = re.match(r'^(\d+)_', dirname)
        if match:
            numbers.append(int(match.group(1)))

    if not numbers:
        return {"status": "no_numbered_dirs"}

    numbers = sorted(numbers)
    expected = list(range(numbers[-1] + 1))
    missing = [n for n in expected if n not in numbers]

    return {
        "status": "ok" if not missing else "missing",
        "total_dirs": len(component_dirs),
        "max_number": numbers[-1],
        "found_numbers": numbers,
        "missing_numbers": missing,
        "gap_count": len(missing)
    }


def main():
    base_dir = Path("data/downloads_by_level")

    all_issues = {}
    stats = defaultdict(int)

    for level_dir in base_dir.iterdir():
        if not level_dir.is_dir():
            continue

        level = level_dir.name
        print(f"\n=== {level} ===")

        for case_dir in sorted(level_dir.iterdir()):
            if not case_dir.is_dir():
                continue

            case_id = case_dir.name
            result = analyze_case_components(case_dir)
            stats[result["status"]] += 1

            if result.get("missing_numbers"):
                all_issues[case_id] = {
                    "level": level,
                    "missing": result["missing_numbers"],
                    "found": result["found_numbers"],
                    "gap_count": result["gap_count"]
                }
                print(f"  {case_id}: Missing {result['missing_numbers']} (gaps: {result['gap_count']})")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_cases = sum(stats.values())
    print(f"\nTotal cases analyzed: {total_cases}")
    for status, count in sorted(stats.items()):
        print(f"  {status}: {count}")

    print(f"\nCases with missing components: {len(all_issues)}")

    if all_issues:
        total_missing = sum(i["gap_count"] for i in all_issues.values())
        print(f"Total missing component directories: {total_missing}")

        # Group by gap count
        by_gap_count = defaultdict(list)
        for case_id, info in all_issues.items():
            by_gap_count[info["gap_count"]].append(case_id)

        print("\nBy number of gaps:")
        for gap_count, cases in sorted(by_gap_count.items()):
            print(f"  {gap_count} gaps: {len(cases)} cases ({', '.join(cases[:5])}{'...' if len(cases) > 5 else ''})")

    # Save detailed report
    report_path = Path("thesis_output/reports/missing_components.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total_cases": total_cases,
                "cases_with_issues": len(all_issues),
                "total_missing_dirs": sum(i["gap_count"] for i in all_issues.values()) if all_issues else 0
            },
            "status_counts": dict(stats),
            "issues": all_issues
        }, f, ensure_ascii=False, indent=2)

    print(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    main()
