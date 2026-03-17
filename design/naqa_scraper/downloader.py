"""File download handler for NAQA scraper"""

import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.async_api import Download, Page

from .config import settings
from .models import DownloadedFile, FormSE

logger = logging.getLogger(__name__)


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Sanitize a string to be used as a safe filename"""
    # Remove/replace invalid characters
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", name)
    # Replace multiple spaces/underscores with single underscore
    safe_name = re.sub(r"[\s_]+", "_", safe_name)
    # Remove leading/trailing underscores and dots
    safe_name = safe_name.strip("_.")
    # Truncate if too long
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]
    return safe_name or "unnamed"


class FileDownloader:
    """Handles downloading all files from Form SE pages"""

    def __init__(self, page: Page, case_id: str):
        self.page = page
        self.case_id = case_id
        self.downloads_base = settings.downloads_dir / case_id
        self.manifest: dict = {
            "case_id": case_id,
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "files": [],
        }

    async def download_all_files_from_form(self, form_se: FormSE) -> dict:
        """Download ALL files found on the form page"""
        logger.info(f"Starting file downloads for case {self.case_id}")

        # Ensure base directories exist
        self.downloads_base.mkdir(parents=True, exist_ok=True)

        # 1. Download main document files
        await self._download_main_documents()

        # 2. Download files from each tab
        await self._download_files_from_tabs(form_se)

        # 3. Download files from Table 1 (educational components)
        await self._download_table1_files(form_se)

        # 4. Download files from all other tables
        await self._download_all_table_files()

        # Save manifest
        await self._save_manifest()

        logger.info(
            f"Download complete for {self.case_id}: "
            f"{self.manifest['successful']}/{self.manifest['total_files']} files"
        )

        return self.manifest

    async def _download_main_documents(self) -> None:
        """Download main document files (Освітня програма, Навчальний план)"""
        logger.info("Downloading main documents")

        main_doc_fields = [
            ("main_documents/освітня_програма", "Освітня програма"),
            ("main_documents/навчальний_план", "Навчальний план"),
        ]

        for folder, field_label in main_doc_fields:
            await self._download_files_near_label(field_label, folder)

    async def _download_files_near_label(self, label: str, folder: str) -> None:
        """Find and download files near a specific label"""
        try:
            # Find container with the label
            selectors = [
                f'div:has-text("{label}")',
                f'tr:has-text("{label}")',
                f'p:has-text("{label}")',
                f'.field:has-text("{label}")',
            ]

            for selector in selectors:
                try:
                    container = self.page.locator(selector)
                    if await container.count() > 0:
                        # Find download links within this container
                        links = await container.first.locator(
                            'a[href*="download"], a[href$=".pdf"], a[href$=".doc"], a[href$=".docx"]'
                        ).all()

                        for link in links:
                            await self._download_from_link(link, folder, label)
                        break
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Error downloading files for {label}: {e}")

    async def _download_files_from_tabs(self, form_se: FormSE) -> None:
        """Download all files from each tab"""
        logger.info("Downloading files from tabs")

        for tab_num in range(1, 12):
            folder = f"tabs/tab_{tab_num:02d}"

            # Click on the tab to make content visible
            await self._click_tab(tab_num)
            await self.page.wait_for_timeout(1000)

            # Find all download links in the active tab content
            tab_content_selectors = [
                ".tab-content.active",
                ".tab-panel.active",
                f'.tab-content[data-tab="{tab_num}"]',
                '[role="tabpanel"]:visible',
            ]

            for selector in tab_content_selectors:
                try:
                    content = self.page.locator(selector)
                    if await content.count() > 0:
                        links = await content.locator(
                            'a[href*="download"], a[href$=".pdf"], '
                            'a[href$=".doc"], a[href$=".docx"], '
                            'a[href$=".xls"], a[href$=".xlsx"]'
                        ).all()

                        for link in links:
                            await self._download_from_link(link, folder, f"tab_{tab_num}")
                        break
                except Exception:
                    continue

    async def _download_table1_files(self, form_se: FormSE) -> None:
        """Download all files from Table 1 (educational components)

        Process:
        1. Navigate to Tab 12 (Таблиця 1)
        2. For each row, click on the component name to open side panel
        3. Click "Переглянути" button to trigger blob download
        4. Save the file with component name
        """
        logger.info("Downloading Table 1 component files")

        # First, navigate to Tab 12 (Таблиця 1)
        role_tabs = await self.page.locator('[role="tab"]').all()
        if len(role_tabs) > 12:
            logger.info("Navigating to Tab 12 (Таблиця 1) for downloads")
            await role_tabs[12].click()
            await self.page.wait_for_timeout(3000)
        else:
            logger.warning("Tab 12 not found, cannot download Table 1 files")
            return

        # Find the table in the visible tabpanel
        panel = self.page.locator('[role="tabpanel"]:visible, .tab-pane.active')
        if await panel.count() == 0:
            logger.warning("Table 1 tabpanel not found")
            return

        table = panel.first.locator("table")
        if await table.count() == 0:
            logger.warning("Table 1 not found in panel")
            return

        table_elem = table.first

        # Get all rows
        try:
            rows = await table_elem.locator("tbody tr").all()
            logger.info(f"Found {len(rows)} components to download")

            for idx, row in enumerate(rows):
                # Get component name from first cell
                try:
                    cells = await row.locator("td").all()
                    if not cells:
                        continue

                    first_cell = cells[0]
                    component_name = await first_cell.text_content() or f"component_{idx}"
                    component_name = component_name.strip()
                    safe_name = sanitize_filename(component_name)

                    # Get syllabus filename from download column (3rd column, index 2)
                    syllabus_filename = ""
                    if len(cells) > 2:
                        syllabus_text = await cells[2].text_content() or ""
                        syllabus_text = syllabus_text.strip()
                        if ".pdf" in syllabus_text.lower():
                            syllabus_filename = syllabus_text

                    logger.info(f"Processing component {idx + 1}/{len(rows)}: {component_name[:50]}...")

                    # Click on the first cell to open side panel
                    await first_cell.click()
                    await self.page.wait_for_timeout(1500)

                    # Find and click the "Переглянути" button
                    view_btn = self.page.locator('button:has-text("Переглянути"):visible')
                    if await view_btn.count() > 0:
                        folder = f"components/{idx:03d}_{safe_name}"

                        # Download the file via blob URL
                        downloaded = await self._download_via_blob_button(
                            view_btn.first,
                            folder,
                            syllabus_filename or f"{safe_name}.pdf",
                            context=f"component_{idx}: {component_name}"
                        )

                        if downloaded:
                            logger.info(f"  Downloaded syllabus for: {component_name[:40]}...")
                        else:
                            logger.warning(f"  No file downloaded for: {component_name[:40]}...")

                        # Wait a bit before next component
                        await self.page.wait_for_timeout(500)
                    else:
                        logger.warning(f"  'Переглянути' button not found for component: {component_name[:40]}...")

                except Exception as e:
                    logger.warning(f"Error processing component {idx}: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error downloading Table 1 files: {e}")

    async def _download_via_blob_button(
        self, button, folder: str, preferred_filename: str, context: str
    ) -> DownloadedFile | None:
        """Download a file by clicking a button that triggers a blob download"""
        try:
            self.manifest["total_files"] += 1

            # Create save directory
            save_dir = self.downloads_base / folder
            save_dir.mkdir(parents=True, exist_ok=True)

            # Try to capture the download
            try:
                async with self.page.expect_download(timeout=settings.download_timeout) as download_info:
                    await button.click()

                download: Download = await download_info.value

                # Get suggested filename (usually UUID-based for blob URLs)
                original_filename = download.suggested_filename
                blob_url = download.url

                # Use preferred filename if it looks valid, otherwise use original
                if preferred_filename and preferred_filename.lower().endswith('.pdf'):
                    filename = sanitize_filename(preferred_filename.replace('.pdf', '')) + '.pdf'
                else:
                    filename = original_filename

                # Ensure unique filename
                filepath = save_dir / filename
                counter = 1
                while filepath.exists():
                    stem = filepath.stem
                    suffix = filepath.suffix
                    filepath = save_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

                # Save the file
                await download.save_as(filepath)

                # Get file size
                file_size = filepath.stat().st_size if filepath.exists() else 0

                downloaded_file = DownloadedFile(
                    original_filename=original_filename,
                    local_path=str(filepath),
                    url=blob_url,
                    link_text=preferred_filename,
                    context=context,
                    size_bytes=file_size,
                    downloaded_at=datetime.now(),
                    status="success",
                )

                self.manifest["successful"] += 1
                self.manifest["files"].append(downloaded_file.model_dump())

                logger.debug(f"Downloaded: {filename} ({file_size} bytes)")
                return downloaded_file

            except asyncio.TimeoutError:
                logger.warning(f"Download timeout for {context}")
                self._record_failed_download("blob:", preferred_filename, context, "timeout")
                return None

        except Exception as e:
            logger.warning(f"Failed to download via button: {e}")
            self._record_failed_download("blob:", preferred_filename, context, str(e))
            return None

    async def _download_all_table_files(self) -> None:
        """Download files from all tables on the page"""
        logger.info("Downloading files from all tables")

        try:
            tables = await self.page.locator("table").all()
            for table_idx, table in enumerate(tables):
                folder = f"tables/table_{table_idx:02d}"

                links = await table.locator(
                    'a[href*="download"], a[href$=".pdf"], a[href$=".doc"], a[href$=".docx"]'
                ).all()

                for link in links:
                    await self._download_from_link(link, folder, f"table_{table_idx}")

        except Exception as e:
            logger.warning(f"Error downloading table files: {e}")

    async def _download_from_link(self, link, folder: str, context: str) -> DownloadedFile | None:
        """Download a file from a link element"""
        try:
            url = await link.get_attribute("href")
            if not url:
                return None

            # Make absolute URL
            full_url = urljoin(settings.base_url, url)

            # Check if we've already downloaded this URL
            if any(f.get("url") == full_url for f in self.manifest["files"]):
                logger.debug(f"Skipping duplicate: {full_url}")
                return None

            link_text = await link.text_content() or ""
            link_text = link_text.strip()

            self.manifest["total_files"] += 1

            # Create save directory
            save_dir = self.downloads_base / folder
            save_dir.mkdir(parents=True, exist_ok=True)

            # Try to download
            try:
                async with self.page.expect_download(timeout=settings.download_timeout) as download_info:
                    await link.click()

                download: Download = await download_info.value

                # Get suggested filename
                filename = download.suggested_filename
                if not filename:
                    # Extract from URL
                    parsed = urlparse(full_url)
                    filename = Path(parsed.path).name or "unknown_file"

                # Ensure unique filename
                filepath = save_dir / filename
                counter = 1
                while filepath.exists():
                    stem = filepath.stem
                    suffix = filepath.suffix
                    filepath = save_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

                # Save the file
                await download.save_as(filepath)

                # Get file size
                file_size = filepath.stat().st_size if filepath.exists() else 0

                downloaded_file = DownloadedFile(
                    original_filename=filename,
                    local_path=str(filepath),
                    url=full_url,
                    link_text=link_text,
                    context=context,
                    size_bytes=file_size,
                    downloaded_at=datetime.now(),
                    status="success",
                )

                self.manifest["successful"] += 1
                self.manifest["files"].append(downloaded_file.model_dump())

                logger.info(f"Downloaded: {filename} ({file_size} bytes)")
                return downloaded_file

            except asyncio.TimeoutError:
                logger.warning(f"Download timeout: {full_url}")
                self._record_failed_download(full_url, link_text, context, "timeout")
                return None

        except Exception as e:
            logger.warning(f"Failed to download from link: {e}")
            if url:
                self._record_failed_download(
                    urljoin(settings.base_url, url), link_text if "link_text" in dir() else "", context, str(e)
                )
            return None

    def _record_failed_download(self, url: str, link_text: str, context: str, error: str) -> None:
        """Record a failed download in the manifest"""
        self.manifest["failed"] += 1
        self.manifest["files"].append(
            {
                "url": url,
                "link_text": link_text,
                "context": context,
                "status": "failed",
                "error": error,
            }
        )

    async def _click_tab(self, tab_number: int) -> bool:
        """Click on a tab to make its content visible"""
        tab_selectors = [
            f'[data-tab="{tab_number}"]',
            f'button:has-text("Таблиця {tab_number}")',
            f'a:has-text("Таблиця {tab_number}")',
            f'.tab-{tab_number}',
            f'[role="tab"]:nth-child({tab_number})',
        ]

        for selector in tab_selectors:
            try:
                elem = self.page.locator(selector)
                if await elem.count() > 0:
                    await elem.first.click()
                    return True
            except Exception:
                continue

        return False

    async def _save_manifest(self) -> None:
        """Save the download manifest to a JSON file"""
        import json

        manifest_path = self.downloads_base / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Manifest saved to {manifest_path}")
