#!/usr/bin/env python3
"""
Reorganize downloaded cases by degree level (Bachelor, Master, PhD)
"""

import json
import re
import shutil
from pathlib import Path
from collections import defaultdict

# Degree level mappings
DEGREE_PATTERNS = {
    'bachelor': [
        r'Рівень вищої освіти\s*Бакалавр',
        r'Рівень вищої освіти:\s*Бакалавр',
        r'"degree_level":\s*"Бакалавр"',
    ],
    'master': [
        r'Рівень вищої освіти\s*Магістр',
        r'Рівень вищої освіти:\s*Магістр',
        r'"degree_level":\s*"Магістр"',
    ],
    'phd': [
        r'Рівень вищої освіти\s*Доктор філософії',
        r'Рівень вищої освіти:\s*Доктор філософії',
        r'"degree_level":\s*"Доктор філософії"',
        r'Рівень вищої освіти\s*PhD',
    ],
    'junior_bachelor': [
        r'Рівень вищої освіти\s*Молодший бакалавр',
        r'Рівень вищої освіти:\s*Молодший бакалавр',
    ],
}

LEVEL_NAMES = {
    'bachelor': 'Бакалавр',
    'master': 'Магістр',
    'phd': 'Доктор_філософії',
    'junior_bachelor': 'Молодший_бакалавр',
    'unknown': 'Невизначено',
}


def detect_degree_level(case_data: dict) -> str:
    """Detect degree level from case data"""
    # First check degree_level field
    if case_data.get('degree_level'):
        level = case_data['degree_level'].lower()
        if 'бакалавр' in level and 'молодший' not in level:
            return 'bachelor'
        elif 'магістр' in level:
            return 'master'
        elif 'доктор' in level or 'phd' in level.lower():
            return 'phd'
        elif 'молодший' in level:
            return 'junior_bachelor'

    # Search in form_se raw text
    content = json.dumps(case_data, ensure_ascii=False)

    for level, patterns in DEGREE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return level

    return 'unknown'


def reorganize_downloads(
    downloads_dir: Path,
    raw_dir: Path,
    output_dir: Path,
    move_files: bool = True
) -> dict:
    """Reorganize downloaded files by degree level

    Args:
        downloads_dir: Current downloads directory
        raw_dir: Directory with case JSON files
        output_dir: New organized output directory
        move_files: If True, move files; if False, copy files

    Returns:
        Statistics dict
    """
    stats = defaultdict(list)

    # Create output directories for each level
    for level_key, level_name in LEVEL_NAMES.items():
        (output_dir / level_name).mkdir(parents=True, exist_ok=True)

    # Process each case
    case_files = list(raw_dir.glob("case_*.json"))
    print(f"Processing {len(case_files)} cases...")

    for case_file in case_files:
        with open(case_file) as f:
            case_data = json.load(f)

        case_id = case_data.get('case_id', case_file.stem.replace('case_', ''))
        level = detect_degree_level(case_data)
        level_name = LEVEL_NAMES[level]

        stats[level].append(case_id)

        # Find source directory
        source_dir = downloads_dir / str(case_id)
        if not source_dir.exists():
            print(f"  Warning: {source_dir} not found")
            continue

        # Target directory
        target_dir = output_dir / level_name / str(case_id)

        if target_dir.exists():
            shutil.rmtree(target_dir)

        if move_files:
            shutil.move(str(source_dir), str(target_dir))
        else:
            shutil.copytree(str(source_dir), str(target_dir))

    return dict(stats)


def main():
    downloads_dir = Path("/home/cc/claude_code/design/data/downloads")
    raw_dir = Path("/home/cc/claude_code/design/data/raw")
    output_dir = Path("/home/cc/claude_code/design/data/downloads_by_level")

    print("Reorganizing downloads by degree level...")
    print(f"Source: {downloads_dir}")
    print(f"Output: {output_dir}")

    stats = reorganize_downloads(downloads_dir, raw_dir, output_dir, move_files=True)

    print(f"\n{'='*50}")
    print("REORGANIZATION COMPLETE")
    print(f"{'='*50}")

    for level, cases in sorted(stats.items()):
        level_name = LEVEL_NAMES.get(level, level)
        print(f"{level_name}: {len(cases)} cases")

    # Count files in each directory
    print(f"\nFile counts:")
    for level_dir in output_dir.iterdir():
        if level_dir.is_dir():
            pdf_count = len(list(level_dir.rglob("*.pdf")))
            print(f"  {level_dir.name}: {pdf_count} PDFs")

    # Save mapping
    mapping_file = output_dir / "level_mapping.json"
    with open(mapping_file, "w") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"\nMapping saved: {mapping_file}")


if __name__ == "__main__":
    main()
