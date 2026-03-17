#!/usr/bin/env python3
"""Quick test of Ukrainian to English translation."""

import sys
sys.path.insert(0, '.')

from translate_all_texts import UkrainianToEnglishTranslator

# Test texts
test_texts = [
    "Метою курсу є формування знань студентів про основи дизайну.",
    "Історія українського мистецтва та культури.",
    "Комп'ютерні технології в графічному дизайні.",
    "Студент має вміти аналізувати та створювати візуальні проекти.",
]

print("Testing Ukrainian to English translation...")
print("=" * 60)

translator = UkrainianToEnglishTranslator()

for i, text in enumerate(test_texts, 1):
    print(f"\n[{i}] Original (Ukrainian):")
    print(f"    {text}")
    translated = translator.translate(text)
    print(f"    Translated (English):")
    print(f"    {translated}")

print("\n" + "=" * 60)
print("Test complete!")
