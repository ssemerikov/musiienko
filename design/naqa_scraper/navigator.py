"""Page navigation logic for NAQA website"""

import logging
import re
from urllib.parse import urljoin

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from .browser import BrowserManager
from .config import settings
from .models import CaseUrl

logger = logging.getLogger(__name__)


class Navigator:
    """Handles navigation through NAQA website"""

    def __init__(self, browser_manager: BrowserManager):
        self.browser = browser_manager
        self.page: Page = browser_manager.page

    async def collect_all_case_urls(self, max_cases: int | None = None) -> list[CaseUrl]:
        """
        Phase A: Collect all case URLs based on configured filters

        Steps:
        1. Navigate to main page
        2. Click filter button (first button - icon)
        3. Apply all configured filters
        4. Close filter panel and wait for results
        5. Paginate through all results
        6. Collect case page URLs

        Args:
            max_cases: Maximum number of cases to collect (for testing). None = all.
        """
        case_urls: list[CaseUrl] = []

        # Step 1: Navigate to main page
        logger.info("Navigating to NAQA public portal")
        await self.browser.rate_limited_navigate(settings.base_url)
        await self.page.wait_for_timeout(2000)

        # Step 2: Click filter button (first button - small icon on left under title)
        logger.info("Opening filter panel")
        # Wait for buttons to be available
        await self.page.wait_for_selector("button", timeout=10000)
        await self.page.wait_for_timeout(1000)

        # The filter button is the small icon button, usually first in the page
        filter_btn = self.page.locator("button").first
        if await filter_btn.count() > 0:
            await filter_btn.click()
            await self.page.wait_for_timeout(2000)  # Wait for panel animation
            logger.info("Filter panel opened")
        else:
            logger.warning("Filter button not found")

        # Step 3: Apply all configured filters
        active_filters = settings.get_active_filters()
        logger.info(f"Applying filters: {active_filters}")

        # Apply specialty filter (Спеціальність dropdown - index 0)
        if settings.specialty:
            await self._select_filter_dropdown("Спеціальність", settings.specialty, dropdown_index=0)

        # Apply status filter only if explicitly specified (no default filter)
        if settings.accreditation_status:
            await self._select_filter_dropdown("Статус", settings.accreditation_status, dropdown_index=2)

        # Apply degree level filter (Рівень вищої освіти - uses standard HTML select, not multiselect)
        if settings.degree_level:
            await self._select_degree_level(settings.degree_level)

        # Apply knowledge area filter (Галузь знань)
        if settings.knowledge_area:
            await self._fill_filter_input("Галузь знань", settings.knowledge_area)

        # Apply institution name filter (Назва університету)
        if settings.institution_name:
            await self._fill_filter_input("Назва університету", settings.institution_name)

        # Apply program name filter (Назва програми)
        if settings.program_name:
            await self._fill_filter_input("Назва програми", settings.program_name)

        await self.browser.human_delay()

        # Step 4: Click "Застосувати" (Apply) button
        logger.info("Clicking Apply button")
        apply_btn = self.page.locator('button:has-text("Застосувати")')
        if await apply_btn.count() > 0:
            await apply_btn.click()
            await self.page.wait_for_timeout(2000)
            logger.info("Filter applied")
        else:
            # Try closing with Escape if no apply button
            await self.page.keyboard.press("Escape")
            await self.page.wait_for_timeout(2000)

        # Wait for table to update
        await self._wait_for_table_load()

        # Step 5: Paginate through all results and collect URLs
        page_num = 1
        while True:
            logger.info(f"Processing results page {page_num}")

            # Find all case rows in the table
            case_elements = await self._find_case_rows()
            logger.info(f"Found {len(case_elements)} cases on page {page_num}")

            for element in case_elements:
                try:
                    case_url = await self._extract_case_info_from_row(element)
                    if case_url:
                        case_urls.append(case_url)
                        logger.debug(f"Found case: {case_url.case_id}")

                        # Check if we've collected enough
                        if max_cases and len(case_urls) >= max_cases:
                            logger.info(f"Reached max_cases limit ({max_cases})")
                            return case_urls

                except Exception as e:
                    logger.warning(f"Failed to extract case info: {e}")

            # Check for next page
            has_next = await self._go_to_next_page()
            if not has_next:
                break

            page_num += 1
            await self.browser.human_delay()

        logger.info(f"Collected {len(case_urls)} case URLs")
        return case_urls

    async def _select_filter_dropdown(self, label: str, value: str, dropdown_index: int = 0) -> bool:
        """Select a value from a filter dropdown (multiselect with checkboxes)

        Args:
            label: Label for logging
            value: Value to select
            dropdown_index: Index of the multiselect dropdown (0=Specialty, 1=Expert council, 2=Status)
        """
        logger.info(f"Selecting {label}: {value} (dropdown index {dropdown_index})")

        try:
            # The NAQA site uses multiselect-dropdown components
            # Dropdown 0: Спеціальність
            # Dropdown 1: Галузева експертна рада
            # Dropdown 2: Статус

            dropdowns = await self.page.locator(".multiselect-dropdown").all()
            if dropdown_index >= len(dropdowns):
                logger.warning(f"Dropdown index {dropdown_index} out of range (found {len(dropdowns)})")
                return False

            dropdown = dropdowns[dropdown_index]

            # Click to open dropdown
            await dropdown.click()
            await self.page.wait_for_timeout(500)

            # First, clear all selections by clicking "Deselect All" if available
            deselect_all = self.page.locator('text="Deselect All", text="Скасувати все"')
            if await deselect_all.count() > 0:
                await deselect_all.first.click()
                await self.page.wait_for_timeout(300)
                logger.info("Cleared all selections")

            # Find and click the checkbox item with the value
            checkbox_item = self.page.locator(f'.multiselect-item-checkbox:has-text("{value}")')

            if await checkbox_item.count() > 0:
                await checkbox_item.first.click()
                await self.page.wait_for_timeout(500)
                logger.info(f"Selected {label}: {value}")

                # Close dropdown by clicking on dropdown header again
                await dropdown.click()
                await self.page.wait_for_timeout(500)
                return True
            else:
                # Try matching by code only (e.g., "022" from "022 Дизайн")
                code = value.split()[0] if " " in value else value
                checkbox_item = self.page.locator(f'.multiselect-item-checkbox:has-text("{code}")')

                if await checkbox_item.count() > 0:
                    await checkbox_item.first.click()
                    await self.page.wait_for_timeout(500)
                    logger.info(f"Selected {label} by code: {code}")
                    # Close dropdown
                    await dropdown.click()
                    await self.page.wait_for_timeout(500)
                    return True

            logger.warning(f"Option '{value}' not found in multiselect")
            # Close dropdown
            await dropdown.click()
            await self.page.wait_for_timeout(300)
            return False

        except Exception as e:
            logger.warning(f"Error selecting {label}: {e}")
            return False

    async def _select_status_filter(self, status_pattern: str) -> bool:
        """Select status filter to find cases with Form SE (completed cases)"""
        # Status dropdown is index 2
        # Select statuses like "20.1. Рішення НА підписане" to find completed cases
        return await self._select_filter_dropdown("Статус", status_pattern, dropdown_index=2)

    async def _select_degree_level(self, degree_level: str) -> bool:
        """Select degree level from HTML select element (not multiselect)

        The degree level filter uses a standard HTML <select> element with options:
        - value="1": Бакалавр
        - value="2": Доктор наук
        - value="3": Доктор філософії
        - value="4": Магістр
        - value="5": Молодший бакалавр
        - value="6": Молодший спеціаліст
        - value="7": Спеціаліст
        - value="8": Доктор мистецтва
        """
        logger.info(f"Selecting Рівень вищої освіти: {degree_level}")

        try:
            # Find the select element after the "Рівень вищої освіти" label
            select_elem = self.page.locator(
                'label:has-text("Рівень вищої освіти") ~ .input-group select, '
                'label:has-text("Рівень вищої освіти") + * select'
            )

            if await select_elem.count() == 0:
                # Try alternative: find select in the same parent container
                select_elem = self.page.locator(
                    'div:has(label:has-text("Рівень вищої освіти")) select.form-control'
                )

            if await select_elem.count() > 0:
                # Select by visible text (label)
                await select_elem.first.select_option(label=degree_level)
                await self.page.wait_for_timeout(500)
                logger.info(f"Selected Рівень вищої освіти: {degree_level}")
                return True
            else:
                logger.warning("Degree level select element not found")
                return False

        except Exception as e:
            logger.warning(f"Error selecting degree level: {e}")
            return False

    async def _fill_filter_input(self, label: str, value: str) -> bool:
        """Fill a filter text input by label"""
        logger.info(f"Filling {label}: {value}")

        try:
            # Find input near the label
            input_elem = self.page.locator(
                f"xpath=//*[contains(text(),'{label}')]/following::input[1]"
            )

            if await input_elem.count() > 0:
                await input_elem.fill(value)
                await self.page.wait_for_timeout(300)
                logger.info(f"Filled {label}: {value}")
                return True

            logger.warning(f"Input for '{label}' not found")
            return False

        except Exception as e:
            logger.warning(f"Error filling {label}: {e}")
            return False

    async def _wait_for_table_load(self) -> None:
        """Wait for the data table to load/update"""
        try:
            # Wait for table rows to appear
            await self.page.wait_for_selector("table tbody tr, .table tbody tr", timeout=10000)
            await self.page.wait_for_timeout(1000)
        except Exception:
            logger.warning("Timeout waiting for table to load")

    async def _find_case_rows(self):
        """Find all case rows in the table"""
        # The table has rows with case data
        # Each row has "Перейти на сторінку акредитаційної справи" link
        rows = await self.page.locator("table tbody tr, tbody tr").all()
        if rows:
            logger.debug(f"Found {len(rows)} table rows")
            return rows

        logger.warning("No table rows found")
        return []

    async def _extract_case_info_from_row(self, row) -> CaseUrl | None:
        """Extract case information from a table row"""
        try:
            # Extract case ID from first cell
            cells = await row.locator("td").all()
            if len(cells) < 7:
                return None

            case_id = await cells[0].text_content() or ""
            case_id = case_id.strip()

            if not case_id:
                return None

            # Extract other info from cells
            # 0: ID, 1: Номер AC, 2: ID ЄДЕБО, 3: Назва університету,
            # 4: Рівень, 5: Галузь, 6: Спеціальність, 7: Назва програми, 8: Статус, 9: Link
            institution_name = await cells[3].text_content() or ""
            specialty = await cells[6].text_content() or ""
            program_name = await cells[7].text_content() if len(cells) > 7 else ""

            # The link uses JavaScript navigation, so we construct URL from case ID
            # URL pattern: /v2/accreditation-folder/{case_id}
            case_url = f"{settings.base_url}/v2/accreditation-folder/{case_id}"

            return CaseUrl(
                case_url=case_url,
                case_id=case_id,
                institution_name=institution_name.strip(),
                program_name=program_name.strip() if program_name else "",
            )

        except Exception as e:
            logger.debug(f"Error extracting case info from row: {e}")
            return None

    async def _go_to_next_page(self) -> bool:
        """Navigate to next page if available"""
        try:
            # Look for pagination controls
            # Common patterns: next button, page numbers, arrow buttons
            next_selectors = [
                'button:has-text(">")',
                'a:has-text(">")',
                '.pagination-next',
                '[aria-label="Next"]',
                'button[aria-label*="next"]',
                '.next-page',
                'li.next a',
                'a[rel="next"]',
            ]

            for selector in next_selectors:
                try:
                    next_btn = self.page.locator(selector)
                    if await next_btn.count() > 0:
                        is_disabled = await next_btn.get_attribute("disabled")
                        aria_disabled = await next_btn.get_attribute("aria-disabled")
                        class_attr = await next_btn.get_attribute("class") or ""

                        if is_disabled or aria_disabled == "true" or "disabled" in class_attr:
                            return False

                        await next_btn.click()
                        await self._wait_for_table_load()
                        return True
                except Exception:
                    continue

            # Also check for numbered pagination
            # Try to find current page and click next number
            current_page = self.page.locator('.pagination .active, [aria-current="page"]')
            if await current_page.count() > 0:
                current_text = await current_page.text_content()
                if current_text and current_text.isdigit():
                    next_num = int(current_text) + 1
                    next_page_link = self.page.locator(f'.pagination a:has-text("{next_num}")')
                    if await next_page_link.count() > 0:
                        await next_page_link.click()
                        await self._wait_for_table_load()
                        return True

            return False

        except Exception as e:
            logger.debug(f"Error navigating to next page: {e}")
            return False

    async def navigate_to_case(self, case_url: str) -> bool:
        """Navigate to a specific case page"""
        try:
            await self.browser.rate_limited_navigate(case_url)
            await self.page.wait_for_timeout(1000)
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to case {case_url}: {e}")
            return False

    async def find_form_se_url(self) -> str | None:
        """Find the Form SE URL on the case page and navigate to it"""
        # On NAQA site, the Form SE button is inside a collapsible section
        # First expand "Відомості про СО і додатки до них" section

        # Try to expand the section containing Form SE button
        section_headers = [
            'button:has-text("Відомості про СО")',
            'button:has-text("СО і додатки")',
            '[class*="accordion"]:has-text("Відомості")',
        ]

        for selector in section_headers:
            try:
                section = self.page.locator(selector)
                if await section.count() > 0:
                    logger.info(f"Expanding section: {selector}")
                    await section.first.click()
                    await self.page.wait_for_timeout(1000)
                    break
            except Exception:
                continue

        # Now find and click the Form SE button
        form_selectors = [
            'button:has-text("Переглянути форму СО")',
            'button:has-text("форму СО")',
            'a:has-text("Переглянути форму СО")',
            'a:has-text("форму СО")',
            'a[href*="form-se"]',
        ]

        for selector in form_selectors:
            try:
                elem = self.page.locator(selector)
                if await elem.count() > 0:
                    # Check if visible
                    is_visible = await elem.first.is_visible()
                    if not is_visible:
                        logger.debug(f"Form SE button not visible: {selector}")
                        continue

                    logger.info(f"Clicking Form SE button: {selector}")
                    await elem.first.click()
                    await self.page.wait_for_timeout(3000)  # Wait for navigation

                    # Get the current URL after navigation
                    current_url = self.page.url
                    if "form-se" in current_url:
                        logger.info(f"Navigated to Form SE: {current_url}")
                        return current_url

                    # If URL didn't change, try to find href
                    href = await elem.first.get_attribute("href")
                    if href:
                        full_url = urljoin(settings.base_url, href)
                        logger.info(f"Found Form SE URL: {full_url}")
                        return full_url

            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        # Fallback: try direct URL access using case_id from current URL
        # URL pattern: /v2/accreditation-folder/{case_id} -> /v2/form-se/{case_id}/view
        try:
            current_url = self.page.url
            if "/accreditation-folder/" in current_url:
                case_id = current_url.split("/accreditation-folder/")[-1].split("/")[0].split("?")[0]
                direct_url = f"{settings.base_url}/v2/form-se/{case_id}/view"
                logger.info(f"Trying direct Form SE URL: {direct_url}")

                await self.browser.rate_limited_navigate(direct_url)
                await self.page.wait_for_timeout(2000)

                # Check if page loaded successfully (look for tabs or form content)
                tabs = await self.page.locator('[role="tab"]').count()
                if tabs > 0:
                    logger.info(f"Successfully accessed Form SE via direct URL: {direct_url}")
                    return direct_url
                else:
                    logger.warning(f"Direct URL did not load Form SE content")
        except Exception as e:
            logger.warning(f"Direct URL fallback failed: {e}")

        logger.warning("Form SE link/button not found on case page")
        return None

    async def navigate_to_form(self, form_url: str) -> bool:
        """Navigate to the Form SE page"""
        try:
            await self.browser.rate_limited_navigate(form_url)
            await self.browser.wait_for_load()
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to form {form_url}: {e}")
            return False

    async def click_tab(self, tab_number: int) -> bool:
        """Click on a specific tab (1-11)"""
        tab_selectors = [
            f'[data-tab="{tab_number}"]',
            f'button:has-text("Таблиця {tab_number}")',
            f'a:has-text("Таблиця {tab_number}")',
            f'.tab-{tab_number}',
            f'[role="tab"]:nth-child({tab_number})',
            f'.tabs button:nth-child({tab_number})',
            f'.tabs a:nth-child({tab_number})',
        ]

        for selector in tab_selectors:
            try:
                tab_elem = self.page.locator(selector)
                if await tab_elem.count() > 0:
                    await tab_elem.click()
                    await self.page.wait_for_timeout(1000)
                    logger.debug(f"Clicked tab {tab_number} using: {selector}")
                    return True
            except Exception:
                continue

        logger.warning(f"Could not click tab {tab_number}")
        return False

    async def get_current_url(self) -> str:
        """Get current page URL"""
        return self.page.url

    async def extract_basic_case_info(self) -> dict:
        """Extract basic information from case page header"""
        info = {
            "institution_name": "",
            "program_name": "",
            "specialty": "",
            "degree_level": "",
            "status": "",
        }

        # Try to extract from common header patterns
        selectors = {
            "institution_name": [".institution-name", "h1", ".header-title", '[class*="university"]'],
            "program_name": [".program-name", "h2", ".subtitle", '[class*="program"]'],
            "specialty": [':has-text("Спеціальність")', ".specialty", '[class*="specialty"]'],
            "degree_level": [':has-text("Рівень")', ".degree-level", '[class*="degree"]'],
            "status": [".accreditation-status", ".status-badge", '[class*="status"]'],
        }

        for field, sel_list in selectors.items():
            for selector in sel_list:
                try:
                    elem = self.page.locator(selector)
                    if await elem.count() > 0:
                        text = await elem.first.text_content()
                        if text:
                            info[field] = text.strip()
                            break
                except Exception:
                    continue

        return info
