"""
Qualitative content analysis of stakeholder reviews and expert reports.
Extracts text from PDFs, applies IKK-aligned thematic coding, extracts quotes.
"""

import json
import re
from pathlib import Path
from collections import Counter

import pandas as pd
import pdfplumber
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent.parent
EXPERIMENT = BASE / "experiment"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "analysis" / "output"
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"

# Source directories
STAKEHOLDER_DIR = EXPERIMENT / "рецензії стейкхолдерів"
EXPERT_GROUP_DIR = EXPERIMENT / "ОПП матеріали" / "Висновок ЕГ"

# Thematic coding scheme aligned with 4 IKK components
CODING_SCHEME = {
    "information_analytical": {
        "label": "Інформаційно-аналітичний",
        "keywords": [
            "інформацій", "аналіз", "пошук", "дослідж", "критичн",
            "оцінюван", "відбір", "джерел", "бази даних", "знання",
        ]
    },
    "communicative": {
        "label": "Комунікативний",
        "keywords": [
            "комунікат", "спілкуван", "презентац", "портфоліо",
            "замовник", "клієнт", "команд", "співпрац", "діалог",
            "партнер", "взаємод",
        ]
    },
    "technological": {
        "label": "Технологічний",
        "keywords": [
            "технолог", "комп'ютер", "програмн", "цифров", "софт",
            "Adobe", "Photoshop", "інструмент", "засоб",
            "інновацій", "сучасн", "модерн", "оновлен",
            "штучн", "інтелект", "ШІ",
        ]
    },
    "reflexive": {
        "label": "Рефлексивний",
        "keywords": [
            "самоосвіт", "саморозвит", "рефлексі", "самооцін",
            "професійн зростан", "вдосконал", "навчан протягом",
            "адаптац", "гнучк",
        ]
    },
    "general_quality": {
        "label": "Загальна якість підготовки",
        "keywords": [
            "якість", "підготовк", "компетентн", "кваліфікац",
            "фаховий", "професійн", "рівень", "відповідн",
            "ринок", "працевлаштуван",
        ]
    },
}


def extract_pdf_text(filepath: Path) -> str:
    """Extract text from PDF."""
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"  Error: {filepath.name}: {e}")
    return text


def code_text(text: str) -> dict:
    """Apply thematic coding to text, return code frequencies and quotes."""
    text_lower = text.lower()
    sentences = re.split(r'[.!?\n]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    results = {}
    for code, config in CODING_SCHEME.items():
        hits = 0
        matched_sentences = []
        for kw in config["keywords"]:
            count = len(re.findall(re.escape(kw.lower()), text_lower))
            hits += count
            if count > 0:
                # Find sentences containing this keyword
                for sent in sentences:
                    if kw.lower() in sent.lower() and sent not in matched_sentences:
                        matched_sentences.append(sent)

        results[code] = {
            "frequency": hits,
            "quotes": matched_sentences[:3],  # Top 3 quotes per code
        }

    return results


def analyze_stakeholder_reviews():
    """Analyze all 9 stakeholder review PDFs."""
    results = []

    if not STAKEHOLDER_DIR.exists():
        print(f"  Stakeholder directory not found: {STAKEHOLDER_DIR}")
        return pd.DataFrame()

    pdfs = sorted(STAKEHOLDER_DIR.glob("*.pdf"))
    print(f"  Found {len(pdfs)} stakeholder review PDFs")

    all_quotes = {}
    for pdf in pdfs:
        text = extract_pdf_text(pdf)
        if not text.strip():
            print(f"    Empty: {pdf.name}")
            continue

        codes = code_text(text)

        # Determine which program this review is for
        name = pdf.name.lower()
        if "одягу" in name or "до" in name.split("_")[0] if "_" in name else "":
            prog = "ДО"
        elif "серед" in name or "дс" in name.split()[0] if " " in name else "":
            prog = "ДС"
        else:
            prog = "ГД"

        row = {
            "file": pdf.name,
            "program": prog,
            "text_length": len(text),
        }
        for code, data in codes.items():
            row[f"{code}_freq"] = data["frequency"]
            # Collect quotes
            for q in data["quotes"]:
                if pdf.name not in all_quotes:
                    all_quotes[pdf.name] = {}
                if code not in all_quotes[pdf.name]:
                    all_quotes[pdf.name][code] = []
                all_quotes[pdf.name][code].append(q)

        results.append(row)

    return pd.DataFrame(results), all_quotes


def analyze_expert_reports():
    """Analyze expert group conclusion PDFs."""
    results = []

    if not EXPERT_GROUP_DIR.exists():
        print(f"  Expert group directory not found: {EXPERT_GROUP_DIR}")
        return pd.DataFrame()

    pdfs = sorted(EXPERT_GROUP_DIR.glob("*.pdf"))
    print(f"  Found {len(pdfs)} expert group PDFs")

    for pdf in pdfs:
        text = extract_pdf_text(pdf)
        if not text.strip():
            print(f"    Empty: {pdf.name}")
            continue

        codes = code_text(text)

        row = {"file": pdf.name, "text_length": len(text)}
        for code, data in codes.items():
            row[f"{code}_freq"] = data["frequency"]

        results.append(row)

    return pd.DataFrame(results)


def plot_coding_frequencies(stakeholder_df: pd.DataFrame, output_path: Path):
    """Bar chart of thematic coding frequencies across stakeholder reviews."""
    if stakeholder_df.empty:
        return

    freq_cols = [c for c in stakeholder_df.columns if c.endswith('_freq')]
    freq_sums = stakeholder_df[freq_cols].sum()
    freq_sums.index = [CODING_SCHEME[c.replace('_freq', '')]["label"] for c in freq_cols]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#607D8B']
    freq_sums.sort_values().plot(kind='barh', ax=ax, color=colors[:len(freq_sums)], edgecolor='white')
    ax.set_xlabel("Частота згадувань", fontsize=12)
    ax.set_title("Тематичне кодування відгуків стейкхолдерів\n(за компонентами ІКК)", fontsize=13)
    plt.tight_layout()
    fig.savefig(output_path, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved coding frequencies: {output_path}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Analyzing stakeholder reviews ===")
    stakeholder_df, quotes = analyze_stakeholder_reviews()

    if not stakeholder_df.empty:
        print(f"\nStakeholder reviews analyzed: {len(stakeholder_df)}")
        print(stakeholder_df.to_string(index=False))
        stakeholder_df.to_csv(OUTPUT_DIR / "stakeholder_coding.csv", index=False)

        # Save quotes for thesis use
        with open(OUTPUT_DIR / "stakeholder_quotes.json", "w", encoding="utf-8") as f:
            json.dump(quotes, f, ensure_ascii=False, indent=2)

        plot_coding_frequencies(stakeholder_df, FIGURES_DIR / "stakeholder_coding_frequencies.pdf")

    print("\n=== Analyzing expert group reports ===")
    expert_df = analyze_expert_reports()

    if not expert_df.empty:
        print(f"\nExpert reports analyzed: {len(expert_df)}")
        print(expert_df.to_string(index=False))
        expert_df.to_csv(OUTPUT_DIR / "expert_report_coding.csv", index=False)

    # Combined summary
    summary = {
        "stakeholder_reviews": len(stakeholder_df) if not stakeholder_df.empty else 0,
        "expert_reports": len(expert_df) if not expert_df.empty else 0,
    }

    if not stakeholder_df.empty:
        freq_cols = [c for c in stakeholder_df.columns if c.endswith('_freq')]
        for col in freq_cols:
            code = col.replace('_freq', '')
            summary[f"stakeholder_{code}_total"] = int(stakeholder_df[col].sum())

    with open(OUTPUT_DIR / "qualitative_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nDone. All outputs in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
