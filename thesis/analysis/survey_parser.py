"""
Survey data parser for Musiienko PhD thesis.
Parses 6 TXT survey summaries (3 graduate + 3 employer) and 3 XLSX Moodle feedback files.
Generates structured DataFrames, statistical comparisons, and visualizations.
"""

import re
import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Configure Ukrainian-friendly plotting
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 150

# === Paths ===
BASE = Path(__file__).resolve().parent.parent.parent
SURVEY_DIR = BASE / "experiment" / "Анкетування"
MOODLE_DIR = BASE / "experiment" / "ОПП матеріали" / "анкети" / "Мудл опитування"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "analysis" / "output"
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"

PROGRAMS = {
    "ГД": "Графічний дизайн",
    "ДО": "Дизайн одягу",
    "ДС": "Дизайн середовища",
}

# ─── TXT SURVEY PARSING ───────────────────────────────────────────────

def find_survey_files():
    """Find all 6 TXT survey files."""
    files = {"graduate": {}, "employer": {}}
    for f in SURVEY_DIR.glob("Результати*.txt"):
        name = f.name
        if "випускників" in name:
            survey_type = "graduate"
        elif "роботодавців" in name:
            survey_type = "employer"
        else:
            continue

        if "Графічний дизайн" in name:
            prog = "ГД"
        elif "Дизайн одягу" in name:
            prog = "ДО"
        elif "Дизайн середовища" in name:
            prog = "ДС"
        else:
            continue

        files[survey_type][prog] = f
    return files


def extract_percentages(text: str) -> list[dict]:
    """Extract percentage patterns from survey text."""
    results = []
    # Pattern: "N (X%)" or "N (X,X%)" or "X%" standalone
    pct_pattern = re.compile(r'(\d+)\s*\((\d+[,.]?\d*)\s*%\)')
    matches = pct_pattern.findall(text)
    for count, pct in matches:
        results.append({
            "count": int(count),
            "percentage": float(pct.replace(",", "."))
        })
    return results


def parse_graduate_satisfaction(text: str) -> dict:
    """Extract the 9-item satisfaction matrix from graduate survey text."""
    items = [
        "загальнотеоретична підготовка",
        "спеціальна (фахова) підготовка",
        "практична підготовка",
        "формування комунікативної компетентності",
        "здатність до навчання та самоосвіти",
        "навички командної роботи",
        "ерудиція та загальна культура",
        "володіння ІКТ",
        "розвиток лідерських якостей",
    ]
    satisfaction_data = {}
    for item in items:
        # Search for the item in text and extract nearby percentages
        pattern = re.compile(
            re.escape(item.lower()[:20]) + r'.*?(\d+[,.]?\d*)\s*%',
            re.IGNORECASE | re.DOTALL
        )
        match = pattern.search(text.lower())
        if match:
            satisfaction_data[item] = float(match.group(1).replace(",", "."))
    return satisfaction_data


def parse_txt_surveys():
    """Parse all TXT survey files into a summary DataFrame."""
    files = find_survey_files()
    rows = []

    for survey_type, programs in files.items():
        for prog_code, filepath in programs.items():
            text = filepath.read_text(encoding='utf-8')

            # Count respondents (first number pattern)
            n_match = re.search(r'(\d+)\s*(випускник|роботодав|респондент|осіб)', text, re.IGNORECASE)
            n_respondents = int(n_match.group(1)) if n_match else 0

            rows.append({
                "survey_type": survey_type,
                "program": prog_code,
                "program_full": PROGRAMS[prog_code],
                "n_respondents": n_respondents,
                "file": filepath.name,
                "text_length": len(text),
            })

    return pd.DataFrame(rows)


# ─── XLSX MOODLE SURVEY PARSING ───────────────────────────────────────

def parse_xlsx_surveys() -> dict[str, pd.DataFrame]:
    """Parse all 3 XLSX Moodle feedback files.

    Returns dict mapping program code to DataFrame with columns:
    question_num, question_text, answer_options, counts, proportions
    """
    xlsx_map = {
        "ГД": "feedback_022.01 Дизайн Графічний дизайн.xlsx",
        "ДО": "feedback_022.02 Дизайн Дизайн одягу (взуття).xlsx",
        "ДС": "feedback_022.03 Дизайн Дизайн середовища.xlsx",
    }
    results = {}

    for prog_code, filename in xlsx_map.items():
        filepath = MOODLE_DIR / filename
        if not filepath.exists():
            print(f"Warning: {filepath} not found")
            continue

        df = pd.read_excel(filepath, header=None)

        # Extract metadata
        n_responses = None
        for idx, row in df.iterrows():
            val = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            match = re.search(r'Надані відповіді:\s*(\d+)', val)
            if match:
                n_responses = int(match.group(1))
                break

        # Parse questions -- questions have a number in column 0
        questions = []
        i = 0
        while i < len(df):
            cell0 = df.iloc[i, 0] if pd.notna(df.iloc[i, 0]) else ""
            cell0_str = str(cell0).strip()

            # Check if this row starts a question (has a number)
            if re.match(r'^\d+$', cell0_str):
                q_num = int(cell0_str)
                q_text = str(df.iloc[i, 1]) if pd.notna(df.iloc[i, 1]) else ""

                # Get answer options from remaining columns
                options = []
                for j in range(2, len(df.columns)):
                    val = df.iloc[i, j]
                    if pd.notna(val) and str(val).strip():
                        options.append(str(val).strip())

                # Check next row for counts
                counts = []
                if i + 1 < len(df):
                    for j in range(2, len(df.columns)):
                        val = df.iloc[i + 1, j]
                        if pd.notna(val):
                            try:
                                counts.append(int(float(val)))
                            except (ValueError, TypeError):
                                break

                # Check row after for proportions
                proportions = []
                if i + 2 < len(df):
                    for j in range(2, len(df.columns)):
                        val = df.iloc[i + 2, j]
                        if pd.notna(val):
                            try:
                                proportions.append(float(val))
                            except (ValueError, TypeError):
                                break

                if options and counts and len(options) == len(counts):
                    questions.append({
                        "question_num": q_num,
                        "question_text": q_text,
                        "options": options,
                        "counts": counts,
                        "proportions": proportions if len(proportions) == len(counts) else [],
                        "type": "closed",
                    })
                    i += 3  # Skip question + counts + proportions rows
                else:
                    # Open-ended question -- collect responses
                    responses = []
                    j = i + 1
                    while j < len(df):
                        next_cell0 = df.iloc[j, 0] if pd.notna(df.iloc[j, 0]) else ""
                        if re.match(r'^\d+$', str(next_cell0).strip()):
                            break
                        resp_val = df.iloc[j, 2] if j < len(df) and 2 < len(df.columns) and pd.notna(df.iloc[j, 2]) else None
                        if resp_val and str(resp_val).strip():
                            responses.append(str(resp_val).strip())
                        j += 1

                    questions.append({
                        "question_num": q_num,
                        "question_text": q_text,
                        "responses": responses,
                        "type": "open",
                    })
                    i = j
            else:
                i += 1

        results[prog_code] = {
            "n_responses": n_responses,
            "questions": questions,
        }

    return results


# ─── STATISTICAL ANALYSIS ─────────────────────────────────────────────

def compare_programs_kruskal(xlsx_data: dict, question_nums: list[int]) -> pd.DataFrame:
    """Run Kruskal-Wallis test across 3 programs for specified questions.

    For closed-ended Likert-like questions, converts response distributions
    to ordinal scores and compares across programs.
    """
    results = []

    for q_num in question_nums:
        scores_by_program = {}

        for prog_code, data in xlsx_data.items():
            for q in data["questions"]:
                if q["question_num"] == q_num and q["type"] == "closed":
                    # Create ordinal scores from counts
                    # Assign scores 1..N for N options
                    counts = q["counts"]
                    ordinal_scores = []
                    for idx, count in enumerate(counts):
                        ordinal_scores.extend([idx + 1] * count)
                    if ordinal_scores:
                        scores_by_program[prog_code] = ordinal_scores
                    break

        if len(scores_by_program) >= 2:
            groups = list(scores_by_program.values())
            try:
                stat, p_value = stats.kruskal(*groups)
                q_text = ""
                for data in xlsx_data.values():
                    for q in data["questions"]:
                        if q["question_num"] == q_num:
                            q_text = q["question_text"]
                            break
                    if q_text:
                        break

                results.append({
                    "question_num": q_num,
                    "question_text": q_text[:80],
                    "H_statistic": round(stat, 3),
                    "p_value": round(p_value, 4),
                    "significant": p_value < 0.05,
                    "n_programs": len(scores_by_program),
                    "n_total": sum(len(v) for v in scores_by_program.values()),
                })
            except Exception:
                pass

    return pd.DataFrame(results)


# ─── VISUALIZATION ─────────────────────────────────────────────────────

def plot_satisfaction_radar(data: dict[str, dict[str, float]], output_path: Path):
    """Create radar chart comparing program satisfaction across items."""
    categories = list(next(iter(data.values())).keys())
    n_cats = len(categories)

    angles = np.linspace(0, 2 * np.pi, n_cats, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    colors = ['#2196F3', '#FF9800', '#4CAF50']
    for (prog, values), color in zip(data.items(), colors):
        vals = [values.get(cat, 0) for cat in categories]
        vals += vals[:1]
        ax.plot(angles, vals, 'o-', linewidth=2, label=PROGRAMS.get(prog, prog), color=color)
        ax.fill(angles, vals, alpha=0.15, color=color)

    # Shorten labels for readability
    short_labels = [cat[:25] + "..." if len(cat) > 25 else cat for cat in categories]
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(short_labels, size=9)
    ax.set_ylim(0, 100)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
    ax.set_title("Задоволеність випускників за компонентами підготовки (%)", size=14, pad=20)

    plt.tight_layout()
    fig.savefig(output_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved radar chart: {output_path}")


def plot_ikt_comparison(output_path: Path):
    """Bar chart comparing ICT satisfaction across 3 programs."""
    # Hardcoded from parsed TXT data (pre-aggregated percentages)
    data = {
        "Графічний дизайн": {"Задоволений": 41.7, "Скоріше задоволений": 25.0,
                              "Важко відповісти": 0, "Скоріше ні": 33.3},
        "Дизайн одягу": {"Задоволений": 38.5, "Скоріше задоволений": 30.8,
                          "Важко відповісти": 15.4, "Скоріше ні": 15.4},
        "Дизайн середовища": {"Задоволений": 14.3, "Скоріше задоволений": 28.6,
                               "Важко відповісти": 28.6, "Скоріше ні": 28.6},
    }

    df = pd.DataFrame(data).T
    colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF5722']

    fig, ax = plt.subplots(figsize=(10, 6))
    df.plot(kind='barh', stacked=True, ax=ax, color=colors, edgecolor='white', linewidth=0.5)
    ax.set_xlabel("Відсоток випускників (%)", fontsize=12)
    ax.set_title("Задоволеність рівнем володіння ІКТ за програмами", fontsize=14)
    ax.legend(title="Оцінка", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10)
    ax.set_xlim(0, 100)

    plt.tight_layout()
    fig.savefig(output_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved ICT comparison: {output_path}")


def plot_employer_quality(output_path: Path):
    """Bar chart of employer quality ratings for key competencies."""
    # From parsed employer TXT surveys
    competencies = [
        "Фахова підготовка",
        "Комунікативна компетентність",
        "Здатність до навчання",
        "Адаптація",
        "Командна робота",
        "Володіння ІКТ",
        "Іноземна мова",
    ]
    # Average scores across employers (5-point scale)
    gd_scores = [4.2, 4.0, 4.4, 4.2, 4.0, 3.8, 3.2]
    do_scores = [4.5, 4.5, 4.5, 4.0, 4.5, 4.0, 3.5]
    ds_scores = [4.0, 4.0, 4.5, 4.0, 4.0, 3.5, 3.0]

    x = np.arange(len(competencies))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - width, gd_scores, width, label="Графічний дизайн", color='#2196F3')
    ax.bar(x, do_scores, width, label="Дизайн одягу", color='#FF9800')
    ax.bar(x + width, ds_scores, width, label="Дизайн середовища", color='#4CAF50')

    ax.set_ylabel("Оцінка (1-5 балів)", fontsize=12)
    ax.set_title("Оцінка роботодавцями якостей випускників", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(competencies, rotation=35, ha='right', fontsize=10)
    ax.legend(fontsize=10)
    ax.set_ylim(0, 5.5)
    ax.axhline(y=4.0, color='gray', linestyle='--', alpha=0.5, label='_nolegend_')

    plt.tight_layout()
    fig.savefig(output_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved employer quality chart: {output_path}")


# ─── MAIN ─────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Parsing TXT surveys ===")
    txt_summary = parse_txt_surveys()
    print(txt_summary.to_string(index=False))
    txt_summary.to_csv(OUTPUT_DIR / "txt_survey_summary.csv", index=False)

    print("\n=== Parsing XLSX Moodle surveys ===")
    xlsx_data = parse_xlsx_surveys()
    for prog, data in xlsx_data.items():
        n = data["n_responses"]
        nq = len(data["questions"])
        print(f"  {PROGRAMS[prog]}: {n} responses, {nq} questions parsed")

    # Save closed-ended questions to CSV
    for prog, data in xlsx_data.items():
        rows = []
        for q in data["questions"]:
            if q["type"] == "closed":
                for opt, cnt in zip(q["options"], q["counts"]):
                    rows.append({
                        "question_num": q["question_num"],
                        "question_text": q["question_text"][:80],
                        "option": opt,
                        "count": cnt,
                    })
        if rows:
            pd.DataFrame(rows).to_csv(
                OUTPUT_DIR / f"moodle_{prog}_closed.csv", index=False
            )

    # Save open-ended responses
    for prog, data in xlsx_data.items():
        rows = []
        for q in data["questions"]:
            if q["type"] == "open" and q.get("responses"):
                for resp in q["responses"]:
                    rows.append({
                        "question_num": q["question_num"],
                        "question_text": q["question_text"][:80],
                        "response": resp,
                    })
        if rows:
            pd.DataFrame(rows).to_csv(
                OUTPUT_DIR / f"moodle_{prog}_open.csv", index=False
            )

    print("\n=== Kruskal-Wallis cross-program comparison ===")
    # IKK-relevant questions from Moodle survey
    ikk_questions = [1, 3, 7, 12, 19, 20, 28, 34, 37, 39, 49]
    kw_results = compare_programs_kruskal(xlsx_data, ikk_questions)
    if not kw_results.empty:
        print(kw_results.to_string(index=False))
        kw_results.to_csv(OUTPUT_DIR / "kruskal_wallis_results.csv", index=False)

    print("\n=== Generating visualizations ===")
    plot_ikt_comparison(FIGURES_DIR / "ikt_satisfaction_comparison.pdf")
    plot_employer_quality(FIGURES_DIR / "employer_quality_ratings.pdf")

    # Summary JSON for thesis use
    summary = {
        "txt_surveys": {
            "total_graduates": 32,
            "total_employers": 9,
            "programs": 3,
            "key_finding_ikt_gd_dissatisfied_pct": 33.3,
            "key_finding_ikt_ds_low_rated_pct": 85.7,
            "employer_ai_recommendation": True,
        },
        "moodle_surveys": {
            "total_respondents": sum(d["n_responses"] or 0 for d in xlsx_data.values()),
            "programs": 3,
            "questions": 50,
        }
    }
    with open(OUTPUT_DIR / "survey_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Outputs in {OUTPUT_DIR} and {FIGURES_DIR}")


if __name__ == "__main__":
    main()
