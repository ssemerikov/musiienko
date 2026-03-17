"""
Configuration settings for the Thesis Analysis System.

Manages paths, API tokens, model settings, and analysis parameters.
"""

from pathlib import Path
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # === Paths ===
    project_root: Path = Field(
        default=Path(__file__).parent.parent,
        description="Root directory of the project"
    )

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def downloads_by_level_dir(self) -> Path:
        return self.data_dir / "downloads_by_level"

    @property
    def text_by_level_dir(self) -> Path:
        return self.data_dir / "text_by_level"

    @property
    def output_dir(self) -> Path:
        return self.project_root / "output"

    @property
    def analysis_output_dir(self) -> Path:
        return self.project_root / "thesis_output"

    @property
    def figures_dir(self) -> Path:
        return self.analysis_output_dir / "figures"

    @property
    def latex_dir(self) -> Path:
        return self.analysis_output_dir / "latex"

    @property
    def level_mapping_path(self) -> Path:
        return self.downloads_by_level_dir / "level_mapping.json"

    # === Hugging Face Configuration ===
    hf_token: str = Field(
        default="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",
        description="Hugging Face API token"
    )

    # Models for different tasks
    embedding_model: str = Field(
        default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        description="Multilingual embedding model for Ukrainian text"
    )

    text_gen_model: str = Field(
        default="mistralai/Mistral-7B-Instruct-v0.3",
        description="Text generation model for analysis"
    )

    summarization_model: str = Field(
        default="facebook/bart-large-cnn",
        description="Model for text summarization"
    )

    translation_model: str = Field(
        default="Helsinki-NLP/opus-mt-uk-en",
        description="Ukrainian to English translation"
    )

    # === Analysis Parameters ===
    min_topic_size: int = Field(
        default=10,
        description="Minimum documents per topic in BERTopic"
    )

    num_topics: Optional[int] = Field(
        default=None,
        description="Number of topics (None = auto-detect)"
    )

    top_n_words: int = Field(
        default=10,
        description="Top words per topic"
    )

    # Clustering
    n_clusters_programs: int = Field(
        default=5,
        description="Number of program clusters"
    )

    n_clusters_courses: int = Field(
        default=15,
        description="Number of course clusters"
    )

    # Network analysis
    min_edge_weight: int = Field(
        default=3,
        description="Minimum edge weight for network visualization"
    )

    # === AI Skills Framework ===
    ai_design_skills: List[str] = Field(
        default=[
            "штучний інтелект",
            "машинне навчання",
            "генеративний дизайн",
            "нейронні мережі",
            "AI-інструменти",
            "комп'ютерний зір",
            "обробка зображень",
            "візуалізація даних",
            "інтерактивний дизайн",
            "цифрові технології",
            "3D-моделювання",
            "параметричний дизайн",
            "анімація",
            "motion design",
            "UX/UI",
            "веб-дизайн",
            "прототипування",
            "Adobe Creative Suite",
            "Figma",
            "Blender",
        ],
        description="AI and digital skills to search for in curricula"
    )

    # === Processing Settings ===
    batch_size: int = Field(
        default=32,
        description="Batch size for embedding generation"
    )

    max_tokens_per_doc: int = Field(
        default=512,
        description="Maximum tokens per document for embedding"
    )

    random_seed: int = Field(
        default=42,
        description="Random seed for reproducibility"
    )

    # === Degree Level Mapping ===
    degree_level_names: dict = Field(
        default={
            "bachelor": "Бакалавр",
            "master": "Магістр",
            "phd": "Доктор філософії",
            "unknown": "Невідомо"
        }
    )

    class Config:
        env_prefix = "THESIS_"
        env_file = ".env"
        env_file_encoding = "utf-8"

    def ensure_dirs(self) -> None:
        """Create output directories if they don't exist."""
        self.analysis_output_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.latex_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
