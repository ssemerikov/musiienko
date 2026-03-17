#!/usr/bin/env python3
"""
Translate all Ukrainian text data to English for deep contextual analysis.

Processes:
- Extracted PDF text files (text_by_level/)
- Scraped JSON data (data/raw/)

Uses Helsinki-NLP/opus-mt-uk-en model via Hugging Face.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from tqdm import tqdm

# Translation model config
MODEL_NAME = "Helsinki-NLP/opus-mt-uk-en"
MAX_LENGTH = 512  # Max tokens per chunk
BATCH_SIZE = 8


class UkrainianToEnglishTranslator:
    """Translates Ukrainian text to English using HF transformers."""

    def __init__(self, model_name: str = MODEL_NAME, use_gpu: bool = False):
        self.model_name = model_name
        self.device = "cuda" if use_gpu else "cpu"
        self._pipeline = None
        self._tokenizer = None

    def _load_model(self):
        """Lazy load the translation model."""
        if self._pipeline is None:
            print(f"Loading translation model: {self.model_name}")
            try:
                from transformers import pipeline, AutoTokenizer

                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._pipeline = pipeline(
                    "translation",
                    model=self.model_name,
                    tokenizer=self._tokenizer,
                    device=-1,  # CPU
                    max_length=MAX_LENGTH,
                )
                print("Model loaded successfully")
            except Exception as e:
                print(f"Error loading model: {e}")
                print("Falling back to simple dictionary-based translation")
                self._pipeline = "fallback"

    def _chunk_text(self, text: str, max_chars: int = 400) -> List[str]:
        """Split text into chunks for translation (max ~400 chars for safety)."""
        if not text:
            return []

        text = text.strip()
        if len(text) <= max_chars:
            return [text]

        chunks = []
        # Split on sentence boundaries first
        sentences = re.split(r'(?<=[.!?।])\s+', text)
        current_chunk = ""

        for sentence in sentences:
            # If single sentence is too long, split by words
            if len(sentence) > max_chars:
                words = sentence.split()
                for word in words:
                    if len(current_chunk) + len(word) + 1 <= max_chars:
                        current_chunk += " " + word if current_chunk else word
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = word
            elif len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def translate(self, text: str) -> str:
        """Translate Ukrainian text to English."""
        if not text or not text.strip():
            return ""

        self._load_model()

        if self._pipeline == "fallback":
            return self._fallback_translate(text)

        try:
            # Split into small chunks (400 chars max for safety with tokenizer)
            chunks = self._chunk_text(text, max_chars=350)

            if not chunks:
                return ""

            translated_chunks = []
            for chunk in chunks:
                if chunk.strip():
                    try:
                        result = self._pipeline(chunk, max_length=512, truncation=True)
                        if result and len(result) > 0:
                            translated_chunks.append(result[0]['translation_text'])
                    except Exception:
                        # Keep original if translation fails
                        translated_chunks.append(chunk)

            return " ".join(translated_chunks)

        except Exception as e:
            return self._fallback_translate(text)

    def translate_batch(self, texts: List[str]) -> List[str]:
        """Translate multiple texts efficiently."""
        self._load_model()

        if self._pipeline == "fallback":
            return [self._fallback_translate(t) for t in texts]

        results = []
        for text in texts:
            results.append(self.translate(text))
        return results

    def _fallback_translate(self, text: str) -> str:
        """Simple fallback using common word replacements."""
        # Import the translation dictionary
        try:
            from thesis_analysis.visualization.plots import COURSE_TRANSLATIONS
        except ImportError:
            COURSE_TRANSLATIONS = {}

        # Extended translations for common academic terms
        FALLBACK_DICT = {
            **COURSE_TRANSLATIONS,
            # Common words
            "та": "and",
            "або": "or",
            "для": "for",
            "від": "from",
            "до": "to",
            "на": "on",
            "про": "about",
            "при": "at",
            "за": "by",
            "що": "that",
            "як": "as",
            "також": "also",
            "інший": "other",
            "новий": "new",
            "перший": "first",
            "другий": "second",
            # Academic terms
            "студент": "student",
            "викладач": "instructor",
            "курс": "course",
            "програма": "program",
            "освіта": "education",
            "навчання": "learning",
            "дизайн": "design",
            "мистецтво": "art",
            "творчість": "creativity",
            "проект": "project",
            "робота": "work",
            "аналіз": "analysis",
            "метод": "method",
            "результат": "result",
            "компетентність": "competency",
            "знання": "knowledge",
            "вміння": "skill",
            "здатність": "ability",
            "оцінювання": "assessment",
            "контроль": "control",
            "практика": "practice",
            "теорія": "theory",
            "основи": "fundamentals",
            "вступ": "introduction",
            "історія": "history",
            "сучасний": "modern",
            "український": "Ukrainian",
            "національний": "national",
            "міжнародний": "international",
            "професійний": "professional",
            "науковий": "scientific",
            "творчий": "creative",
            "візуальний": "visual",
            "графічний": "graphic",
            "комп'ютерний": "computer",
            "цифровий": "digital",
            "інформаційний": "information",
            "технологія": "technology",
            "система": "system",
            "процес": "process",
            "розвиток": "development",
            "формування": "formation",
            "створення": "creation",
            "використання": "usage",
            "застосування": "application",
            "вивчення": "study",
            "дослідження": "research",
            "аспект": "aspect",
            "принцип": "principle",
            "підхід": "approach",
            "концепція": "concept",
            "модель": "model",
            "структура": "structure",
            "функція": "function",
            "елемент": "element",
            "компонент": "component",
            "характеристика": "characteristic",
            "особливість": "feature",
            "властивість": "property",
            "якість": "quality",
            "рівень": "level",
            "ступінь": "degree",
            "етап": "stage",
            "фаза": "phase",
            "період": "period",
            "час": "time",
            "простір": "space",
            "форма": "form",
            "зміст": "content",
            "значення": "meaning",
            "роль": "role",
            "місце": "place",
            "частина": "part",
            "ціле": "whole",
            "зв'язок": "connection",
            "взаємодія": "interaction",
            "вплив": "influence",
            "ефект": "effect",
        }

        result = text.lower()
        for uk, en in sorted(FALLBACK_DICT.items(), key=lambda x: len(x[0]), reverse=True):
            result = re.sub(r'\b' + re.escape(uk) + r'\b', en, result, flags=re.IGNORECASE)

        return result


def translate_text_file(
    input_path: Path,
    output_path: Path,
    translator: UkrainianToEnglishTranslator,
) -> bool:
    """Translate a single text file."""
    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        if not text.strip():
            # Copy empty file as-is
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("")
            return True

        translated = translator.translate(text)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated)

        return True

    except Exception as e:
        print(f"Error translating {input_path}: {e}")
        return False


def translate_json_file(
    input_path: Path,
    output_path: Path,
    translator: UkrainianToEnglishTranslator,
    fields_to_translate: List[str],
) -> bool:
    """Translate specific fields in a JSON file."""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        def translate_recursive(obj, fields):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in fields and isinstance(value, str):
                        obj[key] = translator.translate(value)
                    elif isinstance(value, (dict, list)):
                        translate_recursive(value, fields)
            elif isinstance(obj, list):
                for item in obj:
                    translate_recursive(item, fields)

        translate_recursive(data, fields_to_translate)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        print(f"Error translating {input_path}: {e}")
        return False


def get_text_files(base_dir: Path) -> Generator[Path, None, None]:
    """Get all text files from directory structure."""
    for txt_file in base_dir.rglob("*.txt"):
        yield txt_file


def main():
    print("=" * 60)
    print("UKRAINIAN TO ENGLISH TRANSLATION PIPELINE")
    print("=" * 60)

    # Paths
    data_dir = Path("data")
    text_dir = data_dir / "text_by_level"
    raw_dir = data_dir / "raw"

    output_base = data_dir / "text_english"
    output_json = data_dir / "raw_english"

    # Initialize translator
    print("\n[1/4] Initializing translator...")
    translator = UkrainianToEnglishTranslator()

    # Count files
    print("\n[2/4] Scanning files...")
    text_files = list(get_text_files(text_dir))
    json_files = list(raw_dir.glob("case_*.json"))

    print(f"  Found {len(text_files)} text files")
    print(f"  Found {len(json_files)} JSON files")

    # Translate text files
    print(f"\n[3/4] Translating text files to {output_base}...")
    output_base.mkdir(parents=True, exist_ok=True)

    success_count = 0
    error_count = 0

    for txt_file in tqdm(text_files, desc="Translating texts"):
        # Preserve directory structure
        rel_path = txt_file.relative_to(text_dir)
        output_path = output_base / rel_path

        if translate_text_file(txt_file, output_path, translator):
            success_count += 1
        else:
            error_count += 1

    print(f"  Translated: {success_count}, Errors: {error_count}")

    # Translate JSON files
    print(f"\n[4/4] Translating JSON files to {output_json}...")
    output_json.mkdir(parents=True, exist_ok=True)

    # Fields to translate in JSON
    fields_to_translate = [
        "name", "title", "description", "content", "text",
        "institution", "program_name", "specialty_name",
        "component_name", "competency_text", "learning_outcome",
    ]

    json_success = 0
    json_errors = 0

    for json_file in tqdm(json_files, desc="Translating JSONs"):
        output_path = output_json / json_file.name

        if translate_json_file(json_file, output_path, translator, fields_to_translate):
            json_success += 1
        else:
            json_errors += 1

    print(f"  Translated: {json_success}, Errors: {json_errors}")

    # Summary
    print("\n" + "=" * 60)
    print("TRANSLATION COMPLETE")
    print("=" * 60)
    print(f"\nEnglish text files: {output_base}")
    print(f"English JSON files: {output_json}")
    print(f"\nTotal files processed: {success_count + json_success}")
    print(f"Total errors: {error_count + json_errors}")


if __name__ == "__main__":
    main()
