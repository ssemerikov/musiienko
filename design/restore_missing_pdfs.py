#!/usr/bin/env python3
"""
Restore missing PDF directories by re-downloading from NAQA portal.
Text files exist but PDFs were deleted during cleanup.
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from naqa_scraper.browser import BrowserManager
from naqa_scraper.downloader import FileDownloader
from naqa_scraper.extractor import Extractor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_missing_pdf_cases() -> List[Tuple[str, str, int, int]]:
    """Find cases where PDF directories are missing but text exists."""
    levels = ["Бакалавр", "Магістр", "Доктор_філософії"]
    missing_cases = []

    for level in levels:
        pdf_base = Path(f"data/downloads_by_level/{level}")
        txt_base = Path(f"data/text_by_level/{level}")

        if not pdf_base.exists():
            continue

        for case_dir in sorted(pdf_base.iterdir()):
            if not case_dir.is_dir():
                continue
            case_id = case_dir.name

            pdf_comp = case_dir / "components"
            txt_comp = txt_base / case_id / "components"

            if pdf_comp.exists() and txt_comp.exists():
                pdf_count = len([d for d in pdf_comp.iterdir() if d.is_dir()])
                txt_count = len([d for d in txt_comp.iterdir() if d.is_dir()])

                if pdf_count < txt_count:
                    missing_cases.append((level, case_id, pdf_count, txt_count))

    return missing_cases


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using pdftotext."""
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return result.stdout
    except Exception:
        pass
    return ""


async def restore_case_pdfs(level: str, case_id: str) -> Tuple[int, int]:
    """Re-download all PDFs for a case with missing components."""

    case_url = f"https://public.naqa.gov.ua/v2/form-se/{case_id}/view"
    output_dir = Path(f"data/downloads_by_level/{level}/{case_id}")
    text_dir = Path(f"data/text_by_level/{level}/{case_id}")

    logger.info(f"Re-downloading case {case_id} ({level})")

    browser_manager = BrowserManager()
    downloaded = 0
    extracted = 0

    try:
        page = await browser_manager.start()
        await page.goto(case_url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)

        if "form-se" not in page.url:
            logger.error(f"Failed to load form page for case {case_id}")
            return 0, 0

        extractor = Extractor(page)
        form_se = await extractor.extract_all_tabs()

        downloader = FileDownloader(page, case_id)
        downloader.downloads_base = output_dir
        downloader.downloads_base.mkdir(parents=True, exist_ok=True)

        manifest = await downloader.download_all_files_from_form(form_se)
        downloaded = manifest.get('successful', 0)

        logger.info(f"Case {case_id}: Downloaded {downloaded}/{manifest.get('total_files', 0)} files")

        # Extract text for any new PDFs
        for pdf_path in output_dir.rglob("*.pdf"):
            rel_path = pdf_path.relative_to(output_dir)
            txt_path = text_dir / rel_path.with_suffix(".txt")

            if txt_path.exists() and txt_path.stat().st_size > 0:
                continue

            txt_path.parent.mkdir(parents=True, exist_ok=True)
            text = extract_text_from_pdf(pdf_path)
            if text.strip():
                txt_path.write_text(text, encoding="utf-8")
                extracted += 1

        if extracted > 0:
            logger.info(f"Case {case_id}: Extracted {extracted} new text files")

        return downloaded, extracted

    except Exception as e:
        logger.error(f"Error restoring case {case_id}: {e}")
        return 0, 0
    finally:
        await browser_manager.stop()


async def main():
    """Restore missing PDF directories."""

    missing_cases = find_missing_pdf_cases()

    logger.info(f"Found {len(missing_cases)} cases with missing PDFs")
    logger.info("Cases to restore:")
    for level, case_id, pdf_count, txt_count in missing_cases:
        logger.info(f"  {level}/{case_id}: {pdf_count} PDFs, {txt_count} text dirs")

    total_downloaded = 0
    total_extracted = 0
    results = {}

    for level, case_id, pdf_count, txt_count in missing_cases:
        downloaded, extracted = await restore_case_pdfs(level, case_id)
        results[f"{level}/{case_id}"] = (downloaded, extracted)
        total_downloaded += downloaded
        total_extracted += extracted
        await asyncio.sleep(2)

    logger.info("\n=== SUMMARY ===")
    for case_key, (downloaded, extracted) in results.items():
        status = "✓" if downloaded > 0 else "✗"
        logger.info(f"{status} {case_key}: {downloaded} PDFs, {extracted} new texts")

    logger.info(f"\nTotal: {total_downloaded} PDFs restored, {total_extracted} texts extracted")


if __name__ == "__main__":
    asyncio.run(main())
