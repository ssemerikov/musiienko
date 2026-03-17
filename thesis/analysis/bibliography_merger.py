"""
Bibliography merger for Musiienko PhD thesis.
Parses ~52 .bib files, deduplicates by DOI and fuzzy title matching, normalizes, and merges.
"""

import re
from pathlib import Path
from collections import defaultdict

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from rapidfuzz import fuzz

BASE = Path(__file__).resolve().parent.parent.parent
OUTPUT_BIB = Path(__file__).resolve().parent.parent / "references.bib"

# All directories containing .bib files
BIB_SOURCES = [
    BASE / "articles" / "13_1093_Musiienko" / "source",
    BASE / "articles" / "13_1093_Musiienko" / "materials",
    BASE / "articles" / "13_1112_Musiienko" / "source",
    BASE / "articles" / "13_1112_Musiienko" / "materials",
    BASE / "design" / "thesis_output" / "latex",
]

# Our own entries to always keep (written manually in references.bib)
OWN_KEYS = {"Musiienko2026ScopingReview", "Musiienko2025DesignEducation"}


def collect_bib_files() -> list[Path]:
    """Find all .bib files in source directories."""
    files = []
    for src in BIB_SOURCES:
        if src.exists():
            files.extend(src.glob("*.bib"))
    return sorted(set(files))


def parse_bib_file(filepath: Path) -> list[dict]:
    """Parse a single .bib file with error tolerance."""
    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode
    parser.ignore_nonstandard_types = False

    try:
        with open(filepath, encoding='utf-8', errors='replace') as f:
            content = f.read()
        bib_db = bibtexparser.loads(content, parser=parser)
        return bib_db.entries
    except Exception as e:
        print(f"  Warning: could not parse {filepath.name}: {e}")
        return []


def normalize_doi(doi: str) -> str:
    """Normalize DOI to lowercase, remove URL prefix."""
    doi = doi.strip().lower()
    for prefix in ['https://doi.org/', 'http://doi.org/', 'http://dx.doi.org/', 'https://dx.doi.org/']:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi


def normalize_title(title: str) -> str:
    """Normalize title for fuzzy comparison."""
    title = re.sub(r'[{}\\]', '', title)
    title = re.sub(r'\s+', ' ', title).strip().lower()
    return title


def deduplicate_entries(all_entries: list[dict]) -> list[dict]:
    """Deduplicate entries by DOI (exact) and title (fuzzy)."""
    seen_dois = {}      # doi -> entry
    seen_titles = {}    # normalized_title -> entry
    unique = []
    duplicates = 0

    for entry in all_entries:
        entry_id = entry.get('ID', '')

        # Skip our own manually maintained entries
        if entry_id in OWN_KEYS:
            continue

        doi = entry.get('doi', '')
        title = entry.get('title', '')

        # Check DOI duplicate
        if doi:
            norm_doi = normalize_doi(doi)
            if norm_doi in seen_dois:
                duplicates += 1
                # Keep the entry with more fields
                existing = seen_dois[norm_doi]
                if len(entry) > len(existing):
                    seen_dois[norm_doi] = entry
                    # Replace in unique list
                    for i, u in enumerate(unique):
                        if u.get('ID') == existing.get('ID'):
                            unique[i] = entry
                            break
                continue
            seen_dois[norm_doi] = entry

        # Check fuzzy title duplicate
        if title:
            norm_title = normalize_title(title)
            is_dup = False
            for seen_title, seen_entry in seen_titles.items():
                if fuzz.ratio(norm_title, seen_title) > 90:
                    duplicates += 1
                    is_dup = True
                    # Keep entry with more fields
                    if len(entry) > len(seen_entry):
                        seen_titles[seen_title] = entry
                        for i, u in enumerate(unique):
                            if u.get('ID') == seen_entry.get('ID'):
                                unique[i] = entry
                                break
                    break
            if is_dup:
                continue
            seen_titles[norm_title] = entry

        unique.append(entry)

    return unique, duplicates


def ensure_required_fields(entry: dict) -> dict:
    """Ensure GOST-numeric required fields are present."""
    # Add langid if missing
    if 'langid' not in entry:
        title = entry.get('title', '')
        # Detect Ukrainian/Russian by Cyrillic characters
        if re.search(r'[\u0400-\u04FF]', title):
            entry['langid'] = 'ukrainian'
        else:
            entry['langid'] = 'english'
    return entry


def generate_unique_key(entry: dict, existing_keys: set) -> str:
    """Generate a unique BibTeX key for an entry."""
    author = entry.get('author', 'Unknown')
    year = entry.get('year', 'XXXX')

    # Extract first author's last name
    first_author = author.split(' and ')[0].split(',')[0].strip()
    first_author = re.sub(r'[^a-zA-Z\u0400-\u04FF]', '', first_author)
    if not first_author:
        first_author = 'Unknown'

    # Get first significant word from title
    title = entry.get('title', '')
    title_word = ''
    for word in re.sub(r'[{}]', '', title).split():
        if len(word) > 3 and word.isalpha():
            title_word = word.capitalize()
            break

    base_key = f"{first_author}{year}{title_word}"

    # Ensure uniqueness
    key = base_key
    counter = 1
    while key in existing_keys:
        key = f"{base_key}_{counter}"
        counter += 1

    existing_keys.add(key)
    return key


def write_bib(entries: list[dict], output_path: Path, header: str = ""):
    """Write entries to a .bib file."""
    db = bibtexparser.bibdatabase.BibDatabase()
    db.entries = entries

    writer = bibtexparser.bwriter.BibTexWriter()
    writer.indent = '  '
    writer.comma_first = False

    content = header + bibtexparser.dumps(db, writer)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    print("=== Bibliography Merger ===")

    # Collect all .bib files
    bib_files = collect_bib_files()
    print(f"Found {len(bib_files)} .bib files")

    # Parse all entries
    all_entries = []
    for bf in bib_files:
        entries = parse_bib_file(bf)
        if entries:
            print(f"  {bf.name}: {len(entries)} entries")
            all_entries.extend(entries)

    print(f"\nTotal entries parsed: {len(all_entries)}")

    # Deduplicate
    unique_entries, n_dups = deduplicate_entries(all_entries)
    print(f"Duplicates removed: {n_dups}")
    print(f"Unique entries: {len(unique_entries)}")

    # Normalize fields
    unique_entries = [ensure_required_fields(e) for e in unique_entries]

    # Ensure unique keys
    existing_keys = set(OWN_KEYS)
    for entry in unique_entries:
        old_key = entry.get('ID', '')
        if old_key in existing_keys:
            entry['ID'] = generate_unique_key(entry, existing_keys)
        else:
            existing_keys.add(old_key)

    # Read the header (own entries) from current references.bib
    header = ""
    if OUTPUT_BIB.exists():
        content = OUTPUT_BIB.read_text(encoding='utf-8')
        # Keep everything up to the "Additional references" comment
        marker = "% === Additional references"
        if marker in content:
            header = content[:content.index(marker)]
        else:
            header = content + "\n\n"

    header += "% === Additional references (auto-merged) ===\n\n"

    # Write merged bibliography
    write_bib(unique_entries, OUTPUT_BIB, header=header)

    # Statistics by type
    type_counts = defaultdict(int)
    for e in unique_entries:
        type_counts[e.get('ENTRYTYPE', 'unknown')] += 1
    print(f"\nEntry types: {dict(type_counts)}")

    # Language distribution
    lang_counts = defaultdict(int)
    for e in unique_entries:
        lang_counts[e.get('langid', 'unspecified')] += 1
    print(f"Languages: {dict(lang_counts)}")

    total = len(unique_entries) + len(OWN_KEYS)
    print(f"\nTotal in references.bib: {total} entries (including {len(OWN_KEYS)} own publications)")
    print(f"Output: {OUTPUT_BIB}")


if __name__ == "__main__":
    main()
