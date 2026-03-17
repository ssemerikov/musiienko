"""
Topic modeling for Ukrainian design curricula.

Uses BERTopic with multilingual embeddings to discover
themes and topics in syllabus content.
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
import json

import numpy as np
import pandas as pd

from ...config import settings
from ...data_processing.ukrainian_nlp import (
    lemmatize_ukrainian,
    clean_text,
    UKRAINIAN_STOPWORDS,
)


@dataclass
class Topic:
    """Represents a discovered topic."""

    topic_id: int
    name: str
    top_words: List[Tuple[str, float]]
    document_count: int
    representative_docs: List[str] = field(default_factory=list)


@dataclass
class TopicModelResult:
    """Results from topic modeling."""

    topics: List[Topic]
    document_topics: List[int]
    document_probs: Optional[np.ndarray]
    topic_embeddings: Optional[np.ndarray]
    coherence_score: Optional[float]


class TopicModeler:
    """Topic modeling using BERTopic with Ukrainian support."""

    def __init__(
        self,
        embedding_model: Optional[str] = None,
        min_topic_size: int = 10,
        n_topics: Optional[int] = None,
        top_n_words: int = 10,
    ):
        self.embedding_model_name = embedding_model or settings.embedding_model
        self.min_topic_size = min_topic_size
        self.n_topics = n_topics
        self.top_n_words = top_n_words

        self._model = None
        self._embeddings = None

    def fit(
        self,
        documents: List[str],
        precomputed_embeddings: Optional[np.ndarray] = None,
    ) -> TopicModelResult:
        """
        Fit topic model to documents.

        Args:
            documents: List of text documents (syllabi, course descriptions)
            precomputed_embeddings: Optional pre-computed embeddings

        Returns:
            TopicModelResult with discovered topics
        """
        # Preprocess documents
        processed_docs = [self._preprocess(doc) for doc in documents]

        # Filter empty documents
        valid_indices = [i for i, doc in enumerate(processed_docs) if doc.strip()]
        valid_docs = [processed_docs[i] for i in valid_indices]

        if len(valid_docs) < self.min_topic_size:
            return self._empty_result(len(documents))

        try:
            from bertopic import BERTopic
            from sentence_transformers import SentenceTransformer

            # Load embedding model
            embedding_model = SentenceTransformer(self.embedding_model_name)

            # Configure BERTopic
            self._model = BERTopic(
                embedding_model=embedding_model,
                min_topic_size=self.min_topic_size,
                nr_topics=self.n_topics,
                top_n_words=self.top_n_words,
                language="multilingual",
                calculate_probabilities=True,
                verbose=True,
            )

            # Fit model
            if precomputed_embeddings is not None:
                valid_embeddings = precomputed_embeddings[valid_indices]
                topics, probs = self._model.fit_transform(
                    valid_docs, embeddings=valid_embeddings
                )
            else:
                topics, probs = self._model.fit_transform(valid_docs)

            # Map back to original indices
            full_topics = [-1] * len(documents)
            for idx, orig_idx in enumerate(valid_indices):
                full_topics[orig_idx] = topics[idx]

            # Extract topic information
            topic_info = self._model.get_topic_info()
            topic_list = self._extract_topics(topic_info, valid_docs, topics)

            return TopicModelResult(
                topics=topic_list,
                document_topics=full_topics,
                document_probs=probs,
                topic_embeddings=self._model.topic_embeddings_,
                coherence_score=None,  # Can compute separately
            )

        except ImportError:
            print("BERTopic not installed. Using fallback LDA.")
            return self._fit_lda_fallback(valid_docs, valid_indices, len(documents))

    def _fit_lda_fallback(
        self,
        documents: List[str],
        valid_indices: List[int],
        total_docs: int,
    ) -> TopicModelResult:
        """Fallback to sklearn LDA if BERTopic unavailable."""
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.decomposition import LatentDirichletAllocation

        # Vectorize
        vectorizer = CountVectorizer(
            max_df=0.95,
            min_df=2,
            max_features=1000,
            stop_words=list(UKRAINIAN_STOPWORDS),
        )

        try:
            doc_term_matrix = vectorizer.fit_transform(documents)
        except ValueError:
            return self._empty_result(total_docs)

        # Fit LDA
        n_topics = self.n_topics or 10
        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=settings.random_seed,
            max_iter=20,
        )
        doc_topics = lda.fit_transform(doc_term_matrix)

        # Get topic assignments
        topic_assignments = doc_topics.argmax(axis=1).tolist()

        # Map back to original indices
        full_topics = [-1] * total_docs
        for idx, orig_idx in enumerate(valid_indices):
            full_topics[orig_idx] = topic_assignments[idx]

        # Extract topics
        feature_names = vectorizer.get_feature_names_out()
        topics = []
        for topic_idx, topic in enumerate(lda.components_):
            top_indices = topic.argsort()[:-self.top_n_words - 1:-1]
            top_words = [
                (feature_names[i], float(topic[i]))
                for i in top_indices
            ]
            doc_count = sum(1 for t in topic_assignments if t == topic_idx)
            topics.append(Topic(
                topic_id=topic_idx,
                name=f"Topic {topic_idx}: {', '.join(w for w, _ in top_words[:3])}",
                top_words=top_words,
                document_count=doc_count,
            ))

        return TopicModelResult(
            topics=topics,
            document_topics=full_topics,
            document_probs=doc_topics,
            topic_embeddings=None,
            coherence_score=None,
        )

    def _preprocess(self, text: str) -> str:
        """Preprocess text for topic modeling."""
        # Clean
        text = clean_text(text)

        # Lemmatize
        lemmas = lemmatize_ukrainian(
            text,
            remove_stopwords=True,
            min_length=3,
        )

        return " ".join(lemmas)

    def _extract_topics(
        self,
        topic_info: pd.DataFrame,
        documents: List[str],
        doc_topics: List[int],
    ) -> List[Topic]:
        """Extract Topic objects from BERTopic results."""
        topics = []

        for _, row in topic_info.iterrows():
            topic_id = row["Topic"]
            if topic_id == -1:
                continue  # Skip outlier topic

            # Get top words
            topic_words = self._model.get_topic(topic_id)
            top_words = [(word, float(score)) for word, score in topic_words]

            # Get representative documents
            topic_docs = [
                documents[i][:200]
                for i, t in enumerate(doc_topics)
                if t == topic_id
            ][:3]

            # Generate name from top words
            name = f"Topic {topic_id}: {', '.join(w for w, _ in top_words[:3])}"

            topics.append(Topic(
                topic_id=topic_id,
                name=name,
                top_words=top_words,
                document_count=row.get("Count", 0),
                representative_docs=topic_docs,
            ))

        return topics

    def _empty_result(self, n_docs: int) -> TopicModelResult:
        """Return empty result when modeling fails."""
        return TopicModelResult(
            topics=[],
            document_topics=[-1] * n_docs,
            document_probs=None,
            topic_embeddings=None,
            coherence_score=None,
        )

    def get_topic_distribution(self) -> Dict[int, int]:
        """Get distribution of documents across topics."""
        if self._model is None:
            return {}

        topic_info = self._model.get_topic_info()
        return dict(zip(topic_info["Topic"], topic_info["Count"]))

    def find_similar_topics(
        self,
        query: str,
        top_n: int = 5,
    ) -> List[Tuple[int, float]]:
        """Find topics most similar to a query."""
        if self._model is None:
            return []

        try:
            similar = self._model.find_topics(query, top_n=top_n)
            return list(zip(similar[0], similar[1]))
        except Exception:
            return []

    def visualize_topics(self, output_path: Optional[str] = None):
        """Generate topic visualization."""
        if self._model is None:
            return None

        try:
            fig = self._model.visualize_topics()
            if output_path:
                fig.write_html(output_path)
            return fig
        except Exception as e:
            print(f"Visualization error: {e}")
            return None

    def export_results(self, result: TopicModelResult, output_path: str) -> None:
        """Export topic modeling results to JSON."""
        export_data = {
            "num_topics": len(result.topics),
            "topics": [
                {
                    "id": t.topic_id,
                    "name": t.name,
                    "top_words": t.top_words,
                    "document_count": t.document_count,
                }
                for t in result.topics
            ],
            "document_topics": result.document_topics,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)


def analyze_topics(
    documents: List[str],
    min_topic_size: int = 10,
    n_topics: Optional[int] = None,
) -> TopicModelResult:
    """Convenience function to run topic modeling."""
    modeler = TopicModeler(
        min_topic_size=min_topic_size,
        n_topics=n_topics,
    )
    return modeler.fit(documents)
