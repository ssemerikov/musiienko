"""Pydantic data models for complete data capture"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class DownloadedFile(BaseModel):
    """Represents a downloaded file with metadata"""

    original_filename: str
    local_path: str
    url: str
    link_text: str = ""  # Text of the download link
    context: str = ""  # Where found (tab, table, field name)
    size_bytes: int = 0
    downloaded_at: datetime = Field(default_factory=datetime.now)
    status: str = "success"  # success, failed, skipped
    error: Optional[str] = None


class TableRow(BaseModel):
    """Represents a single table row with all data"""

    row_index: int
    cells: list[str] = Field(default_factory=list)  # Text content of each cell
    cell_html: list[str] = Field(default_factory=list)  # HTML content of each cell
    file_links: list[dict] = Field(default_factory=list)  # Files found in this row


class TableData(BaseModel):
    """Represents a complete table with all content"""

    table_index: int = 0
    caption: str = ""  # Table title/caption
    headers: list[str] = Field(default_factory=list)  # All column headers
    rows: list[TableRow] = Field(default_factory=list)  # All rows with all cell data
    row_count: int = 0
    file_links: list[DownloadedFile] = Field(default_factory=list)  # Files in this table


class TabContent(BaseModel):
    """Represents content from a single tab (0-15)"""

    tab_number: int
    tab_title: str = ""
    full_text: str = ""  # ALL text content
    full_html: str = ""  # Raw HTML for reference
    all_fields: dict[str, str] = Field(default_factory=dict)  # ALL label:value pairs
    all_tables: list[TableData] = Field(default_factory=list)  # ALL tables in this tab
    all_files: list[dict] = Field(default_factory=list)  # File info (may be text-only filenames)


class EducationalComponent(BaseModel):
    """Represents a row from Table 1 - educational components"""

    row_index: int
    component_name: str = ""  # Назва освітнього компонента
    component_type: str = ""  # Вид компонента (навчальна дисципліна, практика, etc.)
    credits: str = ""  # Кількість кредитів
    hours: str = ""  # Кількість годин
    control_form: str = ""  # Форма контролю
    resources: str = ""  # Відомості щодо МТЗ
    syllabus_filename: str = ""  # Filename from download column (text only, not downloadable)
    has_syllabus: bool = False  # Whether syllabus filename is present
    all_columns: dict[str, str] = Field(default_factory=dict)  # ALL column values
    syllabus_files: list[DownloadedFile] = Field(default_factory=list)


class FormSE(BaseModel):
    """Complete Form SE data structure"""

    form_id: str
    form_url: str
    tabs: list[TabContent] = Field(default_factory=list)  # ALL 11 tabs with full content
    table1_components: list[EducationalComponent] = Field(
        default_factory=list
    )  # Table 1 data
    all_tables: list[TableData] = Field(default_factory=list)  # ALL other tables
    main_files: list[DownloadedFile] = Field(
        default_factory=list
    )  # Освітня програма, Навчальний план
    all_files: list[DownloadedFile] = Field(default_factory=list)  # Complete file inventory
    raw_page_text: str = ""  # Full page text backup
    extracted_at: datetime = Field(default_factory=datetime.now)


class AccreditationCase(BaseModel):
    """Complete accreditation case record"""

    case_id: str
    case_url: str
    institution_name: str = ""
    program_name: str = ""
    specialty: str = ""  # Specialty - set from filter
    degree_level: str = ""  # Рівень вищої освіти (бакалавр, магістр, PhD)
    status: str = ""  # Акредитаційний статус
    accreditation_type: str = ""  # Тип акредитації
    decision_date: str = ""  # Дата рішення
    valid_until: str = ""  # Термін дії
    region: str = ""  # Регіон
    institution_type: str = ""  # Тип закладу
    form_se: Optional[FormSE] = None  # Complete form data
    files_manifest: dict[str, Any] = Field(default_factory=dict)  # All downloaded files
    scraped_at: datetime = Field(default_factory=datetime.now)
    scrape_status: str = "pending"  # pending, completed, failed, partial
    error_message: Optional[str] = None


class ScrapeSession(BaseModel):
    """Represents a complete scraping session"""

    session_id: str
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    cases: list[AccreditationCase] = Field(default_factory=list)
    total_cases: int = 0
    completed_cases: int = 0
    failed_cases: int = 0
    total_files_downloaded: int = 0
    extraction_complete: bool = False


class CaseUrl(BaseModel):
    """URL info collected during Phase A"""

    case_url: str
    case_id: str
    form_url: Optional[str] = None
    institution_name: str = ""
    program_name: str = ""
