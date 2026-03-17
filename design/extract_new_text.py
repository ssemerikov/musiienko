#!/usr/bin/env python3
"""
Extract text from newly downloaded PDFs.
"""

import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using pdftotext or PyPDF2."""
    try:
        # Try pdftotext first
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except Exception:
        pass

    # Fallback to PyPDF2
    try:
        import PyPDF2
        text = []
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""


def process_case(case_id: str, level: str = "Бакалавр"):
    """Process all PDFs in a case directory and extract text."""
    pdf_dir = Path(f"data/downloads_by_level/{level}/{case_id}")
    text_dir = Path(f"data/text_by_level/{level}/{case_id}")

    if not pdf_dir.exists():
        logger.error(f"PDF directory not found: {pdf_dir}")
        return 0

    text_dir.mkdir(parents=True, exist_ok=True)

    extracted = 0
    for pdf_path in pdf_dir.rglob("*.pdf"):
        # Determine output path
        rel_path = pdf_path.relative_to(pdf_dir)
        txt_path = text_dir / rel_path.with_suffix(".txt")
        txt_path.parent.mkdir(parents=True, exist_ok=True)

        # Skip if already extracted
        if txt_path.exists() and txt_path.stat().st_size > 0:
            continue

        # Extract text
        text = extract_text_from_pdf(pdf_path)
        if text.strip():
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            extracted += 1
            logger.info(f"Extracted: {txt_path.name}")
        else:
            logger.warning(f"No text extracted from: {pdf_path.name}")

    return extracted


def main():
    # Cases that were just re-downloaded (bachelor)
    bachelor_cases = ["8855", "8856", "8857", "14140"]

    logger.info("Extracting text from newly downloaded PDFs...")

    total = 0
    for case_id in bachelor_cases:
        logger.info(f"\n=== Processing case {case_id} ===")
        extracted = process_case(case_id, "Бакалавр")
        total += extracted
        logger.info(f"Case {case_id}: Extracted {extracted} text files")

    logger.info(f"\n=== TOTAL: Extracted {total} text files ===")


if __name__ == "__main__":
    main()
