#!/usr/bin/env python3
"""Find and remove duplicate files, keeping the first occurrence"""

import hashlib
import json
from pathlib import Path
from collections import defaultdict

def get_file_hash(filepath: Path) -> str:
    """Calculate MD5 hash of file"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def find_duplicates(directory: Path, pattern: str = "*.pdf") -> dict:
    """Find duplicate files by hash"""
    hash_to_files = defaultdict(list)
    
    for filepath in directory.rglob(pattern):
        file_hash = get_file_hash(filepath)
        hash_to_files[file_hash].append(filepath)
    
    # Filter to only duplicates
    duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
    return duplicates

def cleanup_duplicates(directory: Path, pattern: str = "*.pdf", dry_run: bool = False) -> dict:
    """Remove duplicate files, keeping the first occurrence"""
    duplicates = find_duplicates(directory, pattern)
    
    stats = {
        "total_duplicates": 0,
        "files_removed": 0,
        "bytes_freed": 0,
        "kept": [],
        "removed": []
    }
    
    for file_hash, files in duplicates.items():
        # Sort by path to get consistent ordering
        files.sort(key=lambda p: str(p))
        
        # Keep the first file
        keep = files[0]
        stats["kept"].append(str(keep))
        
        # Remove the rest
        for dup in files[1:]:
            stats["total_duplicates"] += 1
            file_size = dup.stat().st_size
            stats["bytes_freed"] += file_size
            
            if not dry_run:
                dup.unlink()
                stats["files_removed"] += 1
                # Also remove corresponding text file if exists
                txt_path = Path(str(dup).replace("/downloads/", "/text/")).with_suffix(".txt")
                if txt_path.exists():
                    txt_path.unlink()
            
            stats["removed"].append(str(dup))
    
    return stats

def main():
    downloads_dir = Path("/home/cc/claude_code/design/data/downloads")
    
    print("Finding duplicates...")
    duplicates = find_duplicates(downloads_dir)
    
    total_dups = sum(len(files) - 1 for files in duplicates.values())
    print(f"Found {len(duplicates)} unique files with duplicates")
    print(f"Total duplicate files to remove: {total_dups}")
    
    if total_dups == 0:
        print("No duplicates found!")
        return
    
    print("\nRemoving duplicates...")
    stats = cleanup_duplicates(downloads_dir, dry_run=False)
    
    print(f"\n{'='*50}")
    print("CLEANUP COMPLETE")
    print(f"{'='*50}")
    print(f"Duplicate files removed: {stats['files_removed']}")
    print(f"Space freed: {stats['bytes_freed'] / 1024 / 1024:.2f} MB")
    
    # Save report
    report_path = downloads_dir.parent / "duplicates_report.json"
    with open(report_path, "w") as f:
        json.dump(stats, f, indent=2, default=str)
    print(f"Report saved: {report_path}")

if __name__ == "__main__":
    main()
