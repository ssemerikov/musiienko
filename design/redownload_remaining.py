#!/usr/bin/env python3
"""
Re-download PDFs for remaining cases with high data loss.
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from naqa_scraper.browser import BrowserManager
from naqa_scraper.downloader import FileDownloader
from naqa_scraper.extractor import Extractor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF."""
    try:
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

    try:
        import PyPDF2
        text = []
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)
    except Exception:
        return ""


async def redownload_case(case_id: str, level_dir: Path, text_dir: Path) -> bool:
    """Re-download all files for a specific case and extract text."""

    case_url = f"https://public.naqa.gov.ua/v2/form-se/{case_id}/view"
    output_dir = level_dir / case_id

    logger.info(f"Re-downloading case {case_id} from {case_url}")

    browser_manager = BrowserManager()

    try:
        page = await browser_manager.start()
        await page.goto(case_url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)

        if "form-se" not in page.url:
            logger.error(f"Failed to load form page for case {case_id}")
            return False

        extractor = Extractor(page)
        form_se = await extractor.extract_all_tabs()

        downloader = FileDownloader(page, case_id)
        downloader.downloads_base = output_dir
        downloader.downloads_base.mkdir(parents=True, exist_ok=True)

        manifest = await downloader.download_all_files_from_form(form_se)

        logger.info(
            f"Case {case_id}: Downloaded {manifest['successful']}/{manifest['total_files']} files"
        )

        # Extract text immediately
        text_case_dir = text_dir / case_id
        text_case_dir.mkdir(parents=True, exist_ok=True)

        extracted = 0
        for pdf_path in output_dir.rglob("*.pdf"):
            rel_path = pdf_path.relative_to(output_dir)
            txt_path = text_case_dir / rel_path.with_suffix(".txt")
            txt_path.parent.mkdir(parents=True, exist_ok=True)

            if txt_path.exists() and txt_path.stat().st_size > 0:
                continue

            text = extract_text_from_pdf(pdf_path)
            if text.strip():
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                extracted += 1

        logger.info(f"Case {case_id}: Extracted {extracted} text files")

        return manifest['successful'] > 0

    except Exception as e:
        logger.error(f"Error re-downloading case {case_id}: {e}")
        return False
    finally:
        await browser_manager.stop()


async def main():
    """Re-download files for cases with high data loss."""

    # Master cases with 100% loss
    master_cases = ["12786", "12787", "13008", "15168", "5365"]
    master_dir = Path("data/downloads_by_level/Магістр")
    master_text_dir = Path("data/text_by_level/Магістр")

    # Bachelor cases with high loss (>50%)
    bachelor_cases = ["8588", "3363", "5160", "3362", "5159"]
    bachelor_dir = Path("data/downloads_by_level/Бакалавр")
    bachelor_text_dir = Path("data/text_by_level/Бакалавр")

    all_cases = [
        (master_cases, master_dir, master_text_dir, "Master"),
        (bachelor_cases, bachelor_dir, bachelor_text_dir, "Bachelor"),
    ]

    results = {}

    for cases, pdf_dir, text_dir, level_name in all_cases:
        logger.info(f"\n=== Processing {level_name} cases ===")

        for case_id in cases:
            success = await redownload_case(case_id, pdf_dir, text_dir)
            results[f"{level_name}:{case_id}"] = success
            await asyncio.sleep(2)

    # Summary
    logger.info("\n=== SUMMARY ===")
    for case_key, success in results.items():
        status = "✓ Success" if success else "✗ Failed"
        logger.info(f"{case_key}: {status}")

    successful = sum(1 for s in results.values() if s)
    logger.info(f"\nTotal: {successful}/{len(results)} cases processed")


if __name__ == "__main__":
    asyncio.run(main())
