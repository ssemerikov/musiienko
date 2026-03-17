#!/usr/bin/env python3
"""
Re-download PDFs for cases that have manifests but missing files.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from naqa_scraper.browser import BrowserManager
from naqa_scraper.downloader import FileDownloader
from naqa_scraper.extractor import Extractor
from naqa_scraper.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def redownload_case(case_id: str, level_dir: Path) -> bool:
    """Re-download all files for a specific case."""

    case_url = f"https://public.naqa.gov.ua/v2/form-se/{case_id}/view"
    output_dir = level_dir / case_id

    logger.info(f"Re-downloading case {case_id} from {case_url}")

    browser_manager = BrowserManager()

    try:
        page = await browser_manager.start()

        # Navigate to the form page
        await page.goto(case_url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)

        # Check if page loaded correctly
        if "form-se" not in page.url:
            logger.error(f"Failed to load form page for case {case_id}")
            return False

        # Extract form data first (needed for context)
        extractor = Extractor(page)
        form_se = await extractor.extract_all_tabs()

        # Create downloader with correct output directory
        downloader = FileDownloader(page, case_id)
        # Override downloads base to use the level directory
        downloader.downloads_base = output_dir
        downloader.downloads_base.mkdir(parents=True, exist_ok=True)

        # Download all files
        manifest = await downloader.download_all_files_from_form(form_se)

        logger.info(
            f"Case {case_id}: Downloaded {manifest['successful']}/{manifest['total_files']} files"
        )

        return manifest['successful'] > 0

    except Exception as e:
        logger.error(f"Error re-downloading case {case_id}: {e}")
        return False
    finally:
        await browser_manager.stop()


async def main():
    """Re-download files for cases with missing PDFs."""

    # Cases to re-download
    cases_to_fix = ["8855", "8856", "8857", "14140"]
    level_dir = Path("data/downloads_by_level/Бакалавр")

    logger.info(f"Re-downloading {len(cases_to_fix)} cases: {cases_to_fix}")

    results = {}
    for case_id in cases_to_fix:
        success = await redownload_case(case_id, level_dir)
        results[case_id] = success

        # Brief pause between cases
        await asyncio.sleep(2)

    # Summary
    logger.info("\n=== SUMMARY ===")
    for case_id, success in results.items():
        status = "✓ Success" if success else "✗ Failed"
        logger.info(f"Case {case_id}: {status}")

    successful = sum(1 for s in results.values() if s)
    logger.info(f"\nTotal: {successful}/{len(cases_to_fix)} cases re-downloaded")


if __name__ == "__main__":
    asyncio.run(main())
