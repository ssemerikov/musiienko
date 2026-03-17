#!/usr/bin/env python3
"""
VTT Parser & Normalizer for SRO2025 lecture transcripts.

Parses 15 VTT files from experiment/SRO2025/, strips headers/timestamps,
applies ASR terminology corrections, assesses quality, and outputs segments.json.
"""

import json
import os
import re
import sys
from pathlib import Path

# Paths
VTT_DIR = Path(__file__).resolve().parent.parent.parent / "experiment" / "SRO2025"
OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = OUTPUT_DIR / "segments.json"

# File metadata: filename -> (week(s), topic)
FILE_META = {
    "СРО01.Вступ до WebAR.vtt": ([1], "Вступ до WebAR"),
    "СРО02.Підготовка зображення для MindAR.vtt": ([2], "Підготовка зображення для MindAR"),
    "СРО03.Завантаження текстур.vtt": ([3], "Завантаження текстур"),
    "СРО04-05.Завантаження моделей.vtt": ([4, 5], "Завантаження 3D-моделей"),
    "СРО06-07.Відтворення відео.vtt": ([6, 7], "Відтворення відео та лаб. робота 1"),
    "СРО08.Опорні точки обличчя.vtt": ([8], "Опорні точки обличчя (Face Tracking)"),
    "СРО09.Накладання маски на обличчя.vtt": ([9], "Накладання маски на обличчя"),
    "СРО10.Перемикання камери та захоплення кадрів.vtt": ([10], "Перемикання камери та захоплення кадрів"),
    "СРО11.Початок роботи із WebXR.vtt": ([11], "Початок роботи із WebXR"),
    "СРО12.Компонент ARButton.vtt": ([12], "Компонент ARButton"),
    "СРО13.Управління контроллерами.vtt": ([13], "Управління контролерами"),
    "СРО14.Розміщення об_єктів.vtt": ([14], "Розміщення об'єктів (EXCLUDED — ASR failure)"),
    "СРО15.Розпізнавання віку та статі.vtt": ([15], "Розпізнавання віку та статі (TensorFlow.js)"),
    "СРО16-17.Перевірка дотику та комерційні засоби.vtt": ([16, 17], "Перевірка дотику та комерційні засоби"),
    "СРО18.8th Wall та середовища для створення імерсивного досвіду.vtt": ([18], "8th Wall та середовища розробки"),
}

EXCLUDED_FILES = {"СРО14.Розміщення об_єктів.vtt"}

# ASR normalization dictionary: pattern -> replacement
NORMALIZATION = {
    # Library/framework names
    r'\bсергій\s*гс\b': 'Three.js',
    r'\bсергій\s*жс\b': 'Three.js',
    r'\bтрі\s*жс\b': 'Three.js',
    r'\bтрі\.жс\b': 'Three.js',
    r'\bсрібд\s*ес\b': 'Three.js',
    r'\bтрьожс\b': 'Three.js',
    r'\bафре[ії]м\b': 'A-Frame',
    r'\bа-фрейм\b': 'A-Frame',
    r'\bафреєм\b': 'A-Frame',
    r'\bмайн[\s-]?[гґ]ер\b': 'MindAR',
    r'\bмайнд[\s-]?ар\b': 'MindAR',
    r'\bмайндар\b': 'MindAR',
    r'\bмайн\s*де\s*ар\b': 'MindAR',
    r'\bбджілбі\b': 'GLTF/GLB',
    r'\bджілбі\b': 'GLTF/GLB',
    r'\bджі\s*ел\s*ті\s*еф\b': 'GLTF',
    r'\bджі\s*ел\s*бі\b': 'GLB',
    r'\bтенсорфлоу\b': 'TensorFlow.js',
    r'\bтензорфлоу\b': 'TensorFlow.js',
    r'\bтенсор\s*флоу\b': 'TensorFlow.js',
    r'\bтенсор\s*флов\b': 'TensorFlow.js',
    r'\bтічебл\s*машін\b': 'Teachable Machine',
    r'\bтічабл\s*машін\b': 'Teachable Machine',
    r'\bенджірок\b': 'ngrok',
    r'\bнджірок\b': 'ngrok',
    r'\bеннзірок\b': 'ngrok',
    r'\bенгрок\b': 'ngrok',
    r'\bнгрок\b': 'ngrok',
    r'\bвебексар\b': 'WebXR',
    r'\bвеб\s*ікс\s*ар\b': 'WebXR',
    r'\bвеб\s*ар\b': 'WebAR',
    r'\bхенд\s*поуз\b': 'handpose',
    r'\bхендпоуз\b': 'handpose',
    r'\bфейс\s*апі\b': 'face-api.js',
    r'\bфейсапі\b': 'face-api.js',
    r'\bхіт\s*тестінг\b': 'hit testing',
    r'\bхіт-тестінг\b': 'hit testing',
    r'\bлайв\s*сервер\b': 'live-server',
    r'\bрендерер\b': 'renderer',
    # Technical terms
    r'\bмарсени\b': 'маркери',
    r'\bвебджіел\b': 'WebGL',
    r'\bвеб\s*джі\s*ел\b': 'WebGL',
    r'\bджавас?крипт\b': 'JavaScript',
    r'\bейч\s*ті\s*ем\s*ел\b': 'HTML',
    r'\bсі\s*ес\s*ес\b': 'CSS',
    r'\bен\s*еф\s*ті\b': 'NFT',
    r'\bлендмарк[иі]?\b': 'landmarks',
    r'\bокклюдер[иі]?\b': 'окклюдери',
    r'\bхіт\s*хап\b': 'GitHub',
    r'\bгітхаб\b': 'GitHub',
    r'\bчисон\b': 'JSON',
}


def parse_timestamp(ts: str) -> float:
    """Convert VTT timestamp to seconds."""
    parts = ts.strip().split(":")
    if len(parts) == 3:
        h, m, s = parts
        s = s.replace(",", ".")
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        s = s.replace(",", ".")
        return int(m) * 60 + float(s)
    return 0.0


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def parse_vtt(filepath: Path) -> list[dict]:
    """Parse a VTT file into a list of {start, end, text} segments."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove WEBVTT header
    content = re.sub(r'^WEBVTT\s*\n', '', content)
    # Remove optional NOTE blocks
    content = re.sub(r'NOTE\s.*?\n\n', '', content, flags=re.DOTALL)

    segments = []
    blocks = re.split(r'\n\n+', content.strip())

    for block in blocks:
        lines = block.strip().split('\n')
        if not lines:
            continue

        # Find timestamp line
        ts_line = None
        text_lines = []
        for line in lines:
            if '-->' in line:
                ts_line = line
            elif ts_line is not None:
                text_lines.append(line.strip())

        if ts_line and text_lines:
            match = re.match(
                r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})',
                ts_line.strip()
            )
            if match:
                start = parse_timestamp(match.group(1))
                end = parse_timestamp(match.group(2))
                text = ' '.join(text_lines).strip()
                if text:
                    segments.append({
                        "start": start,
                        "end": end,
                        "text": text
                    })

    # Sort by start time
    segments.sort(key=lambda s: s["start"])
    return segments


def merge_overlapping(segments: list[dict], gap_threshold: float = 2.0) -> list[dict]:
    """Merge overlapping or closely adjacent segments."""
    if not segments:
        return []

    merged = [segments[0].copy()]
    for seg in segments[1:]:
        prev = merged[-1]
        # Merge if overlapping or within gap threshold
        if seg["start"] <= prev["end"] + gap_threshold:
            prev["end"] = max(prev["end"], seg["end"])
            # Avoid duplicating text
            if seg["text"] not in prev["text"]:
                prev["text"] = prev["text"] + " " + seg["text"]
        else:
            merged.append(seg.copy())

    return merged


def normalize_text(text: str) -> str:
    """Apply ASR normalization dictionary to text."""
    normalized = text
    for pattern, replacement in NORMALIZATION.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    return normalized


def is_ukrainian(text: str) -> bool:
    """Check if text contains Ukrainian/Cyrillic characters."""
    cyrillic = len(re.findall(r'[а-яА-ЯіІїЇєЄґҐ]', text))
    latin = len(re.findall(r'[a-zA-Z]', text))
    total = cyrillic + latin
    if total == 0:
        return False
    return cyrillic / total > 0.3


def assess_quality(segments: list[dict]) -> dict:
    """Calculate quality metrics for a file's segments."""
    total = len(segments)
    if total == 0:
        return {"total_segments": 0, "ukrainian_pct": 0, "avg_length": 0, "quality": "excluded"}

    ukrainian_count = sum(1 for s in segments if is_ukrainian(s["text"]))
    avg_len = sum(len(s["text"]) for s in segments) / total
    short_segments = sum(1 for s in segments if len(s["text"]) < 10)
    ukr_pct = round(ukrainian_count / total * 100, 1)

    # Quality tiers
    if ukr_pct < 30:
        quality = "poor"
    elif ukr_pct < 60:
        quality = "fair"
    elif ukr_pct < 85:
        quality = "good"
    else:
        quality = "excellent"

    total_duration = segments[-1]["end"] - segments[0]["start"] if segments else 0

    return {
        "total_segments": total,
        "ukrainian_pct": ukr_pct,
        "avg_segment_length": round(avg_len, 1),
        "short_segments_pct": round(short_segments / total * 100, 1),
        "total_duration_sec": round(total_duration),
        "total_duration_min": round(total_duration / 60, 1),
        "quality": quality,
    }


def process_file(filepath: Path, filename: str) -> dict:
    """Process a single VTT file."""
    meta = FILE_META.get(filename, ([0], "Unknown"))
    weeks, topic = meta

    is_excluded = filename in EXCLUDED_FILES

    # Parse
    raw_segments = parse_vtt(filepath)

    # Merge overlapping
    merged = merge_overlapping(raw_segments)

    # Normalize and build output segments
    output_segments = []
    for seg in merged:
        normalized = normalize_text(seg["text"])
        output_segments.append({
            "start": format_timestamp(seg["start"]),
            "end": format_timestamp(seg["end"]),
            "start_sec": round(seg["start"], 1),
            "end_sec": round(seg["end"], 1),
            "text": seg["text"],
            "normalized_text": normalized,
        })

    quality = assess_quality(merged)
    if is_excluded:
        quality["quality"] = "excluded"
        quality["exclusion_reason"] = "ASR produced English gibberish instead of Ukrainian"

    return {
        "file": filename,
        "weeks": weeks,
        "topic": topic,
        "excluded": is_excluded,
        "quality": quality,
        "segments": output_segments,
    }


def main():
    if not VTT_DIR.exists():
        print(f"ERROR: VTT directory not found: {VTT_DIR}", file=sys.stderr)
        sys.exit(1)

    vtt_files = sorted(VTT_DIR.glob("*.vtt"))
    print(f"Found {len(vtt_files)} VTT files in {VTT_DIR}")

    results = []
    for vtt_file in vtt_files:
        print(f"  Processing: {vtt_file.name} ...", end=" ")
        result = process_file(vtt_file, vtt_file.name)
        results.append(result)
        q = result["quality"]
        status = "EXCLUDED" if result["excluded"] else q["quality"].upper()
        print(f"{q['total_segments']} segments, "
              f"{q.get('ukrainian_pct', 0)}% Ukrainian, "
              f"{q.get('total_duration_min', 0)} min — {status}")

    # Summary
    usable = [r for r in results if not r["excluded"]]
    total_segments = sum(r["quality"]["total_segments"] for r in usable)
    total_minutes = sum(r["quality"].get("total_duration_min", 0) for r in usable)
    print(f"\nCorpus summary:")
    print(f"  Total files: {len(results)} ({len(usable)} usable, "
          f"{len(results) - len(usable)} excluded)")
    print(f"  Total segments (after merging): {total_segments}")
    print(f"  Total duration: {total_minutes:.0f} min")

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nOutput written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
