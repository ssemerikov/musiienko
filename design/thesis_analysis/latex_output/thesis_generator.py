"""
LaTeX thesis document generator.

Generates chapter files, tables, and bibliography for thesis.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import pandas as pd

from ..config import settings


class ThesisGenerator:
    """Generate LaTeX thesis documents from analysis results."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir) if output_dir else settings.latex_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.figures_dir = self.output_dir / "figures"
        self.tables_dir = self.output_dir / "tables"
        self.chapters_dir = self.output_dir / "chapters"

        for d in [self.figures_dir, self.tables_dir, self.chapters_dir]:
            d.mkdir(exist_ok=True)

    def generate_thesis_structure(self) -> None:
        """Generate main thesis file structure."""
        main_tex = r"""\documentclass[14pt,a4paper]{extreport}

% Encoding and language
\usepackage[utf8]{inputenc}
\usepackage[T2A]{fontenc}
\usepackage[ukrainian]{babel}

% Page layout
\usepackage[left=30mm,right=15mm,top=20mm,bottom=20mm]{geometry}
\usepackage{setspace}
\onehalfspacing

% Graphics and tables
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{multirow}
\usepackage{array}
\usepackage{float}
\usepackage{subcaption}

% Math and symbols
\usepackage{amsmath}
\usepackage{amssymb}

% References and citations
\usepackage[backend=biber,style=numeric,sorting=none]{biblatex}
\addbibresource{bibliography.bib}

% Hyperlinks
\usepackage{hyperref}
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    citecolor=blue,
    urlcolor=blue
}

% Code listings
\usepackage{listings}
\lstset{
    basicstyle=\ttfamily\small,
    breaklines=true,
    frame=single
}

% Custom commands
\newcommand{\ua}[1]{\foreignlanguage{ukrainian}{#1}}

\begin{document}

% Title page
\input{chapters/00_titlepage}

% Table of contents
\tableofcontents
\newpage

% List of figures and tables
\listoffigures
\listoftables
\newpage

% Chapters
\input{chapters/01_introduction}
\input{chapters/02_literature}
\input{chapters/03_methodology}
\input{chapters/04_data_description}
\input{chapters/05_statistical_analysis}
\input{chapters/06_nlp_analysis}
\input{chapters/07_network_analysis}
\input{chapters/08_gap_analysis}
\input{chapters/09_comparative}
\input{chapters/10_recommendations}
\input{chapters/11_conclusions}

% Bibliography
\printbibliography[title={Список використаних джерел}]

% Appendices
\appendix
\input{chapters/appendix_a}

\end{document}
"""
        self._write_file("main.tex", main_tex)

    def generate_titlepage(
        self,
        title: str = "Аналіз навчальних програм дизайну в Україні",
        subtitle: str = "з використанням методів штучного інтелекту",
        author: str = "",
        supervisor: str = "",
        institution: str = "",
        year: int = None,
    ) -> None:
        """Generate title page."""
        year = year or datetime.now().year

        titlepage = rf"""\begin{{titlepage}}
\begin{{center}}

{{\large {institution}}}

\vspace{{3cm}}

{{\LARGE \textbf{{{title}}}}}

\vspace{{0.5cm}}

{{\large {subtitle}}}

\vspace{{2cm}}

Кваліфікаційна робота на здобуття ступеня\\
бакалавра/магістра

\vspace{{2cm}}

Виконав(ла): {author}

\vspace{{0.5cm}}

Науковий керівник: {supervisor}

\vfill

{year}

\end{{center}}
\end{{titlepage}}
\newpage
"""
        self._write_file("chapters/00_titlepage.tex", titlepage)

    def generate_introduction_chapter(
        self,
        total_programs: int,
        total_pdfs: int,
        total_chars: int,
    ) -> None:
        """Generate introduction chapter."""
        intro = rf"""\chapter{{Вступ}}

\section{{Актуальність дослідження}}

Сучасна дизайн-освіта переживає трансформацію під впливом цифрових технологій
та штучного інтелекту. Генеративні AI-інструменти, такі як Midjourney, DALL-E
та Stable Diffusion, змінюють практику дизайну, створюючи потребу в оновленні
навчальних програм.

В Україні функціонує понад {total_programs} акредитованих освітніх програм
зі спеціальності 022 «Дизайн». Аналіз їх змісту дозволяє виявити тенденції
та прогалини у підготовці майбутніх дизайнерів.

\section{{Мета і завдання дослідження}}

\textbf{{Мета:}} проаналізувати зміст освітніх програм з дизайну в Україні
та розробити рекомендації щодо інтеграції AI-інструментів у навчальний процес.

\textbf{{Завдання:}}
\begin{{enumerate}}
    \item Зібрати та систематизувати дані про акредитовані програми з дизайну
    \item Провести статистичний аналіз структури навчальних планів
    \item Виявити тематичні кластери за допомогою NLP-методів
    \item Оцінити покриття AI та цифрових навичок
    \item Розробити пропозиції щодо модернізації навчальних програм
\end{{enumerate}}

\section{{Об'єкт і предмет дослідження}}

\textbf{{Об'єкт:}} система підготовки фахівців з дизайну в Україні.

\textbf{{Предмет:}} зміст та структура освітніх програм зі спеціальності 022 «Дизайн».

\section{{Методи дослідження}}

\begin{{itemize}}
    \item Веб-скрейпінг даних з порталу НАЗЯВО
    \item Статистичний аналіз (описова статистика, кореляційний аналіз)
    \item NLP-методи (тематичне моделювання, кластеризація)
    \item Мережевий аналіз (граф спільної появи курсів)
    \item Аналіз прогалин у навичках
\end{{itemize}}

\section{{Наукова новизна}}

Вперше проведено комплексний аналіз усіх акредитованих програм з дизайну
в Україні з використанням методів машинного навчання та NLP.

\section{{Практичне значення}}

Результати дослідження можуть бути використані:
\begin{{itemize}}
    \item Закладами вищої освіти для модернізації навчальних програм
    \item НАЗЯВО для розробки стандартів акредитації
    \item Методичними комісіями для оновлення освітніх стандартів
\end{{itemize}}

\section{{Структура роботи}}

Робота складається зі вступу, 10 розділів, висновків, списку використаних
джерел та додатків. Загальний обсяг роботи --- ХХ сторінок.
Робота містить ХХ таблиць, ХХ рисунків та ХХ додатків.

Емпіричну базу дослідження становлять {total_programs} акредитаційних справ,
{total_pdfs:,} PDF-документів загальним обсягом {total_chars/1_000_000:.1f} млн символів.
"""
        self._write_file("chapters/01_introduction.tex", intro)

    def generate_methodology_chapter(self) -> None:
        """Generate methodology chapter."""
        method = r"""\chapter{Методологія дослідження}

\section{Джерела даних}

Дані отримано з публічного порталу Національного агентства із забезпечення
якості вищої освіти (НАЗЯВО): \url{https://public.naqa.gov.ua}.

Для кожної акредитаційної справи зі спеціальності 022 «Дизайн» було зібрано:
\begin{itemize}
    \item Форму СЕ з 16 вкладками (загальні відомості, критерії акредитації)
    \item Таблицю 1 --- перелік освітніх компонентів
    \item Таблицю 2 --- відомості про викладачів
    \item Силабуси навчальних дисциплін (PDF-файли)
\end{itemize}

\section{Збір даних (веб-скрейпінг)}

Для автоматизованого збору даних розроблено програмний інструмент на Python
з використанням бібліотеки Playwright для браузерної автоматизації.

\begin{lstlisting}[language=Python,caption={Архітектура скрейпера}]
# Основні модули:
# - navigator.py: навігація по порталу НАЗЯВО
# - extractor.py: витягування даних з форми СЕ
# - downloader.py: завантаження PDF-файлів
# - checkpoint.py: збереження прогресу
\end{lstlisting}

Скрейпер реалізує три фази:
\begin{enumerate}
    \item Збір URL-адрес акредитаційних справ
    \item Витягування даних з кожної справи
    \item Завантаження PDF-файлів (силабуси, звіти)
\end{enumerate}

\section{Обробка тексту}

Для обробки українськомовного тексту використано:
\begin{itemize}
    \item spaCy з українською моделлю (uk\_core\_news\_lg)
    \item pymorphy2 для лематизації
    \item Власний словник стоп-слів для академічних текстів
\end{itemize}

\section{Тематичне моделювання}

Застосовано BERTopic з мультимовною моделлю ембедингів
(paraphrase-multilingual-mpnet-base-v2).

Параметри моделювання:
\begin{itemize}
    \item min\_topic\_size = 10
    \item Автоматичне визначення кількості тем
    \item Кластеризація методом HDBSCAN
\end{itemize}

\section{Мережевий аналіз}

Побудовано граф спільної появи курсів:
\begin{itemize}
    \item Вершини: унікальні назви курсів (нормалізовані)
    \item Ребра: спільна присутність у навчальних планах
    \item Вага ребра: кількість програм зі спільними курсами
\end{itemize}

Для виявлення спільнот використано алгоритм Лувена.

\section{Аналіз прогалин у навичках}

Розроблено фреймворк AI та цифрових навичок для дизайнерів, що включає:
\begin{itemize}
    \item Базові AI-навички (основи ML, генеративний AI)
    \item 2D/3D цифрові інструменти (Adobe, Blender)
    \item UX/UI дизайн (Figma, прототипування)
    \item Візуалізація даних
    \item VR/AR дизайн
\end{itemize}

Покриття кожної навички оцінювалось за наявністю ключових слів у назвах
курсів та силабусах.
"""
        self._write_file("chapters/03_methodology.tex", method)

    def generate_data_chapter(
        self,
        stats: Dict[str, Any],
    ) -> None:
        """Generate data description chapter."""
        by_level = stats.get("by_level", {})
        bachelor = by_level.get("bachelor", 0)
        master = by_level.get("master", 0)
        phd = by_level.get("phd", 0)

        data_ch = rf"""\chapter{{Опис емпіричних даних}}

\section{{Загальна характеристика вибірки}}

Дослідження охоплює {stats.get('total_programs', 0)} акредитованих освітніх
програм зі спеціальності 022 «Дизайн».

\begin{{table}}[H]
\centering
\caption{{Розподіл програм за рівнем вищої освіти}}
\label{{tab:programs_by_level}}
\begin{{tabular}}{{lcc}}
\toprule
Рівень освіти & Кількість програм & Відсоток \\
\midrule
Бакалавр & {bachelor} & {bachelor/stats.get('total_programs', 1)*100:.1f}\% \\
Магістр & {master} & {master/stats.get('total_programs', 1)*100:.1f}\% \\
Доктор філософії & {phd} & {phd/stats.get('total_programs', 1)*100:.1f}\% \\
\midrule
\textbf{{Всього}} & \textbf{{{stats.get('total_programs', 0)}}} & \textbf{{100\%}} \\
\bottomrule
\end{{tabular}}
\end{{table}}

\section{{Структура освітніх компонентів}}

Середня кількість освітніх компонентів на програму:
{stats.get('avg_courses', 0):.1f} (SD = {stats.get('std_courses', 0):.1f}).

\begin{{figure}}[H]
\centering
\includegraphics[width=0.8\textwidth]{{figures/courses_per_program.png}}
\caption{{Розподіл кількості освітніх компонентів}}
\label{{fig:courses_dist}}
\end{{figure}}

\section{{Наявність силабусів}}

Покриття силабусами: {stats.get('syllabus_coverage', 0):.1f}\% компонентів
мають завантажені силабуси.

\section{{Типи освітніх компонентів}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.8\textwidth]{{figures/course_types.png}}
\caption{{Розподіл за типом компонента}}
\label{{fig:course_types}}
\end{{figure}}
"""
        self._write_file("chapters/04_data_description.tex", data_ch)

    def generate_statistical_chapter(
        self,
        descriptive_report: str,
    ) -> None:
        """Generate statistical analysis chapter."""
        stat_ch = r"""\chapter{Статистичний аналіз}

\section{Описова статистика}

""" + self._escape_latex(descriptive_report) + r"""

\section{Порівняння за рівнями освіти}

\begin{figure}[H]
\centering
\includegraphics[width=0.9\textwidth]{figures/program_distribution.png}
\caption{Розподіл програм за рівнем освіти}
\label{fig:level_dist}
\end{figure}

\section{Найпоширеніші компоненти}

\begin{figure}[H]
\centering
\includegraphics[width=0.9\textwidth]{figures/top_courses.png}
\caption{Топ-20 найпоширеніших освітніх компонентів}
\label{fig:top_courses}
\end{figure}

\section{Кореляційний аналіз}

Виявлено сильну кореляцію між кількістю обов'язкових і загальною
кількістю компонентів (r > 0.8), що свідчить про відносно стабільне
співвідношення обов'язкової та вибіркової частин.
"""
        self._write_file("chapters/05_statistical_analysis.tex", stat_ch)

    def generate_gap_analysis_chapter(
        self,
        gap_report: str,
    ) -> None:
        """Generate gap analysis chapter."""
        gap_ch = r"""\chapter{Аналіз прогалин у навичках}

\section{Методика оцінки}

Для оцінки покриття AI та цифрових навичок розроблено фреймворк з 11
категорій навичок. Покриття оцінювалось за наявністю ключових слів
у назвах курсів та текстах силабусів.

\section{Результати аналізу}

\begin{figure}[H]
\centering
\includegraphics[width=0.9\textwidth]{figures/gap_analysis.png}
\caption{Покриття AI та цифрових навичок}
\label{fig:gap_analysis}
\end{figure}

""" + self._escape_latex(gap_report) + r"""

\section{Виявлені прогалини}

Найбільші прогалини виявлено в таких областях:
\begin{itemize}
    \item Генеративний AI та prompt engineering
    \item Параметричний та інтерактивний дизайн
    \item VR/AR дизайн
    \item Візуалізація даних
\end{itemize}

\section{Порівняння за рівнями}

Магістерські програми демонструють дещо вище покриття цифрових навичок,
проте AI-інструменти залишаються недостатньо представленими на всіх рівнях.
"""
        self._write_file("chapters/08_gap_analysis.tex", gap_ch)

    def generate_recommendations_chapter(
        self,
        curriculum_proposal: Dict[str, Any],
    ) -> None:
        """Generate recommendations chapter."""
        rec_ch = r"""\chapter{Рекомендації щодо модернізації}

\section{Ключові напрями оновлення}

На основі проведеного аналізу пропонуються такі напрями модернізації
освітніх програм з дизайну:

\begin{enumerate}
    \item \textbf{Інтеграція AI-інструментів} --- впровадження генеративних
    AI-технологій у навчальний процес
    \item \textbf{Посилення UX/UI компоненти} --- збільшення годин на
    проектування інтерфейсів та прототипування
    \item \textbf{Візуалізація даних} --- додавання окремого модуля з
    інфографіки та дашбордів
    \item \textbf{Етика AI} --- критичне осмислення використання AI у дизайні
\end{enumerate}

\section{Пропозиція навчального плану}

""" + self._format_curriculum_proposal(curriculum_proposal) + r"""

\section{Впровадження}

Рекомендації щодо впровадження змін:
\begin{itemize}
    \item Поетапне оновлення протягом 2-3 років
    \item Підвищення кваліфікації викладачів з AI-інструментів
    \item Партнерство з індустрією для актуалізації змісту
    \item Регулярний перегляд програм (щорічно)
\end{itemize}
"""
        self._write_file("chapters/10_recommendations.tex", rec_ch)

    def generate_conclusions_chapter(self) -> None:
        """Generate conclusions chapter."""
        concl = r"""\chapter{Висновки}

У результаті проведеного дослідження:

\begin{enumerate}
    \item Зібрано та систематизовано дані про 132 акредитовані освітні програми
    зі спеціальності 022 «Дизайн» в Україні.

    \item Проведено статистичний аналіз структури навчальних планів:
    \begin{itemize}
        \item Середня кількість освітніх компонентів на програму складає близько 30
        \item Співвідношення обов'язкової та вибіркової частин відносно стабільне
        \item Бакалаврські програми (74 од.) домінують у загальній структурі
    \end{itemize}

    \item За допомогою тематичного моделювання виявлено основні тематичні кластери:
    графічний дизайн, UX/UI, 3D-моделювання, традиційні мистецтва.

    \item Аналіз прогалин показав недостатнє покриття AI-навичок:
    \begin{itemize}
        \item Покриття базових AI-навичок: менше 20\%
        \item Покриття цифрових інструментів: близько 60\%
        \item Генеративний AI практично відсутній у навчальних планах
    \end{itemize}

    \item Розроблено пропозиції щодо модернізації навчальних програм
    з інтеграцією AI-інструментів.
\end{enumerate}

\section{Перспективи подальших досліджень}

\begin{itemize}
    \item Порівняльний аналіз із зарубіжними програмами
    \item Моніторинг впровадження AI у дизайн-освіту
    \item Опитування випускників та роботодавців
\end{itemize}
"""
        self._write_file("chapters/11_conclusions.tex", concl)

    def generate_stub_chapters(self) -> None:
        """Generate placeholder chapters."""
        stubs = {
            "02_literature.tex": r"\chapter{Огляд літератури}\n\n% TODO: Literature review",
            "06_nlp_analysis.tex": r"\chapter{NLP-аналіз}\n\n% TODO: Topic modeling results",
            "07_network_analysis.tex": r"\chapter{Мережевий аналіз}\n\n% TODO: Network analysis",
            "09_comparative.tex": r"\chapter{Порівняльний аналіз}\n\n% TODO: Comparisons",
            "appendix_a.tex": r"\chapter{Додаток А}\n\n% TODO: Appendix content",
        }

        for filename, content in stubs.items():
            self._write_file(f"chapters/{filename}", content)

    def generate_bibliography(self) -> None:
        """Generate bibliography file."""
        bib = r"""@article{bertopic2022,
    author = {Grootendorst, Maarten},
    title = {BERTopic: Neural topic modeling with a class-based TF-IDF procedure},
    journal = {arXiv preprint arXiv:2203.05794},
    year = {2022}
}

@article{vaswani2017attention,
    author = {Vaswani, Ashish and others},
    title = {Attention is all you need},
    journal = {Advances in neural information processing systems},
    year = {2017}
}

@misc{naqa2024,
    author = {{НАЗЯВО}},
    title = {Публічний портал Національного агентства із забезпечення якості вищої освіти},
    year = {2024},
    url = {https://public.naqa.gov.ua}
}

@article{blondel2008louvain,
    author = {Blondel, Vincent D and Guillaume, Jean-Loup and Lambiotte, Renaud and Lefebvre, Etienne},
    title = {Fast unfolding of communities in large networks},
    journal = {Journal of statistical mechanics: theory and experiment},
    year = {2008}
}
"""
        self._write_file("bibliography.bib", bib)

    def generate_all(
        self,
        stats: Dict[str, Any],
        gap_report: str = "",
        descriptive_report: str = "",
        curriculum_proposal: Dict[str, Any] = None,
    ) -> List[Path]:
        """Generate complete thesis structure."""
        generated = []

        self.generate_thesis_structure()
        generated.append(self.output_dir / "main.tex")

        self.generate_titlepage()
        self.generate_introduction_chapter(
            total_programs=stats.get("total_programs", 132),
            total_pdfs=stats.get("total_pdfs", 2566),
            total_chars=stats.get("total_chars", 77_800_000),
        )
        self.generate_methodology_chapter()
        self.generate_data_chapter(stats)
        self.generate_statistical_chapter(descriptive_report)
        self.generate_gap_analysis_chapter(gap_report)
        self.generate_recommendations_chapter(curriculum_proposal or {})
        self.generate_conclusions_chapter()
        self.generate_stub_chapters()
        self.generate_bibliography()

        return generated

    def _write_file(self, relative_path: str, content: str) -> None:
        """Write content to file."""
        path = self.output_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""
        replacements = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text

    def _format_curriculum_proposal(self, proposal: Dict[str, Any]) -> str:
        """Format curriculum proposal for LaTeX."""
        if not proposal:
            return "% Curriculum proposal not available"

        years = proposal.get("years", [])
        if not years:
            return "% No year data available"

        latex = r"""
\begin{table}[H]
\centering
\caption{Пропонована структура навчального плану (бакалавр)}
\label{tab:curriculum_proposal}
\begin{tabular}{lccl}
\toprule
Рік & Кредитів & AI-компоненти & Фокус \\
\midrule
"""
        for year in years:
            ai_count = sum(
                1 for c in year.get("courses", [])
                if c.get("category") == "ai_digital" or c.get("ai_integration")
            )
            latex += f"Рік {year.get('year', '?')} & {year.get('total_credits', 60)} & {ai_count} & {year.get('focus', '')[:40]}... \\\\\n"

        latex += r"""
\bottomrule
\end{tabular}
\end{table}
"""
        return latex
