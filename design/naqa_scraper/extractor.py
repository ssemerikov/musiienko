"""Form and table data extraction from NAQA pages"""

import logging
import re
from typing import Any

from playwright.async_api import Locator, Page

from .models import (
    EducationalComponent,
    FormSE,
    TabContent,
    TableData,
    TableRow,
)

logger = logging.getLogger(__name__)


class Extractor:
    """Extracts all data from Form SE pages"""

    # Tab structure based on actual page:
    # Tab 0: "Загальні відомості" (General info)
    # Tabs 1-11: Sections 1-11 (criteria)
    # Tab 12: "Таблиця 1" (Educational components)
    # Tab 13: "Таблиця 2" (Teachers)
    # Tab 14: "Таблиця 3" (Matrix)
    # Tab 15: "Запевнення" (Assurance)

    TAB_NAMES = {
        0: "Загальні відомості",
        1: "1. Проєктування освітньої програми",
        2: "2. Структура та зміст освітньої програми",
        3: "3. Доступ до освітньої програми та визнання результатів навчання",
        4: "4. Навчання і викладання за освітньою програмою",
        5: "5. Контрольні заходи, оцінювання здобувачів вищої освіти та академічна доброчесність",
        6: "6. Людські ресурси",
        7: "7. Освітнє середовище та матеріальні ресурси",
        8: "8. Внутрішнє забезпечення якості освітньої програми",
        9: "9. Прозорість і публічність",
        10: "10. Навчання через дослідження",
        11: "11. Перспективи подальшого розвитку ОП",
        12: "Таблиця 1. Інформація про обов'язкові освітні компоненти ОП",
        13: "Таблиця 2. Зведена інформація про викладачів",
        14: "Таблиця 3. Матриця відповідності",
        15: "Запевнення",
    }

    def __init__(self, page: Page):
        self.page = page
        self._role_tabs: list | None = None

    async def _get_role_tabs(self) -> list:
        """Get all tabs using role='tab' selector (cached)"""
        if self._role_tabs is None:
            # Wait for page to load and tabs to appear
            try:
                await self.page.wait_for_selector('[role="tab"]', timeout=10000)
            except Exception as e:
                logger.warning(f"Timeout waiting for tabs: {e}")
            self._role_tabs = await self.page.locator('[role="tab"]').all()
        return self._role_tabs

    async def extract_form_se(self, form_id: str, form_url: str) -> FormSE:
        """Extract complete Form SE data including all tabs"""
        logger.info(f"Extracting Form SE: {form_id}")

        form_se = FormSE(form_id=form_id, form_url=form_url)

        # Wait for page to fully load
        await self.page.wait_for_timeout(3000)

        # Extract raw page text as backup
        try:
            form_se.raw_page_text = await self.page.locator("body").text_content() or ""
        except Exception as e:
            logger.warning(f"Failed to extract raw page text: {e}")

        # Get all tabs
        role_tabs = await self._get_role_tabs()
        logger.info(f"Found {len(role_tabs)} tabs on page")

        # Extract all tabs (0-15 or however many exist)
        form_se.tabs = await self.extract_all_tabs()

        # Extract Table 1 - educational components (from tab 12)
        form_se.table1_components = await self.extract_table1_components()

        # Extract all tables on the page
        form_se.all_tables = await self.extract_all_tables()

        logger.info(
            f"Extracted {len(form_se.tabs)} tabs, "
            f"{len(form_se.table1_components)} components, "
            f"{len(form_se.all_tables)} tables"
        )

        return form_se

    async def extract_all_tabs(self) -> list[TabContent]:
        """Extract content from all tabs using [role='tab'] selector"""
        tabs_data: list[TabContent] = []
        role_tabs = await self._get_role_tabs()

        for tab_idx in range(len(role_tabs)):
            logger.debug(f"Extracting tab {tab_idx}")
            tab_content = await self._extract_single_tab(tab_idx)
            tabs_data.append(tab_content)

        return tabs_data

    async def _extract_single_tab(self, tab_idx: int) -> TabContent:
        """Extract all content from a single tab using its index"""
        tab_content = TabContent(tab_number=tab_idx)

        # Click on the tab using role="tab" selector
        clicked = await self._click_tab(tab_idx)
        if not clicked:
            logger.warning(f"Could not click tab {tab_idx}, extracting visible content")

        await self.page.wait_for_timeout(1500)  # Wait for content to load

        # Get tab title from the tab element itself
        role_tabs = await self._get_role_tabs()
        if tab_idx < len(role_tabs):
            try:
                tab_content.tab_title = await role_tabs[tab_idx].text_content() or ""
                tab_content.tab_title = tab_content.tab_title.strip()
            except Exception:
                tab_content.tab_title = self.TAB_NAMES.get(tab_idx, f"Tab {tab_idx}")

        # Find tab content container - use visible tabpanel
        content_container = None
        try:
            panel = self.page.locator('[role="tabpanel"]:visible, .tab-pane.active')
            if await panel.count() > 0:
                content_container = panel.first
        except Exception:
            pass

        if content_container is None:
            # Fallback to main content area
            content_container = self.page.locator("main, .main-content, body").first

        # Extract full text content
        try:
            tab_content.full_text = await content_container.text_content() or ""
        except Exception as e:
            logger.warning(f"Failed to extract tab {tab_idx} text: {e}")

        # Extract full HTML
        try:
            tab_content.full_html = await content_container.inner_html()
        except Exception as e:
            logger.warning(f"Failed to extract tab {tab_idx} HTML: {e}")

        # Extract all field label:value pairs
        tab_content.all_fields = await self._extract_fields(content_container)

        # Extract all tables in this tab
        tab_content.all_tables = await self._extract_tables_from_container(content_container)

        # Find all file links in this tab (note: most files are text-only, not downloadable)
        file_links = await self._find_file_links(content_container)
        for link_info in file_links:
            tab_content.all_files.append(link_info)

        # Also extract PDF filenames from text (they appear as text, not links)
        pdf_filenames = await self._extract_pdf_filenames(content_container)
        for filename in pdf_filenames:
            tab_content.all_files.append({"text": filename, "url": None, "type": "filename_only"})

        logger.debug(
            f"Tab {tab_idx}: {len(tab_content.all_fields)} fields, "
            f"{len(tab_content.all_tables)} tables, {len(tab_content.all_files)} files"
        )

        return tab_content

    async def _click_tab(self, tab_idx: int) -> bool:
        """Click on a tab by its index using [role='tab'] selector"""
        try:
            role_tabs = await self._get_role_tabs()
            if tab_idx < len(role_tabs):
                await role_tabs[tab_idx].click()
                return True
        except Exception as e:
            logger.debug(f"Failed to click tab {tab_idx}: {e}")
        return False

    async def _extract_pdf_filenames(self, container: Locator) -> list[str]:
        """Extract PDF filenames from text content (they may not be links)"""
        filenames: list[str] = []
        try:
            text = await container.text_content() or ""
            # Find .pdf mentions
            import re
            pattern = r'([А-ЯІЇЄҐа-яіїєґA-Za-z0-9_\-\s\.]+\.pdf)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                filename = match.strip()
                if filename and len(filename) > 5:  # Skip very short matches
                    filenames.append(filename)
        except Exception:
            pass
        return list(set(filenames))  # Remove duplicates

    async def _extract_fields(self, container: Locator) -> dict[str, str]:
        """Extract all label:value pairs from a container"""
        fields: dict[str, str] = {}

        # Common patterns for field rows
        field_selectors = [
            ".field-row",
            ".form-field",
            ".form-group",
            ".info-row",
            "dl dt, dl dd",  # Definition lists
            "tr",  # Table rows as fields
        ]

        # Try structured field extraction
        for selector in field_selectors[:4]:  # Skip table rows for now
            try:
                field_elements = await container.locator(selector).all()
                for field_elem in field_elements:
                    label = await self._extract_label(field_elem)
                    value = await self._extract_value(field_elem)
                    if label and value:
                        fields[label.strip()] = value.strip()
            except Exception:
                continue

        # Also extract from definition lists
        try:
            dt_elements = await container.locator("dt").all()
            dd_elements = await container.locator("dd").all()
            for dt, dd in zip(dt_elements, dd_elements):
                label = await dt.text_content() or ""
                value = await dd.text_content() or ""
                if label and value:
                    fields[label.strip()] = value.strip()
        except Exception:
            pass

        # Extract from text content using regex patterns
        try:
            text = await container.text_content() or ""
            # Pattern: "Label: Value" or "Label - Value"
            pattern = r"([А-ЯІЇЄҐа-яіїєґA-Za-z\s\(\)]+)[\:\-]\s*([^\n]+)"
            matches = re.findall(pattern, text)
            for label, value in matches:
                if label.strip() and value.strip():
                    fields[label.strip()] = value.strip()
        except Exception:
            pass

        return fields

    async def _extract_label(self, elem: Locator) -> str:
        """Extract label from a field element"""
        label_selectors = [".label", "label", ".field-label", "strong", "b", "th"]
        for selector in label_selectors:
            try:
                label_elem = elem.locator(selector)
                if await label_elem.count() > 0:
                    return await label_elem.first.text_content() or ""
            except Exception:
                continue
        return ""

    async def _extract_value(self, elem: Locator) -> str:
        """Extract value from a field element"""
        value_selectors = [".value", ".field-value", "span", "p", "td"]
        for selector in value_selectors:
            try:
                value_elem = elem.locator(selector)
                if await value_elem.count() > 0:
                    return await value_elem.first.text_content() or ""
            except Exception:
                continue

        # Fallback to full element text minus any label
        try:
            full_text = await elem.text_content() or ""
            return full_text
        except Exception:
            return ""

    async def _extract_tables_from_container(self, container: Locator) -> list[TableData]:
        """Extract all tables from a container"""
        tables: list[TableData] = []

        try:
            table_elements = await container.locator("table").all()
            for idx, table_elem in enumerate(table_elements):
                table_data = await self._extract_full_table(table_elem, idx)
                tables.append(table_data)
        except Exception as e:
            logger.warning(f"Error extracting tables: {e}")

        return tables

    async def _extract_full_table(self, table_element: Locator, table_index: int = 0) -> TableData:
        """Extract complete table with headers and all rows"""
        table_data = TableData(table_index=table_index)

        # Get table caption/title
        try:
            caption_elem = table_element.locator("caption, .table-title, thead tr:first-child")
            if await caption_elem.count() > 0:
                table_data.caption = await caption_elem.first.text_content() or ""
        except Exception:
            pass

        # Get headers
        try:
            header_cells = await table_element.locator("thead th, tr:first-child th").all()
            for cell in header_cells:
                text = await cell.text_content() or ""
                table_data.headers.append(text.strip())
        except Exception:
            pass

        # Get all rows
        try:
            row_elements = await table_element.locator("tbody tr, tr:not(:first-child)").all()
            for row_idx, row_elem in enumerate(row_elements):
                row_data = TableRow(row_index=row_idx)

                # Get cell texts
                cells = await row_elem.locator("td, th").all()
                for cell in cells:
                    text = await cell.text_content() or ""
                    html = await cell.inner_html()
                    row_data.cells.append(text.strip())
                    row_data.cell_html.append(html)

                    # Find file links in cell
                    file_links = await self._find_file_links_in_element(cell)
                    row_data.file_links.extend(file_links)

                table_data.rows.append(row_data)

            table_data.row_count = len(table_data.rows)
        except Exception as e:
            logger.warning(f"Error extracting table rows: {e}")

        return table_data

    async def extract_all_tables(self) -> list[TableData]:
        """Extract all tables from the entire page"""
        tables: list[TableData] = []

        try:
            table_elements = await self.page.locator("table").all()
            for idx, table_elem in enumerate(table_elements):
                table_data = await self._extract_full_table(table_elem, idx)
                tables.append(table_data)
        except Exception as e:
            logger.warning(f"Error extracting all tables: {e}")

        return tables

    async def extract_table1_components(self) -> list[EducationalComponent]:
        """Extract Table 1 - educational components (from Tab 12)"""
        components: list[EducationalComponent] = []

        # First, click on Tab 12 (Таблиця 1)
        role_tabs = await self._get_role_tabs()
        if len(role_tabs) > 12:
            logger.info("Clicking Tab 12 (Таблиця 1) to access educational components")
            try:
                await role_tabs[12].click()
                await self.page.wait_for_timeout(2000)
            except Exception as e:
                logger.warning(f"Failed to click Tab 12: {e}")

        # Try to find Table 1 within the visible tabpanel
        table_element = None

        # First try to find table in the visible tabpanel
        try:
            panel = self.page.locator('[role="tabpanel"]:visible, .tab-pane.active')
            if await panel.count() > 0:
                table = panel.first.locator("table")
                if await table.count() > 0:
                    table_element = table.first
                    logger.info("Found Table 1 in visible tabpanel")
        except Exception:
            pass

        # Fallback selectors
        if table_element is None:
            table1_selectors = [
                'table:has-text("Назва освітнього компонента")',
                'table:has-text("обов\'язкові освітні компоненти")',
                'table:has-text("Інформація про обов")',
                ".table-1",
                "#table-1",
            ]

            for selector in table1_selectors:
                try:
                    elem = self.page.locator(selector)
                    if await elem.count() > 0:
                        table_element = elem.first
                        break
                except Exception:
                    continue

        if table_element is None:
            logger.warning("Table 1 (educational components) not found")
            return components

        # Extract headers to understand column mapping
        headers: list[str] = []
        try:
            header_cells = await table_element.locator("thead th, tr:first-child th").all()
            for cell in header_cells:
                text = await cell.text_content() or ""
                headers.append(text.strip().lower())
        except Exception:
            pass

        # Map common column names to indices
        # Actual columns: Назва освітнього компонента | Вид компонента | Поле для завантаження | Відомості щодо МТЗ
        column_map = {}
        for idx, header in enumerate(headers):
            header_lower = header.lower()
            if "назва" in header_lower and "компонент" in header_lower:
                column_map["name"] = idx
            elif "вид" in header_lower and "компонент" in header_lower:
                column_map["type"] = idx
            elif "тип" in header_lower:
                column_map["type"] = idx
            elif "кредит" in header_lower:
                column_map["credits"] = idx
            elif "годин" in header_lower:
                column_map["hours"] = idx
            elif "контрол" in header_lower:
                column_map["control"] = idx
            elif "завантаж" in header_lower:
                column_map["download"] = idx
            elif "мтз" in header_lower or "матеріально" in header_lower:
                column_map["resources"] = idx

        logger.debug(f"Table 1 column mapping: {column_map}")

        # Extract rows
        try:
            row_elements = await table_element.locator("tbody tr").all()
            for row_idx, row_elem in enumerate(row_elements):
                component = EducationalComponent(row_index=row_idx)

                cells = await row_elem.locator("td").all()
                cell_texts = []
                for cell in cells:
                    text = await cell.text_content() or ""
                    cell_texts.append(text.strip())

                # Fill component data based on column mapping
                if "name" in column_map and column_map["name"] < len(cell_texts):
                    component.component_name = cell_texts[column_map["name"]]
                if "type" in column_map and column_map["type"] < len(cell_texts):
                    component.component_type = cell_texts[column_map["type"]]
                if "credits" in column_map and column_map["credits"] < len(cell_texts):
                    component.credits = cell_texts[column_map["credits"]]
                if "hours" in column_map and column_map["hours"] < len(cell_texts):
                    component.hours = cell_texts[column_map["hours"]]
                if "control" in column_map and column_map["control"] < len(cell_texts):
                    component.control_form = cell_texts[column_map["control"]]

                # Store all columns
                for idx, text in enumerate(cell_texts):
                    header_name = headers[idx] if idx < len(headers) else f"column_{idx}"
                    component.all_columns[header_name] = text

                # Get syllabus filename from download column (it's text, not a link)
                if "download" in column_map and column_map["download"] < len(cell_texts):
                    syllabus_text = cell_texts[column_map["download"]]
                    if syllabus_text and ".pdf" in syllabus_text.lower():
                        component.syllabus_filename = syllabus_text.strip()
                        component.has_syllabus = True

                # Get resources/МТЗ info
                if "resources" in column_map and column_map["resources"] < len(cell_texts):
                    component.resources = cell_texts[column_map["resources"]]

                # Find any actual download links in this row (though usually none exist)
                file_links = await self._find_file_links_in_element(row_elem)
                # Note: actual download handled separately

                if component.component_name:
                    components.append(component)

        except Exception as e:
            logger.warning(f"Error extracting Table 1 components: {e}")

        logger.info(f"Extracted {len(components)} educational components from Table 1")
        return components

    async def _find_file_links(self, container: Locator) -> list[dict]:
        """Find all file download links in a container"""
        return await self._find_file_links_in_element(container)

    async def _find_file_links_in_element(self, element: Locator) -> list[dict]:
        """Find file download links within an element"""
        file_links: list[dict] = []

        link_selectors = [
            'a[href*="download"]',
            'a[href$=".pdf"]',
            'a[href$=".doc"]',
            'a[href$=".docx"]',
            'a[href$=".xls"]',
            'a[href$=".xlsx"]',
            'a[href*="file"]',
            'a[href*="document"]',
        ]

        seen_urls = set()
        for selector in link_selectors:
            try:
                links = await element.locator(selector).all()
                for link in links:
                    url = await link.get_attribute("href")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        text = await link.text_content() or ""
                        file_links.append({"url": url, "text": text.strip()})
            except Exception:
                continue

        return file_links

    async def extract_main_document_links(self) -> dict[str, list[dict]]:
        """Find main document links (Освітня програма, Навчальний план)"""
        main_docs: dict[str, list[dict]] = {
            "освітня_програма": [],
            "навчальний_план": [],
            "other": [],
        }

        # Look for main document fields
        doc_patterns = [
            ("освітня_програма", ["Освітня програма", "освітня програма", "ОП"]),
            ("навчальний_план", ["Навчальний план", "навчальний план", "Curriculum"]),
        ]

        for field_key, patterns in doc_patterns:
            for pattern in patterns:
                try:
                    # Find elements containing this label
                    container = self.page.locator(f':has-text("{pattern}")')
                    if await container.count() > 0:
                        links = await self._find_file_links(container.first)
                        main_docs[field_key].extend(links)
                except Exception:
                    continue

        return main_docs
