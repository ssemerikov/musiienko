"""
Thesis Analysis System - Main CLI Orchestrator

Coordinates data loading, analysis, visualization, and output generation
for Ukrainian design education curriculum analysis.
"""

import json
import sys
from pathlib import Path
from typing import Optional, List
from dataclasses import asdict

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import settings
from .data_processing import DataLoader
from .analysis.statistical import DescriptiveAnalyzer
from .analysis.nlp import TopicModeler, EmbeddingGenerator
from .analysis.network import CurriculumGraphAnalyzer
from .analysis.llm import HFAnalyzer, AIGapAnalyzer
from .synthesis import CurriculumDesigner
from .visualization import ThesisPlotter
from .latex_output import ThesisGenerator

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Thesis Analysis System for Ukrainian Design Programs."""
    pass


@cli.command()
@click.option("--levels", "-l", multiple=True, default=["bachelor"],
              help="Degree levels to analyze (bachelor, master, phd)")
@click.option("--max-cases", "-n", type=int, default=None,
              help="Maximum number of cases to load")
@click.option("--output", "-o", type=Path, default=None,
              help="Output directory for results")
def analyze(levels: tuple, max_cases: Optional[int], output: Optional[Path]):
    """Run complete analysis pipeline."""
    settings.ensure_dirs()
    output_dir = output or settings.analysis_output_dir

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load data
        task = progress.add_task("Loading data...", total=None)
        loader = DataLoader()
        data = loader.load_all(
            levels=list(levels),
            max_cases=max_cases,
            include_text=True,
        )
        progress.update(task, completed=True)
        console.print(f"[green]✓[/green] Loaded {len(data.cases)} cases")

        # Statistical analysis
        task = progress.add_task("Running statistical analysis...", total=None)
        stat_analyzer = DescriptiveAnalyzer(data.df_programs, data.df_courses)
        prog_stats = stat_analyzer.analyze_programs()
        course_stats = stat_analyzer.analyze_courses()
        stat_report = stat_analyzer.generate_report()
        progress.update(task, completed=True)
        console.print("[green]✓[/green] Statistical analysis complete")

        # Gap analysis
        task = progress.add_task("Running gap analysis...", total=None)
        gap_analyzer = AIGapAnalyzer()
        all_courses = data.df_courses["name"].tolist()
        gap_result = gap_analyzer.analyze(all_courses)
        gap_report = gap_analyzer.generate_report(gap_result)
        progress.update(task, completed=True)
        console.print("[green]✓[/green] Gap analysis complete")

        # Network analysis
        task = progress.add_task("Building curriculum network...", total=None)
        network_analyzer = CurriculumGraphAnalyzer(min_edge_weight=3)
        network_analyzer.build_course_cooccurrence_graph(data.df_courses)
        network_result = network_analyzer.analyze()
        network_report = network_analyzer.generate_report(network_result)
        progress.update(task, completed=True)
        console.print("[green]✓[/green] Network analysis complete")

        # Generate visualizations
        task = progress.add_task("Generating visualizations...", total=None)
        plotter = ThesisPlotter(output_dir / "figures")

        gap_dict = {
            "coverage_scores": gap_result.coverage_scores,
            "skill_details": [
                {"skill": s.skill, "coverage_score": s.coverage_score}
                for s in gap_result.skill_details
            ],
        }
        network_dict = {
            "network_metrics": asdict(network_result.network_metrics),
            "communities": [
                {"size": c.size, "label": c.label}
                for c in network_result.communities
            ],
            "node_metrics": [
                {"node": n.node, "degree": n.degree, "betweenness_centrality": n.betweenness_centrality}
                for n in network_result.node_metrics[:20]
            ],
        }

        plotter.generate_all_plots(
            data.df_programs,
            data.df_courses,
            gap_result=gap_dict,
            network_result=network_dict,
        )
        progress.update(task, completed=True)
        console.print("[green]✓[/green] Visualizations generated")

        # Design curriculum proposal
        task = progress.add_task("Generating curriculum proposal...", total=None)
        designer = CurriculumDesigner()
        proposal = designer.design_bachelor_curriculum(
            gap_analysis=gap_result.coverage_scores,
            common_courses=course_stats.most_common_courses[:20],
        )
        designer.export_to_json(proposal, output_dir / "curriculum_proposal.json")
        progress.update(task, completed=True)
        console.print("[green]✓[/green] Curriculum proposal generated")

        # Generate LaTeX
        task = progress.add_task("Generating LaTeX thesis...", total=None)
        latex_gen = ThesisGenerator(output_dir / "latex")
        stats_dict = {
            "total_programs": prog_stats.total_programs,
            "by_level": prog_stats.by_level,
            "avg_courses": prog_stats.courses_per_program.mean,
            "std_courses": prog_stats.courses_per_program.std,
            "syllabus_coverage": prog_stats.syllabus_coverage,
            "total_pdfs": 2566,
            "total_chars": 77_800_000,
        }

        # Load curriculum proposal as dict
        with open(output_dir / "curriculum_proposal.json", "r", encoding="utf-8") as f:
            proposal_dict = json.load(f)

        latex_gen.generate_all(
            stats=stats_dict,
            gap_report=gap_report,
            descriptive_report=stat_report,
            curriculum_proposal=proposal_dict,
        )
        progress.update(task, completed=True)
        console.print("[green]✓[/green] LaTeX thesis generated")

    # Save reports
    (output_dir / "reports").mkdir(exist_ok=True)
    with open(output_dir / "reports" / "statistical_analysis.txt", "w", encoding="utf-8") as f:
        f.write(stat_report)
    with open(output_dir / "reports" / "gap_analysis.txt", "w", encoding="utf-8") as f:
        f.write(gap_report)
    with open(output_dir / "reports" / "network_analysis.txt", "w", encoding="utf-8") as f:
        f.write(network_report)

    # Summary
    console.print("\n[bold green]Analysis Complete![/bold green]")
    console.print(f"\nResults saved to: {output_dir}")

    summary = Table(title="Analysis Summary")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="green")

    summary.add_row("Programs analyzed", str(prog_stats.total_programs))
    summary.add_row("Total courses", str(course_stats.total_courses))
    summary.add_row("Unique courses", str(course_stats.unique_courses))
    summary.add_row("AI coverage", f"{gap_result.overall_ai_coverage:.1%}")
    summary.add_row("Digital tools coverage", f"{gap_result.overall_digital_coverage:.1%}")
    summary.add_row("Network nodes", str(network_result.network_metrics.num_nodes))
    summary.add_row("Network edges", str(network_result.network_metrics.num_edges))
    summary.add_row("Communities detected", str(len(network_result.communities)))

    console.print(summary)


@cli.command()
@click.option("--levels", "-l", multiple=True, default=["bachelor"])
@click.option("--max-cases", "-n", type=int, default=None)
def load(levels: tuple, max_cases: Optional[int]):
    """Load and display data summary."""
    loader = DataLoader()
    data = loader.load_all(levels=list(levels), max_cases=max_cases, include_text=False)

    console.print(f"\n[bold]Loaded {len(data.cases)} cases[/bold]")
    console.print(f"Programs DataFrame: {data.df_programs.shape}")
    console.print(f"Courses DataFrame: {data.df_courses.shape}")
    console.print(f"Competencies DataFrame: {data.df_competencies.shape}")

    # Show level distribution
    table = Table(title="Programs by Level")
    table.add_column("Level")
    table.add_column("Count")

    for level, count in data.df_programs["degree_level"].value_counts().items():
        table.add_row(level, str(count))

    console.print(table)


@cli.command()
@click.option("--levels", "-l", multiple=True, default=["bachelor"])
def stats(levels: tuple):
    """Run statistical analysis only."""
    loader = DataLoader()
    data = loader.load_all(levels=list(levels), include_text=False)

    analyzer = DescriptiveAnalyzer(data.df_programs, data.df_courses)
    report = analyzer.generate_report()

    console.print(report)


@cli.command()
@click.option("--levels", "-l", multiple=True, default=["bachelor"])
def gaps(levels: tuple):
    """Run gap analysis only."""
    loader = DataLoader()
    data = loader.load_all(levels=list(levels), include_text=False)

    analyzer = AIGapAnalyzer()
    courses = data.df_courses["name"].tolist()
    result = analyzer.analyze(courses)
    report = analyzer.generate_report(result)

    console.print(report)


@cli.command()
@click.option("--levels", "-l", multiple=True, default=["bachelor"])
@click.option("--min-documents", "-m", type=int, default=10)
def topics(levels: tuple, min_documents: int):
    """Run topic modeling on syllabi."""
    loader = DataLoader()
    data = loader.load_all(levels=list(levels), include_text=True)

    # Collect syllabus texts
    texts = []
    for case in data.cases:
        for course in case.courses:
            if course.syllabus_text:
                texts.append(course.syllabus_text[:5000])

    if len(texts) < min_documents:
        console.print(f"[red]Not enough documents ({len(texts)}). Need at least {min_documents}.[/red]")
        return

    console.print(f"Running topic modeling on {len(texts)} documents...")

    modeler = TopicModeler(min_topic_size=min_documents)
    result = modeler.fit(texts)

    console.print(f"\n[bold]Discovered {len(result.topics)} topics[/bold]\n")

    for topic in result.topics[:10]:
        console.print(f"[cyan]{topic.name}[/cyan]")
        console.print(f"  Documents: {topic.document_count}")
        console.print(f"  Top words: {', '.join(w for w, _ in topic.top_words[:5])}")
        console.print()


@cli.command()
@click.option("--output", "-o", type=Path, default=None)
def latex(output: Optional[Path]):
    """Generate LaTeX thesis structure."""
    output_dir = output or settings.latex_dir

    generator = ThesisGenerator(output_dir)
    generator.generate_thesis_structure()
    generator.generate_titlepage()
    generator.generate_methodology_chapter()
    generator.generate_stub_chapters()
    generator.generate_bibliography()

    console.print(f"[green]✓[/green] LaTeX structure generated in {output_dir}")


@cli.command()
def info():
    """Show configuration and paths."""
    console.print("\n[bold]Thesis Analysis System Configuration[/bold]\n")

    table = Table()
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    table.add_row("Project root", str(settings.project_root))
    table.add_row("Data directory", str(settings.data_dir))
    table.add_row("Raw data", str(settings.raw_data_dir))
    table.add_row("Output directory", str(settings.analysis_output_dir))
    table.add_row("LaTeX output", str(settings.latex_dir))
    table.add_row("Embedding model", settings.embedding_model)
    table.add_row("Text gen model", settings.text_gen_model)
    table.add_row("HF token", f"{settings.hf_token[:10]}..." if settings.hf_token else "Not set")

    console.print(table)

    # Check data availability
    console.print("\n[bold]Data Availability[/bold]\n")

    raw_files = list(settings.raw_data_dir.glob("case_*.json"))
    console.print(f"Case JSON files: {len(raw_files)}")

    if settings.level_mapping_path.exists():
        with open(settings.level_mapping_path) as f:
            mapping = json.load(f)
        console.print(f"Level mapping: ✓")
        console.print(f"  Bachelor: {len(mapping.get('bachelor', []))}")
        console.print(f"  Master: {len(mapping.get('master', []))}")
        console.print(f"  PhD: {len(mapping.get('phd', []))}")
    else:
        console.print("Level mapping: [red]✗[/red]")


def main():
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
