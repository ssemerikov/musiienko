#!/usr/bin/env python3
"""Map citation codes to BibTeX keys and replace \hl{} markers in chapter files."""

# Code -> BibTeX key mapping
MAPPING = {
    # Foreign sources (Latin-letter codes)
    'U-1': 'UNESCO2021DigEd',
    'A-1': 'Alalwan2020VR',
    'D-1': 'Dalgarno2010What',
    'D-2': 'DiNatale2020Immersive',
    'R-1': 'Radianti2020VR',
    'Ke-1': 'Kerr2020Augmented',
    'Ke-2': 'Kennedy2023Immersive',
    'Аe-1': 'Akdeniz2023AR',  # Cyrillic А + Latin e
    'Re-2': 'Parong2021Cognitive',
    'Re-3': 'Krokos2019Virtual',
    'S-1': 'Semerikov2022IERDesign',  # in mypaper.bib
    'ITE-2025': 'ITE2025Conf',
    # Ukrainian sources (Cyrillic codes)
    'А-1': 'Angelov2025Synergy',
    'А-3': 'Burov2024Interactive',
    'А-4': 'Andrushchenko2018Prof',
    'Б-2': 'Boiko2024Immersive',
    'Б-3': 'Batsenko2025Blended',
    'Б-4': 'Bilovus2024Hub',
    'Б-5': 'Bogachkov2023Immersive',
    'Б-6': 'Brovko2024Foreign',
    'Б-9': 'Bei2020Model',
    'Б-10': 'Borovyk2019Research',
    'В-4': 'Vorovka2018Modeling',
    'В-5': 'Vdovychyn2015Conditions',
    'В-7': 'VTSSM2005',
    'Г-1': 'Goncharenko2011Pedagogy',
    'Г-3': 'Hryhorenko2024Experience',
    'Г-6': 'Granchak2023Heritage',
    'Г-9': 'Gordeev2025Printing',
    'Г-10': 'Gurska2025Personalized',
    'Г-11': 'Gnedina2025Quality',
    'Г-16': 'Grebeniuk2018Didactic',
    'Г-17': 'Goncharova2017Differentiated',
    'Г-18': 'Goncharenko1997Dictionary',
    'Г-20': 'Gurevych2015Integration',
    'Г-21': 'Gurevych2012Pedagogy',
    'Д-1': 'Dotsenko2023Immersive',  # Cyrillic Д - Доценко
    'Д-3': 'Drokina2025STEM',
    'Д-7': 'Dychkivska2012Innovative',
    'Д-8': 'Dubaseniuk2017Freedom',
    'Д-9': 'Dubaseniuk2008Modeling',
    'З-2': 'Ziaziun2000Philosophy',
    'К-5': 'Kibenko2022Digital',
    'К-6': 'Kyriienko2023Biology',
    'К-7': 'Kravchyna2023Entrepreneurial',
    'К-9': 'Kulyk2024Ukrainian',
    'К-10': 'Kindzhibala2025Creative',
    'К-16': 'Kremen2016Axiological',
    'К-17': 'KVR2017Definition',
    'К-19': 'Kopniak2020Structural',
    'К-20': 'Kosianchuk2019Modeling',
    'К-21': 'Kuzminskyi2012Pedagogy',
    'К-22': 'Kit2018Reflexivity',
    'К-23': 'KMotivation2023',
    'К-24': 'KInnovation2023',
    'К-25': 'KGeneral2020',
    'Л-2': 'Lytvynova2024NAES',
    'Л-4': 'Lytvynova2025Emotional',
    'Л-8': 'Lytvynova2023Comparative',
    'Л-9': 'Lytvynova2023Health',
    'Л-12': 'Lytvynova2023Monograph',
    'Л-13': 'Lodatko2011Modeling',
    'М-2': 'Malytska2022EU',
    'М-3': 'Matviienko2023Modernization',
    'М-4': 'Medvedieva2024STEAM',
    'М-5': 'Matviienko2022Special',
    'М-8': 'Mintii2023Ref',
    'М-9': 'Mulesa2020Integration',
    'М-10': 'ModelProgram2022',
    'Н-1': 'Nosenko2025ITE',
    'Н-2': 'Nosenko2024Typology',
    'Н-3': 'Nikitina2023Telecom',
    'Н-6': 'Nosenko2023Blended',
    'О-1': 'Omelchuk2024Secondary',
    'О-2': 'Orlov2024Innovative',
    'О-5': 'Olizko2019Accessibility',
    'О-6': 'ProfIdentity2024',
    'П-3': 'Pinchuk2022AR',
    'П-8': 'Pometun2004Interactive',
    'П-11': 'Lytvynova2023Model',
    'П-13': 'PolozhennyaOsvProces2023',
    'Р-2': 'Radkevych2017Approaches',
    'Р-3': 'ReflexiveApproach2018',
    'Ре-2': 'Parong2021Cognitive',  # same as Re-2
    'Ре-3': 'Krokos2019Virtual',  # same as Re-3
    'С-2': 'Sukhikh2024Inclusive',
    'С-5': 'Sokoliuk2024VirtualLab',
    'С-6': 'Sabodashko2024Humanities',
    'С-7': 'Soroko2021Eastern',
    'С-13': 'Semerikov2023Presence',
    'С-14': 'Semerikov2021Ref',
    'С-17': 'Sarkisova2019Didactic',
    'С-18': 'Sysoieva2015Pedagogy',
    'С-19': 'Semerikov2022RefP165',
    'С-20': 'Spirin2020Ref',
    'С-21': 'Stefanenko2002Pedagogy',
    'С-22': 'Semerikov2023Motivational',
    'Т-2': 'TechGlossaryAR2020',
    'У-2': 'Udovychenko2024Wartime',
    'У-3': 'Uman2015Pedagogy',
    'Ф-2': 'Fitsula2006Pedagogics',
    'Ц-1': 'Tsymbaliuk2024Classification',
    'Ц-2': 'Tsvirkun2020Approaches',
    'Ч-1': 'Chubinska2025AI',
    'Ч-2': 'Chornous2025Presence',
    'Ч-3': 'Chyhryna2023Inclusive',
    'Ш-1': 'Shvardak2023Primary',
    'Ш-2': 'Shepiliev2020Digital',
    'Ш-3': 'Shepiliev2019Master',
    'Ш-4': 'Shevchuk2024Readiness',
    'Ш-5': 'Shtefan2018Didactic',
    'Ю-1': 'Yudenkova2023EdTech',
    'Я-2': 'Yaremchuk2024VisualAids',
    'І-3': 'Izbash2020OER',
}

# Competency codes - not citations, just text to keep
COMPETENCY_CODES = {'СК-03', 'СК-09', 'СК-13', 'СК-16'}

import re, sys, os

def resolve_code(code):
    """Look up a citation code and return the bibkey."""
    code = code.strip()
    # Handle page references like "К-5, с. 257"
    page = None
    if ', с.' in code or ',с.' in code:
        parts = re.split(r',\s*с\.?\s*', code)
        code = parts[0].strip()
        page = parts[1].strip() if len(parts) > 1 else None
    elif ', с ' in code:
        parts = code.split(', с ')
        code = parts[0].strip()
        page = parts[1].strip()

    bibkey = MAPPING.get(code)
    if not bibkey:
        return None, None
    return bibkey, page

def process_hl(match_text):
    """Process the content inside \hl{...} and return replacement text."""
    text = match_text

    # Pattern 1: Just a citation code like {[}Н-2{]}
    # or {[}Н-2{]},  or {[}Н-2{]}.
    m = re.match(r'^\{?\[?\}?\s*\{?\[?\}?([A-ZА-Яа-яa-z]+-\d+(?:,\s*с\.?\s*\d+(?:\{?\]?\}?)?)?)\{?\]?\}?[.,)]*$', text)
    if m:
        bibkey, page = resolve_code(m.group(1))
        if bibkey:
            if page:
                return f'\\cite[с.~{page}]{{{bibkey}}}'
            return f'\\cite{{{bibkey}}}'

    # Pattern 2: Text with embedded citation(s) like "...text... {[}CODE{]}. More text..."
    # Find all embedded citation codes
    codes_found = list(re.finditer(r'\{?\[?\}?\s*(?:\\textbf\{)?([A-ZА-Яа-яa-z]+-\d+(?:,\s*с\.?\s*\d+)?)\}?\s*\{?\]?\}?', text))
    if codes_found:
        result = text
        for cm in reversed(codes_found):
            code_text = cm.group(1)
            bibkey, page = resolve_code(code_text)
            if bibkey:
                cite_str = f'\\cite[с.~{page}]{{{bibkey}}}' if page else f'\\cite{{{bibkey}}}'
                # Replace the whole code pattern including brackets
                start = cm.start()
                end = cm.end()
                # Expand to include surrounding brackets
                while start > 0 and result[start-1] in '{[} ':
                    start -= 1
                while end < len(result) and result[end] in '{]} ':
                    end += 1
                result = result[:start] + cite_str + result[end:]
        # Clean up any remaining pandoc bracket artifacts
        result = result.replace('{[}', '[').replace('{]}', ']')
        return result

    # Pattern 3: Figure/appendix references or other text - just return without \hl
    return text

def process_file(filepath):
    """Process a single .tex file, replacing all \hl{...} markers."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Find and replace all \hl{...} occurrences
    # Need to handle nested braces carefully
    i = 0
    result = []
    while i < len(content):
        if content[i:i+4] == '\\hl{':
            # Find the matching closing brace
            start = i + 4
            depth = 1
            j = start
            while j < len(content) and depth > 0:
                if content[j] == '{':
                    depth += 1
                elif content[j] == '}':
                    depth -= 1
                j += 1
            # content[start:j-1] is inside \hl{...}
            inner = content[start:j-1]
            replacement = process_hl(inner)
            result.append(replacement)
            i = j
        else:
            result.append(content[i])
            i += 1

    new_content = ''.join(result)

    if new_content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        changes = original.count('\\hl{')
        print(f"  {filepath}: {changes} \\hl markers replaced")
    else:
        print(f"  {filepath}: no changes")

# Also handle bare citation codes like {[}С-5{]} (without \hl wrapper)
def process_bare_codes(filepath):
    """Replace bare {[}CODE{]} patterns that aren't inside \hl{}."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Pattern: {[}CODE{]} or [CODE] not inside \hl
    def replace_bare(m):
        code = m.group(1)
        bibkey, page = resolve_code(code)
        if bibkey:
            trailing = m.group(2) or ''
            if page:
                return f'\\cite[с.~{page}]{{{bibkey}}}' + trailing
            return f'\\cite{{{bibkey}}}' + trailing
        return m.group(0)  # leave unchanged if not in mapping

    # Match {[}CODE{]} or {[}CODE, с. N{]}
    content = re.sub(
        r'\{\[\}([A-ZА-Яа-яa-z]+-\d+(?:,\s*с\.?\s*\d+)?)\{\]\}([.,)]?)',
        replace_bare, content
    )

    if content != original:
        changes = len(re.findall(r'\\cite\{', content)) - len(re.findall(r'\\cite\{', original))
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  {filepath}: {changes} bare codes replaced")

if __name__ == '__main__':
    base = '/home/cc/claude_code/shepilev/thesis_final/chapters'
    files = []
    for d in ['chap1', 'chap2']:
        for fn in sorted(os.listdir(os.path.join(base, d))):
            if fn.endswith('.tex'):
                files.append(os.path.join(base, d, fn))

    print("=== Processing \\hl{} markers ===")
    for f in files:
        process_file(f)

    print("\n=== Processing bare {[}CODE{]} markers ===")
    for f in files:
        process_bare_codes(f)

    print("\n=== Verification ===")
    import subprocess
    r = subprocess.run(['grep', '-rc', r'\\hl{', base + '/chap1', base + '/chap2'],
                      capture_output=True, text=True)
    print("Remaining \\hl{} markers:", r.stdout.strip() or "0")
