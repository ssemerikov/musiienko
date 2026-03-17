"""Analysis modules for thesis analysis."""

from .statistical.descriptive import DescriptiveAnalyzer
from .nlp.topic_modeling import TopicModeler
from .nlp.embeddings import EmbeddingGenerator
from .network.curriculum_graph import CurriculumGraphAnalyzer
from .llm.hf_analyzer import HFAnalyzer
from .llm.gap_analysis import AIGapAnalyzer

__all__ = [
    "DescriptiveAnalyzer",
    "TopicModeler",
    "EmbeddingGenerator",
    "CurriculumGraphAnalyzer",
    "HFAnalyzer",
    "AIGapAnalyzer",
]
