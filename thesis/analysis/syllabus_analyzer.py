"""
KDPU Syllabus and OPP Analyzer for Musiienko PhD thesis.
Extracts text from ~134 syllabi PDFs, performs IKK keyword analysis,
tracks curriculum evolution 2017-2021, and classifies courses by IKK relevance.
"""

import json
import re
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
import pdfplumber
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

BASE = Path(__file__).resolve().parent.parent.parent
EXPERIMENT = BASE / "experiment"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "analysis" / "output"
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"

# Directories with syllabi PDFs
SYLLABUS_DIRS = {
    "ГД_програми": EXPERIMENT / "Програми на сайт" / "ДГ пдф",
    "ДО_програми": EXPERIMENT / "Програми на сайт" / "Програми ДО пдф",
    "ДС_програми": EXPERIMENT / "Програми на сайт" / "ДС програма ПДФ",
    "Дизайн_програми": EXPERIMENT / "Програми на сайт" / "Дизайн пдф",
    "ГД_силабуси": EXPERIMENT / "Програми на сайт" / "силабуси ДГ пдф",
    "ДО_силабуси": EXPERIMENT / "Програми на сайт" / "силабуси ДО пдф",
    "ДС_силабуси": EXPERIMENT / "Програми на сайт" / "силабуси ДС пдф",
    "каф_ОМ": EXPERIMENT / "Програми на сайт" / "каф. ОМ",
    "Загальні": EXPERIMENT / "Програми на сайт" / "Заг. кафедри",
}

# OPP evolution files
OPP_FILES = {
    2017: EXPERIMENT / "ОСВІТНІ ПРОГРАМИ" / "ОП Дизайн 2017.pdf",
    2018: EXPERIMENT / "ОСВІТНІ ПРОГРАМИ" / "ОП Дизайн 2018.pdf",
    "ГД_2019": EXPERIMENT / "ОСВІТНІ ПРОГРАМИ" / "ОП Графічний дизайн 2019.pdf",
    "ДО_2019": EXPERIMENT / "ОСВІТНІ ПРОГРАМИ" / "ОП Дизайн одягу 2019.pdf",
    "ДС_2019": EXPERIMENT / "ОСВІТНІ ПРОГРАМИ" / "ОП Дизайн середовища 2019.pdf",
}

OPP_APPROVED = {
    "ГД_2021": EXPERIMENT / "ОПП матеріали" / "ОП затверджені" / "ОПП  Графічний дизайн 2021.pdf",
    "ДО_2021": EXPERIMENT / "ОПП матеріали" / "ОП затверджені" / "ОПП Дизайн одягу 2021.pdf",
    "ДС_2021": EXPERIMENT / "ОПП матеріали" / "ОП затверджені" / "ОПП Дизайн середовища 2021.pdf",
}

# IKK keyword dictionaries (Ukrainian)
IKK_KEYWORDS = {
    "information_analytical": [
        "інформацій", "інформаційн", "пошук", "аналіз даних", "бази даних",
        "інтернет", "цифров", "електронн", "онлайн", "веб",
        "штучн", "інтелект", "ШІ", "AI", "машинн", "нейронн",
        "генератив", "prompt", "промпт",
    ],
    "communicative": [
        "комунікат", "комунікацій", "спілкуван", "презентац",
        "портфоліо", "візуальн", "візуалізац", "співпрац",
        "команд", "колабора", "соціальн", "мережев",
    ],
    "technological": [
        "комп'ютер", "програмн", "технолог", "софт", "software",
        "Adobe", "Photoshop", "Illustrator", "InDesign", "Figma",
        "Blender", "3ds Max", "AutoCAD", "SketchUp", "ArchiCAD",
        "CorelDraw", "Corel", "мультимедій", "анімац", "відео",
        "3D", "моделюван", "рендер", "верст", "вебдизайн",
    ],
    "reflexive": [
        "рефлекс", "самооцін", "самоаналіз", "самоосвіт",
        "самовдоскон", "саморозвит", "крити", "етик", "етичн",
        "авторськ", "інтелектуальн", "плагіат",
    ],
}


def extract_pdf_text(filepath: Path) -> str:
    """Extract text from a PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"  Error extracting {filepath.name}: {e}")
    return text


def count_ikk_keywords(text: str) -> dict[str, dict[str, int]]:
    """Count IKK keyword occurrences in text by component."""
    text_lower = text.lower()
    results = {}
    for component, keywords in IKK_KEYWORDS.items():
        keyword_counts = {}
        for kw in keywords:
            count = len(re.findall(re.escape(kw.lower()), text_lower))
            if count > 0:
                keyword_counts[kw] = count
        results[component] = keyword_counts
    return results


def classify_ikk_relevance(keyword_counts: dict) -> str:
    """Classify course IKK relevance: high/medium/low/none."""
    total = sum(sum(v.values()) for v in keyword_counts.values())
    n_components = sum(1 for v in keyword_counts.values() if sum(v.values()) > 0)

    if total >= 15 and n_components >= 3:
        return "high"
    elif total >= 8 and n_components >= 2:
        return "medium"
    elif total >= 3:
        return "low"
    else:
        return "none"


def analyze_syllabi():
    """Analyze all syllabi PDFs for IKK content."""
    results = []

    for dir_label, dir_path in SYLLABUS_DIRS.items():
        if not dir_path.exists():
            print(f"  Directory not found: {dir_path}")
            continue

        pdf_files = list(dir_path.glob("*.pdf")) + list(dir_path.glob("*.PDF"))
        print(f"  {dir_label}: {len(pdf_files)} PDFs")

        for pdf in sorted(pdf_files):
            text = extract_pdf_text(pdf)
            if not text.strip():
                print(f"    Skipped (empty): {pdf.name}")
                continue

            kw_counts = count_ikk_keywords(text)
            relevance = classify_ikk_relevance(kw_counts)

            # Determine program from directory
            prog = "shared"
            if "ГД" in dir_label or "ДГ" in dir_label:
                prog = "ГД"
            elif "ДО" in dir_label:
                prog = "ДО"
            elif "ДС" in dir_label:
                prog = "ДС"

            doc_type = "syllabus" if "силабус" in dir_label.lower() else "program"

            results.append({
                "file": pdf.name,
                "directory": dir_label,
                "program": prog,
                "doc_type": doc_type,
                "text_length": len(text),
                "ikk_relevance": relevance,
                "info_analytical_total": sum(kw_counts["information_analytical"].values()),
                "communicative_total": sum(kw_counts["communicative"].values()),
                "technological_total": sum(kw_counts["technological"].values()),
                "reflexive_total": sum(kw_counts["reflexive"].values()),
                "total_ikk_keywords": sum(sum(v.values()) for v in kw_counts.values()),
                "top_keywords": "; ".join(
                    f"{kw}({c})" for comp in kw_counts.values()
                    for kw, c in sorted(comp.items(), key=lambda x: -x[1])[:3]
                    if c > 0
                ),
            })

    return pd.DataFrame(results)


def analyze_opp_evolution():
    """Track curriculum evolution 2017-2021 from OPP documents."""
    opp_texts = {}

    # Read all OPP files
    for label, filepath in {**OPP_FILES, **OPP_APPROVED}.items():
        if filepath.exists():
            text = extract_pdf_text(filepath)
            opp_texts[label] = text
            print(f"  OPP {label}: {len(text)} chars extracted")
        else:
            print(f"  OPP {label}: file not found ({filepath})")

    # Extract course names from each OPP (look for table-like structures)
    courses_by_opp = {}
    for label, text in opp_texts.items():
        # Find lines that look like course names (after numbers or table markers)
        lines = text.split('\n')
        courses = set()
        for line in lines:
            line = line.strip()
            # Skip very short or very long lines
            if 5 < len(line) < 100:
                # Remove leading numbers, dots, parentheses
                cleaned = re.sub(r'^[\d\.\)\s]+', '', line).strip()
                if cleaned and not re.match(r'^[\d\.]+$', cleaned):
                    courses.add(cleaned)
        courses_by_opp[label] = courses

    return courses_by_opp, opp_texts


def plot_ikk_heatmap(df: pd.DataFrame, output_path: Path):
    """Create heatmap of IKK keyword density by course and component."""
    # Select top 30 courses by total IKK keywords
    top_courses = df.nlargest(30, 'total_ikk_keywords')

    if top_courses.empty:
        print("  No courses with IKK keywords found for heatmap")
        return

    heatmap_data = top_courses.set_index('file')[
        ['info_analytical_total', 'communicative_total', 'technological_total', 'reflexive_total']
    ]
    heatmap_data.columns = ['Інформаційно-\nаналітичний', 'Комунікативний', 'Технологічний', 'Рефлексивний']

    # Shorten file names
    heatmap_data.index = [name[:40] + "..." if len(name) > 40 else name for name in heatmap_data.index]

    fig, ax = plt.subplots(figsize=(10, max(8, len(heatmap_data) * 0.35)))
    sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='YlOrRd', ax=ax,
                linewidths=0.5, cbar_kws={'label': 'Кількість ключових слів'})
    ax.set_title('Насиченість ІКК-контентом за компонентами (топ-30 дисциплін)', fontsize=13)
    ax.set_ylabel('')
    plt.tight_layout()
    fig.savefig(output_path, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved heatmap: {output_path}")


def plot_relevance_distribution(df: pd.DataFrame, output_path: Path):
    """Pie chart of IKK relevance classification."""
    counts = df['ikk_relevance'].value_counts()
    colors = {'high': '#4CAF50', 'medium': '#FFC107', 'low': '#FF9800', 'none': '#F44336'}
    labels_ukr = {'high': 'Висока', 'medium': 'Середня', 'low': 'Низька', 'none': 'Відсутня'}

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        [counts.get(k, 0) for k in ['high', 'medium', 'low', 'none']],
        labels=[labels_ukr[k] for k in ['high', 'medium', 'low', 'none']],
        colors=[colors[k] for k in ['high', 'medium', 'low', 'none']],
        autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12}
    )
    ax.set_title('Розподіл дисциплін за рівнем ІКК-релевантності', fontsize=14)
    plt.tight_layout()
    fig.savefig(output_path, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved relevance distribution: {output_path}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Analyzing KDPU syllabi for IKK content ===")
    syllabus_df = analyze_syllabi()

    if not syllabus_df.empty:
        print(f"\nTotal documents analyzed: {len(syllabus_df)}")
        print(f"IKK relevance distribution:")
        print(syllabus_df['ikk_relevance'].value_counts().to_string())
        print(f"\nBy program:")
        print(syllabus_df.groupby(['program', 'ikk_relevance']).size().unstack(fill_value=0).to_string())

        syllabus_df.to_csv(OUTPUT_DIR / "syllabus_ikk_analysis.csv", index=False)
        print(f"\nSaved to {OUTPUT_DIR / 'syllabus_ikk_analysis.csv'}")

        print("\n=== Generating visualizations ===")
        plot_ikk_heatmap(syllabus_df, FIGURES_DIR / "syllabus_ikk_heatmap.pdf")
        plot_relevance_distribution(syllabus_df, FIGURES_DIR / "syllabus_ikk_relevance.pdf")

    print("\n=== Analyzing OPP evolution 2017-2021 ===")
    courses_by_opp, opp_texts = analyze_opp_evolution()

    # Save OPP course lists
    opp_summary = {}
    for label, courses in courses_by_opp.items():
        opp_summary[str(label)] = {
            "n_courses_extracted": len(courses),
            "text_length": len(opp_texts.get(label, "")),
        }
    with open(OUTPUT_DIR / "opp_evolution_summary.json", "w", encoding="utf-8") as f:
        json.dump(opp_summary, f, ensure_ascii=False, indent=2)

    # IKK keyword analysis on OPP texts
    opp_ikk = []
    for label, text in opp_texts.items():
        kw_counts = count_ikk_keywords(text)
        opp_ikk.append({
            "opp": str(label),
            "info_analytical": sum(kw_counts["information_analytical"].values()),
            "communicative": sum(kw_counts["communicative"].values()),
            "technological": sum(kw_counts["technological"].values()),
            "reflexive": sum(kw_counts["reflexive"].values()),
            "total": sum(sum(v.values()) for v in kw_counts.values()),
        })

    opp_ikk_df = pd.DataFrame(opp_ikk)
    print("\nOPP IKK keyword counts:")
    print(opp_ikk_df.to_string(index=False))
    opp_ikk_df.to_csv(OUTPUT_DIR / "opp_ikk_evolution.csv", index=False)

    # Summary statistics for thesis
    summary = {
        "total_syllabi_analyzed": len(syllabus_df),
        "relevance_counts": syllabus_df['ikk_relevance'].value_counts().to_dict() if not syllabus_df.empty else {},
        "mean_ikk_keywords": round(syllabus_df['total_ikk_keywords'].mean(), 1) if not syllabus_df.empty else 0,
        "top_technological_course": syllabus_df.nlargest(1, 'technological_total')['file'].values[0] if not syllabus_df.empty else "",
        "opp_files_processed": len(opp_texts),
    }
    with open(OUTPUT_DIR / "syllabus_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nDone. All outputs in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
