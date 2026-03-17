#!/usr/bin/env python3
"""
Analysis & Visualization Data Generator.

Reads coded_segments.json and produces:
- Frequency tables by dimension × stage
- Temporal distributions
- Co-occurrence patterns
- Exemplar segments per code
- CSV files for pgfplots
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

INPUT_FILE = Path(__file__).resolve().parent / "coded_segments.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# Human-readable labels
CODE_LABELS = {
    "CAM-PRES": "Presence",
    "CAM-AGEN": "Agency",
    "CAM-EMBO": "Embodiment",
    "CAM-COGN": "Cognitive load mgmt",
    "CAM-MOTI": "Motivation",
    "CAM-SREG": "Self-regulation",
    "TPACK-TK": "TK",
    "TPACK-PK": "PK",
    "TPACK-TPK": "TPK",
    "TPACK-INT": "TPACK-integrated",
    "PC-PSYCH": "Психолого-педагогічна",
    "PC-METHOD": "Методична",
    "PC-TECH": "Технологічна",
    "PC-ORG": "Організаційна",
    "MS-THEOR": "Теоретико-аналітичний",
    "MS-PRACT": "Практико-розвивальний",
    "MS-INTEG": "Інтегративно-рефлексивний",
    "TS-MODEL": "Modeling",
    "TS-SCAFF": "Scaffolding",
    "TS-QUEST": "Questioning",
    "TS-FEEDB": "Feedback",
    "TS-TROUB": "Troubleshooting",
    "TS-REAL": "Real-world connection",
    "RC-MVAL": "Мотиваційно-ціннісний",
    "RC-COGN": "Когнітивний",
    "RC-ACTD": "Діяльнісно-проєктувальний",
    "RC-TECH": "Технологічний",
    "RC-INTR": "Інтерактивний",
    "RC-REFL": "Рефлексивний",
}

STAGE_LABELS = {
    "theoretical-analytical": "Теоретико-аналітичний",
    "practical-developmental": "Практико-розвивальний",
    "integrative-reflective": "Інтегративно-рефлексивний",
}

STAGE_ORDER = ["theoretical-analytical", "practical-developmental", "integrative-reflective"]

# Week ranges per stage
STAGE_WEEKS = {
    "theoretical-analytical": list(range(1, 7)),
    "practical-developmental": list(range(7, 15)),
    "integrative-reflective": list(range(15, 19)),
}


def load_data():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_codes(segment):
    """Extract all codes from a segment as a flat list of (dimension, code) tuples."""
    result = []
    for dim, codes in segment.get("codes", {}).items():
        for c in codes:
            result.append((dim, c["code"], c["confidence"]))
    return result


def aggregate_by_dimension_stage(data):
    """Count code occurrences by dimension × methodology stage."""
    counts = defaultdict(lambda: defaultdict(int))
    totals_by_stage = defaultdict(int)

    for file_data in data:
        if file_data.get("excluded"):
            continue
        stage = file_data.get("methodology_stage", "unknown")
        for seg in file_data.get("segments", []):
            totals_by_stage[stage] += 1
            for dim, code, conf in get_all_codes(seg):
                counts[(dim, code)][stage] += 1

    return counts, totals_by_stage


def temporal_distribution(data):
    """Code frequencies by week number."""
    week_counts = defaultdict(lambda: defaultdict(int))
    week_totals = defaultdict(int)

    for file_data in data:
        if file_data.get("excluded"):
            continue
        weeks = file_data.get("weeks", [])
        for seg in file_data.get("segments", []):
            for w in weeks:
                week_totals[w] += 1
                for dim, code, conf in get_all_codes(seg):
                    week_counts[w][(dim, code)] += 1

    return week_counts, week_totals


def find_exemplars(data, max_per_code=5):
    """Find best exemplar segments per code (highest confidence, longest text)."""
    exemplars = defaultdict(list)

    for file_data in data:
        if file_data.get("excluded"):
            continue
        for seg in file_data.get("segments", []):
            for dim, code, conf in get_all_codes(seg):
                text = seg.get("normalized_text", "")
                if len(text) > 50:  # Skip very short segments
                    exemplars[(dim, code)].append({
                        "text": text,
                        "file": file_data["file"],
                        "weeks": file_data["weeks"],
                        "start": seg["start"],
                        "end": seg["end"],
                        "confidence": conf,
                        "length": len(text),
                    })

    # Rank: high confidence first, then by length
    conf_order = {"high": 0, "medium": 1, "low": 2}
    for key in exemplars:
        exemplars[key].sort(key=lambda x: (conf_order.get(x["confidence"], 3), -x["length"]))
        exemplars[key] = exemplars[key][:max_per_code]

    return exemplars


def compute_cooccurrences(data):
    """Find how often codes from different dimensions co-occur in the same segment."""
    cooccur = defaultdict(int)

    for file_data in data:
        if file_data.get("excluded"):
            continue
        for seg in file_data.get("segments", []):
            all_codes = get_all_codes(seg)
            codes_list = [(dim, code) for dim, code, _ in all_codes]
            for i in range(len(codes_list)):
                for j in range(i + 1, len(codes_list)):
                    if codes_list[i][0] != codes_list[j][0]:  # Different dimensions
                        pair = tuple(sorted([codes_list[i][1], codes_list[j][1]]))
                        cooccur[pair] += 1

    return cooccur


def write_csv(filepath, headers, rows):
    """Write a CSV file."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def generate_camil_temporal_csv(week_counts, week_totals):
    """Generate CSV for CAMIL temporal line chart (pgfplots)."""
    camil_codes = ["CAM-PRES", "CAM-AGEN", "CAM-EMBO", "CAM-COGN", "CAM-MOTI", "CAM-SREG"]
    weeks = sorted(week_totals.keys())

    headers = ["week"] + [CODE_LABELS.get(c, c) for c in camil_codes]
    rows = []
    for w in weeks:
        total = max(week_totals[w], 1)
        row = [w]
        for code in camil_codes:
            count = week_counts[w].get(("CAMIL", code), 0)
            pct = round(count / total * 100, 1)
            row.append(pct)
        rows.append(row)

    write_csv(OUTPUT_DIR / "camil_temporal.csv", headers, rows)
    return weeks, camil_codes


def generate_teaching_strategies_csv(counts):
    """Generate CSV for teaching strategies stacked bar chart."""
    ts_codes = ["TS-MODEL", "TS-SCAFF", "TS-QUEST", "TS-FEEDB", "TS-TROUB", "TS-REAL"]

    headers = ["stage"] + [CODE_LABELS.get(c, c) for c in ts_codes]
    rows = []
    for stage in STAGE_ORDER:
        row = [STAGE_LABELS.get(stage, stage)]
        stage_total = 0
        for code in ts_codes:
            stage_total += counts.get(("TEACHING_STRATEGIES", code), {}).get(stage, 0)

        for code in ts_codes:
            count = counts.get(("TEACHING_STRATEGIES", code), {}).get(stage, 0)
            pct = round(count / max(stage_total, 1) * 100, 1)
            row.append(pct)
        rows.append(row)

    write_csv(OUTPUT_DIR / "teaching_strategies.csv", headers, rows)


def generate_camil_by_stage_csv(counts):
    """Generate CSV for CAMIL factor frequencies by methodology stage."""
    camil_codes = ["CAM-PRES", "CAM-AGEN", "CAM-EMBO", "CAM-COGN", "CAM-MOTI", "CAM-SREG"]

    headers = ["factor"] + [STAGE_LABELS[s] for s in STAGE_ORDER]
    rows = []
    for code in camil_codes:
        row = [CODE_LABELS.get(code, code)]
        for stage in STAGE_ORDER:
            count = counts.get(("CAMIL", code), {}).get(stage, 0)
            row.append(count)
        rows.append(row)

    write_csv(OUTPUT_DIR / "camil_by_stage.csv", headers, rows)


def generate_tpack_by_stage_csv(counts):
    """Generate CSV for TPACK components by methodology stage."""
    tpack_codes = ["TPACK-TK", "TPACK-PK", "TPACK-TPK", "TPACK-INT"]

    headers = ["component"] + [STAGE_LABELS[s] for s in STAGE_ORDER]
    rows = []
    for code in tpack_codes:
        row = [CODE_LABELS.get(code, code)]
        for stage in STAGE_ORDER:
            count = counts.get(("TPACK", code), {}).get(stage, 0)
            row.append(count)
        rows.append(row)

    write_csv(OUTPUT_DIR / "tpack_by_stage.csv", headers, rows)


def generate_conditions_csv(counts):
    """Generate CSV for pedagogical conditions by stage."""
    pc_codes = ["PC-PSYCH", "PC-METHOD", "PC-TECH", "PC-ORG"]

    headers = ["condition"] + [STAGE_LABELS[s] for s in STAGE_ORDER]
    rows = []
    for code in pc_codes:
        row = [CODE_LABELS.get(code, code)]
        for stage in STAGE_ORDER:
            count = counts.get(("PED_CONDITIONS", code), {}).get(stage, 0)
            row.append(count)
        rows.append(row)

    write_csv(OUTPUT_DIR / "conditions_by_stage.csv", headers, rows)


def generate_corpus_description(data):
    """Generate corpus description CSV for the methodology section."""
    headers = ["file", "weeks", "topic", "segments", "duration_min",
               "ukrainian_pct", "quality", "stage"]
    rows = []
    for fd in data:
        q = fd.get("quality", {})
        rows.append([
            fd["file"],
            "-".join(str(w) for w in fd["weeks"]),
            fd["topic"],
            q.get("total_segments", 0),
            q.get("total_duration_min", 0),
            q.get("ukrainian_pct", 0),
            q.get("quality", ""),
            fd.get("methodology_stage", ""),
        ])

    write_csv(OUTPUT_DIR / "corpus_description.csv", headers, rows)


def print_summary_tables(counts, totals, exemplars, cooccurrences):
    """Print summary tables to console."""
    print("\n" + "=" * 70)
    print("CAMIL FACTORS BY METHODOLOGY STAGE")
    print("=" * 70)
    camil_codes = ["CAM-MOTI", "CAM-COGN", "CAM-PRES", "CAM-AGEN", "CAM-EMBO", "CAM-SREG"]
    print(f"{'Factor':<25} {'Theor-Anal':>12} {'Pract-Dev':>12} {'Integ-Refl':>12} {'Total':>8}")
    print("-" * 70)
    for code in camil_codes:
        total = 0
        vals = []
        for stage in STAGE_ORDER:
            v = counts.get(("CAMIL", code), {}).get(stage, 0)
            vals.append(v)
            total += v
        print(f"{CODE_LABELS.get(code, code):<25} {vals[0]:>12} {vals[1]:>12} {vals[2]:>12} {total:>8}")

    print("\n" + "=" * 70)
    print("TPACK COMPONENTS BY METHODOLOGY STAGE")
    print("=" * 70)
    tpack_codes = ["TPACK-TK", "TPACK-PK", "TPACK-TPK", "TPACK-INT"]
    print(f"{'Component':<25} {'Theor-Anal':>12} {'Pract-Dev':>12} {'Integ-Refl':>12} {'Total':>8}")
    print("-" * 70)
    for code in tpack_codes:
        total = 0
        vals = []
        for stage in STAGE_ORDER:
            v = counts.get(("TPACK", code), {}).get(stage, 0)
            vals.append(v)
            total += v
        print(f"{CODE_LABELS.get(code, code):<25} {vals[0]:>12} {vals[1]:>12} {vals[2]:>12} {total:>8}")

    print("\n" + "=" * 70)
    print("TEACHING STRATEGIES BY METHODOLOGY STAGE")
    print("=" * 70)
    ts_codes = ["TS-MODEL", "TS-SCAFF", "TS-QUEST", "TS-FEEDB", "TS-TROUB", "TS-REAL"]
    print(f"{'Strategy':<25} {'Theor-Anal':>12} {'Pract-Dev':>12} {'Integ-Refl':>12} {'Total':>8}")
    print("-" * 70)
    for code in ts_codes:
        total = 0
        vals = []
        for stage in STAGE_ORDER:
            v = counts.get(("TEACHING_STRATEGIES", code), {}).get(stage, 0)
            vals.append(v)
            total += v
        print(f"{CODE_LABELS.get(code, code):<25} {vals[0]:>12} {vals[1]:>12} {vals[2]:>12} {total:>8}")

    print("\n" + "=" * 70)
    print("TOP 15 CO-OCCURRENCES (cross-dimension)")
    print("=" * 70)
    sorted_co = sorted(cooccurrences.items(), key=lambda x: x[1], reverse=True)[:15]
    for (c1, c2), count in sorted_co:
        print(f"  {CODE_LABELS.get(c1, c1):<25} + {CODE_LABELS.get(c2, c2):<25} = {count}")

    # Print top exemplars
    print("\n" + "=" * 70)
    print("TOP EXEMPLARS (1 per code, high confidence)")
    print("=" * 70)
    for key in sorted(exemplars.keys()):
        dim, code = key
        exs = exemplars[key]
        if exs:
            ex = exs[0]
            text_preview = ex["text"][:120] + ("..." if len(ex["text"]) > 120 else "")
            print(f"\n  [{code}] ({dim}) — week {ex['weeks']}, {ex['start']}")
            print(f"    \"{text_preview}\"")


def main():
    if not INPUT_FILE.exists():
        print(f"ERROR: Input not found: {INPUT_FILE}", file=sys.stderr)
        print("Run precode.py first.", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)

    data = load_data()
    usable = [d for d in data if not d.get("excluded")]
    print(f"Loaded {len(data)} files ({len(usable)} usable)")

    # Aggregate
    print("\nAggregating frequencies...")
    counts, totals = aggregate_by_dimension_stage(usable)

    print("Computing temporal distributions...")
    week_counts, week_totals = temporal_distribution(usable)

    print("Finding exemplar segments...")
    exemplars = find_exemplars(usable)

    print("Computing co-occurrences...")
    cooccurrences = compute_cooccurrences(usable)

    # Generate CSVs
    print("\nGenerating CSV files...")
    generate_camil_temporal_csv(week_counts, week_totals)
    print("  camil_temporal.csv")

    generate_teaching_strategies_csv(counts)
    print("  teaching_strategies.csv")

    generate_camil_by_stage_csv(counts)
    print("  camil_by_stage.csv")

    generate_tpack_by_stage_csv(counts)
    print("  tpack_by_stage.csv")

    generate_conditions_csv(counts)
    print("  conditions_by_stage.csv")

    generate_corpus_description(data)
    print("  corpus_description.csv")

    # Save exemplars
    exemplars_json = {}
    for (dim, code), exs in exemplars.items():
        exemplars_json[f"{dim}/{code}"] = exs
    with open(OUTPUT_DIR / "exemplars.json", "w", encoding="utf-8") as f:
        json.dump(exemplars_json, f, ensure_ascii=False, indent=2)
    print("  exemplars.json")

    # Print summary
    print_summary_tables(counts, totals, exemplars, cooccurrences)

    print(f"\nAll output written to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
