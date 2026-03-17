#!/usr/bin/env python3
"""Clean up duplicate text files"""

import hashlib
from pathlib import Path
from collections import defaultdict

def get_file_hash(filepath: Path) -> str:
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

text_dir = Path("/home/cc/claude_code/design/data/text")
hash_to_files = defaultdict(list)

for filepath in text_dir.rglob("*.txt"):
    file_hash = get_file_hash(filepath)
    hash_to_files[file_hash].append(filepath)

removed = 0
for file_hash, files in hash_to_files.items():
    if len(files) > 1:
        files.sort(key=lambda p: str(p))
        for dup in files[1:]:
            dup.unlink()
            removed += 1

print(f"Removed {removed} duplicate text files")
