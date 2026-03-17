#!/usr/bin/env python3
"""
BERTopic Topic Modeling of 3,043 NAQA Design Courses.

Runs topic modeling on course names from 122 Ukrainian design programs,
generating tables and figures for Chapter 2.1 of the thesis.
"""

import sys
import json
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Configure matplotlib for Ukrainian text
rcParams["font.family"] = "DejaVu Sans"
rcParams["font.size"] = 11

# Add design package to path
DESIGN_DIR = Path(__file__).resolve().parent.parent.parent / "design"
sys.path.insert(0, str(DESIGN_DIR))

from thesis_analysis.config import settings
from thesis_analysis.data_processing.loader import DataLoader

# Output paths
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def load_courses():
    """Load all courses from NAQA data."""
    print("Loading NAQA accreditation data...")
    loader = DataLoader()
    data = loader.load_all(include_text=False)
    print(f"  Loaded {len(data.df_programs)} programs, {len(data.df_courses)} courses")
    return data


def run_topic_modeling(df_courses: pd.DataFrame):
    """Run BERTopic on course names."""
    from thesis_analysis.analysis.nlp.topic_modeling import TopicModeler

    # Get unique course names (to avoid duplicates inflating topics)
    course_names = df_courses["name"].dropna().tolist()
    unique_names = list(set(course_names))
    print(f"  Total courses: {len(course_names)}, unique: {len(unique_names)}")

    # Use all courses (not unique) for accurate per-program analysis
    modeler = TopicModeler(
        min_topic_size=8,
        n_topics=None,  # auto-detect
        top_n_words=10,
    )

    print("  Running BERTopic (this may take a few minutes)...")
    result = modeler.fit(course_names)

    print(f"  Found {len(result.topics)} topics")
    return result, modeler, course_names


def build_topic_table(result, course_names):
    """Build topic distribution table."""
    rows = []
    for topic in sorted(result.topics, key=lambda t: t.document_count, reverse=True):
        top_words_str = ", ".join(w for w, _ in topic.top_words[:5])
        rows.append({
            "topic_id": topic.topic_id,
            "name": topic.name,
            "top_words": top_words_str,
            "document_count": topic.document_count,
            "pct": round(100 * topic.document_count / len(course_names), 1),
        })

    # Count outliers (topic -1)
    outlier_count = sum(1 for t in result.document_topics if t == -1)
    if outlier_count > 0:
        rows.append({
            "topic_id": -1,
            "name": "Нерозподілені",
            "top_words": "---",
            "document_count": outlier_count,
            "pct": round(100 * outlier_count / len(course_names), 1),
        })

    return pd.DataFrame(rows)


def build_level_heatmap(result, df_courses):
    """Build topic-by-level heatmap data."""
    df = df_courses.copy()
    df["topic"] = result.document_topics

    # Cross-tabulate topic vs degree level
    level_map = {"bachelor": "Бакалавр", "master": "Магістр", "phd": "PhD"}
    df["level_ua"] = df["degree_level"].map(level_map).fillna("Інше")

    # Exclude outliers
    df_valid = df[df["topic"] >= 0]

    crosstab = pd.crosstab(
        df_valid["topic"],
        df_valid["level_ua"],
        normalize="columns",
    )
    return crosstab


def plot_topic_distribution(topic_table, output_path):
    """Bar chart of top topics."""
    df = topic_table[topic_table["topic_id"] >= 0].head(15)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(
        range(len(df)),
        df["document_count"],
        color="#2196F3",
        edgecolor="white",
    )
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(
        [f"T{row.topic_id}: {row.top_words[:40]}" for _, row in df.iterrows()],
        fontsize=9,
    )
    ax.set_xlabel("Кількість дисциплін")
    ax.set_title("Тематичне моделювання навчальних дисциплін (BERTopic, 122 програми)")
    ax.invert_yaxis()

    for bar, pct in zip(bars, df["pct"]):
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2,
                f"{pct}%", va="center", fontsize=8)

    plt.tight_layout()
    fig.savefig(output_path, format="pdf", bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  Saved topic distribution: {output_path}")


def plot_level_heatmap(crosstab, topic_table, output_path):
    """Heatmap of topic distribution by degree level."""
    # Only show top 12 topics
    top_topics = topic_table[topic_table["topic_id"] >= 0].head(12)["topic_id"].tolist()
    ct = crosstab.loc[crosstab.index.isin(top_topics)]

    fig, ax = plt.subplots(figsize=(8, 8))
    im = ax.imshow(ct.values, aspect="auto", cmap="YlOrRd")

    ax.set_xticks(range(ct.shape[1]))
    ax.set_xticklabels(ct.columns, fontsize=10)
    ax.set_yticks(range(ct.shape[0]))

    # Create short labels from topic_table
    labels = []
    for tid in ct.index:
        row = topic_table[topic_table["topic_id"] == tid]
        if not row.empty:
            words = row.iloc[0]["top_words"][:30]
            labels.append(f"T{tid}: {words}")
        else:
            labels.append(f"T{tid}")
    ax.set_yticklabels(labels, fontsize=8)

    ax.set_title("Розподіл тем за рівнями освіти")
    ax.set_xlabel("Рівень освіти")

    # Add value annotations
    for i in range(ct.shape[0]):
        for j in range(ct.shape[1]):
            val = ct.values[i, j]
            ax.text(j, i, f"{val:.1%}", ha="center", va="center",
                    fontsize=7, color="black" if val < 0.3 else "white")

    plt.colorbar(im, ax=ax, label="Частка", shrink=0.8)
    plt.tight_layout()
    fig.savefig(output_path, format="pdf", bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  Saved level heatmap: {output_path}")


def check_ai_in_topics(result):
    """Check if any topics relate to AI/digital technologies."""
    ai_keywords = {
        "штучний", "інтелект", "нейронн", "генеративн", "машинн",
        "ai", "digital", "цифров", "комп'ютер", "програмн",
    }
    ai_topics = []
    for topic in result.topics:
        words = [w.lower() for w, _ in topic.top_words]
        matches = [w for w in words if any(kw in w for kw in ai_keywords)]
        if matches:
            ai_topics.append((topic.topic_id, topic.name, matches))

    return ai_topics


def main():
    print("=" * 60)
    print("BERTopic Topic Modeling: NAQA Design Programs")
    print("=" * 60)

    # 1. Load data
    data = load_courses()
    df_courses = data.df_courses

    # 2. Run topic modeling
    result, modeler, course_names = run_topic_modeling(df_courses)

    # 3. Build tables
    topic_table = build_topic_table(result, course_names)
    print("\nTopic Distribution:")
    print(topic_table[["topic_id", "top_words", "document_count", "pct"]].to_string())

    # 4. Level heatmap
    crosstab = build_level_heatmap(result, df_courses)

    # 5. Generate figures
    plot_topic_distribution(topic_table, FIGURES_DIR / "topic_distribution.pdf")
    plot_level_heatmap(crosstab, topic_table, FIGURES_DIR / "topic_level_heatmap.pdf")

    # 6. Check for AI topics
    ai_topics = check_ai_in_topics(result)
    if ai_topics:
        print(f"\n⚠ Found {len(ai_topics)} topic(s) with AI/digital keywords:")
        for tid, name, matches in ai_topics:
            print(f"  Topic {tid}: {name} → {matches}")
    else:
        print("\n✓ CONFIRMED: No topics centered on AI/digital technologies")

    # 7. Save results
    export = {
        "num_topics": len(result.topics),
        "total_courses": len(course_names),
        "ai_topics_found": len(ai_topics),
        "topics": [
            {
                "id": t.topic_id,
                "name": t.name,
                "top_words": t.top_words[:10],
                "document_count": t.document_count,
                "pct": round(100 * t.document_count / len(course_names), 1),
            }
            for t in sorted(result.topics, key=lambda t: t.document_count, reverse=True)
        ],
    }
    out_path = OUTPUT_DIR / "topic_modeling_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {out_path}")

    # Also save LaTeX table fragment
    latex_rows = []
    for _, row in topic_table[topic_table["topic_id"] >= 0].head(10).iterrows():
        latex_rows.append(
            f"    {int(row.topic_id)} & {row.top_words} & {row.document_count} & {row.pct}\\% \\\\"
        )
    latex_table = (
        "\\begin{table}[htbp]\n"
        "\\centering\n"
        "\\caption{Результати тематичного моделювання навчальних дисциплін (BERTopic)}\\label{tab:topic-modeling}\n"
        "\\small\n"
        "\\begin{tabularx}{\\textwidth}{@{}cXrr@{}}\n"
        "\\toprule\n"
        "\\textbf{Тема} & \\textbf{Ключові слова} & \\textbf{$N$} & \\textbf{\\%} \\\\\n"
        "\\midrule\n"
        + "\n".join(latex_rows) + "\n"
        "\\bottomrule\n"
        "\\end{tabularx}\n"
        "\\end{table}"
    )
    latex_path = OUTPUT_DIR / "topic_modeling_table.tex"
    with open(latex_path, "w", encoding="utf-8") as f:
        f.write(latex_table)
    print(f"LaTeX table saved to {latex_path}")

    print("\n✓ Topic modeling complete!")
    return export


if __name__ == "__main__":
    main()
