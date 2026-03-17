"""
Thesis Analysis System for Ukrainian Design Programs

Analyzes 132 accreditation cases from NAQA portal to:
- Extract curriculum patterns
- Identify AI/digital skills gaps
- Generate curriculum recommendations
- Produce LaTeX thesis output
"""

__version__ = "1.0.0"
__author__ = "Design Education Research"

from .config import settings

__all__ = ["settings"]
