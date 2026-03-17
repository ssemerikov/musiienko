"""JSON and CSV output writers for scraped data"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import settings
from .models import AccreditationCase, ScrapeSession

logger = logging.getLogger(__name__)


class StorageManager:
    """Handles saving scraped data to JSON and CSV formats"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.output_dir = settings.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_session_json(self, session: ScrapeSession) -> Path:
        """Save complete session data as JSON"""
        filepath = self.output_dir / "all_programs.json"

        data = {
            "session_id": session.session_id,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "total_cases": session.total_cases,
            "completed_cases": session.completed_cases,
            "failed_cases": session.failed_cases,
            "total_files_downloaded": session.total_files_downloaded,
            "programs": [self._serialize_case(case) for case in session.cases],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Saved session JSON to {filepath}")
        return filepath

    def save_case_json(self, case: AccreditationCase) -> Path:
        """Save individual case data as JSON in raw directory"""
        filepath = settings.raw_dir / f"case_{case.case_id}.json"
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = self._serialize_case(case)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        logger.debug(f"Saved case JSON to {filepath}")
        return filepath

    def _serialize_case(self, case: AccreditationCase) -> dict:
        """Convert AccreditationCase to serializable dict"""
        data = case.model_dump()
        # Handle datetime objects
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

    def save_programs_csv(self, cases: list[AccreditationCase]) -> Path:
        """Save flattened program data as CSV"""
        filepath = self.output_dir / "all_programs.csv"

        fieldnames = [
            "case_id",
            "case_url",
            "institution_name",
            "program_name",
            "specialty",
            "degree_level",
            "status",
            "form_id",
            "form_url",
            "tabs_count",
            "components_count",
            "files_count",
            "scrape_status",
            "scraped_at",
        ]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for case in cases:
                row = {
                    "case_id": case.case_id,
                    "case_url": case.case_url,
                    "institution_name": case.institution_name,
                    "program_name": case.program_name,
                    "specialty": case.specialty,
                    "degree_level": case.degree_level,
                    "status": case.status,
                    "form_id": case.form_se.form_id if case.form_se else "",
                    "form_url": case.form_se.form_url if case.form_se else "",
                    "tabs_count": len(case.form_se.tabs) if case.form_se else 0,
                    "components_count": len(case.form_se.table1_components) if case.form_se else 0,
                    "files_count": len(case.form_se.all_files) if case.form_se else 0,
                    "scrape_status": case.scrape_status,
                    "scraped_at": case.scraped_at.isoformat() if case.scraped_at else "",
                }
                writer.writerow(row)

        logger.info(f"Saved programs CSV to {filepath} ({len(cases)} rows)")
        return filepath

    def save_components_csv(self, cases: list[AccreditationCase]) -> Path:
        """Save educational components summary as CSV"""
        filepath = self.output_dir / "components_summary.csv"

        fieldnames = [
            "case_id",
            "institution_name",
            "program_name",
            "component_index",
            "component_name",
            "component_type",
            "credits",
            "hours",
            "control_form",
            "has_syllabus",
            "syllabus_filename",
            "resources",
        ]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            row_count = 0
            for case in cases:
                if not case.form_se:
                    continue

                for component in case.form_se.table1_components:
                    row = {
                        "case_id": case.case_id,
                        "institution_name": case.institution_name,
                        "program_name": case.program_name,
                        "component_index": component.row_index,
                        "component_name": component.component_name,
                        "component_type": component.component_type,
                        "credits": component.credits,
                        "hours": component.hours,
                        "control_form": component.control_form,
                        "has_syllabus": component.has_syllabus,
                        "syllabus_filename": component.syllabus_filename,
                        "resources": component.resources[:200] if component.resources else "",  # Truncate long resources
                    }
                    writer.writerow(row)
                    row_count += 1

        logger.info(f"Saved components CSV to {filepath} ({row_count} rows)")
        return filepath

    def save_files_manifest(self, cases: list[AccreditationCase]) -> Path:
        """Save complete file inventory as JSON"""
        filepath = self.output_dir / "files_manifest.json"

        manifest = {
            "generated_at": datetime.now().isoformat(),
            "total_cases": len(cases),
            "total_files": 0,
            "files_by_case": {},
        }

        for case in cases:
            case_files = []
            if case.form_se:
                for file_info in case.form_se.all_files:
                    case_files.append(file_info.model_dump())
                    manifest["total_files"] += 1

            if case.files_manifest:
                case_files.extend(case.files_manifest.get("files", []))

            manifest["files_by_case"][case.case_id] = {
                "institution_name": case.institution_name,
                "program_name": case.program_name,
                "files": case_files,
            }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Saved files manifest to {filepath} ({manifest['total_files']} files)")
        return filepath

    def save_tabs_content(self, cases: list[AccreditationCase]) -> Path:
        """Save all tab content as separate JSON for reference"""
        filepath = self.output_dir / "tabs_content.json"

        tabs_data: dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "cases": {},
        }

        for case in cases:
            if not case.form_se:
                continue

            tabs_data["cases"][case.case_id] = {
                "institution_name": case.institution_name,
                "program_name": case.program_name,
                "tabs": [
                    {
                        "tab_number": tab.tab_number,
                        "tab_title": tab.tab_title,
                        "fields_count": len(tab.all_fields),
                        "tables_count": len(tab.all_tables),
                        "files_count": len(tab.all_files),
                        "all_fields": tab.all_fields,
                        "full_text": tab.full_text[:5000] if tab.full_text else "",  # Truncate for manageability
                    }
                    for tab in case.form_se.tabs
                ],
            }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(tabs_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Saved tabs content to {filepath}")
        return filepath

    def save_all(self, session: ScrapeSession) -> dict[str, Path]:
        """Save all output files"""
        return {
            "session_json": self.save_session_json(session),
            "programs_csv": self.save_programs_csv(session.cases),
            "components_csv": self.save_components_csv(session.cases),
            "files_manifest": self.save_files_manifest(session.cases),
            "tabs_content": self.save_tabs_content(session.cases),
        }
