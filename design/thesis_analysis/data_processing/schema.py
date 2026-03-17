"""
Pydantic models for thesis analysis data structures.

Defines schemas for programs, courses, competencies, and form data
extracted from NAQA accreditation cases.
"""

from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel, Field


class EducationalComponent(BaseModel):
    """Single educational component (course/module) from Tab 12."""

    component_code: str = Field(default="", description="Component code (e.g., 'ОА.01')")
    name: str = Field(..., description="Full name of the component")
    component_type: str = Field(
        default="",
        description="Type: обов'язкова, вибіркова, практика, підсумкова атестація"
    )
    credits: Optional[float] = Field(default=None, description="ECTS credits")
    semester: Optional[int] = Field(default=None, description="Semester number")
    syllabus_file: str = Field(default="", description="Syllabus PDF filename")
    material_base: str = Field(default="", description="Material/technical base info")


class Course(BaseModel):
    """Normalized course record for analysis."""

    case_id: str = Field(..., description="Parent case ID")
    course_id: str = Field(default="", description="Unique course identifier")
    name: str = Field(..., description="Course name")
    name_normalized: str = Field(default="", description="Normalized/lemmatized name")
    credits: Optional[float] = Field(default=None, description="ECTS credits")
    course_type: str = Field(
        default="required",
        description="required, elective, practice, attestation"
    )
    semester: Optional[int] = Field(default=None, description="Semester number")
    syllabus_text: str = Field(default="", description="Extracted syllabus text")
    has_syllabus: bool = Field(default=False, description="Whether syllabus exists")


class Competency(BaseModel):
    """Competency from Tab 14 (competency matrix)."""

    code: str = Field(..., description="Competency code (e.g., 'ЗК1', 'ФК2')")
    description: str = Field(default="", description="Competency description")
    competency_type: str = Field(
        default="general",
        description="general (ЗК) or professional (ФК)"
    )
    mapped_courses: List[str] = Field(
        default_factory=list,
        description="Course codes/names that cover this competency"
    )


class FormSETab(BaseModel):
    """Single tab content from Form SE document."""

    tab_number: int = Field(..., description="Tab index (0-15)")
    tab_title: str = Field(default="", description="Tab title in Ukrainian")
    full_text: str = Field(default="", description="Full text content of the tab")
    all_fields: Dict[str, str] = Field(
        default_factory=dict,
        description="Key-value fields extracted from tab"
    )
    all_tables: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Tables extracted from tab"
    )


class FormSE(BaseModel):
    """Complete Form SE document with all 16 tabs."""

    form_id: str = Field(..., description="Form ID (same as case_id)")
    form_url: str = Field(default="", description="URL to Form SE page")
    tabs: List[FormSETab] = Field(default_factory=list, description="All 16 tabs")

    def get_tab(self, tab_number: int) -> Optional[FormSETab]:
        """Get specific tab by number."""
        for tab in self.tabs:
            if tab.tab_number == tab_number:
                return tab
        return None

    def get_general_info(self) -> Optional[FormSETab]:
        """Get Tab 0: General information."""
        return self.get_tab(0)

    def get_educational_components_tab(self) -> Optional[FormSETab]:
        """Get Tab 12: Educational components table."""
        return self.get_tab(12)

    def get_teachers_tab(self) -> Optional[FormSETab]:
        """Get Tab 13: Teachers table."""
        return self.get_tab(13)

    def get_competency_matrix_tab(self) -> Optional[FormSETab]:
        """Get Tab 14: Competency-course matrix."""
        return self.get_tab(14)


class Program(BaseModel):
    """Educational program extracted from accreditation case."""

    case_id: str = Field(..., description="Unique case identifier")
    institution_name: str = Field(default="", description="Higher education institution name")
    program_name: str = Field(default="", description="Educational program name")
    specialty_code: str = Field(default="022", description="Specialty code")
    specialty_name: str = Field(default="Дизайн", description="Specialty name")
    degree_level: str = Field(
        default="bachelor",
        description="Degree level: bachelor, master, phd"
    )
    degree_level_ukrainian: str = Field(
        default="Бакалавр",
        description="Degree level in Ukrainian"
    )
    program_type: str = Field(
        default="",
        description="Program type (освітньо-професійна, освітньо-наукова)"
    )
    accreditation_date: Optional[date] = Field(
        default=None,
        description="Accreditation decision date"
    )
    valid_until: Optional[date] = Field(
        default=None,
        description="Accreditation valid until date"
    )
    status: str = Field(default="", description="Accreditation status")
    region: str = Field(default="", description="Region of institution")
    institution_type: str = Field(default="", description="Type of institution")
    total_credits: float = Field(default=240.0, description="Total ECTS credits")
    num_courses: int = Field(default=0, description="Number of educational components")
    num_required: int = Field(default=0, description="Number of required courses")
    num_elective: int = Field(default=0, description="Number of elective courses")


class AccreditationCase(BaseModel):
    """Complete accreditation case with all data."""

    case_id: str = Field(..., description="Unique case identifier")
    case_url: str = Field(default="", description="URL to accreditation folder")
    program: Program = Field(..., description="Program information")
    form_se: Optional[FormSE] = Field(default=None, description="Form SE document")
    courses: List[Course] = Field(
        default_factory=list,
        description="Educational components/courses"
    )
    competencies: List[Competency] = Field(
        default_factory=list,
        description="Competencies from matrix"
    )
    downloaded_files: List[str] = Field(
        default_factory=list,
        description="List of downloaded PDF files"
    )
    raw_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Original raw JSON data"
    )

    class Config:
        extra = "allow"
