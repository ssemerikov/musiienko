"""
Embedding generation for Ukrainian design curricula.

Uses sentence-transformers with multilingual models to generate
embeddings for courses, syllabi, and competencies.
"""

from typing import List, Optional, Dict, Union
from pathlib import Path
import json

import numpy as np

from ...config import settings


class EmbeddingGenerator:
    """Generate embeddings using HuggingFace sentence-transformers."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        batch_size: int = 32,
        max_length: int = 512,
        cache_dir: Optional[Path] = None,
    ):
        self.model_name = model_name or settings.embedding_model
        self.batch_size = batch_size
        self.max_length = max_length
        self.cache_dir = cache_dir

        self._model = None

    @property
    def model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(
                    self.model_name,
                    cache_folder=str(self.cache_dir) if self.cache_dir else None,
                )
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
        return self._model

    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = True,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Generate embeddings for texts.

        Args:
            texts: Single text or list of texts
            show_progress: Show progress bar
            normalize: L2 normalize embeddings

        Returns:
            Numpy array of embeddings (n_texts, embedding_dim)
        """
        if isinstance(texts, str):
            texts = [texts]

        # Truncate long texts
        truncated = [
            text[:self.max_length * 4] if len(text) > self.max_length * 4 else text
            for text in texts
        ]

        embeddings = self.model.encode(
            truncated,
            batch_size=self.batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize,
        )

        return embeddings

    def encode_courses(
        self,
        course_names: List[str],
        course_descriptions: Optional[List[str]] = None,
    ) -> np.ndarray:
        """
        Generate embeddings for courses.

        Combines course name with description if available.
        """
        if course_descriptions:
            texts = [
                f"{name}. {desc}" if desc else name
                for name, desc in zip(course_names, course_descriptions)
            ]
        else:
            texts = course_names

        return self.encode(texts)

    def compute_similarity(
        self,
        embeddings1: np.ndarray,
        embeddings2: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Compute cosine similarity between embeddings.

        Args:
            embeddings1: First set of embeddings (n1, dim)
            embeddings2: Second set (n2, dim). If None, computes self-similarity.

        Returns:
            Similarity matrix (n1, n2)
        """
        if embeddings2 is None:
            embeddings2 = embeddings1

        # Normalize if not already
        norm1 = embeddings1 / np.linalg.norm(embeddings1, axis=1, keepdims=True)
        norm2 = embeddings2 / np.linalg.norm(embeddings2, axis=1, keepdims=True)

        return np.dot(norm1, norm2.T)

    def find_similar(
        self,
        query: str,
        corpus: List[str],
        corpus_embeddings: Optional[np.ndarray] = None,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Find most similar items in corpus to query.

        Args:
            query: Query text
            corpus: List of corpus texts
            corpus_embeddings: Pre-computed corpus embeddings
            top_k: Number of results to return

        Returns:
            List of dicts with text, score, and index
        """
        query_embedding = self.encode(query, show_progress=False)

        if corpus_embeddings is None:
            corpus_embeddings = self.encode(corpus)

        similarities = self.compute_similarity(query_embedding, corpus_embeddings)[0]

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "text": corpus[idx],
                "score": float(similarities[idx]),
                "index": int(idx),
            })

        return results

    def cluster_embeddings(
        self,
        embeddings: np.ndarray,
        n_clusters: int = 10,
        method: str = "kmeans",
    ) -> np.ndarray:
        """
        Cluster embeddings.

        Args:
            embeddings: Embedding matrix (n, dim)
            n_clusters: Number of clusters
            method: 'kmeans' or 'hierarchical'

        Returns:
            Cluster labels for each embedding
        """
        from sklearn.cluster import KMeans, AgglomerativeClustering

        if method == "kmeans":
            clusterer = KMeans(
                n_clusters=n_clusters,
                random_state=settings.random_seed,
                n_init=10,
            )
        elif method == "hierarchical":
            clusterer = AgglomerativeClustering(n_clusters=n_clusters)
        else:
            raise ValueError(f"Unknown method: {method}")

        labels = clusterer.fit_predict(embeddings)
        return labels

    def reduce_dimensions(
        self,
        embeddings: np.ndarray,
        n_components: int = 2,
        method: str = "umap",
    ) -> np.ndarray:
        """
        Reduce embedding dimensions for visualization.

        Args:
            embeddings: High-dimensional embeddings
            n_components: Target dimensions (2 or 3)
            method: 'umap', 'tsne', or 'pca'

        Returns:
            Reduced embeddings
        """
        if method == "pca":
            from sklearn.decomposition import PCA
            reducer = PCA(n_components=n_components, random_state=settings.random_seed)
        elif method == "tsne":
            from sklearn.manifold import TSNE
            reducer = TSNE(
                n_components=n_components,
                random_state=settings.random_seed,
                perplexity=min(30, len(embeddings) - 1),
            )
        elif method == "umap":
            try:
                import umap
                reducer = umap.UMAP(
                    n_components=n_components,
                    random_state=settings.random_seed,
                    n_neighbors=min(15, len(embeddings) - 1),
                )
            except ImportError:
                print("UMAP not installed, falling back to t-SNE")
                from sklearn.manifold import TSNE
                reducer = TSNE(
                    n_components=n_components,
                    random_state=settings.random_seed,
                )
        else:
            raise ValueError(f"Unknown method: {method}")

        return reducer.fit_transform(embeddings)

    def save_embeddings(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        output_path: Path,
    ) -> None:
        """Save embeddings and texts to disk."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        np.save(output_path.with_suffix(".npy"), embeddings)

        with open(output_path.with_suffix(".json"), "w", encoding="utf-8") as f:
            json.dump(texts, f, ensure_ascii=False)

    def load_embeddings(
        self,
        input_path: Path,
    ) -> tuple:
        """Load embeddings and texts from disk."""
        input_path = Path(input_path)

        embeddings = np.load(input_path.with_suffix(".npy"))

        with open(input_path.with_suffix(".json"), "r", encoding="utf-8") as f:
            texts = json.load(f)

        return embeddings, texts


def generate_course_embeddings(
    course_names: List[str],
    model_name: Optional[str] = None,
) -> np.ndarray:
    """Convenience function to generate course embeddings."""
    generator = EmbeddingGenerator(model_name=model_name)
    return generator.encode_courses(course_names)
