"""Progress tracking and resume functionality"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import settings
from .models import CaseUrl

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manages checkpoint saves for resumable scraping"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.checkpoint_file = settings.checkpoints_dir / f"{session_id}.json"
        self.data: dict[str, Any] = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "phase": "init",  # init, collecting_urls, scraping, completed
            "case_urls": [],  # All collected case URLs
            "completed_cases": [],  # IDs of successfully scraped cases
            "failed_cases": [],  # Failed cases with error info
            "current_index": 0,  # Current position in case list
            "total_cases": 0,
            "statistics": {
                "total_files_downloaded": 0,
                "total_components_extracted": 0,
            },
        }

    def load(self) -> bool:
        """Load existing checkpoint if available"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                logger.info(
                    f"Loaded checkpoint: {len(self.data['completed_cases'])}/"
                    f"{self.data['total_cases']} cases completed"
                )
                return True
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
                return False
        return False

    def save(self) -> None:
        """Save checkpoint atomically (write to temp, then rename)"""
        self.data["updated_at"] = datetime.now().isoformat()

        temp_file = self.checkpoint_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)

            # Atomic rename
            shutil.move(str(temp_file), str(self.checkpoint_file))
            logger.debug("Checkpoint saved")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def set_phase(self, phase: str) -> None:
        """Update current phase"""
        self.data["phase"] = phase
        self.save()

    def set_case_urls(self, urls: list[CaseUrl]) -> None:
        """Store collected case URLs"""
        self.data["case_urls"] = [u.model_dump() for u in urls]
        self.data["total_cases"] = len(urls)
        self.save()

    def get_case_urls(self) -> list[CaseUrl]:
        """Retrieve stored case URLs"""
        return [CaseUrl(**u) for u in self.data.get("case_urls", [])]

    def get_pending_cases(self) -> list[CaseUrl]:
        """Get cases that haven't been processed yet"""
        all_urls = self.get_case_urls()
        completed_ids = set(self.data["completed_cases"])
        failed_ids = {f["case_id"] for f in self.data["failed_cases"]}

        return [u for u in all_urls if u.case_id not in completed_ids and u.case_id not in failed_ids]

    def mark_completed(self, case_id: str) -> None:
        """Mark a case as successfully completed"""
        if case_id not in self.data["completed_cases"]:
            self.data["completed_cases"].append(case_id)
            self.data["current_index"] = len(self.data["completed_cases"])

        # Auto-save every N completions
        if len(self.data["completed_cases"]) % settings.checkpoint_every == 0:
            self.save()
            logger.info(
                f"Checkpoint: {len(self.data['completed_cases'])}/"
                f"{self.data['total_cases']} cases completed"
            )

    def mark_failed(self, case_id: str, error: str) -> None:
        """Mark a case as failed"""
        self.data["failed_cases"].append(
            {
                "case_id": case_id,
                "error": error,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.save()

    def update_statistics(self, files_downloaded: int = 0, components_extracted: int = 0) -> None:
        """Update running statistics"""
        self.data["statistics"]["total_files_downloaded"] += files_downloaded
        self.data["statistics"]["total_components_extracted"] += components_extracted

    def get_progress(self) -> dict:
        """Get current progress info"""
        return {
            "phase": self.data["phase"],
            "total_cases": self.data["total_cases"],
            "completed": len(self.data["completed_cases"]),
            "failed": len(self.data["failed_cases"]),
            "pending": self.data["total_cases"]
            - len(self.data["completed_cases"])
            - len(self.data["failed_cases"]),
            "statistics": self.data["statistics"],
        }

    def is_completed(self) -> bool:
        """Check if all cases have been processed"""
        total_processed = len(self.data["completed_cases"]) + len(self.data["failed_cases"])
        return total_processed >= self.data["total_cases"] and self.data["total_cases"] > 0

    def get_failed_cases(self) -> list[dict]:
        """Get list of failed cases for retry"""
        return self.data["failed_cases"]

    def clear_failed(self, case_id: str) -> None:
        """Remove a case from failed list (for retry)"""
        self.data["failed_cases"] = [f for f in self.data["failed_cases"] if f["case_id"] != case_id]
        self.save()

    def finalize(self) -> None:
        """Mark session as completed"""
        self.data["phase"] = "completed"
        self.data["completed_at"] = datetime.now().isoformat()
        self.save()
        logger.info("Session finalized")
