"""
Descriptive statistical analysis of Ukrainian design programs.

Provides statistics on credit distributions, course counts, program
characteristics, and comparisons across degree levels.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import pandas as pd
import numpy as np

from ...config import settings


@dataclass
class DistributionStats:
    """Statistics for a numeric distribution."""

    count: int
    mean: float
    std: float
    min: float
    max: float
    median: float
    q25: float
    q75: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "count": self.count,
            "mean": self.mean,
            "std": self.std,
            "min": self.min,
            "max": self.max,
            "median": self.median,
            "q25": self.q25,
            "q75": self.q75,
        }


@dataclass
class ProgramStatistics:
    """Complete statistics for program analysis."""

    total_programs: int
    by_level: Dict[str, int]
    by_region: Dict[str, int]
    by_institution_type: Dict[str, int]

    courses_per_program: DistributionStats
    required_courses: DistributionStats
    elective_courses: DistributionStats
    syllabus_coverage: float  # Percentage of courses with syllabi

    level_comparisons: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class CourseStatistics:
    """Statistics for course analysis."""

    total_courses: int
    unique_courses: int
    by_type: Dict[str, int]
    by_level: Dict[str, int]

    credits_distribution: Optional[DistributionStats]
    name_length_distribution: DistributionStats

    most_common_courses: List[tuple]  # (name, count)
    course_type_by_level: pd.DataFrame


class DescriptiveAnalyzer:
    """Performs descriptive statistical analysis."""

    def __init__(
        self,
        df_programs: pd.DataFrame,
        df_courses: pd.DataFrame,
    ):
        self.df_programs = df_programs
        self.df_courses = df_courses

    def analyze_programs(self) -> ProgramStatistics:
        """Generate comprehensive program statistics."""
        df = self.df_programs

        # Basic counts
        total = len(df)
        by_level = df["degree_level"].value_counts().to_dict()
        by_region = df["region"].value_counts().to_dict() if "region" in df.columns else {}
        by_inst = df["institution_type"].value_counts().to_dict() if "institution_type" in df.columns else {}

        # Course distributions
        courses_stats = self._compute_distribution(df["num_courses"])
        required_stats = self._compute_distribution(df["num_required"])
        elective_stats = self._compute_distribution(df["num_elective"])

        # Syllabus coverage
        if "has_syllabus" in self.df_courses.columns:
            syllabus_coverage = self.df_courses["has_syllabus"].mean() * 100
        else:
            syllabus_coverage = 0.0

        # Comparisons by level
        level_comparisons = self._compare_by_level()

        return ProgramStatistics(
            total_programs=total,
            by_level=by_level,
            by_region=by_region,
            by_institution_type=by_inst,
            courses_per_program=courses_stats,
            required_courses=required_stats,
            elective_courses=elective_stats,
            syllabus_coverage=syllabus_coverage,
            level_comparisons=level_comparisons,
        )

    def analyze_courses(self) -> CourseStatistics:
        """Generate comprehensive course statistics."""
        df = self.df_courses

        # Basic counts
        total = len(df)
        unique = df["name"].nunique()
        by_type = df["course_type"].value_counts().to_dict()
        by_level = df["degree_level"].value_counts().to_dict()

        # Credits distribution (if available)
        if "credits" in df.columns and df["credits"].notna().any():
            credits_stats = self._compute_distribution(df["credits"].dropna())
        else:
            credits_stats = None

        # Name length distribution
        name_lengths = df["name"].str.len()
        name_stats = self._compute_distribution(name_lengths)

        # Most common courses
        most_common = df["name"].value_counts().head(30).items()
        most_common_list = [(name, count) for name, count in most_common]

        # Course type by level
        type_by_level = pd.crosstab(
            df["degree_level"],
            df["course_type"],
            margins=True,
        )

        return CourseStatistics(
            total_courses=total,
            unique_courses=unique,
            by_type=by_type,
            by_level=by_level,
            credits_distribution=credits_stats,
            name_length_distribution=name_stats,
            most_common_courses=most_common_list,
            course_type_by_level=type_by_level,
        )

    def _compare_by_level(self) -> Dict[str, Dict[str, Any]]:
        """Compare program characteristics across degree levels."""
        comparisons = {}

        for level in ["bachelor", "master", "phd"]:
            level_df = self.df_programs[self.df_programs["degree_level"] == level]

            if len(level_df) == 0:
                continue

            comparisons[level] = {
                "count": len(level_df),
                "avg_courses": level_df["num_courses"].mean(),
                "std_courses": level_df["num_courses"].std(),
                "avg_required": level_df["num_required"].mean(),
                "avg_elective": level_df["num_elective"].mean(),
                "elective_ratio": (
                    level_df["num_elective"].sum() /
                    level_df["num_courses"].sum()
                    if level_df["num_courses"].sum() > 0 else 0
                ),
            }

        return comparisons

    def get_summary_table(self) -> pd.DataFrame:
        """Create summary table for thesis (English)."""
        levels = ["bachelor", "master", "phd"]
        level_names = {
            "bachelor": "Bachelor",
            "master": "Master",
            "phd": "PhD",
        }

        rows = []
        for level in levels:
            level_df = self.df_programs[self.df_programs["degree_level"] == level]
            level_courses = self.df_courses[self.df_courses["degree_level"] == level]

            if len(level_df) == 0:
                continue

            rows.append({
                "Level": level_names.get(level, level),
                "Program Count": len(level_df),
                "Avg Components": f"{level_df['num_courses'].mean():.1f}",
                "Required": f"{level_df['num_required'].mean():.1f}",
                "Elective": f"{level_df['num_elective'].mean():.1f}",
                "Unique Courses": level_courses["name"].nunique(),
            })

        return pd.DataFrame(rows)

    def get_credit_analysis(self) -> Dict[str, Any]:
        """Analyze credit distribution (target: 240 ECTS for bachelor)."""
        results = {}

        for level in ["bachelor", "master", "phd"]:
            target = {
                "bachelor": 240,
                "master": 90,
                "phd": 60,
            }.get(level, 0)

            level_df = self.df_programs[self.df_programs["degree_level"] == level]

            if len(level_df) == 0:
                continue

            # Estimate credits from course count (typical: 30 ECTS = 6 courses)
            estimated_credits = level_df["num_courses"] * 5  # Rough estimate

            results[level] = {
                "target_ects": target,
                "estimated_mean": estimated_credits.mean(),
                "estimated_std": estimated_credits.std(),
                "num_programs": len(level_df),
            }

        return results

    def correlation_analysis(self) -> pd.DataFrame:
        """Analyze correlations between program features."""
        numeric_cols = ["num_courses", "num_required", "num_elective"]
        available_cols = [c for c in numeric_cols if c in self.df_programs.columns]

        if len(available_cols) < 2:
            return pd.DataFrame()

        return self.df_programs[available_cols].corr()

    @staticmethod
    def _compute_distribution(series: pd.Series) -> DistributionStats:
        """Compute distribution statistics for a series."""
        series = series.dropna()

        if len(series) == 0:
            return DistributionStats(
                count=0, mean=0, std=0, min=0, max=0,
                median=0, q25=0, q75=0,
            )

        return DistributionStats(
            count=len(series),
            mean=float(series.mean()),
            std=float(series.std()) if len(series) > 1 else 0.0,
            min=float(series.min()),
            max=float(series.max()),
            median=float(series.median()),
            q25=float(series.quantile(0.25)),
            q75=float(series.quantile(0.75)),
        )

    def generate_report(self) -> str:
        """Generate text report of descriptive statistics (English only)."""
        prog_stats = self.analyze_programs()
        course_stats = self.analyze_courses()

        report = []
        report.append("=" * 60)
        report.append("DESCRIPTIVE STATISTICS REPORT")
        report.append("Ukrainian Design Education Programs (Specialty 022)")
        report.append("=" * 60)

        report.append("\n## PROGRAM OVERVIEW\n")
        report.append(f"Total programs analyzed: {prog_stats.total_programs}")
        report.append("\nBy degree level:")
        for level, count in prog_stats.by_level.items():
            report.append(f"  - {level.capitalize()}: {count}")

        report.append("\n## COURSE STATISTICS\n")
        report.append(f"Total educational components: {course_stats.total_courses}")
        report.append(f"Unique course names: {course_stats.unique_courses}")
        report.append("\nBy component type:")
        type_translations = {
            "required": "Required",
            "elective": "Elective",
            "practice": "Practice",
            "attestation": "Attestation",
        }
        for ctype, count in course_stats.by_type.items():
            ctype_en = type_translations.get(ctype, ctype.capitalize())
            report.append(f"  - {ctype_en}: {count}")

        report.append("\n## COURSES PER PROGRAM\n")
        stats = prog_stats.courses_per_program
        report.append(f"Mean: {stats.mean:.1f} (SD: {stats.std:.1f})")
        report.append(f"Range: {stats.min:.0f} - {stats.max:.0f}")
        report.append(f"Median: {stats.median:.0f}")

        report.append("\n## SYLLABUS COVERAGE\n")
        report.append(f"{prog_stats.syllabus_coverage:.1f}% of courses have syllabi")

        report.append("\n## LEVEL COMPARISONS\n")
        for level, comp in prog_stats.level_comparisons.items():
            report.append(f"\n{level.capitalize()} (n={comp['count']}):")
            report.append(f"  Avg courses: {comp['avg_courses']:.1f}")
            report.append(f"  Required: {comp['avg_required']:.1f}")
            report.append(f"  Elective: {comp['avg_elective']:.1f}")
            report.append(f"  Elective ratio: {comp['elective_ratio']*100:.1f}%")

        report.append("\n## MOST COMMON COURSES (translated to English)\n")
        for name, count in course_stats.most_common_courses[:15]:
            english_name = self._translate_course_name(name)
            report.append(f"  {count:3d} | {english_name[:50]}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)

    def _translate_course_name(self, name: str) -> str:
        """Translate Ukrainian course name to English."""
        if not name:
            return ""

        # Import translation dict
        from ...visualization.plots import COURSE_TRANSLATIONS

        name_lower = name.lower().strip()

        # Direct match
        if name_lower in COURSE_TRANSLATIONS:
            return COURSE_TRANSLATIONS[name_lower]

        # Partial match
        for uk, en in COURSE_TRANSLATIONS.items():
            if uk in name_lower:
                return en

        # Check if already English
        if all(ord(c) < 128 or c in ' -_' for c in name):
            return name.title()

        return name[:30] + "..." if len(name) > 30 else name
