#!/usr/bin/env python3
"""
NAQA Accreditation Scraper
Main entry point for scraping accreditation records for any specialty
"""

import argparse
import asyncio
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

from .browser import get_browser
from .checkpoint import CheckpointManager
from .config import settings, COMMON_SPECIALTIES, DEGREE_LEVELS, REGIONS, ACCREDITATION_STATUSES
from .downloader import FileDownloader
from .extractor import Extractor
from .models import AccreditationCase, CaseUrl, ScrapeSession
from .navigator import Navigator
from .storage import StorageManager


def setup_logging(session_id: str) -> logging.Logger:
    """Configure logging for the session"""
    settings.ensure_directories()

    log_file = settings.logs_dir / f"{session_id}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    logger = logging.getLogger("naqa_scraper")
    logger.info(f"Session started: {session_id}")
    logger.info(f"Log file: {log_file}")

    return logger


async def collect_case_urls(
    navigator: Navigator, checkpoint: CheckpointManager, max_cases: int | None = None
) -> list[CaseUrl]:
    """Phase 1: Collect all case URLs for the specialty"""
    logger = logging.getLogger("naqa_scraper")

    # Check if we already have URLs from a previous run
    existing_urls = checkpoint.get_case_urls()
    if existing_urls:
        logger.info(f"Resuming with {len(existing_urls)} previously collected URLs")
        # Apply max_cases limit if needed
        if max_cases and len(existing_urls) > max_cases:
            return existing_urls[:max_cases]
        return existing_urls

    logger.info("Phase 1: Collecting case URLs")
    checkpoint.set_phase("collecting_urls")

    case_urls = await navigator.collect_all_case_urls(max_cases=max_cases)

    checkpoint.set_case_urls(case_urls)
    logger.info(f"Collected {len(case_urls)} case URLs")

    return case_urls


async def scrape_single_case(
    navigator: Navigator,
    case_url: CaseUrl,
    session_id: str,
) -> AccreditationCase:
    """Scrape a single accreditation case"""
    logger = logging.getLogger("naqa_scraper")
    logger.info(f"Scraping case: {case_url.case_id}")

    case = AccreditationCase(
        case_id=case_url.case_id,
        case_url=case_url.case_url,
        institution_name=case_url.institution_name,
        program_name=case_url.program_name,
    )

    try:
        # Navigate to case page
        if not await navigator.navigate_to_case(case_url.case_url):
            raise Exception(f"Failed to navigate to case page: {case_url.case_url}")

        # Extract basic case info
        basic_info = await navigator.extract_basic_case_info()
        case.institution_name = basic_info.get("institution_name", case.institution_name)
        case.program_name = basic_info.get("program_name", case.program_name)
        case.degree_level = basic_info.get("degree_level", "")
        case.status = basic_info.get("status", "")

        # Find and navigate to Form SE (clicking the button navigates directly)
        form_url = await navigator.find_form_se_url()
        if not form_url:
            logger.warning(f"Form SE not found for case {case_url.case_id}")
            case.scrape_status = "partial"
            return case

        # Note: find_form_se_url already clicked and navigated to the form page

        # Extract form ID from URL
        import re

        form_id_match = re.search(r"/form-se/(\d+)", form_url)
        form_id = form_id_match.group(1) if form_id_match else case_url.case_id

        # Extract form data
        extractor = Extractor(navigator.page)
        form_se = await extractor.extract_form_se(form_id, form_url)

        # Extract main document links
        main_docs = await extractor.extract_main_document_links()

        # Download all files
        downloader = FileDownloader(navigator.page, case_url.case_id)
        files_manifest = await downloader.download_all_files_from_form(form_se)

        # Update form with file info
        form_se.all_files = []  # Will be populated from manifest

        case.form_se = form_se
        case.files_manifest = files_manifest
        case.scrape_status = "completed"
        case.scraped_at = datetime.now()

        logger.info(
            f"Case {case_url.case_id} completed: "
            f"{len(form_se.tabs)} tabs, "
            f"{len(form_se.table1_components)} components, "
            f"{files_manifest.get('successful', 0)} files"
        )

    except Exception as e:
        logger.error(f"Error scraping case {case_url.case_id}: {e}")
        case.scrape_status = "failed"
        case.error_message = str(e)
        raise

    return case


async def main_async(
    session_id: str | None = None,
    resume: bool = True,
    max_cases: int | None = None,
    headless: bool = True,
    specialty: str | None = None,
    degree_level: str | None = None,
    accreditation_status: str | None = None,
    region: str | None = None,
    institution_name: str | None = None,
    program_name: str | None = None,
) -> None:
    """Main async entry point"""
    # Set all filter parameters if provided
    settings.set_filters(
        specialty=specialty,
        degree_level=degree_level,
        accreditation_status=accreditation_status,
        region=region,
        institution_name=institution_name,
        program_name=program_name,
    )

    # Generate or use provided session ID (include specialty code for uniqueness)
    if session_id is None:
        spec_code = settings.specialty.split()[0] if settings.specialty else "all"
        session_id = f"naqa_{spec_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    logger = setup_logging(session_id)
    active_filters = settings.get_active_filters()
    logger.info(f"Active filters: {active_filters}")
    settings.headless = headless
    settings.ensure_directories()

    # Initialize checkpoint manager
    checkpoint = CheckpointManager(session_id)
    if resume:
        checkpoint.load()

    # Initialize storage manager
    storage = StorageManager(session_id)

    # Initialize session
    session = ScrapeSession(
        session_id=session_id,
        started_at=datetime.now(),
    )

    async with get_browser() as browser_manager:
        navigator = Navigator(browser_manager)

        # Phase 1: Collect URLs (limit during collection for efficiency)
        case_urls = await collect_case_urls(navigator, checkpoint, max_cases=max_cases)

        session.total_cases = len(case_urls)
        if max_cases:
            logger.info(f"Limited to {len(case_urls)} cases")

        # Phase 2: Scrape each case
        checkpoint.set_phase("scraping")
        pending_cases = checkpoint.get_pending_cases()
        logger.info(f"Processing {len(pending_cases)} pending cases")

        for case_url in pending_cases:
            try:
                case_data = await scrape_single_case(navigator, case_url, session_id)
                session.cases.append(case_data)
                session.completed_cases += 1

                # Update statistics
                if case_data.files_manifest:
                    checkpoint.update_statistics(
                        files_downloaded=case_data.files_manifest.get("successful", 0),
                        components_extracted=len(case_data.form_se.table1_components)
                        if case_data.form_se
                        else 0,
                    )

                checkpoint.mark_completed(case_url.case_id)

                # Save individual case JSON
                storage.save_case_json(case_data)

            except Exception as e:
                logger.error(f"Failed to scrape case {case_url.case_id}: {e}")
                checkpoint.mark_failed(case_url.case_id, str(e))
                session.failed_cases += 1

    # Phase 3: Finalize and save output
    session.completed_at = datetime.now()
    session.total_files_downloaded = checkpoint.data["statistics"]["total_files_downloaded"]
    session.extraction_complete = checkpoint.is_completed()

    # Load all completed cases for final output
    completed_ids = set(checkpoint.data["completed_cases"])
    all_cases = []

    # Load from raw files
    for case_id in completed_ids:
        case_file = settings.raw_dir / f"case_{case_id}.json"
        if case_file.exists():
            import json

            with open(case_file, "r", encoding="utf-8") as f:
                case_data = json.load(f)
                all_cases.append(AccreditationCase(**case_data))

    session.cases = all_cases

    # Save all outputs
    output_files = storage.save_all(session)
    checkpoint.finalize()

    # Print summary
    progress = checkpoint.get_progress()
    logger.info("=" * 60)
    logger.info("SCRAPING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Total cases: {progress['total_cases']}")
    logger.info(f"Completed: {progress['completed']}")
    logger.info(f"Failed: {progress['failed']}")
    logger.info(f"Files downloaded: {progress['statistics']['total_files_downloaded']}")
    logger.info(f"Components extracted: {progress['statistics']['total_components_extracted']}")
    logger.info("Output files:")
    for name, path in output_files.items():
        logger.info(f"  - {name}: {path}")


def main() -> None:
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="NAQA Accreditation Scraper - Scrapes accreditation records with flexible filtering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape default specialty (022 Дизайн)
  python -m naqa_scraper

  # Scrape a specific specialty by code
  python -m naqa_scraper --specialty "122 Комп'ютерні науки"

  # Scrape by partial match (code only)
  python -m naqa_scraper --specialty 122

  # Scrape with multiple filters
  python -m naqa_scraper --specialty 022 --degree "Бакалавр" --region "Львівська область"

  # Scrape only accredited programs
  python -m naqa_scraper --specialty 022 --status "Акредитована"

  # Search by institution name
  python -m naqa_scraper --institution "Київський"

  # List all available filter options
  python -m naqa_scraper --list-specialties
  python -m naqa_scraper --list-degrees
  python -m naqa_scraper --list-regions
  python -m naqa_scraper --list-statuses

  # Limit to 5 cases for testing
  python -m naqa_scraper --specialty 022 --max-cases 5 --headed
        """,
    )

    # Filter arguments
    filter_group = parser.add_argument_group("Filter Options")
    filter_group.add_argument(
        "--specialty",
        "-s",
        type=str,
        default=None,
        help="Specialty (Спеціальність) - e.g., '022 Дизайн' or just '022'. Default: 022 Дизайн",
    )
    filter_group.add_argument(
        "--degree",
        "-d",
        type=str,
        default=None,
        help="Degree level (Рівень вищої освіти) - e.g., 'Бакалавр', 'Магістр'",
    )
    filter_group.add_argument(
        "--status",
        type=str,
        default=None,
        help="Accreditation status (Статус) - e.g., 'Акредитована'",
    )
    filter_group.add_argument(
        "--region",
        "-r",
        type=str,
        default=None,
        help="Region (Регіон) - e.g., 'Київська область', 'м. Київ'",
    )
    filter_group.add_argument(
        "--institution",
        type=str,
        default=None,
        help="Institution name search (Назва закладу) - partial match",
    )
    filter_group.add_argument(
        "--program",
        type=str,
        default=None,
        help="Program name search (Назва програми) - partial match",
    )

    # List options
    list_group = parser.add_argument_group("List Filter Values")
    list_group.add_argument(
        "--list-specialties",
        action="store_true",
        help="List all available specialties and exit",
    )
    list_group.add_argument(
        "--list-degrees",
        action="store_true",
        help="List all degree levels and exit",
    )
    list_group.add_argument(
        "--list-regions",
        action="store_true",
        help="List all regions and exit",
    )
    list_group.add_argument(
        "--list-statuses",
        action="store_true",
        help="List all accreditation statuses and exit",
    )
    list_group.add_argument(
        "--find-specialty",
        type=str,
        metavar="QUERY",
        help="Search for specialties matching a query (by code or name)",
    )

    # Session arguments
    session_group = parser.add_argument_group("Session Options")
    session_group.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="Session ID (for resuming). If not provided, generates a new one.",
    )
    session_group.add_argument(
        "--no-resume",
        action="store_true",
        help="Start fresh, don't resume from checkpoint",
    )
    session_group.add_argument(
        "--list-failed",
        action="store_true",
        help="List failed cases from checkpoint and exit",
    )
    session_group.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry only failed cases",
    )

    # Execution arguments
    exec_group = parser.add_argument_group("Execution Options")
    exec_group.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="Maximum number of cases to scrape (for testing)",
    )
    exec_group.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed mode (visible window)",
    )

    args = parser.parse_args()

    # Handle list commands
    if args.list_specialties:
        print("Available specialties (Спеціальності):")
        print("-" * 60)
        for spec in COMMON_SPECIALTIES:
            print(f"  {spec}")
        print("-" * 60)
        print(f"Total: {len(COMMON_SPECIALTIES)} specialties")
        return

    if args.list_degrees:
        print("Available degree levels (Рівні вищої освіти):")
        print("-" * 40)
        for degree in DEGREE_LEVELS:
            print(f"  {degree}")
        return

    if args.list_regions:
        print("Available regions (Регіони):")
        print("-" * 40)
        for region in REGIONS:
            print(f"  {region}")
        return

    if args.list_statuses:
        print("Available accreditation statuses (Статуси):")
        print("-" * 50)
        for status in ACCREDITATION_STATUSES:
            print(f"  {status}")
        return

    # Handle find-specialty
    if args.find_specialty:
        matches = settings.find_specialty(args.find_specialty)
        if matches:
            print(f"Specialties matching '{args.find_specialty}':")
            for spec in matches:
                print(f"  {spec}")
        else:
            print(f"No specialties found matching '{args.find_specialty}'")
        return

    # Handle list-failed
    if args.list_failed and args.session_id:
        checkpoint = CheckpointManager(args.session_id)
        if checkpoint.load():
            failed = checkpoint.get_failed_cases()
            if failed:
                print(f"Failed cases ({len(failed)}):")
                for f in failed:
                    print(f"  - {f['case_id']}: {f['error']}")
            else:
                print("No failed cases")
        else:
            print("Checkpoint not found")
        return

    # Resolve specialty if provided as code only
    specialty = args.specialty
    if specialty:
        # If just a number (code), try to find full specialty name
        if specialty.isdigit() or (len(specialty) == 3 and specialty[0].isdigit()):
            matches = settings.find_specialty(specialty)
            if len(matches) == 1:
                specialty = matches[0]
                print(f"Resolved specialty: {specialty}")
            elif len(matches) > 1:
                print(f"Multiple specialties match '{args.specialty}':")
                for m in matches:
                    print(f"  {m}")
                print("Please specify the full specialty name.")
                return
            else:
                print(f"No specialty found matching '{args.specialty}'")
                print("Use --list-specialties to see available options.")
                return

    # Print active filters
    print("Active filters:")
    if specialty:
        print(f"  - Specialty: {specialty}")
    if args.degree:
        print(f"  - Degree level: {args.degree}")
    if args.status:
        print(f"  - Status: {args.status}")
    if args.region:
        print(f"  - Region: {args.region}")
    if args.institution:
        print(f"  - Institution: {args.institution}")
    if args.program:
        print(f"  - Program: {args.program}")

    # Run main async function
    asyncio.run(
        main_async(
            session_id=args.session_id,
            resume=not args.no_resume,
            max_cases=args.max_cases,
            headless=not args.headed,
            specialty=specialty,
            degree_level=args.degree,
            accreditation_status=args.status,
            region=args.region,
            institution_name=args.institution,
            program_name=args.program,
        )
    )


if __name__ == "__main__":
    main()
