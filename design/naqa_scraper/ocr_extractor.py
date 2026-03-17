#!/usr/bin/env python3
"""
OCR Text Extraction for Failed PDFs
Uses Tesseract OCR to extract text from scanned/image-based PDFs.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

try:
    import pytesseract
    from pdf2image import convert_from_path
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def ocr_pdf(pdf_path: Path, languages: str = "ukr+eng") -> tuple[Path, str, bool]:
    """Extract text from PDF using OCR

    Args:
        pdf_path: Path to PDF file
        languages: Tesseract language codes (default: Ukrainian + English)

    Returns:
        (pdf_path, extracted_text, success)
    """
    try:
        # Convert PDF pages to images
        images = convert_from_path(pdf_path, dpi=200)

        text_parts = []
        for i, image in enumerate(images):
            # Run OCR on each page
            page_text = pytesseract.image_to_string(image, lang=languages)
            if page_text.strip():
                text_parts.append(f"--- Page {i+1} ---\n{page_text}")

        full_text = "\n\n".join(text_parts)
        return (pdf_path, full_text, bool(full_text.strip()))

    except Exception as e:
        logger.debug(f"OCR failed for {pdf_path}: {e}")
        return (pdf_path, "", False)


def process_single_pdf(args: tuple) -> dict:
    """Process a single PDF with OCR

    Args:
        args: (pdf_path, output_dir, languages)

    Returns:
        dict with status info
    """
    pdf_path, output_dir, languages = args
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)

    result = {
        "pdf_path": str(pdf_path),
        "success": False,
        "text_path": None,
        "chars": 0,
        "error": None,
        "method": "ocr"
    }

    try:
        _, text, success = ocr_pdf(pdf_path, languages)

        if success and text.strip():
            # Create output path maintaining directory structure
            # Go up from downloads/{case_id}/components/{component}/file.pdf
            try:
                relative_path = pdf_path.relative_to(pdf_path.parents[3])
            except ValueError:
                relative_path = pdf_path.name

            txt_path = output_dir / Path(str(relative_path)).with_suffix(".txt")
            txt_path.parent.mkdir(parents=True, exist_ok=True)

            txt_path.write_text(text, encoding="utf-8")

            result["success"] = True
            result["text_path"] = str(txt_path)
            result["chars"] = len(text)
        else:
            result["error"] = "No text extracted via OCR"

    except Exception as e:
        result["error"] = str(e)

    return result


def get_failed_pdfs(manifest_path: Path) -> list[str]:
    """Get list of PDFs that failed regular extraction"""
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return []

    with open(manifest_path) as f:
        manifest = json.load(f)

    failed = [
        f["pdf_path"] for f in manifest.get("files", [])
        if not f.get("success", False)
    ]

    logger.info(f"Found {len(failed)} PDFs that need OCR")
    return failed


def run_ocr(
    failed_pdfs: list[str],
    output_dir: Path,
    languages: str = "ukr+eng",
    max_workers: int = 2
) -> dict:
    """Run OCR on failed PDFs

    Args:
        failed_pdfs: List of PDF paths
        output_dir: Directory to save text files
        languages: Tesseract language codes
        max_workers: Number of parallel workers (OCR is CPU intensive)

    Returns:
        Summary statistics
    """
    if not failed_pdfs:
        logger.warning("No PDFs to process")
        return {"total": 0, "success": 0, "failed": 0}

    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    success_count = 0
    failed_count = 0
    total_chars = 0

    # Prepare arguments for parallel processing
    args_list = [(pdf, output_dir, languages) for pdf in failed_pdfs]

    # Process PDFs (fewer workers since OCR is CPU intensive)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_pdf, args): args[0]
            for args in args_list
        }

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)

            if result["success"]:
                success_count += 1
                total_chars += result["chars"]
                logger.info(f"[{i}/{len(failed_pdfs)}] OCR success: {Path(result['pdf_path']).name} ({result['chars']} chars)")
            else:
                failed_count += 1
                logger.warning(f"[{i}/{len(failed_pdfs)}] OCR failed: {Path(result['pdf_path']).name}")

    # Save OCR manifest
    manifest_path = output_dir / "ocr_manifest.json"
    manifest = {
        "total_pdfs": len(failed_pdfs),
        "successful": success_count,
        "failed": failed_count,
        "total_characters": total_chars,
        "languages": languages,
        "files": results
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    logger.info(f"\n{'='*60}")
    logger.info(f"OCR EXTRACTION COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Total PDFs: {len(failed_pdfs)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {failed_count}")
    logger.info(f"Total characters: {total_chars:,}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Manifest: {manifest_path}")

    return manifest


def main():
    parser = argparse.ArgumentParser(description="OCR extraction for failed PDFs")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("/home/cc/claude_code/design/data/text/extraction_manifest.json"),
        help="Path to extraction manifest with failed PDFs"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/home/cc/claude_code/design/data/text"),
        help="Directory to save extracted text files"
    )
    parser.add_argument(
        "--languages",
        type=str,
        default="ukr+eng",
        help="Tesseract language codes (default: ukr+eng)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Number of parallel workers (default: 2, OCR is CPU intensive)"
    )

    args = parser.parse_args()

    if not HAS_OCR:
        logger.error("OCR libraries not available. Install pytesseract and pdf2image")
        sys.exit(1)

    # Get failed PDFs from manifest
    failed_pdfs = get_failed_pdfs(args.manifest)

    if not failed_pdfs:
        logger.info("No failed PDFs to process")
        return

    run_ocr(failed_pdfs, args.output_dir, args.languages, args.workers)


if __name__ == "__main__":
    main()
