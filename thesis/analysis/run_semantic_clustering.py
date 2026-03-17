#!/usr/bin/env python3
"""
Semantic Similarity Clustering of 122 NAQA Design Programs.

Computes inter-program similarity based on course portfolios using
multilingual sentence embeddings, then clusters and visualizes.
"""

import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams["font.family"] = "DejaVu Sans"
rcParams["font.size"] = 11

# Add design package to path
DESIGN_DIR = Path(__file__).resolve().parent.parent.parent / "design"
sys.path.insert(0, str(DESIGN_DIR))

from thesis_analysis.config import settings
from thesis_analysis.data_processing.loader import DataLoader
from thesis_analysis.analysis.nlp.embeddings import EmbeddingGenerator

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def load_program_courses():
    """Load programs and build per-program course portfolios."""
    print("Loading NAQA data...")
    loader = DataLoader()
    data = loader.load_all(include_text=False)

    # Build program-level course portfolios
    programs = []
    for _, prog in data.df_programs.iterrows():
        case_id = prog["case_id"]
        courses = data.df_courses[data.df_courses["case_id"] == case_id]
        course_names = courses["name"].dropna().tolist()
        if not course_names:
            continue

        # Concatenate course names into a single text
        portfolio_text = "; ".join(course_names)
        programs.append({
            "case_id": case_id,
            "institution": prog["institution_name"],
            "program_name": prog["program_name"],
            "degree_level": prog["degree_level"],
            "num_courses": len(course_names),
            "portfolio_text": portfolio_text,
        })

    df = pd.DataFrame(programs)
    print(f"  {len(df)} programs with courses")
    return df


def compute_embeddings(df):
    """Generate embeddings for each program's course portfolio."""
    print("Computing program embeddings...")
    generator = EmbeddingGenerator(batch_size=16)
    texts = df["portfolio_text"].tolist()
    embeddings = generator.encode(texts, show_progress=True, normalize=True)
    print(f"  Embedding shape: {embeddings.shape}")
    return generator, embeddings


def compute_similarity(generator, embeddings):
    """Compute 122x122 cosine similarity matrix."""
    print("Computing similarity matrix...")
    sim_matrix = generator.compute_similarity(embeddings)
    mean_sim = np.mean(sim_matrix[np.triu_indices_from(sim_matrix, k=1)])
    print(f"  Mean pairwise similarity: {mean_sim:.3f}")
    return sim_matrix


def cluster_programs(generator, embeddings, n_clusters=5):
    """Cluster programs using K-Means on embeddings."""
    print(f"Clustering into {n_clusters} groups...")
    labels = generator.cluster_embeddings(embeddings, n_clusters=n_clusters, method="kmeans")
    print(f"  Cluster sizes: {dict(zip(*np.unique(labels, return_counts=True)))}")
    return labels


def reduce_2d(generator, embeddings):
    """Reduce to 2D for visualization."""
    print("Reducing dimensions (UMAP)...")
    coords_2d = generator.reduce_dimensions(embeddings, n_components=2, method="umap")
    return coords_2d


def plot_cluster_scatter(df, coords_2d, labels, output_path):
    """Scatter plot of program clusters."""
    level_markers = {"bachelor": "o", "master": "s", "phd": "D", "unknown": "^"}
    level_labels = {"bachelor": "Бакалавр", "master": "Магістр", "phd": "PhD", "unknown": "Інше"}
    colors = plt.cm.Set2(np.linspace(0, 1, max(labels) + 1))

    fig, ax = plt.subplots(figsize=(10, 8))

    for level, marker in level_markers.items():
        mask = df["degree_level"] == level
        if not mask.any():
            continue
        for cluster_id in sorted(set(labels)):
            cmask = mask & (labels == cluster_id)
            if not cmask.any():
                continue
            ax.scatter(
                coords_2d[cmask, 0], coords_2d[cmask, 1],
                c=[colors[cluster_id]],
                marker=marker,
                s=60, alpha=0.7,
                label=f"К{cluster_id+1}, {level_labels[level]}" if cmask.sum() > 0 else None,
            )

    ax.set_title("Семантична кластеризація 122 програм дизайну")
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")

    # Deduplicate legend
    handles, lab = ax.get_legend_handles_labels()
    by_label = dict(zip(lab, handles))
    ax.legend(by_label.values(), by_label.keys(), fontsize=7, ncol=2, loc="best")

    plt.tight_layout()
    fig.savefig(output_path, format="pdf", bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  Saved cluster scatter: {output_path}")


def plot_similarity_heatmap(sim_matrix, df, output_path):
    """Heatmap of inter-program similarity."""
    # Sort by degree level for visual grouping
    order = df.sort_values("degree_level").index.tolist()
    sorted_sim = sim_matrix[np.ix_(order, order)]
    sorted_levels = df.loc[order, "degree_level"].tolist()

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(sorted_sim, cmap="YlOrRd", vmin=0, vmax=1, aspect="auto")

    # Add level dividers
    level_changes = [0]
    for i in range(1, len(sorted_levels)):
        if sorted_levels[i] != sorted_levels[i - 1]:
            level_changes.append(i)
            ax.axhline(y=i - 0.5, color="black", linewidth=1)
            ax.axvline(x=i - 0.5, color="black", linewidth=1)

    # Label level blocks
    level_names = {"bachelor": "Бакалавр", "master": "Магістр", "phd": "PhD", "unknown": "Інше"}
    for i, pos in enumerate(level_changes):
        end = level_changes[i + 1] if i + 1 < len(level_changes) else len(sorted_levels)
        mid = (pos + end) / 2
        lvl = sorted_levels[pos]
        ax.text(-3, mid, level_names.get(lvl, lvl), ha="right", va="center", fontsize=9)

    ax.set_title("Матриця семантичної подібності програм дизайну")
    ax.set_xticks([])
    ax.set_yticks([])
    plt.colorbar(im, ax=ax, label="Косинусна подібність", shrink=0.8)
    plt.tight_layout()
    fig.savefig(output_path, format="pdf", bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  Saved similarity heatmap: {output_path}")


def describe_clusters(df, labels):
    """Describe each cluster's composition."""
    df = df.copy()
    df["cluster"] = labels
    descriptions = []
    for cid in sorted(df["cluster"].unique()):
        cdf = df[df["cluster"] == cid]
        levels = cdf["degree_level"].value_counts().to_dict()
        # Find most common courses via portfolio text
        all_courses = "; ".join(cdf["portfolio_text"].tolist()).split("; ")
        from collections import Counter
        common = Counter(all_courses).most_common(5)
        descriptions.append({
            "cluster": cid + 1,
            "size": len(cdf),
            "levels": levels,
            "common_courses": [c for c, _ in common],
        })
    return descriptions


def main():
    print("=" * 60)
    print("Semantic Similarity Clustering: NAQA Design Programs")
    print("=" * 60)

    # 1. Load data
    df = load_program_courses()

    # 2. Compute embeddings
    generator, embeddings = compute_embeddings(df)

    # 3. Similarity matrix
    sim_matrix = compute_similarity(generator, embeddings)

    # 4. Cluster
    labels = cluster_programs(generator, embeddings, n_clusters=5)
    df["cluster"] = labels

    # 5. Reduce dimensions
    coords_2d = reduce_2d(generator, embeddings)

    # 6. Visualize
    plot_cluster_scatter(df, coords_2d, labels, FIGURES_DIR / "semantic_clusters.pdf")
    plot_similarity_heatmap(sim_matrix, df, FIGURES_DIR / "similarity_heatmap.pdf")

    # 7. Describe clusters
    cluster_info = describe_clusters(df, labels)
    print("\nCluster Descriptions:")
    for c in cluster_info:
        print(f"  Cluster {c['cluster']} ({c['size']} programs): {c['levels']}")
        print(f"    Common: {', '.join(c['common_courses'][:3])}")

    # 8. Save results
    export = {
        "n_programs": len(df),
        "n_clusters": 5,
        "mean_similarity": float(np.mean(sim_matrix[np.triu_indices_from(sim_matrix, k=1)])),
        "clusters": cluster_info,
        "similarity_stats": {
            "mean": float(np.mean(sim_matrix[np.triu_indices_from(sim_matrix, k=1)])),
            "std": float(np.std(sim_matrix[np.triu_indices_from(sim_matrix, k=1)])),
            "min": float(np.min(sim_matrix[np.triu_indices_from(sim_matrix, k=1)])),
            "max": float(np.max(sim_matrix[np.triu_indices_from(sim_matrix, k=1)])),
        },
    }
    out_path = OUTPUT_DIR / "semantic_clustering_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nResults saved to {out_path}")

    # Save cluster membership
    df[["case_id", "institution", "program_name", "degree_level", "cluster", "num_courses"]].to_csv(
        OUTPUT_DIR / "program_clusters.csv", index=False, encoding="utf-8"
    )

    print("\n✓ Semantic clustering complete!")
    return export


if __name__ == "__main__":
    main()
