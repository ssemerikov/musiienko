#!/usr/bin/env python3
"""Reorganize extracted text files by degree level"""

import json
import shutil
from pathlib import Path

# Load level mapping
mapping_file = Path("/home/cc/claude_code/design/data/downloads_by_level/level_mapping.json")
with open(mapping_file) as f:
    level_mapping = json.load(f)

# Create reverse mapping: case_id -> level
case_to_level = {}
LEVEL_NAMES = {
    'bachelor': 'Бакалавр',
    'master': 'Магістр',
    'phd': 'Доктор_філософії',
    'junior_bachelor': 'Молодший_бакалавр',
    'unknown': 'Невизначено',
}

for level, cases in level_mapping.items():
    level_name = LEVEL_NAMES.get(level, level)
    for case_id in cases:
        case_to_level[str(case_id)] = level_name

# Reorganize text files
text_dir = Path("/home/cc/claude_code/design/data/text")
output_dir = Path("/home/cc/claude_code/design/data/text_by_level")

# Create level directories
for level_name in LEVEL_NAMES.values():
    (output_dir / level_name).mkdir(parents=True, exist_ok=True)

moved = 0
for case_dir in text_dir.iterdir():
    if case_dir.is_dir() and case_dir.name.isdigit():
        case_id = case_dir.name
        level_name = case_to_level.get(case_id, 'Невизначено')
        
        target_dir = output_dir / level_name / case_id
        if target_dir.exists():
            shutil.rmtree(target_dir)
        
        shutil.move(str(case_dir), str(target_dir))
        moved += 1

print(f"Moved {moved} case directories")

# Count files
print("\nFile counts:")
for level_dir in sorted(output_dir.iterdir()):
    if level_dir.is_dir():
        txt_count = len(list(level_dir.rglob("*.txt")))
        if txt_count > 0:
            print(f"  {level_dir.name}: {txt_count} text files")
