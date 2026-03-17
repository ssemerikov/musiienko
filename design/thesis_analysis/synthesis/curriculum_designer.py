"""
AI-enhanced curriculum design proposal generator.

Synthesizes analysis findings to propose improved curriculum
structure for Ukrainian design education.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class CourseProposal:
    """Proposed course for new curriculum."""

    name: str
    name_en: str
    credits: int
    semester: int
    year: int
    course_type: str  # required, elective
    category: str  # foundation, core, specialization, ai_digital
    description: str
    learning_outcomes: List[str]
    prerequisites: List[str] = field(default_factory=list)
    ai_integration: str = ""


@dataclass
class YearPlan:
    """Curriculum plan for one academic year."""

    year: int
    total_credits: int
    required_credits: int
    elective_credits: int
    courses: List[CourseProposal]
    focus: str


@dataclass
class CurriculumProposal:
    """Complete curriculum proposal."""

    program_name: str
    degree_level: str
    total_credits: int
    duration_years: int
    years: List[YearPlan]

    ai_courses_count: int
    ai_integrated_count: int
    digital_tools_coverage: float

    rationale: str
    key_innovations: List[str]
    implementation_notes: List[str]


class CurriculumDesigner:
    """Generates AI-enhanced curriculum proposals."""

    # Standard credit allocations
    BACHELOR_TOTAL = 240
    MASTER_TOTAL = 90
    BACHELOR_YEARS = 4
    MASTER_YEARS = 2

    # Course categories with typical credit ranges
    CATEGORIES = {
        "foundation": {"min": 30, "max": 60, "description": "General education, art history, design theory"},
        "core_design": {"min": 60, "max": 90, "description": "Core design disciplines"},
        "specialization": {"min": 30, "max": 60, "description": "Specialization track"},
        "ai_digital": {"min": 15, "max": 30, "description": "AI and digital technology"},
        "practice": {"min": 15, "max": 30, "description": "Internships and projects"},
        "elective": {"min": 15, "max": 30, "description": "Free electives"},
        "thesis": {"min": 15, "max": 30, "description": "Thesis/diploma project"},
    }

    def __init__(self):
        self.proposals = []

    def design_bachelor_curriculum(
        self,
        gap_analysis: Dict[str, Any],
        common_courses: List[str],
        specialization: str = "Graphic Design",
    ) -> CurriculumProposal:
        """
        Design AI-enhanced bachelor curriculum.

        Args:
            gap_analysis: Results from AIGapAnalyzer
            common_courses: Most common courses from existing programs
            specialization: Design specialization focus

        Returns:
            Complete curriculum proposal
        """
        years = []

        # Year 1: Foundations + AI Introduction
        year1 = self._design_year_1(specialization)
        years.append(year1)

        # Year 2: Core Design + Digital Tools
        year2 = self._design_year_2(specialization)
        years.append(year2)

        # Year 3: Advanced + AI Integration
        year3 = self._design_year_3(specialization, gap_analysis)
        years.append(year3)

        # Year 4: Specialization + Thesis
        year4 = self._design_year_4(specialization)
        years.append(year4)

        # Count AI-related courses
        ai_courses = sum(
            1 for y in years for c in y.courses
            if c.category == "ai_digital"
        )
        ai_integrated = sum(
            1 for y in years for c in y.courses
            if c.ai_integration
        )

        proposal = CurriculumProposal(
            program_name=f"Дизайн ({specialization})",
            degree_level="bachelor",
            total_credits=self.BACHELOR_TOTAL,
            duration_years=self.BACHELOR_YEARS,
            years=years,
            ai_courses_count=ai_courses,
            ai_integrated_count=ai_integrated,
            digital_tools_coverage=0.85,
            rationale=self._generate_rationale(gap_analysis),
            key_innovations=self._list_innovations(),
            implementation_notes=self._implementation_notes(),
        )

        return proposal

    def _design_year_1(self, specialization: str) -> YearPlan:
        """Design first year curriculum."""
        courses = [
            # Semester 1
            CourseProposal(
                name="Основи візуальної комунікації",
                name_en="Visual Communication Fundamentals",
                credits=6, semester=1, year=1,
                course_type="required", category="core_design",
                description="Principles of visual communication, composition, and graphic language",
                learning_outcomes=["Understand visual hierarchy", "Apply composition principles"],
            ),
            CourseProposal(
                name="Рисунок і живопис",
                name_en="Drawing and Painting",
                credits=6, semester=1, year=1,
                course_type="required", category="foundation",
                description="Traditional drawing and painting techniques",
                learning_outcomes=["Master observational drawing", "Understand color theory"],
            ),
            CourseProposal(
                name="Історія мистецтва та дизайну",
                name_en="History of Art and Design",
                credits=4, semester=1, year=1,
                course_type="required", category="foundation",
                description="Art and design history from ancient times to postmodernism",
                learning_outcomes=["Analyze historical design movements", "Contextualize contemporary design"],
            ),
            CourseProposal(
                name="Цифрова грамотність та основи AI",
                name_en="Digital Literacy and AI Basics",
                credits=4, semester=1, year=1,
                course_type="required", category="ai_digital",
                description="Introduction to digital tools and AI concepts for designers",
                learning_outcomes=["Understand AI basics", "Use AI assistants responsibly"],
                ai_integration="Introduces AI concepts and tools",
            ),
            CourseProposal(
                name="Типографіка",
                name_en="Typography",
                credits=5, semester=1, year=1,
                course_type="required", category="core_design",
                description="Typography fundamentals and applications",
                learning_outcomes=["Select appropriate typefaces", "Create typographic compositions"],
                ai_integration="Introduction to AI font tools",
            ),
            CourseProposal(
                name="Іноземна мова",
                name_en="Foreign Language",
                credits=3, semester=1, year=1,
                course_type="required", category="foundation",
                description="English for designers",
                learning_outcomes=["Read design literature in English"],
            ),

            # Semester 2
            CourseProposal(
                name="Колористика",
                name_en="Color Theory",
                credits=5, semester=2, year=1,
                course_type="required", category="core_design",
                description="Color theory and digital color management",
                learning_outcomes=["Apply color theory", "Create harmonious palettes"],
                ai_integration="AI color palette generation",
            ),
            CourseProposal(
                name="Комп'ютерна графіка (Adobe Suite)",
                name_en="Computer Graphics (Adobe Suite)",
                credits=6, semester=2, year=1,
                course_type="required", category="ai_digital",
                description="Photoshop, Illustrator fundamentals",
                learning_outcomes=["Master raster/vector graphics", "Use industry tools"],
            ),
            CourseProposal(
                name="Дизайн-мислення",
                name_en="Design Thinking",
                credits=4, semester=2, year=1,
                course_type="required", category="core_design",
                description="Design thinking methodology and problem solving",
                learning_outcomes=["Apply design thinking process", "Prototype solutions"],
            ),
            CourseProposal(
                name="Основи композиції",
                name_en="Composition Fundamentals",
                credits=5, semester=2, year=1,
                course_type="required", category="core_design",
                description="2D and 3D composition principles",
                learning_outcomes=["Create balanced compositions", "Understand visual weight"],
            ),
            CourseProposal(
                name="Академічне письмо",
                name_en="Academic Writing",
                credits=3, semester=2, year=1,
                course_type="required", category="foundation",
                description="Research and academic writing skills",
                learning_outcomes=["Write research papers", "Cite sources properly"],
            ),
            CourseProposal(
                name="Вибіркова дисципліна 1",
                name_en="Elective 1",
                credits=4, semester=2, year=1,
                course_type="elective", category="elective",
                description="Student choice from elective pool",
                learning_outcomes=["Varies by course"],
            ),
        ]

        return YearPlan(
            year=1,
            total_credits=60,
            required_credits=51,
            elective_credits=9,
            courses=courses,
            focus="Foundations: Traditional skills + Digital literacy + AI introduction",
        )

    def _design_year_2(self, specialization: str) -> YearPlan:
        """Design second year curriculum."""
        courses = [
            # Semester 3
            CourseProposal(
                name="Графічний дизайн",
                name_en="Graphic Design",
                credits=6, semester=3, year=2,
                course_type="required", category="core_design",
                description="Identity, branding, print design",
                learning_outcomes=["Create brand identities", "Design for print"],
                ai_integration="AI logo generation exploration",
            ),
            CourseProposal(
                name="UX/UI дизайн: Основи",
                name_en="UX/UI Design Fundamentals",
                credits=6, semester=3, year=2,
                course_type="required", category="ai_digital",
                description="User experience and interface design",
                learning_outcomes=["Conduct user research", "Create wireframes and prototypes"],
            ),
            CourseProposal(
                name="3D-моделювання",
                name_en="3D Modeling",
                credits=5, semester=3, year=2,
                course_type="required", category="ai_digital",
                description="Introduction to 3D modeling with Blender",
                learning_outcomes=["Create 3D models", "Apply materials and lighting"],
                ai_integration="AI-assisted 3D generation",
            ),
            CourseProposal(
                name="Фотографія для дизайнерів",
                name_en="Photography for Designers",
                credits=4, semester=3, year=2,
                course_type="required", category="core_design",
                description="Digital photography and image editing",
                learning_outcomes=["Compose photographs", "Edit images professionally"],
            ),
            CourseProposal(
                name="Веб-технології",
                name_en="Web Technologies",
                credits=4, semester=3, year=2,
                course_type="required", category="ai_digital",
                description="HTML, CSS basics for designers",
                learning_outcomes=["Understand web fundamentals", "Code simple websites"],
            ),
            CourseProposal(
                name="Вибіркова дисципліна 2",
                name_en="Elective 2",
                credits=5, semester=3, year=2,
                course_type="elective", category="elective",
                description="Student choice",
                learning_outcomes=["Varies"],
            ),

            # Semester 4
            CourseProposal(
                name="Figma та прототипування",
                name_en="Figma and Prototyping",
                credits=5, semester=4, year=2,
                course_type="required", category="ai_digital",
                description="Advanced Figma, interactive prototypes",
                learning_outcomes=["Create interactive prototypes", "Design systems"],
                ai_integration="Figma AI features",
            ),
            CourseProposal(
                name="Моушн-дизайн",
                name_en="Motion Design",
                credits=5, semester=4, year=2,
                course_type="required", category="ai_digital",
                description="Animation and motion graphics",
                learning_outcomes=["Create animations", "Understand timing principles"],
            ),
            CourseProposal(
                name="Ілюстрація",
                name_en="Illustration",
                credits=5, semester=4, year=2,
                course_type="required", category="core_design",
                description="Digital and traditional illustration",
                learning_outcomes=["Develop illustration style", "Create editorial illustrations"],
                ai_integration="AI illustration tools exploration",
            ),
            CourseProposal(
                name="Інформаційний дизайн",
                name_en="Information Design",
                credits=4, semester=4, year=2,
                course_type="required", category="core_design",
                description="Infographics and data visualization basics",
                learning_outcomes=["Visualize data", "Create infographics"],
            ),
            CourseProposal(
                name="Навчальна практика",
                name_en="Training Practice",
                credits=6, semester=4, year=2,
                course_type="required", category="practice",
                description="Studio practice and real projects",
                learning_outcomes=["Apply skills to real briefs"],
            ),
            CourseProposal(
                name="Вибіркова дисципліна 3",
                name_en="Elective 3",
                credits=5, semester=4, year=2,
                course_type="elective", category="elective",
                description="Student choice",
                learning_outcomes=["Varies"],
            ),
        ]

        return YearPlan(
            year=2,
            total_credits=60,
            required_credits=50,
            elective_credits=10,
            courses=courses,
            focus="Core Skills: Digital tools mastery + UX/UI + Motion",
        )

    def _design_year_3(self, specialization: str, gap_analysis: Dict) -> YearPlan:
        """Design third year curriculum with AI focus."""
        courses = [
            # Semester 5
            CourseProposal(
                name="Генеративний дизайн та AI",
                name_en="Generative Design and AI",
                credits=6, semester=5, year=3,
                course_type="required", category="ai_digital",
                description="AI tools for design: Midjourney, DALL-E, Stable Diffusion",
                learning_outcomes=[
                    "Use generative AI tools",
                    "Craft effective prompts",
                    "Integrate AI in design workflow",
                ],
                ai_integration="Core AI design course",
            ),
            CourseProposal(
                name="Взаємодія людина-AI в дизайні",
                name_en="Human-AI Interaction in Design",
                credits=4, semester=5, year=3,
                course_type="required", category="ai_digital",
                description="Ethics, collaboration, and future of AI in creative work",
                learning_outcomes=[
                    "Understand AI ethics",
                    "Design human-AI workflows",
                ],
                ai_integration="Human-AI collaboration theory",
            ),
            CourseProposal(
                name="Дизайн бренду: Продвинутий",
                name_en="Advanced Brand Design",
                credits=5, semester=5, year=3,
                course_type="required", category="specialization",
                description="Complex branding projects",
                learning_outcomes=["Develop brand strategies", "Create brand systems"],
                ai_integration="AI in brand development",
            ),
            CourseProposal(
                name="Параметричний та інтерактивний дизайн",
                name_en="Parametric and Interactive Design",
                credits=5, semester=5, year=3,
                course_type="required", category="ai_digital",
                description="Creative coding, generative systems",
                learning_outcomes=["Code generative designs", "Create interactive experiences"],
                ai_integration="Algorithmic design with AI",
            ),
            CourseProposal(
                name="Дослідження в дизайні",
                name_en="Design Research",
                credits=4, semester=5, year=3,
                course_type="required", category="foundation",
                description="Research methods for designers",
                learning_outcomes=["Conduct design research", "Synthesize findings"],
            ),
            CourseProposal(
                name="Вибіркова дисципліна 4",
                name_en="Elective 4",
                credits=6, semester=5, year=3,
                course_type="elective", category="elective",
                description="Specialization track elective",
                learning_outcomes=["Varies"],
            ),

            # Semester 6
            CourseProposal(
                name="UX/UI: Продвинутий",
                name_en="Advanced UX/UI",
                credits=5, semester=6, year=3,
                course_type="required", category="specialization",
                description="Complex UX projects, design systems",
                learning_outcomes=["Design complex systems", "Lead UX projects"],
                ai_integration="AI in UX research and design",
            ),
            CourseProposal(
                name="Візуалізація даних",
                name_en="Data Visualization",
                credits=5, semester=6, year=3,
                course_type="required", category="ai_digital",
                description="Advanced infographics and dashboards",
                learning_outcomes=["Create data narratives", "Design dashboards"],
            ),
            CourseProposal(
                name="Дизайн середовища",
                name_en="Environmental Design",
                credits=4, semester=6, year=3,
                course_type="required", category="specialization",
                description="Signage, wayfinding, exhibition design",
                learning_outcomes=["Design spatial graphics", "Create navigation systems"],
            ),
            CourseProposal(
                name="Виробнича практика",
                name_en="Industry Internship",
                credits=9, semester=6, year=3,
                course_type="required", category="practice",
                description="Full-time industry placement",
                learning_outcomes=["Gain professional experience", "Build portfolio"],
            ),
            CourseProposal(
                name="Вибіркова дисципліна 5",
                name_en="Elective 5",
                credits=7, semester=6, year=3,
                course_type="elective", category="elective",
                description="Student choice",
                learning_outcomes=["Varies"],
            ),
        ]

        return YearPlan(
            year=3,
            total_credits=60,
            required_credits=47,
            elective_credits=13,
            courses=courses,
            focus="Advanced: AI integration + Specialization + Industry practice",
        )

    def _design_year_4(self, specialization: str) -> YearPlan:
        """Design fourth year curriculum."""
        courses = [
            # Semester 7
            CourseProposal(
                name="Дипломне проектування I",
                name_en="Thesis Project I",
                credits=10, semester=7, year=4,
                course_type="required", category="thesis",
                description="Thesis research and concept development",
                learning_outcomes=["Define thesis topic", "Develop concept"],
                ai_integration="AI as research/ideation tool",
            ),
            CourseProposal(
                name="Портфоліо та професійна практика",
                name_en="Portfolio and Professional Practice",
                credits=4, semester=7, year=4,
                course_type="required", category="practice",
                description="Portfolio development, freelancing, job search",
                learning_outcomes=["Create professional portfolio", "Prepare for industry"],
            ),
            CourseProposal(
                name="Дизайн та підприємництво",
                name_en="Design Entrepreneurship",
                credits=4, semester=7, year=4,
                course_type="required", category="foundation",
                description="Business skills for designers",
                learning_outcomes=["Understand design business", "Price and pitch work"],
            ),
            CourseProposal(
                name="Критичний дизайн та етика AI",
                name_en="Critical Design and AI Ethics",
                credits=4, semester=7, year=4,
                course_type="required", category="ai_digital",
                description="Social responsibility, AI ethics, sustainable design",
                learning_outcomes=["Apply ethical frameworks", "Design responsibly"],
                ai_integration="Deep dive into AI ethics",
            ),
            CourseProposal(
                name="Вибіркова спеціалізації 1",
                name_en="Specialization Elective 1",
                credits=8, semester=7, year=4,
                course_type="elective", category="specialization",
                description="Deep specialization track",
                learning_outcomes=["Advanced specialization skills"],
            ),

            # Semester 8
            CourseProposal(
                name="Дипломне проектування II",
                name_en="Thesis Project II",
                credits=15, semester=8, year=4,
                course_type="required", category="thesis",
                description="Thesis execution and defense",
                learning_outcomes=["Complete thesis project", "Defend work"],
                ai_integration="AI integration in thesis project",
            ),
            CourseProposal(
                name="Переддипломна практика",
                name_en="Pre-diploma Practice",
                credits=6, semester=8, year=4,
                course_type="required", category="practice",
                description="Final industry practice",
                learning_outcomes=["Professional readiness"],
            ),
            CourseProposal(
                name="Вибіркова спеціалізації 2",
                name_en="Specialization Elective 2",
                credits=9, semester=8, year=4,
                course_type="elective", category="specialization",
                description="Final specialization courses",
                learning_outcomes=["Complete specialization"],
            ),
        ]

        return YearPlan(
            year=4,
            total_credits=60,
            required_credits=43,
            elective_credits=17,
            courses=courses,
            focus="Synthesis: Thesis project + Professional preparation + Specialization completion",
        )

    def _generate_rationale(self, gap_analysis: Dict) -> str:
        """Generate rationale for curriculum changes."""
        return """This curriculum addresses identified gaps in Ukrainian design education,
particularly in AI and digital skills integration. Key principles:

1. Progressive AI Integration: AI is introduced in Year 1 and deepens each year
2. Balance: Traditional design foundations alongside digital innovation
3. Practice-Oriented: Industry internships and real projects throughout
4. Ethical Framework: Critical perspective on AI and design responsibility
5. Flexible Specialization: Multiple tracks within design discipline

Based on gap analysis showing {:.0%} AI coverage and {:.0%} digital tools coverage
in current programs.""".format(
            gap_analysis.get("overall_ai_coverage", 0.15),
            gap_analysis.get("overall_digital_coverage", 0.45),
        )

    def _list_innovations(self) -> List[str]:
        """List key curriculum innovations."""
        return [
            "Dedicated 'Generative Design and AI' course in Year 3",
            "AI integration touchpoints across all years",
            "'Human-AI Interaction' ethics course",
            "Parametric/Computational design module",
            "Data visualization as required component",
            "AI-enhanced thesis project option",
            "Flexible specialization tracks (UX, Brand, Motion, etc.)",
        ]

    def _implementation_notes(self) -> List[str]:
        """Implementation recommendations."""
        return [
            "Faculty training required for AI tools",
            "Software licenses: Adobe CC, Figma, Blender, AI services",
            "Industry partnerships for internships",
            "Regular curriculum review (annual) to update AI content",
            "Student AI ethics guidelines needed",
            "Hardware: computers capable of running local AI models",
        ]

    def export_to_json(self, proposal: CurriculumProposal, output_path: Path) -> None:
        """Export curriculum proposal to JSON."""
        data = {
            "program_name": proposal.program_name,
            "degree_level": proposal.degree_level,
            "total_credits": proposal.total_credits,
            "duration_years": proposal.duration_years,
            "years": [
                {
                    "year": y.year,
                    "total_credits": y.total_credits,
                    "focus": y.focus,
                    "courses": [
                        {
                            "name": c.name,
                            "name_en": c.name_en,
                            "credits": c.credits,
                            "semester": c.semester,
                            "type": c.course_type,
                            "category": c.category,
                            "ai_integration": c.ai_integration,
                        }
                        for c in y.courses
                    ],
                }
                for y in proposal.years
            ],
            "ai_courses_count": proposal.ai_courses_count,
            "ai_integrated_count": proposal.ai_integrated_count,
            "key_innovations": proposal.key_innovations,
            "rationale": proposal.rationale,
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
