"""
AI and digital skills gap analysis for design curricula.

Identifies missing AI/digital skills in Ukrainian design programs
by comparing course content against modern skill frameworks.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import re
from collections import defaultdict

from ...config import settings
from ...data_processing.ukrainian_nlp import lemmatize_ukrainian, clean_text


@dataclass
class SkillCoverage:
    """Coverage information for a specific skill."""

    skill: str
    is_covered: bool
    coverage_score: float  # 0-1
    matching_courses: List[str]
    matching_keywords: List[str]


@dataclass
class GapAnalysisResult:
    """Complete gap analysis result."""

    total_skills_checked: int
    covered_skills: int
    missing_skills: List[str]
    partially_covered: List[str]

    skill_details: List[SkillCoverage]
    coverage_scores: Dict[str, float]

    overall_ai_coverage: float
    overall_digital_coverage: float

    recommendations: List[str] = field(default_factory=list)


# AI and digital skills framework for design education
AI_DESIGN_SKILLS_FRAMEWORK = {
    # Core AI Skills
    "ai_fundamentals": {
        "name": "AI Fundamentals",
        "keywords_uk": [
            "штучний інтелект", "машинне навчання", "нейронна мережа",
            "глибоке навчання", "алгоритм", "модель", "навчання з учителем",
        ],
        "keywords_en": [
            "artificial intelligence", "machine learning", "neural network",
            "deep learning", "algorithm", "model", "AI",
        ],
    },
    "generative_ai": {
        "name": "Generative AI & Design",
        "keywords_uk": [
            "генеративний дизайн", "генеративне мистецтво", "AI-дизайн",
            "автоматична генерація", "промт", "текст в зображення",
            "midjourney", "stable diffusion", "dall-e",
        ],
        "keywords_en": [
            "generative design", "generative art", "AI design",
            "prompt engineering", "text to image", "diffusion model",
        ],
    },
    "computer_vision": {
        "name": "Computer Vision",
        "keywords_uk": [
            "комп'ютерний зір", "розпізнавання зображень", "обробка зображень",
            "аналіз зображень", "детекція об'єктів", "сегментація",
        ],
        "keywords_en": [
            "computer vision", "image recognition", "image processing",
            "object detection", "segmentation",
        ],
    },

    # Digital Design Tools
    "digital_tools_2d": {
        "name": "2D Digital Design Tools",
        "keywords_uk": [
            "photoshop", "illustrator", "figma", "sketch", "canva",
            "графічний редактор", "векторна графіка", "растрова графіка",
            "цифрова ілюстрація", "adobe",
        ],
        "keywords_en": [
            "photoshop", "illustrator", "figma", "digital illustration",
            "vector graphics", "raster graphics",
        ],
    },
    "digital_tools_3d": {
        "name": "3D Design & Modeling",
        "keywords_uk": [
            "3d-моделювання", "тривимірна графіка", "blender", "3ds max",
            "maya", "cinema 4d", "rhino", "autocad", "sketchup",
            "візуалізація", "рендеринг",
        ],
        "keywords_en": [
            "3d modeling", "3d graphics", "rendering", "visualization",
            "cad", "parametric design",
        ],
    },
    "motion_design": {
        "name": "Motion Design & Animation",
        "keywords_uk": [
            "моушн-дизайн", "анімація", "after effects", "motion graphics",
            "відео", "монтаж", "premiere", "спецефекти",
        ],
        "keywords_en": [
            "motion design", "animation", "motion graphics", "video editing",
            "after effects",
        ],
    },

    # UX/UI & Interactive
    "ux_ui": {
        "name": "UX/UI Design",
        "keywords_uk": [
            "ux", "ui", "інтерфейс", "взаємодія", "користувацький досвід",
            "прототипування", "wireframe", "usability", "юзабіліті",
            "веб-дизайн", "мобільний дизайн", "адаптивний",
        ],
        "keywords_en": [
            "ux design", "ui design", "user experience", "user interface",
            "prototyping", "wireframe", "usability", "web design",
        ],
    },
    "interactive_design": {
        "name": "Interactive & Computational Design",
        "keywords_uk": [
            "інтерактивний дизайн", "параметричний дизайн", "алгоритмічний",
            "processing", "touchdesigner", "grasshopper", "код", "програмування",
        ],
        "keywords_en": [
            "interactive design", "parametric design", "computational design",
            "coding for designers", "creative coding",
        ],
    },

    # Data & Visualization
    "data_visualization": {
        "name": "Data Visualization",
        "keywords_uk": [
            "візуалізація даних", "інфографіка", "дашборд", "діаграма",
            "статистика", "аналітика", "big data",
        ],
        "keywords_en": [
            "data visualization", "infographics", "dashboard", "data analytics",
        ],
    },

    # Emerging Tech
    "vr_ar": {
        "name": "VR/AR Design",
        "keywords_uk": [
            "віртуальна реальність", "доповнена реальність", "vr", "ar",
            "xr", "метавсесвіт", "immersive", "360",
        ],
        "keywords_en": [
            "virtual reality", "augmented reality", "mixed reality",
            "metaverse", "immersive design",
        ],
    },
}


class AIGapAnalyzer:
    """Analyzes AI and digital skills gaps in curricula."""

    def __init__(
        self,
        skills_framework: Optional[Dict] = None,
        coverage_threshold: float = 0.3,
    ):
        self.skills_framework = skills_framework or AI_DESIGN_SKILLS_FRAMEWORK
        self.coverage_threshold = coverage_threshold

    def analyze(
        self,
        courses: List[str],
        syllabus_texts: Optional[List[str]] = None,
    ) -> GapAnalysisResult:
        """
        Analyze curriculum for AI/digital skills gaps.

        Args:
            courses: List of course names
            syllabus_texts: Optional list of syllabus texts

        Returns:
            GapAnalysisResult with coverage analysis
        """
        # Combine all text for analysis
        all_text = " ".join(courses)
        if syllabus_texts:
            all_text += " " + " ".join(syllabus_texts[:50])  # Limit

        # Clean and prepare text
        all_text_lower = clean_text(all_text).lower()
        all_text_lemmas = set(lemmatize_ukrainian(all_text))

        # Analyze each skill
        skill_details = []
        covered = []
        missing = []
        partial = []

        for skill_id, skill_info in self.skills_framework.items():
            coverage = self._check_skill_coverage(
                skill_info,
                courses,
                all_text_lower,
                all_text_lemmas,
            )
            skill_details.append(coverage)

            if coverage.is_covered:
                covered.append(skill_info["name"])
            elif coverage.coverage_score > 0:
                partial.append(skill_info["name"])
            else:
                missing.append(skill_info["name"])

        # Calculate overall scores
        ai_skills = ["ai_fundamentals", "generative_ai", "computer_vision"]
        digital_skills = [
            "digital_tools_2d", "digital_tools_3d", "motion_design",
            "ux_ui", "interactive_design", "data_visualization", "vr_ar",
        ]

        ai_coverage = self._calculate_category_coverage(skill_details, ai_skills)
        digital_coverage = self._calculate_category_coverage(skill_details, digital_skills)

        # Generate recommendations
        recommendations = self._generate_recommendations(missing, partial)

        return GapAnalysisResult(
            total_skills_checked=len(self.skills_framework),
            covered_skills=len(covered),
            missing_skills=missing,
            partially_covered=partial,
            skill_details=skill_details,
            coverage_scores={
                "ai_core": ai_coverage,
                "digital_tools": digital_coverage,
                "overall": (ai_coverage + digital_coverage) / 2,
            },
            overall_ai_coverage=ai_coverage,
            overall_digital_coverage=digital_coverage,
            recommendations=recommendations,
        )

    def _check_skill_coverage(
        self,
        skill_info: Dict,
        courses: List[str],
        text_lower: str,
        text_lemmas: Set[str],
    ) -> SkillCoverage:
        """Check coverage for a single skill."""
        keywords_uk = skill_info.get("keywords_uk", [])
        keywords_en = skill_info.get("keywords_en", [])
        all_keywords = keywords_uk + keywords_en

        matching_keywords = []
        matching_courses = []

        # Check keywords in full text
        for keyword in all_keywords:
            if keyword.lower() in text_lower:
                matching_keywords.append(keyword)

        # Check courses specifically
        for course in courses:
            course_lower = course.lower()
            for keyword in all_keywords:
                if keyword.lower() in course_lower:
                    if course not in matching_courses:
                        matching_courses.append(course)

        # Calculate coverage score
        if matching_keywords:
            coverage_score = min(1.0, len(matching_keywords) / 3)
        else:
            coverage_score = 0.0

        is_covered = coverage_score >= self.coverage_threshold

        return SkillCoverage(
            skill=skill_info["name"],
            is_covered=is_covered,
            coverage_score=coverage_score,
            matching_courses=matching_courses[:5],
            matching_keywords=matching_keywords[:10],
        )

    def _calculate_category_coverage(
        self,
        skill_details: List[SkillCoverage],
        skill_ids: List[str],
    ) -> float:
        """Calculate average coverage for a category of skills."""
        scores = []
        skill_names = [
            self.skills_framework[sid]["name"]
            for sid in skill_ids
            if sid in self.skills_framework
        ]

        for detail in skill_details:
            if detail.skill in skill_names:
                scores.append(detail.coverage_score)

        return sum(scores) / len(scores) if scores else 0.0

    def _generate_recommendations(
        self,
        missing: List[str],
        partial: List[str],
    ) -> List[str]:
        """Generate recommendations based on gaps."""
        recommendations = []

        # Priority missing skills
        if "AI Fundamentals" in missing:
            recommendations.append(
                "Add introductory course on AI/ML basics for designers, "
                "covering concepts without deep technical requirements"
            )

        if "Generative AI & Design" in missing:
            recommendations.append(
                "Integrate generative AI tools (Midjourney, DALL-E, Stable Diffusion) "
                "into existing design courses or create dedicated workshop"
            )

        if "UX/UI Design" in missing:
            recommendations.append(
                "Strengthen UX/UI curriculum with Figma, prototyping, "
                "and user research methods"
            )

        if "Data Visualization" in missing:
            recommendations.append(
                "Add data visualization module covering infographics, "
                "dashboard design, and data storytelling"
            )

        if "Interactive & Computational Design" in missing or "Interactive & Computational Design" in partial:
            recommendations.append(
                "Introduce creative coding course using Processing, p5.js, "
                "or TouchDesigner for interactive design"
            )

        if "VR/AR Design" in missing:
            recommendations.append(
                "Consider adding VR/AR design module as emerging technology elective"
            )

        # General recommendations
        if len(missing) > 3:
            recommendations.append(
                "Consider curriculum modernization review to address "
                f"multiple skill gaps ({len(missing)} areas identified)"
            )

        return recommendations

    def compare_programs(
        self,
        programs: List[Dict],
    ) -> Dict[str, GapAnalysisResult]:
        """Compare multiple programs' AI/digital coverage."""
        results = {}

        for program in programs:
            case_id = program.get("case_id", "unknown")
            courses = program.get("courses", [])
            syllabi = program.get("syllabus_texts", [])

            result = self.analyze(courses, syllabi)
            results[case_id] = result

        return results

    def generate_report(self, result: GapAnalysisResult) -> str:
        """Generate text report of gap analysis (English only)."""
        lines = []
        lines.append("=" * 60)
        lines.append("AI & DIGITAL SKILLS GAP ANALYSIS")
        lines.append("Ukrainian Design Education Programs (Specialty 022)")
        lines.append("=" * 60)

        lines.append(f"\n## COVERAGE SUMMARY\n")
        lines.append(f"Skills checked: {result.total_skills_checked}")
        lines.append(f"Fully covered: {result.covered_skills}")
        lines.append(f"Partially covered: {len(result.partially_covered)}")
        lines.append(f"Missing: {len(result.missing_skills)}")

        lines.append(f"\n## COVERAGE SCORES\n")
        lines.append(f"AI Core Skills: {result.overall_ai_coverage:.1%}")
        lines.append(f"Digital Tools: {result.overall_digital_coverage:.1%}")
        lines.append(f"Overall: {result.coverage_scores['overall']:.1%}")

        lines.append(f"\n## MISSING SKILLS\n")
        for skill in result.missing_skills:
            lines.append(f"  [X] {skill}")

        if result.partially_covered:
            lines.append(f"\n## PARTIALLY COVERED\n")
            for skill in result.partially_covered:
                lines.append(f"  [~] {skill}")

        lines.append(f"\n## SKILL DETAILS\n")
        for detail in sorted(result.skill_details, key=lambda x: x.coverage_score, reverse=True):
            status = "[+]" if detail.is_covered else ("[~]" if detail.coverage_score > 0 else "[X]")
            lines.append(f"{status} {detail.skill}: {detail.coverage_score:.1%}")
            if detail.matching_courses:
                # Translate course names to English
                translated = [self._translate_course_name(c) for c in detail.matching_courses[:3]]
                lines.append(f"    Matching courses: {', '.join(translated)}")

        if result.recommendations:
            lines.append(f"\n## RECOMMENDATIONS\n")
            for i, rec in enumerate(result.recommendations, 1):
                lines.append(f"{i}. {rec}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

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
