#!/usr/bin/env python3
"""
Prepare data package for Google Colab translation.

Creates a ZIP file with text data for upload to Google Drive.
"""

import os
import shutil
from pathlib import Path
import zipfile
from tqdm import tqdm


def main():
    print("=" * 60)
    print("PREPARING DATA FOR COLAB UPLOAD")
    print("=" * 60)

    # Paths
    data_dir = Path("data")
    text_dir = data_dir / "text_by_level"
    raw_dir = data_dir / "raw"

    output_dir = Path("colab_upload")
    output_dir.mkdir(exist_ok=True)

    zip_path = output_dir / "thesis_data.zip"

    # Count files
    text_files = list(text_dir.rglob("*.txt"))
    json_files = list(raw_dir.glob("case_*.json"))

    print(f"\nFiles to package:")
    print(f"  Text files: {len(text_files)}")
    print(f"  JSON files: {len(json_files)}")

    # Calculate total size
    total_size = 0
    for f in text_files:
        total_size += f.stat().st_size
    for f in json_files:
        total_size += f.stat().st_size

    print(f"  Total size: {total_size / 1024 / 1024:.1f} MB")

    # Create ZIP file
    print(f"\nCreating: {zip_path}")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add text files
        print("Adding text files...")
        for txt_file in tqdm(text_files, desc="  Text files"):
            arcname = f"thesis_data/text_by_level/{txt_file.relative_to(text_dir)}"
            zf.write(txt_file, arcname)

        # Add JSON files
        print("Adding JSON files...")
        for json_file in tqdm(json_files, desc="  JSON files"):
            arcname = f"thesis_data/raw/{json_file.name}"
            zf.write(json_file, arcname)

    # Report
    zip_size = zip_path.stat().st_size
    compression = (1 - zip_size / total_size) * 100

    print(f"\n" + "=" * 60)
    print("PACKAGE READY")
    print("=" * 60)
    print(f"\nOutput: {zip_path}")
    print(f"Size: {zip_size / 1024 / 1024:.1f} MB (compressed {compression:.1f}%)")
    print(f"\nNext steps:")
    print("1. Upload thesis_data.zip to Google Drive")
    print("2. Extract to: MyDrive/thesis_data/")
    print("3. Open notebooks/translate_ukrainian_to_english.ipynb in Colab")
    print("4. Set GPU runtime and run all cells")


if __name__ == "__main__":
    main()
