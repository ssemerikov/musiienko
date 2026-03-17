#!/usr/bin/env python3
"""
PDF Text Extraction for NAQA Scraped Syllabi
Extracts text from downloaded PDF files and saves as TXT files.
"""

import argparse
import logging
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import json

# Try multiple PDF libraries for best results
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def extract_with_pdfplumber(pdf_path: Path) -> str:
    """Extract text using pdfplumber"""
    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        logger.debug(f"pdfplumber failed for {pdf_path}: {e}")
        return ""
    return "\n\n".join(text_parts)


def extract_with_pymupdf(pdf_path: Path) -> str:
    """Extract text using PyMuPDF"""
    text_parts = []
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
    except Exception as e:
        logger.debug(f"PyMuPDF failed for {pdf_path}: {e}")
        return ""
    return "\n\n".join(text_parts)


def extract_text_from_pdf(pdf_path: Path) -> tuple[Path, str, bool]:
    """Extract text from a single PDF file

    Returns: (pdf_path, extracted_text, success)
    """
    # Try pdfplumber first (often better for structured PDFs)
    if HAS_PDFPLUMBER:
        text = extract_with_pdfplumber(pdf_path)
        if text.strip():
            return (pdf_path, text, True)

    # Fallback to PyMuPDF
    if HAS_PYMUPDF:
        text = extract_with_pymupdf(pdf_path)
        if text.strip():
            return (pdf_path, text, True)

    return (pdf_path, "", False)


def process_single_pdf(pdf_path: Path, output_dir: Path) -> dict:
    """Process a single PDF and save text file

    Returns: dict with status info
    """
    result = {
        "pdf_path": str(pdf_path),
        "success": False,
        "text_path": None,
        "chars": 0,
        "error": None
    }

    try:
        pdf_path, text, success = extract_text_from_pdf(pdf_path)

        if success and text.strip():
            # Create output path maintaining directory structure
            relative_path = pdf_path.relative_to(pdf_path.parents[3])  # Go up from components/xxx/file.pdf
            txt_path = output_dir / relative_path.with_suffix(".txt")
            txt_path.parent.mkdir(parents=True, exist_ok=True)

            txt_path.write_text(text, encoding="utf-8")

            result["success"] = True
            result["text_path"] = str(txt_path)
            result["chars"] = len(text)
        else:
            result["error"] = "No text extracted"

    except Exception as e:
        result["error"] = str(e)

    return result


def find_all_pdfs(downloads_dir: Path) -> list[Path]:
    """Find all PDF files in downloads directory"""
    pdfs = list(downloads_dir.rglob("*.pdf"))
    logger.info(f"Found {len(pdfs)} PDF files")
    return pdfs


def extract_all(downloads_dir: Path, output_dir: Path, max_workers: int = 4) -> dict:
    """Extract text from all PDFs in downloads directory

    Args:
        downloads_dir: Path to downloaded files (data/downloads)
        output_dir: Path to save text files (data/text)
        max_workers: Number of parallel workers

    Returns:
        Summary statistics
    """
    pdfs = find_all_pdfs(downloads_dir)

    if not pdfs:
        logger.warning("No PDF files found")
        return {"total": 0, "success": 0, "failed": 0}

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    success_count = 0
    failed_count = 0
    total_chars = 0

    # Process PDFs in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_pdf, pdf, output_dir): pdf
            for pdf in pdfs
        }

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)

            if result["success"]:
                success_count += 1
                total_chars += result["chars"]
            else:
                failed_count += 1

            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(pdfs)} PDFs ({success_count} success, {failed_count} failed)")

    # Save extraction manifest
    manifest_path = output_dir / "extraction_manifest.json"
    manifest = {
        "total_pdfs": len(pdfs),
        "successful": success_count,
        "failed": failed_count,
        "total_characters": total_chars,
        "files": results
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    logger.info(f"\n{'='*60}")
    logger.info(f"PDF TEXT EXTRACTION COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Total PDFs: {len(pdfs)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {failed_count}")
    logger.info(f"Total characters: {total_chars:,}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Manifest: {manifest_path}")

    return manifest


def main():
    parser = argparse.ArgumentParser(description="Extract text from downloaded PDF syllabi")
    parser.add_argument(
        "--downloads-dir",
        type=Path,
        default=Path("/home/cc/claude_code/design/data/downloads"),
        help="Directory containing downloaded PDFs"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/home/cc/claude_code/design/data/text"),
        help="Directory to save extracted text files"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers"
    )

    args = parser.parse_args()

    if not args.downloads_dir.exists():
        logger.error(f"Downloads directory not found: {args.downloads_dir}")
        sys.exit(1)

    if not HAS_PDFPLUMBER and not HAS_PYMUPDF:
        logger.error("No PDF library available. Install pdfplumber or PyMuPDF")
        sys.exit(1)

    logger.info(f"Available PDF libraries: pdfplumber={HAS_PDFPLUMBER}, PyMuPDF={HAS_PYMUPDF}")

    extract_all(args.downloads_dir, args.output_dir, args.workers)


if __name__ == "__main__":
    main()
