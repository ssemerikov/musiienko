"""
Ukrainian NLP utilities for thesis analysis.

Provides tokenization, lemmatization, stopword filtering, and
entity extraction for Ukrainian text using spaCy and pymorphy2.
"""

import re
from typing import List, Set, Optional, Tuple
from dataclasses import dataclass

# Lazy imports for optional dependencies
_spacy = None
_morph = None
_langdetect = None


def _get_spacy():
    """Lazy load spaCy with Ukrainian model."""
    global _spacy
    if _spacy is None:
        try:
            import spacy
            try:
                _spacy = spacy.load("uk_core_news_lg")
            except OSError:
                try:
                    _spacy = spacy.load("uk_core_news_sm")
                except OSError:
                    print("Warning: Ukrainian spaCy model not found. Install with:")
                    print("  python -m spacy download uk_core_news_lg")
                    _spacy = spacy.blank("uk")
        except ImportError:
            print("Warning: spaCy not installed")
            _spacy = None
    return _spacy


def _get_morph():
    """Lazy load pymorphy2 with Ukrainian dictionary."""
    global _morph
    if _morph is None:
        try:
            import pymorphy2
            _morph = pymorphy2.MorphAnalyzer(lang="uk")
        except ImportError:
            print("Warning: pymorphy2 not installed")
            _morph = None
    return _morph


def _get_langdetect():
    """Lazy load langdetect."""
    global _langdetect
    if _langdetect is None:
        try:
            from langdetect import detect, detect_langs
            _langdetect = (detect, detect_langs)
        except ImportError:
            _langdetect = (None, None)
    return _langdetect


@dataclass
class NamedEntity:
    """Named entity extracted from text."""

    text: str
    label: str
    start: int
    end: int


# Extended Ukrainian stopwords for academic texts
UKRAINIAN_STOPWORDS: Set[str] = {
    # Standard stopwords
    "і", "в", "у", "на", "з", "із", "до", "від", "для", "за", "про",
    "що", "як", "та", "або", "чи", "не", "це", "той", "такий", "який",
    "так", "ще", "вже", "б", "би", "ж", "же", "ні", "ось", "он", "ану",
    "він", "вона", "воно", "вони", "ми", "ви", "я", "ти", "їх", "його",
    "її", "їм", "мене", "тебе", "нас", "вас", "собі", "себе",
    "бути", "є", "був", "була", "було", "були", "буде", "будуть",
    "мати", "має", "мають", "могти", "може", "можуть",
    "цей", "ця", "ці", "цього", "цієї", "цих",
    "весь", "вся", "всі", "все", "всього",
    "інший", "інша", "інші", "інше",
    "один", "одна", "одне", "перший", "друга", "третя",
    "коли", "де", "куди", "звідки", "чому", "тому",
    "тут", "там", "сюди", "туди", "тоді", "зараз", "потім",
    "дуже", "більш", "менш", "найбільш",
    "а", "але", "однак", "проте", "тобто", "також", "тільки", "лише",
    "при", "під", "над", "між", "перед", "після", "через", "щодо",

    # Academic/educational context stopwords
    "студент", "студенти", "викладач", "викладачі",
    "курс", "семестр", "кредит", "кредитів",
    "освітній", "освітня", "освітнє", "освітні",
    "програма", "компонент", "компонента",
    "навчальний", "навчальна", "навчальне",
    "практичний", "практична", "практичне",
    "лекція", "лекції", "семінар", "семінари",
    "година", "години", "годин",
    "робота", "роботи", "завдання",
    "знання", "вміння", "навички",
    "результат", "результати", "результатів",
    "метод", "методи", "форма", "форми",
    "контроль", "оцінювання", "оцінка",
    "зміст", "тема", "теми", "модуль",
    "мета", "завдання", "ціль", "цілі",
}


def detect_language(text: str) -> str:
    """
    Detect language of text.

    Returns 'uk' for Ukrainian, 'en' for English, or ISO code.
    """
    detect, _ = _get_langdetect()
    if detect is None:
        return "uk"  # Default assumption

    try:
        return detect(text[:1000])  # Use first 1000 chars
    except Exception:
        return "uk"


def is_ukrainian(text: str, threshold: float = 0.7) -> bool:
    """Check if text is primarily Ukrainian."""
    _, detect_langs = _get_langdetect()
    if detect_langs is None:
        return True

    try:
        langs = detect_langs(text[:1000])
        for lang in langs:
            if lang.lang == "uk" and lang.prob >= threshold:
                return True
        return False
    except Exception:
        return True


def tokenize_ukrainian(
    text: str,
    lowercase: bool = True,
    remove_punctuation: bool = True,
    remove_numbers: bool = False,
    min_length: int = 2,
) -> List[str]:
    """
    Tokenize Ukrainian text.

    Args:
        text: Input text
        lowercase: Convert to lowercase
        remove_punctuation: Remove punctuation tokens
        remove_numbers: Remove numeric tokens
        min_length: Minimum token length

    Returns:
        List of tokens
    """
    nlp = _get_spacy()

    if nlp is None:
        # Fallback: simple regex tokenization
        tokens = re.findall(r"\b[\w'-]+\b", text, re.UNICODE)
    else:
        doc = nlp(text)
        tokens = [token.text for token in doc]

    # Post-processing
    result = []
    for token in tokens:
        if lowercase:
            token = token.lower()

        if remove_punctuation and not re.search(r"\w", token, re.UNICODE):
            continue

        if remove_numbers and token.isdigit():
            continue

        if len(token) < min_length:
            continue

        result.append(token)

    return result


def lemmatize_ukrainian(
    text: str,
    remove_stopwords: bool = True,
    custom_stopwords: Optional[Set[str]] = None,
    min_length: int = 2,
) -> List[str]:
    """
    Lemmatize Ukrainian text.

    Args:
        text: Input text
        remove_stopwords: Remove stopwords
        custom_stopwords: Additional stopwords to remove
        min_length: Minimum lemma length

    Returns:
        List of lemmas
    """
    morph = _get_morph()
    nlp = _get_spacy()

    stopwords = UKRAINIAN_STOPWORDS.copy()
    if custom_stopwords:
        stopwords.update(custom_stopwords)

    # Tokenize first
    tokens = tokenize_ukrainian(text, lowercase=True)

    # Lemmatize
    lemmas = []
    for token in tokens:
        # Skip stopwords early
        if remove_stopwords and token in stopwords:
            continue

        # Get lemma
        if morph:
            parsed = morph.parse(token)
            if parsed:
                lemma = parsed[0].normal_form
            else:
                lemma = token
        elif nlp:
            doc = nlp(token)
            lemma = doc[0].lemma_ if doc else token
        else:
            lemma = token

        # Skip short lemmas
        if len(lemma) < min_length:
            continue

        # Skip stopwords (lemma form)
        if remove_stopwords and lemma in stopwords:
            continue

        lemmas.append(lemma)

    return lemmas


def extract_entities(text: str) -> List[NamedEntity]:
    """
    Extract named entities from Ukrainian text.

    Returns entities like organizations, persons, locations.
    """
    nlp = _get_spacy()
    if nlp is None:
        return []

    doc = nlp(text)
    entities = []

    for ent in doc.ents:
        entities.append(
            NamedEntity(
                text=ent.text,
                label=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
            )
        )

    return entities


def extract_noun_phrases(text: str) -> List[str]:
    """Extract noun phrases from text."""
    nlp = _get_spacy()
    if nlp is None:
        return []

    doc = nlp(text)
    return [chunk.text for chunk in doc.noun_chunks]


def clean_text(
    text: str,
    remove_urls: bool = True,
    remove_emails: bool = True,
    remove_html: bool = True,
    normalize_whitespace: bool = True,
) -> str:
    """
    Clean and normalize text.

    Args:
        text: Input text
        remove_urls: Remove URLs
        remove_emails: Remove email addresses
        remove_html: Remove HTML tags
        normalize_whitespace: Collapse multiple spaces

    Returns:
        Cleaned text
    """
    # Remove HTML tags
    if remove_html:
        text = re.sub(r"<[^>]+>", " ", text)

    # Remove URLs
    if remove_urls:
        text = re.sub(r"https?://\S+", " ", text)
        text = re.sub(r"www\.\S+", " ", text)

    # Remove emails
    if remove_emails:
        text = re.sub(r"\S+@\S+\.\S+", " ", text)

    # Remove file references
    text = re.sub(r"\S+\.(pdf|docx?|xlsx?|pptx?)", " ", text, flags=re.IGNORECASE)

    # Normalize whitespace
    if normalize_whitespace:
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

    return text


def get_word_frequencies(
    texts: List[str],
    top_n: int = 100,
    lemmatize: bool = True,
) -> List[Tuple[str, int]]:
    """
    Get word frequencies across texts.

    Args:
        texts: List of text documents
        top_n: Number of top words to return
        lemmatize: Whether to lemmatize words

    Returns:
        List of (word, count) tuples sorted by frequency
    """
    from collections import Counter

    all_words = []
    for text in texts:
        if lemmatize:
            words = lemmatize_ukrainian(text)
        else:
            words = tokenize_ukrainian(text)
        all_words.extend(words)

    counter = Counter(all_words)
    return counter.most_common(top_n)


def normalize_course_name(name: str) -> str:
    """
    Normalize course name for comparison.

    Removes codes, normalizes case, removes extra whitespace.
    """
    if not name:
        return ""

    # Remove component codes like ОА.01, ОП.04, ВБ.1, ОК 12
    name = re.sub(r"^(?:ОА|ОП|ВБ|ВВ|ВК|ОК|ОДЗ|ОДФ|НК|ПП)[\s._]*\d*[\s._]*", "", name, flags=re.IGNORECASE)

    # Remove leading numbers with dots/spaces (e.g., "1. ", "12. ")
    name = re.sub(r"^\d+[\s.]+", "", name)

    # Remove quotes
    name = name.replace('"', "").replace("'", "").replace("«", "").replace("»", "")

    # Normalize whitespace
    name = re.sub(r"\s+", " ", name).strip()

    # Lowercase
    name = name.lower()

    # Return original if normalization produced empty string
    if not name:
        return name.lower() if name else ""

    return name


def extract_credits_from_text(text: str) -> Optional[float]:
    """Extract ECTS credits from text."""
    patterns = [
        r"(\d+(?:[.,]\d+)?)\s*(?:кредит|ECTS|ЄКТС)",
        r"кредит[іи]?[вс]?:?\s*(\d+(?:[.,]\d+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                continue

    return None
