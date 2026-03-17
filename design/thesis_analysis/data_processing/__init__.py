"""Data processing modules for thesis analysis."""

from .loader import DataLoader
from .schema import (
    Program,
    Course,
    Competency,
    EducationalComponent,
    FormSETab,
    AccreditationCase,
)

__all__ = [
    "DataLoader",
    "Program",
    "Course",
    "Competency",
    "EducationalComponent",
    "FormSETab",
    "AccreditationCase",
]
