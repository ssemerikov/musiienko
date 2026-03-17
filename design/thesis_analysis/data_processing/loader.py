"""
Data loader for thesis analysis.

Loads accreditation case JSONs, level mappings, and extracted text files.
Builds unified DataFrames for analysis.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

import pandas as pd
from tqdm import tqdm

from ..config import settings
from .schema import (
    Program,
    Course,
    Competency,
    FormSE,
    FormSETab,
    AccreditationCase,
    EducationalComponent,
)


@dataclass
class LoadedData:
    """Container for all loaded data."""

    cases: List[AccreditationCase]
    df_programs: pd.DataFrame
    df_courses: pd.DataFrame
    df_competencies: pd.DataFrame
    level_mapping: Dict[str, List[str]]


class DataLoader:
    """Loads and processes NAQA accreditation data."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.data_dir
        self.raw_dir = self.data_dir / "raw"
        self.text_dir = self.data_dir / "text_by_level"
        self.level_mapping_path = settings.level_mapping_path
        self._level_mapping: Optional[Dict[str, List[str]]] = None

    @property
    def level_mapping(self) -> Dict[str, List[str]]:
        """Load and cache level mapping."""
        if self._level_mapping is None:
            self._level_mapping = self._load_level_mapping()
        return self._level_mapping

    def _load_level_mapping(self) -> Dict[str, List[str]]:
        """Load case ID to degree level mapping."""
        if not self.level_mapping_path.exists():
            return {"bachelor": [], "master": [], "phd": [], "unknown": []}

        with open(self.level_mapping_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_case_level(self, case_id: str) -> str:
        """Get degree level for a case ID."""
        for level, case_ids in self.level_mapping.items():
            if case_id in case_ids:
                return level
        return "unknown"

    def load_all(
        self,
        levels: Optional[List[str]] = None,
        max_cases: Optional[int] = None,
        include_text: bool = True,
    ) -> LoadedData:
        """
        Load all accreditation cases and build DataFrames.

        Args:
            levels: Filter by degree levels (bachelor, master, phd)
            max_cases: Maximum number of cases to load
            include_text: Whether to load extracted syllabus text

        Returns:
            LoadedData with cases and DataFrames
        """
        cases = self.load_cases(levels=levels, max_cases=max_cases)

        if include_text:
            self._attach_syllabus_text(cases)

        df_programs = self._build_programs_df(cases)
        df_courses = self._build_courses_df(cases)
        df_competencies = self._build_competencies_df(cases)

        return LoadedData(
            cases=cases,
            df_programs=df_programs,
            df_courses=df_courses,
            df_competencies=df_competencies,
            level_mapping=self.level_mapping,
        )

    def load_cases(
        self,
        levels: Optional[List[str]] = None,
        max_cases: Optional[int] = None,
    ) -> List[AccreditationCase]:
        """Load accreditation cases from JSON files."""
        case_files = sorted(self.raw_dir.glob("case_*.json"))

        if not case_files:
            raise FileNotFoundError(f"No case files found in {self.raw_dir}")

        # Filter by level if specified
        if levels:
            target_ids = set()
            for level in levels:
                target_ids.update(self.level_mapping.get(level, []))
            case_files = [
                f for f in case_files
                if self._extract_case_id(f.name) in target_ids
            ]

        if max_cases:
            case_files = case_files[:max_cases]

        cases = []
        for case_file in tqdm(case_files, desc="Loading cases"):
            try:
                case = self._load_single_case(case_file)
                cases.append(case)
            except Exception as e:
                print(f"Error loading {case_file}: {e}")
                continue

        return cases

    def _load_single_case(self, case_file: Path) -> AccreditationCase:
        """Load a single case from JSON file."""
        with open(case_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        case_id = raw_data.get("case_id", self._extract_case_id(case_file.name))
        level = self.get_case_level(case_id)

        # Parse program info
        program = self._parse_program(raw_data, case_id, level)

        # Parse Form SE
        form_se = self._parse_form_se(raw_data.get("form_se", {}))

        # Extract courses from Tab 12
        courses = self._extract_courses(form_se, case_id)

        # Extract competencies from Tab 14
        competencies = self._extract_competencies(form_se, case_id)

        # Update program stats
        program.num_courses = len(courses)
        program.num_required = sum(1 for c in courses if c.course_type == "required")
        program.num_elective = sum(1 for c in courses if c.course_type == "elective")

        return AccreditationCase(
            case_id=case_id,
            case_url=raw_data.get("case_url", ""),
            program=program,
            form_se=form_se,
            courses=courses,
            competencies=competencies,
            downloaded_files=raw_data.get("downloaded_files", []),
            raw_data=raw_data,
        )

    def _parse_program(
        self, raw_data: Dict[str, Any], case_id: str, level: str
    ) -> Program:
        """Parse program information from raw data."""
        # Extract institution name from Tab 0 if available
        institution = raw_data.get("institution_name", "")
        program_name = raw_data.get("program_name", "")

        # Try to extract from form_se Tab 0
        form_se = raw_data.get("form_se", {})
        tabs = form_se.get("tabs", [])

        for tab in tabs:
            if tab.get("tab_number") == 0:
                full_text = tab.get("full_text", "")
                all_fields = tab.get("all_fields", {})

                # Extract institution name
                if not institution:
                    for key in ["Повна назва ЗВО", "Назва ЗВО"]:
                        if key in all_fields:
                            institution = all_fields[key]
                            break
                    # Try regex from full text
                    if not institution:
                        match = re.search(
                            r"Повна назва ЗВО\s*([^\n]+)", full_text
                        )
                        if match:
                            institution = match.group(1).strip()

                # Extract program name
                if not program_name or program_name == "Документи акредитаційної справи":
                    for key in ["Повна назва ОП", "Назва ОП"]:
                        if key in all_fields:
                            program_name = all_fields[key]
                            break
                    if not program_name:
                        match = re.search(
                            r"Повна назва ОП\s*([^\n]+)", full_text
                        )
                        if match:
                            program_name = match.group(1).strip()
                break

        # Map level to Ukrainian name
        level_ukrainian = settings.degree_level_names.get(level, "Невідомо")

        return Program(
            case_id=case_id,
            institution_name=institution,
            program_name=program_name,
            specialty_code="022",
            specialty_name="Дизайн",
            degree_level=level,
            degree_level_ukrainian=level_ukrainian,
            status=raw_data.get("status", ""),
            region=raw_data.get("region", ""),
            institution_type=raw_data.get("institution_type", ""),
        )

    def _parse_form_se(self, form_data: Dict[str, Any]) -> Optional[FormSE]:
        """Parse Form SE data."""
        if not form_data:
            return None

        tabs = []
        for tab_data in form_data.get("tabs", []):
            tab = FormSETab(
                tab_number=tab_data.get("tab_number", 0),
                tab_title=tab_data.get("tab_title", ""),
                full_text=tab_data.get("full_text", ""),
                all_fields=tab_data.get("all_fields", {}),
                all_tables=tab_data.get("all_tables", []),
            )
            tabs.append(tab)

        return FormSE(
            form_id=form_data.get("form_id", ""),
            form_url=form_data.get("form_url", ""),
            tabs=tabs,
        )

    def _extract_courses(
        self, form_se: Optional[FormSE], case_id: str
    ) -> List[Course]:
        """Extract courses from Tab 12 (Educational Components)."""
        if not form_se:
            return []

        tab12 = form_se.get_educational_components_tab()
        if not tab12 or not tab12.all_tables:
            return []

        courses = []
        for table in tab12.all_tables:
            headers = table.get("headers", [])
            rows = table.get("rows", [])

            # Find column indices
            name_col = self._find_column_index(headers, ["Назва освітнього компонента", "Назва"])
            type_col = self._find_column_index(headers, ["Вид компонента", "Тип"])
            file_col = self._find_column_index(headers, ["Поле для завантаження", "Файл"])

            for row in rows:
                cells = row.get("cells", [])
                if not cells or len(cells) <= name_col:
                    continue

                name = cells[name_col] if name_col < len(cells) else ""
                if not name or name == "Назва освітнього компонента":
                    continue  # Skip header rows

                # Extract component code
                code_match = re.match(r"^([ОА|ОП|ВБ|ВВ|ВК|ОК]\S*\.?\d*)\s*", name)
                code = code_match.group(1) if code_match else ""
                clean_name = name[len(code):].strip() if code else name

                # Determine course type
                comp_type = cells[type_col] if type_col < len(cells) else ""
                course_type = self._map_course_type(comp_type, code)

                # Extract syllabus filename
                syllabus = cells[file_col] if file_col < len(cells) else ""

                course = Course(
                    case_id=case_id,
                    course_id=f"{case_id}_{code}" if code else f"{case_id}_{len(courses)}",
                    name=clean_name,
                    name_normalized="",  # Will be filled by NLP module
                    course_type=course_type,
                    syllabus_text="",
                    has_syllabus=bool(syllabus and ".pdf" in syllabus.lower()),
                )
                courses.append(course)

        return courses

    def _extract_competencies(
        self, form_se: Optional[FormSE], case_id: str
    ) -> List[Competency]:
        """Extract competencies from Tab 14 (Competency Matrix)."""
        if not form_se:
            return []

        tab14 = form_se.get_competency_matrix_tab()
        if not tab14:
            return []

        competencies = []

        # Try to extract from full_text using regex
        text = tab14.full_text
        if not text:
            return []

        # Pattern for general competencies (ЗК)
        zk_pattern = r"(ЗК\d+)[:\.]?\s*([^\n]+)"
        for match in re.finditer(zk_pattern, text):
            comp = Competency(
                code=match.group(1),
                description=match.group(2).strip(),
                competency_type="general",
            )
            competencies.append(comp)

        # Pattern for professional competencies (ФК)
        fk_pattern = r"(ФК\d+)[:\.]?\s*([^\n]+)"
        for match in re.finditer(fk_pattern, text):
            comp = Competency(
                code=match.group(1),
                description=match.group(2).strip(),
                competency_type="professional",
            )
            competencies.append(comp)

        return competencies

    def _attach_syllabus_text(self, cases: List[AccreditationCase]) -> None:
        """Attach extracted syllabus text to courses."""
        if not self.text_dir.exists():
            return

        for case in tqdm(cases, desc="Attaching syllabus text"):
            level_dir_name = {
                "bachelor": "Бакалавр",
                "master": "Магістр",
                "phd": "Доктор_філософії",
            }.get(case.program.degree_level, "")

            if not level_dir_name:
                continue

            case_text_dir = self.text_dir / level_dir_name / case.case_id
            if not case_text_dir.exists():
                continue

            # Load all text files for this case
            text_files = list(case_text_dir.glob("*.txt"))
            all_text = ""
            for txt_file in text_files:
                try:
                    content = txt_file.read_text(encoding="utf-8")
                    all_text += f"\n{content}"
                except Exception:
                    continue

            # Distribute text to courses (simplified - attach all to case)
            for course in case.courses:
                course.syllabus_text = all_text[:10000]  # Limit per course

    def _build_programs_df(self, cases: List[AccreditationCase]) -> pd.DataFrame:
        """Build DataFrame of programs."""
        records = []
        for case in cases:
            p = case.program
            records.append({
                "case_id": p.case_id,
                "institution_name": p.institution_name,
                "program_name": p.program_name,
                "specialty_code": p.specialty_code,
                "specialty_name": p.specialty_name,
                "degree_level": p.degree_level,
                "degree_level_ukrainian": p.degree_level_ukrainian,
                "status": p.status,
                "region": p.region,
                "institution_type": p.institution_type,
                "total_credits": p.total_credits,
                "num_courses": p.num_courses,
                "num_required": p.num_required,
                "num_elective": p.num_elective,
            })
        return pd.DataFrame(records)

    def _build_courses_df(self, cases: List[AccreditationCase]) -> pd.DataFrame:
        """Build DataFrame of all courses."""
        records = []
        for case in cases:
            for course in case.courses:
                records.append({
                    "case_id": course.case_id,
                    "course_id": course.course_id,
                    "name": course.name,
                    "name_normalized": course.name_normalized,
                    "credits": course.credits,
                    "course_type": course.course_type,
                    "semester": course.semester,
                    "has_syllabus": course.has_syllabus,
                    "syllabus_length": len(course.syllabus_text),
                    "degree_level": case.program.degree_level,
                })
        return pd.DataFrame(records)

    def _build_competencies_df(
        self, cases: List[AccreditationCase]
    ) -> pd.DataFrame:
        """Build DataFrame of competencies."""
        records = []
        for case in cases:
            for comp in case.competencies:
                records.append({
                    "case_id": case.case_id,
                    "code": comp.code,
                    "description": comp.description,
                    "competency_type": comp.competency_type,
                    "num_mapped_courses": len(comp.mapped_courses),
                    "degree_level": case.program.degree_level,
                })
        return pd.DataFrame(records)

    @staticmethod
    def _extract_case_id(filename: str) -> str:
        """Extract case ID from filename like 'case_8588.json'."""
        match = re.search(r"case_(\d+)", filename)
        return match.group(1) if match else ""

    @staticmethod
    def _find_column_index(headers: List[str], candidates: List[str]) -> int:
        """Find column index matching any of the candidate names."""
        for i, header in enumerate(headers):
            for candidate in candidates:
                if candidate.lower() in header.lower():
                    return i
        return 0

    @staticmethod
    def _map_course_type(type_str: str, code: str) -> str:
        """Map Ukrainian course type to standard type."""
        type_lower = type_str.lower()
        code_upper = code.upper()

        if "вибірк" in type_lower or code_upper.startswith("ВБ") or code_upper.startswith("ВВ"):
            return "elective"
        elif "практик" in type_lower or code_upper.startswith("ОП"):
            return "practice"
        elif "атестац" in type_lower or code_upper.startswith("ОА"):
            return "attestation"
        else:
            return "required"


def load_data(
    levels: Optional[List[str]] = None,
    max_cases: Optional[int] = None,
) -> LoadedData:
    """Convenience function to load all data."""
    loader = DataLoader()
    return loader.load_all(levels=levels, max_cases=max_cases)
