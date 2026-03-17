#!/usr/bin/env python3
"""
Run complete thesis analysis with English-only output and multi-format figures.
Generates PDF, PNG, and TikZ for all visualizations.
"""

import sys
import json
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from thesis_analysis.data_processing.loader import DataLoader
from thesis_analysis.analysis.statistical.descriptive import DescriptiveAnalyzer
from thesis_analysis.analysis.network.curriculum_graph import CurriculumGraphAnalyzer
from thesis_analysis.analysis.llm.gap_analysis import AIGapAnalyzer
from thesis_analysis.visualization.plots import ThesisPlotter


def main():
    print("=" * 60)
    print("THESIS ANALYSIS - ENGLISH OUTPUT WITH MULTI-FORMAT FIGURES")
    print("=" * 60)

    # Paths
    data_dir = Path("data")
    output_dir = Path("thesis_output")
    output_dir.mkdir(exist_ok=True)
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(exist_ok=True)

    # 1. Load data
    print("\n[1/5] Loading data...")
    loader = DataLoader(data_dir)
    data = loader.load_all()
    df_programs = data.df_programs
    df_courses = data.df_courses
    print(f"  Loaded {len(df_programs)} programs, {len(df_courses)} courses")

    # 2. Statistical analysis
    print("\n[2/5] Running statistical analysis...")
    stat_analyzer = DescriptiveAnalyzer(df_programs, df_courses)
    stat_report = stat_analyzer.generate_report()

    # Save report
    with open(reports_dir / "statistical_analysis.txt", "w", encoding="utf-8") as f:
        f.write(stat_report)
    print(f"  Saved: {reports_dir / 'statistical_analysis.txt'}")

    # 3. Gap analysis
    print("\n[3/5] Running AI/digital skills gap analysis...")
    courses_list = df_courses["name"].dropna().tolist()

    gap_analyzer = AIGapAnalyzer()
    gap_result = gap_analyzer.analyze(courses_list)
    gap_report = gap_analyzer.generate_report(gap_result)

    # Save report
    with open(reports_dir / "gap_analysis.txt", "w", encoding="utf-8") as f:
        f.write(gap_report)
    print(f"  Saved: {reports_dir / 'gap_analysis.txt'}")

    # 4. Network analysis
    print("\n[4/5] Running network analysis...")
    network_analyzer = CurriculumGraphAnalyzer(min_edge_weight=2)
    G = network_analyzer.build_course_cooccurrence_graph(df_courses)
    network_result = network_analyzer.analyze()
    network_report = network_analyzer.generate_report(network_result)

    # Save report
    with open(reports_dir / "network_analysis.txt", "w", encoding="utf-8") as f:
        f.write(network_report)
    print(f"  Saved: {reports_dir / 'network_analysis.txt'}")

    # 5. Generate figures in all formats
    print("\n[5/5] Generating figures (PNG, PDF, TikZ)...")
    plotter = ThesisPlotter(output_dir=figures_dir)

    # Convert results to dict format for plotter
    gap_dict = {
        "coverage_scores": gap_result.coverage_scores,
        "skill_details": [
            {"skill": d.skill, "coverage_score": d.coverage_score}
            for d in gap_result.skill_details
        ]
    }

    network_dict = {
        "network_metrics": {
            "num_nodes": network_result.network_metrics.num_nodes,
            "num_edges": network_result.network_metrics.num_edges,
            "density": network_result.network_metrics.density,
            "avg_degree": network_result.network_metrics.avg_degree,
            "avg_clustering": network_result.network_metrics.avg_clustering,
            "num_components": network_result.network_metrics.num_components,
        },
        "communities": [
            {"community_id": c.community_id, "size": c.size, "label": c.label}
            for c in network_result.communities
        ],
        "node_metrics": [
            {"node": nm.node, "degree": nm.degree, "betweenness_centrality": nm.betweenness_centrality}
            for nm in network_result.node_metrics
        ]
    }

    all_paths = plotter.generate_all_plots(
        df_programs=df_programs,
        df_courses=df_courses,
        gap_result=gap_dict,
        network_result=network_dict,
    )

    print(f"\n  Generated figures:")
    for name, paths in all_paths.items():
        print(f"    - {name}:")
        for fmt, path in paths.items():
            print(f"        {fmt}: {path}")

    # Summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE - ALL OUTPUT IN ENGLISH")
    print("=" * 60)
    print(f"\nReports saved to: {reports_dir}")
    print(f"Figures saved to: {figures_dir}")
    print(f"  - PNG: {figures_dir / 'png'}")
    print(f"  - PDF: {figures_dir / 'pdf'}")
    print(f"  - TikZ: {figures_dir / 'tikz'}")


if __name__ == "__main__":
    main()
