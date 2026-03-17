"""
Publication-quality plots for thesis.

Generates statistical visualizations, network diagrams,
and topic model visualizations in PDF, PNG, and TikZ formats.
"""

from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
import re

import pandas as pd
import numpy as np

# Lazy imports for plotting libraries
_plt = None
_sns = None
_tikzplotlib = None


def _get_matplotlib():
    global _plt
    if _plt is None:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        _plt = plt
    return _plt


def _get_seaborn():
    global _sns
    if _sns is None:
        import seaborn as sns
        _sns = sns
    return _sns


def _get_tikzplotlib():
    """Lazy load tikzplotlib for TikZ export."""
    global _tikzplotlib
    if _tikzplotlib is None:
        try:
            import tikzplotlib
            _tikzplotlib = tikzplotlib
        except ImportError:
            print("Warning: tikzplotlib not installed. TikZ export disabled.")
            print("Install with: pip install tikzplotlib")
            _tikzplotlib = False
    return _tikzplotlib


# Ukrainian to English course name translations
COURSE_TRANSLATIONS = {
    # Core design courses
    "філософія": "Philosophy",
    "живопис": "Painting",
    "рисунок": "Drawing",
    "іноземна мова": "Foreign Language",
    "практика": "Practice",
    "українська мова за професійним спрямуванням": "Ukrainian for Professional Communication",
    "навчальна практика": "Educational Practice",
    "графіка": "Graphics",
    "історія мистецтва": "Art History",
    "історія культури": "Cultural History",
    "проектування": "Design/Projecting",
    "проєктування": "Design/Projecting",
    "формотворення": "Form Making",
    "педагогічна практика": "Pedagogical Practice",
    "переддипломна практика": "Pre-Diploma Practice",
    "дизайн інтер'єру": "Interior Design",
    "матеріалознавство": "Materials Science",
    "композиція": "Composition",
    "кольорознавство": "Color Science",
    "комп'ютерна графіка": "Computer Graphics",
    "типографіка": "Typography",
    "web дизайн": "Web Design",
    "web-дизайн": "Web Design",
    "веб-дизайн": "Web Design",
    "3d-моделювання": "3D Modeling",
    "технології 3d-моделювання": "3D Modeling Technologies",
    "фотографія": "Photography",
    "анімація": "Animation",
    "дизайн реклами": "Advertising Design",
    "шрифт": "Font/Typography",
    "ергономіка": "Ergonomics",
    "інфографіка": "Infographics",
    "дизайн інтерфейсів": "Interface Design",
    "візуальна комунікація": "Visual Communication",
    "основи дизайну": "Design Fundamentals",
    "історія дизайну": "Design History",
    "теорія дизайну": "Design Theory",
    "проектна графіка": "Project Graphics",
    "академічний рисунок": "Academic Drawing",
    "академічний живопис": "Academic Painting",
    "декоративно-прикладне мистецтво": "Decorative and Applied Arts",
    "скульптура": "Sculpture",
    "пластична анатомія": "Plastic Anatomy",
    "перспектива": "Perspective",
    "нарисна геометрія": "Descriptive Geometry",
    "естетика": "Aesthetics",
    "етика": "Ethics",
    "психологія": "Psychology",
    "педагогіка": "Pedagogy",
    "економіка": "Economics",
    "менеджмент": "Management",
    "маркетинг": "Marketing",
    "безпека життєдіяльності": "Life Safety",
    "охорона праці": "Occupational Safety",
    "фізичне виховання": "Physical Education",
    "цифрова ілюстрація": "Digital Illustration",
    "друкована графіка": "Print Graphics",
    "поліграфія": "Polygraphy/Printing",
    "упаковка": "Packaging",
    "брендинг": "Branding",
    "фірмовий стиль": "Corporate Identity",
    "редакційний дизайн": "Editorial Design",
    "видавнича справа": "Publishing",
    "мультимедіа": "Multimedia",
    "інтерактивний дизайн": "Interactive Design",
    "motion design": "Motion Design",
    "моушн-дизайн": "Motion Design",
    "відеомонтаж": "Video Editing",
    "звуковий дизайн": "Sound Design",
    "гейм-дизайн": "Game Design",
    "ux/ui дизайн": "UX/UI Design",
    "дизайн середовища": "Environmental Design",
    "ландшафтний дизайн": "Landscape Design",
    "меблі": "Furniture",
    "текстильний дизайн": "Textile Design",
    "модний дизайн": "Fashion Design",
    "костюм": "Costume",
    "робота": "Work/Project",
    "курсова робота": "Course Work",
    "дипломна робота": "Diploma Work",
    "виробнича практика": "Industrial Practice",
    "переддипломна практика": "Pre-Diploma Practice",
    "методологія наукових досліджень": "Research Methodology",
    "інтелектуальна власність": "Intellectual Property",
    "правознавство": "Law",
    "соціологія": "Sociology",
    "культурологія": "Cultural Studies",
    "релігієзнавство": "Religious Studies",
    "політологія": "Political Science",
    "логіка": "Logic",
    "риторика": "Rhetoric",
    "ділова комунікація": "Business Communication",
    "англійська мова": "English",
    "німецька мова": "German",
    "французька мова": "French",
    "іноземна мова за професійним спрямуванням": "Professional Foreign Language",
    "інформаційні технології": "Information Technologies",
    "інформатика": "Informatics",
    "вища математика": "Higher Mathematics",
    "архітектура": "Architecture",
    "дизайн архітектурного середовища": "Architectural Environment Design",
    "благоустрій": "Landscaping",
    "освітлення": "Lighting",
    "кераміка": "Ceramics",
    "вітраж": "Stained Glass",
    "батик": "Batik",
    "вишивка": "Embroidery",
    "ткацтво": "Weaving",
    "розпис": "Painting/Decoration",
    "різьба": "Carving",
    "ковальство": "Blacksmithing",
    "ювелірна справа": "Jewelry Making",
    "реставрація": "Restoration",
    "музеєзнавство": "Museum Studies",
    "виставкова діяльність": "Exhibition Activities",
    "арт-менеджмент": "Art Management",
    "креативні індустрії": "Creative Industries",
    "візуальні комунікації": "Visual Communications",
    "середовищний дизайн": "Environmental Design",
    "предметний дизайн": "Product Design",
    "промисловий дизайн": "Industrial Design",
    "графічний дизайн": "Graphic Design",
    "дизайн одягу": "Clothing Design",
    "дизайн тканин": "Fabric Design",
    "дизайн меблів": "Furniture Design",
    "дизайн освітлення": "Lighting Design",
    "виробнича (проєктна)": "Industrial (Project)",
    "теорія дизайну візуа": "Visual Design Theory",
    "практикум": "Practicum",
    "історія зарубіжного": "History of Foreign",
    "методологія і органі": "Methodology and Organization",
    "інформаційні та цифр": "Information and Digital",
    "навчально-ознайомча": "Educational-Introductory",
    "іноземна мова (англі": "Foreign Language (English)",
    "дипломне проектуванн": "Diploma Design",
    # Additional translations
    "українська мова (за професійни": "Ukrainian for Prof. Purposes",
    "наукових досліджень": "Research Studies",
    "кваліфікаційної роботи": "Qualification Work",
    "теорія та методика дизайну": "Design Theory and Methods",
    "ергономіки": "Ergonomics",
    "основи наукових досліджень": "Research Fundamentals",
    "історія українського мистецтва": "History of Ukrainian Art",
    "етнодизайн": "Ethno-design",
    "історія мистецтв": "Art History",
    "комп'ютерні технології в дизай": "Computer Technologies in Design",
    "історія мистецтв та дизайну": "History of Art and Design",
    "фото та відео монтаж": "Photo and Video Editing",
    "основи фотовідеодизайну": "Photo-Video Design Basics",
    "web_дизайн_та_web_програмуванн": "Web Design and Programming",
    "шовкодрук": "Screen Printing",
    "english for career development": "English for Career Development",
    "дизайн інтер'єру": "Interior Design",
    "практичні студії": "Practical Studios",
    "основи академічного письма": "Academic Writing Fundamentals",
    "історія та культура україни": "History and Culture of Ukraine",
    "комп'ютерні технології": "Computer Technologies",
    "інтелектуальна власність": "Intellectual Property",
    "академічне письмо": "Academic Writing",
    "наукове дослідження": "Scientific Research",
    "магістерська робота": "Master's Thesis",
    "бакалаврська робота": "Bachelor's Thesis",
    "дипломна робота": "Diploma Thesis",
    "курсова робота": "Coursework",
    "атестація": "Attestation",
    "практика": "Practice",
    "переддипломна": "Pre-Diploma",
    "виробнича": "Industrial",
    "навчальна": "Educational",
    "педагогічна": "Pedagogical",
    "стажування": "Internship",
    "дизайн": "Design",
    "мистецтво": "Art",
    "культура": "Culture",
    "історія": "History",
    "теорія": "Theory",
    "методика": "Methodology",
    "основи": "Fundamentals",
}


def _translate_course_for_report(name: str) -> str:
    """Quick translation for reports - fallback function."""
    if not name:
        return ""

    name_lower = name.lower().strip()

    # Check direct match
    if name_lower in COURSE_TRANSLATIONS:
        return COURSE_TRANSLATIONS[name_lower]

    # Partial match
    for uk, en in COURSE_TRANSLATIONS.items():
        if uk in name_lower:
            return en

    # Already English
    if all(ord(c) < 128 or c in ' -_' for c in name):
        return name.title()

    return name[:30] + "..." if len(name) > 30 else name


class ThesisPlotter:
    """Generate publication-quality plots for thesis in multiple formats."""

    # Color palette
    COLORS = {
        "primary": "#1f77b4",
        "secondary": "#ff7f0e",
        "accent": "#2ca02c",
        "bachelor": "#3498db",
        "master": "#e74c3c",
        "phd": "#9b59b6",
        "required": "#2ecc71",
        "elective": "#f1c40f",
    }

    # Plot style settings
    STYLE = {
        "figure.figsize": (10, 6),
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": 150,
    }

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir) if output_dir else Path("thesis_output/figures")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for each format
        (self.output_dir / "png").mkdir(exist_ok=True)
        (self.output_dir / "pdf").mkdir(exist_ok=True)
        (self.output_dir / "tikz").mkdir(exist_ok=True)

        plt = _get_matplotlib()
        plt.rcParams.update(self.STYLE)

    def _save_figure_all_formats(self, fig, base_filename: str) -> Dict[str, Path]:
        """
        Save figure in PNG, PDF, and TikZ formats.

        Returns dict with paths to each format.
        """
        plt = _get_matplotlib()
        tikzplotlib = _get_tikzplotlib()

        paths = {}
        base_name = Path(base_filename).stem

        # Save PNG
        png_path = self.output_dir / "png" / f"{base_name}.png"
        fig.savefig(png_path, bbox_inches="tight", dpi=300)
        paths["png"] = png_path

        # Save PDF
        pdf_path = self.output_dir / "pdf" / f"{base_name}.pdf"
        fig.savefig(pdf_path, bbox_inches="tight", format="pdf")
        paths["pdf"] = pdf_path

        # Save TikZ
        if tikzplotlib:
            tikz_path = self.output_dir / "tikz" / f"{base_name}.tex"
            try:
                tikzplotlib.save(str(tikz_path), figure=fig)
                paths["tikz"] = tikz_path
            except Exception as e:
                # Some plots may not be fully supported by tikzplotlib
                print(f"Warning: TikZ export failed for {base_name}: {e}")
                # Create a manual TikZ stub
                self._create_tikz_stub(tikz_path, base_name)
                paths["tikz"] = tikz_path
        else:
            # Create manual TikZ stub if tikzplotlib not available
            tikz_path = self.output_dir / "tikz" / f"{base_name}.tex"
            self._create_tikz_stub(tikz_path, base_name)
            paths["tikz"] = tikz_path

        return paths

    def _create_tikz_stub(self, path: Path, name: str):
        """Create a TikZ stub that includes the PDF figure."""
        tikz_content = f"""% TikZ/PGFplots figure: {name}
% Auto-generated - includes PDF version
\\begin{{figure}}[htbp]
    \\centering
    \\includegraphics[width=\\textwidth]{{figures/pdf/{name}.pdf}}
    \\caption{{{name.replace('_', ' ').title()}}}
    \\label{{fig:{name}}}
\\end{{figure}}
"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(tikz_content)

    def _translate_course_name(self, name: str) -> str:
        """Translate Ukrainian course name to English."""
        if not name:
            return ""

        name_lower = name.lower().strip()

        # Direct match
        if name_lower in COURSE_TRANSLATIONS:
            return COURSE_TRANSLATIONS[name_lower]

        # Partial match - check if any key is contained in name
        for uk, en in COURSE_TRANSLATIONS.items():
            if uk in name_lower:
                return en

        # Check if it's already English (contains mostly ASCII)
        if all(ord(c) < 128 or c in ' -_' for c in name):
            return name.title()

        # Return original with note that it's untranslated
        # Clean up for display
        return name[:30] + "..." if len(name) > 30 else name

    def plot_program_distribution(
        self,
        df_programs: pd.DataFrame,
        filename: str = "program_distribution",
    ) -> Dict[str, Path]:
        """Plot distribution of programs by degree level."""
        plt = _get_matplotlib()
        sns = _get_seaborn()

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Pie chart by level
        level_counts = df_programs["degree_level"].value_counts()
        colors = [self.COLORS.get(l, "#gray") for l in level_counts.index]

        axes[0].pie(
            level_counts.values,
            labels=[self._translate_level(l) for l in level_counts.index],
            autopct="%1.1f%%",
            colors=colors,
            startangle=90,
        )
        axes[0].set_title("Programs by Degree Level")

        # Bar chart by level
        level_names = [self._translate_level(l) for l in level_counts.index]
        bars = axes[1].bar(level_names, level_counts.values, color=colors)
        axes[1].set_ylabel("Number of Programs")
        axes[1].set_title("Program Count by Level")

        # Add value labels
        for bar, count in zip(bars, level_counts.values):
            axes[1].text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                str(count),
                ha="center",
            )

        plt.tight_layout()

        paths = self._save_figure_all_formats(fig, filename)
        plt.close()

        return paths

    def plot_courses_per_program(
        self,
        df_programs: pd.DataFrame,
        filename: str = "courses_per_program",
    ) -> Dict[str, Path]:
        """Plot distribution of courses per program."""
        plt = _get_matplotlib()
        sns = _get_seaborn()

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Histogram overall
        sns.histplot(
            df_programs["num_courses"],
            bins=20,
            ax=axes[0],
            color=self.COLORS["primary"],
        )
        axes[0].axvline(
            df_programs["num_courses"].mean(),
            color="red",
            linestyle="--",
            label=f"Mean: {df_programs['num_courses'].mean():.1f}",
        )
        axes[0].set_xlabel("Number of Educational Components")
        axes[0].set_ylabel("Number of Programs")
        axes[0].set_title("Distribution of Components per Program")
        axes[0].legend()

        # Box plot by level
        level_order = ["bachelor", "master", "phd"]
        available_levels = [l for l in level_order if l in df_programs["degree_level"].values]

        sns.boxplot(
            data=df_programs[df_programs["degree_level"].isin(available_levels)],
            x="degree_level",
            y="num_courses",
            order=available_levels,
            palette=[self.COLORS.get(l, "gray") for l in available_levels],
            ax=axes[1],
        )
        axes[1].set_xticklabels([self._translate_level(l) for l in available_levels])
        axes[1].set_xlabel("Degree Level")
        axes[1].set_ylabel("Number of Components")
        axes[1].set_title("Components by Degree Level")

        plt.tight_layout()

        paths = self._save_figure_all_formats(fig, filename)
        plt.close()

        return paths

    def plot_course_type_distribution(
        self,
        df_courses: pd.DataFrame,
        filename: str = "course_types",
    ) -> Dict[str, Path]:
        """Plot distribution of course types."""
        plt = _get_matplotlib()
        sns = _get_seaborn()

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Overall distribution
        type_counts = df_courses["course_type"].value_counts()
        type_labels = [self._translate_type(t) for t in type_counts.index]

        axes[0].pie(
            type_counts.values,
            labels=type_labels,
            autopct="%1.1f%%",
            colors=[self.COLORS.get(t, "gray") for t in type_counts.index],
        )
        axes[0].set_title("Distribution by Component Type")

        # Stacked bar by level
        pivot = pd.crosstab(
            df_courses["degree_level"],
            df_courses["course_type"],
            normalize="index",
        ) * 100

        pivot_filtered = pivot.reindex(["bachelor", "master", "phd"]).dropna()
        pivot_filtered.plot(
            kind="bar",
            stacked=True,
            ax=axes[1],
            color=[self.COLORS.get(c, "gray") for c in pivot_filtered.columns],
        )
        axes[1].set_xticklabels(
            [self._translate_level(l) for l in pivot_filtered.index],
            rotation=0,
        )
        axes[1].set_xlabel("Degree Level")
        axes[1].set_ylabel("Percentage of Components")
        axes[1].set_title("Component Types by Level")
        axes[1].legend(
            [self._translate_type(t) for t in pivot_filtered.columns],
            loc="upper right",
        )

        plt.tight_layout()

        paths = self._save_figure_all_formats(fig, filename)
        plt.close()

        return paths

    def plot_top_courses(
        self,
        df_courses: pd.DataFrame,
        top_n: int = 20,
        filename: str = "top_courses",
    ) -> Dict[str, Path]:
        """Plot most common courses across programs (translated to English)."""
        plt = _get_matplotlib()
        sns = _get_seaborn()

        # Get top courses
        course_counts = df_courses["name"].value_counts().head(top_n)

        fig, ax = plt.subplots(figsize=(10, 8))

        # Horizontal bar chart
        y_pos = range(len(course_counts))
        bars = ax.barh(
            y_pos,
            course_counts.values,
            color=self.COLORS["primary"],
        )

        # Translate and truncate names
        labels = [
            self._translate_course_name(name)
            for name in course_counts.index
        ]
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()

        ax.set_xlabel("Number of Programs")
        ax.set_title(f"Top-{top_n} Most Common Components")

        # Add value labels
        for bar, count in zip(bars, course_counts.values):
            ax.text(
                bar.get_width() + 0.3,
                bar.get_y() + bar.get_height() / 2,
                str(count),
                va="center",
            )

        plt.tight_layout()

        paths = self._save_figure_all_formats(fig, filename)
        plt.close()

        return paths

    def plot_gap_analysis(
        self,
        gap_result: Dict[str, Any],
        filename: str = "gap_analysis",
    ) -> Dict[str, Path]:
        """Plot AI/digital skills gap analysis results."""
        plt = _get_matplotlib()
        sns = _get_seaborn()

        fig, axes = plt.subplots(1, 2, figsize=(12, 6))

        # Coverage scores
        coverage = gap_result.get("coverage_scores", {})
        if coverage:
            categories = list(coverage.keys())
            scores = [coverage[c] * 100 for c in categories]
            cat_labels = [self._translate_coverage(c) for c in categories]

            bars = axes[0].barh(cat_labels, scores, color=self.COLORS["primary"])
            axes[0].set_xlim(0, 100)
            axes[0].set_xlabel("Coverage (%)")
            axes[0].set_title("AI & Digital Skills Coverage")

            # Add value labels
            for bar, score in zip(bars, scores):
                axes[0].text(
                    bar.get_width() + 1,
                    bar.get_y() + bar.get_height() / 2,
                    f"{score:.1f}%",
                    va="center",
                )

        # Skill coverage details
        skill_details = gap_result.get("skill_details", [])
        if skill_details:
            skills = [d["skill"] if isinstance(d, dict) else d.skill for d in skill_details]
            scores = [
                (d["coverage_score"] if isinstance(d, dict) else d.coverage_score) * 100
                for d in skill_details
            ]

            # Color by coverage level
            colors = [
                "#2ecc71" if s >= 30 else ("#f1c40f" if s > 0 else "#e74c3c")
                for s in scores
            ]

            y_pos = range(len(skills))
            bars = axes[1].barh(y_pos, scores, color=colors)
            axes[1].set_yticks(y_pos)
            axes[1].set_yticklabels([s[:25] for s in skills])
            axes[1].invert_yaxis()
            axes[1].set_xlim(0, 100)
            axes[1].set_xlabel("Coverage (%)")
            axes[1].set_title("Detailed Skills Analysis")

            # Add threshold line
            axes[1].axvline(30, color="gray", linestyle="--", alpha=0.5)

        plt.tight_layout()

        paths = self._save_figure_all_formats(fig, filename)
        plt.close()

        return paths

    def plot_topic_distribution(
        self,
        topic_result: Dict[str, Any],
        filename: str = "topic_distribution",
    ) -> Optional[Dict[str, Path]]:
        """Plot topic modeling results."""
        plt = _get_matplotlib()
        sns = _get_seaborn()

        topics = topic_result.get("topics", [])
        if not topics:
            return None

        fig, ax = plt.subplots(figsize=(10, 6))

        # Get topic sizes
        topic_names = []
        topic_sizes = []

        for t in topics[:15]:  # Top 15 topics
            if isinstance(t, dict):
                name = t.get("name", f"Topic {t.get('id', '?')}")
                size = t.get("document_count", 0)
            else:
                name = t.name
                size = t.document_count

            # Shorten name
            topic_names.append(name[:30] + "..." if len(name) > 30 else name)
            topic_sizes.append(size)

        # Bar chart
        y_pos = range(len(topic_names))
        bars = ax.barh(y_pos, topic_sizes, color=self.COLORS["primary"])
        ax.set_yticks(y_pos)
        ax.set_yticklabels(topic_names)
        ax.invert_yaxis()

        ax.set_xlabel("Number of Documents")
        ax.set_title("Topic Distribution in Curricula")

        plt.tight_layout()

        paths = self._save_figure_all_formats(fig, filename)
        plt.close()

        return paths

    def plot_network_summary(
        self,
        network_result: Dict[str, Any],
        filename: str = "network_summary",
    ) -> Dict[str, Path]:
        """Plot network analysis summary statistics (English only)."""
        plt = _get_matplotlib()

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        metrics = network_result.get("network_metrics", {})

        # Metrics summary as text
        axes[0, 0].axis("off")
        metrics_text = f"""
        Network Summary:

        Nodes: {metrics.get('num_nodes', 'N/A')}
        Edges: {metrics.get('num_edges', 'N/A')}
        Density: {metrics.get('density', 0):.4f}
        Avg Degree: {metrics.get('avg_degree', 0):.2f}
        Clustering: {metrics.get('avg_clustering', 0):.4f}
        Components: {metrics.get('num_components', 'N/A')}
        """
        axes[0, 0].text(
            0.1, 0.5, metrics_text,
            fontsize=12,
            fontfamily="monospace",
            verticalalignment="center",
        )
        axes[0, 0].set_title("Network Metrics")

        # Community sizes
        communities = network_result.get("communities", [])
        if communities:
            comm_sizes = [
                c.get("size", 0) if isinstance(c, dict) else c.size
                for c in communities[:10]
            ]
            comm_labels = [f"C{i+1}" for i in range(len(comm_sizes))]
            axes[0, 1].bar(comm_labels, comm_sizes, color=self.COLORS["secondary"])
            axes[0, 1].set_xlabel("Community")
            axes[0, 1].set_ylabel("Size (courses)")
            axes[0, 1].set_title("Community Sizes (Top 10)")

        # Top nodes by degree - TRANSLATED TO ENGLISH
        node_metrics = network_result.get("node_metrics", [])
        if node_metrics:
            top_nodes = node_metrics[:10]
            names = []
            degrees = []
            for n in top_nodes:
                raw_name = n.get("node", "?") if isinstance(n, dict) else n.node
                # Translate course name to English
                english_name = self._translate_course_name(raw_name)
                names.append(english_name[:25] if len(english_name) > 25 else english_name)
                degrees.append(n.get("degree", 0) if isinstance(n, dict) else n.degree)

            axes[1, 0].barh(range(len(names)), degrees, color=self.COLORS["accent"])
            axes[1, 0].set_yticks(range(len(names)))
            axes[1, 0].set_yticklabels(names)
            axes[1, 0].invert_yaxis()
            axes[1, 0].set_xlabel("Degree (co-occurrences)")
            axes[1, 0].set_title("Top-10 Central Courses")

        # Degree distribution
        if node_metrics:
            all_degrees = [
                n.get("degree", 0) if isinstance(n, dict) else n.degree
                for n in node_metrics
            ]
            axes[1, 1].hist(all_degrees, bins=30, color=self.COLORS["primary"], edgecolor='white')
            axes[1, 1].set_xlabel("Degree")
            axes[1, 1].set_ylabel("Frequency")
            axes[1, 1].set_title("Degree Distribution")
            axes[1, 1].set_yscale('log')

        plt.tight_layout()

        paths = self._save_figure_all_formats(fig, filename)
        plt.close()

        return paths

    def _translate_level(self, level: str) -> str:
        """Return English degree level name."""
        translations = {
            "bachelor": "Bachelor",
            "master": "Master",
            "phd": "PhD",
            "unknown": "Unknown",
        }
        return translations.get(level, level)

    def _translate_type(self, course_type: str) -> str:
        """Return English course type name."""
        translations = {
            "required": "Required",
            "elective": "Elective",
            "practice": "Practice",
            "attestation": "Attestation",
        }
        return translations.get(course_type, course_type)

    def _translate_coverage(self, category: str) -> str:
        """Return English coverage category name."""
        translations = {
            "ai_core": "AI Core Skills",
            "digital_tools": "Digital Tools",
            "overall": "Overall",
            "ai_digital": "AI & Digital",
        }
        return translations.get(category, category.replace("_", " ").title())

    def generate_all_plots(
        self,
        df_programs: pd.DataFrame,
        df_courses: pd.DataFrame,
        gap_result: Optional[Dict] = None,
        topic_result: Optional[Dict] = None,
        network_result: Optional[Dict] = None,
    ) -> Dict[str, Dict[str, Path]]:
        """Generate all thesis plots in PNG, PDF, and TikZ formats."""
        all_paths = {}

        all_paths["program_distribution"] = self.plot_program_distribution(df_programs)
        all_paths["courses_per_program"] = self.plot_courses_per_program(df_programs)
        all_paths["course_types"] = self.plot_course_type_distribution(df_courses)
        all_paths["top_courses"] = self.plot_top_courses(df_courses)

        if gap_result:
            all_paths["gap_analysis"] = self.plot_gap_analysis(gap_result)

        if topic_result:
            result = self.plot_topic_distribution(topic_result)
            if result:
                all_paths["topic_distribution"] = result

        if network_result:
            all_paths["network_summary"] = self.plot_network_summary(network_result)

        return all_paths
