#!/usr/bin/env python3
"""
Automated pre-coding of lecture transcript segments.

Reads segments.json (from parse_vtt.py) and applies keyword-based code
assignment across 6 dimensions: CAMIL, TPACK, Pedagogical Conditions,
Methodology Stages, Teaching Strategies, Readiness Components.

Output: coded_segments.json with multi-label codes per segment.
"""

import json
import re
import sys
from pathlib import Path

INPUT_FILE = Path(__file__).resolve().parent / "segments.json"
OUTPUT_FILE = Path(__file__).resolve().parent / "coded_segments.json"

# ──────────────────────────────────────────────────────────────
# Coding scheme: dimension -> code -> keywords (Ukrainian + normalized)
# ──────────────────────────────────────────────────────────────

CODING_SCHEME = {
    "CAMIL": {
        "CAM-PRES": {  # Presence
            "keywords": [
                r"занурен", r"присутніст", r"реалістичн", r"як справжн",
                r"відчуваєте.*реальн", r"ефект присутності", r"immersive",
                r"оточуюч", r"ніби.*справжн", r"відчуття.*простор",
            ],
        },
        "CAM-AGEN": {  # Agency
            "keywords": [
                r"самостійн", r"обирає?те", r"вирішує?те", r"варіант.*реалізац",
                r"ваш.*вибір", r"можете.*обрати", r"ваше.*рішення",
                r"спробуйте.*сам", r"свій.*проект", r"власн.*модел",
                r"індивідуальн", r"творч.*завданн",
            ],
        },
        "CAM-EMBO": {  # Embodiment
            "keywords": [
                r"жест", r"рук[аи]", r"руки", r"обличчя", r"тіл[оа]",
                r"handpose", r"face.*tracking", r"маска", r"окклюдер",
                r"landmarks", r"опорн.*точк", r"перемикання камер",
                r"захоплення кадр", r"дотик",
            ],
        },
        "CAM-COGN": {  # Cognitive load
            "keywords": [
                r"поступов", r"крок.*за.*кроком", r"спочатку.*потім",
                r"давайте.*розбер", r"не.*лякайтесь", r"спрощен",
                r"складн", r"простіш", r"не.*хвилюйтесь", r"полегш",
                r"по.*черз", r"важлив.*зрозумі", r"зверніть увагу",
                r"нагадаю", r"пригадайте",
            ],
        },
        "CAM-MOTI": {  # Motivation
            "keywords": [
                r"цікав[оеі]", r"круто", r"вражаюч", r"побачите.*результат",
                r"зможете", r"уявіт", r"мотивац", r"надихає?",
                r"реальн.*застосуван", r"можливост", r"перспектив",
                r"приклад.*з.*жит", r"практичн.*значен", r"корисн",
            ],
        },
        "CAM-SREG": {  # Self-regulation
            "keywords": [
                r"рефлексі", r"самооціню", r"проаналізуй", r"перевірте.*себ",
                r"подумайте.*що.*вдал", r"які.*труднощі", r"зворотн.*зв'яз",
                r"взаємооціню", r"оцінюван", r"критері.*оцінк",
                r"портфоліо", r"есе", r"захист.*проєкт",
            ],
        },
    },
    "TPACK": {
        "TPACK-TK": {  # Technological Knowledge
            "keywords": [
                r"Three\.js", r"MindAR", r"WebXR", r"A-Frame",
                r"TensorFlow", r"JavaScript", r"WebGL", r"HTML",
                r"бібліотек[аи]", r"фреймворк", r"API",
                r"renderer", r"сцен[аи]", r"камер[аи]", r"об'єкт",
                r"матеріал", r"текстур", r"освітлен", r"анімаці",
                r"GLTF", r"GLB", r"ngrok", r"Teachable Machine",
                r"handpose", r"face-api", r"модел[ьі]",
                r"hit testing", r"контролер",
            ],
        },
        "TPACK-PK": {  # Pedagogical Knowledge
            "keywords": [
                r"методик[аи]", r"педагогічн", r"навчальн.*процес",
                r"дидактичн", r"навчальн.*мет[аи]", r"учні",
                r"студент", r"засвоєнн", r"компетентніст",
                r"навчальн.*ситуац", r"педагогічн.*дизайн",
            ],
        },
        "TPACK-TPK": {  # Technological Pedagogical Knowledge
            "keywords": [
                r"як.*використ.*навчанн", r"освітн.*ресурс",
                r"навчальн.*WebAR", r"імерсивн.*освіт",
                r"педагогічн.*доцільн", r"для.*якої.*теми",
                r"навчальн.*мет.*технолог", r"WebAR.*освіт",
                r"для.*учнів", r"у.*школі",
            ],
        },
        "TPACK-INT": {  # Full TPACK integration
            "keywords": [
                r"хімічн.*лаборатор", r"anchem", r"навчальн.*AR.*ресурс",
                r"предметн.*галуз", r"обґрунтуван.*педагогічн",
                r"повний.*цикл.*розробк", r"від.*ідеї.*до.*реалізац",
                r"інтеграц.*ML.*освіт",
            ],
        },
    },
    "PED_CONDITIONS": {
        "PC-PSYCH": {  # Psychological-pedagogical
            "keywords": [
                r"мотивуюч", r"підтримк", r"успіх", r"ситуац.*успіх",
                r"не.*бійтесь", r"помилк.*нормальн", r"допомож",
                r"підтримувальн", r"заохочен", r"позитивн.*досвід",
                r"довірливе.*середовищ", r"це.*нормальн",
            ],
        },
        "PC-METHOD": {  # Methodological
            "keywords": [
                r"посібник", r"підручник", r"розділ.*посібник",
                r"відеолекці", r"відеоматеріал", r"зразок",
                r"покроков.*інструкц", r"навчальн.*матеріал",
                r"тест.*для.*перевірк", r"систематичн",
            ],
        },
        "PC-TECH": {  # Technological
            "keywords": [
                r"ngrok", r"live.*server", r"середовищ.*розробк",
                r"HTTPS", r"Chrome.*DevTools", r"налагоджен",
                r"мобільн.*пристр", r"тестуван.*на.*пристро",
                r"браузер", r"код.*редактор",
            ],
        },
        "PC-ORG": {  # Organizational
            "keywords": [
                r"дедлайн", r"термін", r"здач", r"тиждень",
                r"Moodle", r"розклад", r"завданн.*на.*тижден",
                r"домашн.*завданн", r"лаборатор.*робот",
                r"форум", r"курс.*синтетичн",
            ],
        },
    },
    "METHODOLOGY_STAGES": {
        "MS-THEOR": {  # Theoretical-analytical (weeks 1-6)
            "keywords": [
                r"теоретичн", r"основи", r"принципи",
                r"що.*таке.*WebAR", r"ознайомл", r"вступ",
                r"як.*працює", r"архітектур", r"класифікац",
                r"означен", r"визначен",
            ],
        },
        "MS-PRACT": {  # Practical-developmental (weeks 7-14)
            "keywords": [
                r"розробля", r"реалізу[єй]", r"створю[єй]",
                r"запрограму", r"пишемо.*код", r"додаємо",
                r"практичн", r"лаборатор", r"завданн",
            ],
        },
        "MS-INTEG": {  # Integrative-reflective (weeks 15-18)
            "keywords": [
                r"інтегр[аую]", r"комплексн", r"узагальн",
                r"підсумков", r"проєкт", r"повноцінн",
                r"від.*початку.*до.*кінц", r"повний.*цикл",
            ],
        },
    },
    "TEACHING_STRATEGIES": {
        "TS-MODEL": {  # Modeling/Demonstration
            "keywords": [
                r"подивимось", r"подивимося", r"подивіться",
                r"демонструю", r"покажу", r"бачите",
                r"дивіться", r"ось.*бачите", r"показую",
                r"зараз.*побачите", r"як.*виглядає",
                r"спробую.*показати", r"як.*це.*працює",
                r"давайте.*подивимось", r"ось.*результат",
            ],
        },
        "TS-SCAFF": {  # Scaffolding
            "keywords": [
                r"спочатку.*потім", r"крок.*за.*кроком",
                r"починаємо.*з", r"поступово",
                r"на.*попередньому.*занятті", r"вже.*знаємо",
                r"пам'ятаєте", r"як.*ми.*робили",
                r"базуючись.*на", r"вже.*вміємо", r"раніше",
            ],
        },
        "TS-QUEST": {  # Questioning
            "keywords": [
                r"як.*думаєте", r"чому", r"навіщо",
                r"що.*буде.*якщо", r"хто.*може.*сказати",
                r"питанн[яі]", r"запитанн",
                r"є.*питання", r"хто.*знає",
            ],
        },
        "TS-FEEDB": {  # Feedback
            "keywords": [
                r"молодц", r"правильно", r"добре.*зроблено",
                r"вірно", r"так.*саме", r"чудово",
                r"помилк[аи]", r"неправильно", r"виправ",
                r"зверніть.*увагу.*на.*помилк",
            ],
        },
        "TS-TROUB": {  # Troubleshooting
            "keywords": [
                r"проблем[аи]", r"помилк[аи]", r"не.*працює",
                r"вирішен", r"як.*виправити", r"debug",
                r"налагоджен", r"консоль", r"error",
                r"виникають.*труднощ", r"якщо.*не.*працює",
                r"причин[аи]", r"типов.*помилк",
            ],
        },
        "TS-REAL": {  # Real-world connection
            "keywords": [
                r"реальн.*приклад", r"у.*реальному.*житт",
                r"на.*практиц", r"застосуванн.*в.*освіт",
                r"хімічн.*лаборатор", r"профорієнтац",
                r"у.*школ[іі]", r"для.*учнів", r"у.*промисловост",
                r"комерційн",
            ],
        },
    },
    "READINESS": {
        "RC-MVAL": {  # Motivational-value
            "keywords": [
                r"значущ", r"важлив.*для", r"цінніст",
                r"чому.*це.*потрібн", r"навіщо.*вчител",
                r"значенн.*для.*освіт",
            ],
        },
        "RC-COGN": {  # Cognitive
            "keywords": [
                r"знанн[яі]", r"розумінн[яі]", r"теорі[яї]",
                r"концепці[яї]", r"архітектур[аи]",
                r"як.*влаштован", r"як.*працює",
            ],
        },
        "RC-ACTD": {  # Activity-design
            "keywords": [
                r"розробляє?мо", r"створює?мо", r"реалізує?мо",
                r"програмує?мо", r"практичн.*завданн",
                r"лабораторн", r"проєкт",
            ],
        },
        "RC-TECH": {  # Technological
            "keywords": [
                r"інструмент", r"засо[бі]", r"технолог",
                r"бібліотек", r"фреймворк", r"платформ",
                r"середовищ.*розробк",
            ],
        },
        "RC-INTR": {  # Interactive
            "keywords": [
                r"взаємоді[яї]", r"інтерактивн", r"спільн",
                r"обговор", r"форум", r"допомож.*один",
                r"взаємодопомог", r"командн",
            ],
        },
        "RC-REFL": {  # Reflective
            "keywords": [
                r"рефлексі", r"самоаналіз", r"самооцінк",
                r"аналіз.*власн", r"що.*вдалос",
                r"що.*не.*вдалос", r"подумайте",
            ],
        },
    },
}

# Week → methodology stage mapping
WEEK_TO_STAGE = {}
for w in range(1, 7):
    WEEK_TO_STAGE[w] = "theoretical-analytical"
for w in range(7, 15):
    WEEK_TO_STAGE[w] = "practical-developmental"
for w in range(15, 19):
    WEEK_TO_STAGE[w] = "integrative-reflective"


def code_segment(text: str) -> dict:
    """Apply keyword-based coding to a text segment across all dimensions."""
    codes = {}
    for dimension, dim_codes in CODING_SCHEME.items():
        matched = []
        for code, info in dim_codes.items():
            hits = 0
            for kw in info["keywords"]:
                if re.search(kw, text, re.IGNORECASE):
                    hits += 1
            if hits > 0:
                confidence = "high" if hits >= 3 else "medium" if hits >= 2 else "low"
                matched.append({"code": code, "hits": hits, "confidence": confidence})
        if matched:
            matched.sort(key=lambda x: x["hits"], reverse=True)
            codes[dimension] = matched
    return codes


def determine_stage(weeks: list[int]) -> str:
    """Determine methodology stage from week numbers."""
    if not weeks:
        return "unknown"
    primary_week = weeks[0]
    return WEEK_TO_STAGE.get(primary_week, "unknown")


def main():
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}", file=sys.stderr)
        print("Run parse_vtt.py first.", file=sys.stderr)
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} files from segments.json")

    coded_files = []
    total_coded = 0
    total_segments = 0
    dim_counts = {}

    for file_data in data:
        if file_data.get("excluded"):
            coded_files.append({
                **file_data,
                "methodology_stage": "unknown",
            })
            continue

        stage = determine_stage(file_data["weeks"])
        coded_segments = []

        for seg in file_data["segments"]:
            text = seg["normalized_text"]
            codes = code_segment(text)

            coded_seg = {
                **seg,
                "codes": codes,
                "coded": bool(codes),
            }
            coded_segments.append(coded_seg)

            if codes:
                total_coded += 1
                for dim in codes:
                    dim_counts[dim] = dim_counts.get(dim, 0) + 1
            total_segments += 1

        coded_files.append({
            "file": file_data["file"],
            "weeks": file_data["weeks"],
            "topic": file_data["topic"],
            "excluded": False,
            "quality": file_data["quality"],
            "methodology_stage": stage,
            "segments": coded_segments,
        })

        coded_count = sum(1 for s in coded_segments if s["coded"])
        print(f"  {file_data['file']}: {coded_count}/{len(coded_segments)} segments coded "
              f"[stage: {stage}]")

    # Summary
    print(f"\nPre-coding summary:")
    print(f"  Total segments: {total_segments}")
    print(f"  Coded segments: {total_coded} ({total_coded/total_segments*100:.1f}%)")
    print(f"  Dimension distribution:")
    for dim, count in sorted(dim_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    {dim}: {count} segments")

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(coded_files, f, ensure_ascii=False, indent=2)
    print(f"\nOutput written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
