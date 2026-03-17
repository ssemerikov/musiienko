# CLAUDE.md - NAQA Design Programs Analysis System

## Research Mission

Build a comprehensive analysis system for Ukrainian Design (022) bachelor's program accreditation data to support a thesis titled:

**"Data-Driven Analysis of Design Education in Ukraine: Toward an AI-Enhanced Bachelor's Curriculum"**

### Primary Research Questions
1. What are the structural patterns and commonalities across accredited design programs?
2. How do curricula differ in course composition, credit distribution, and competency mapping?
3. What gaps exist in current programs regarding AI/digital transformation?
4. What data-driven recommendations can inform a modern, AI-integrated design curriculum?

### Input Data Location
- Individual cases: `data/raw/case_*.json`
- Aggregated data: `output/all_programs.json`
- Components: `output/components_summary.csv`
- Tab contents: `output/tabs_content.json`
- Downloaded documents: `data/downloads/{case_id}/`
- PDF text extracts: `data/extracted_text/` (after running pdf_extractor.py)

---

## System Architecture Requirements

Create the following directory structure:

```
thesis_analysis/
├── __init__.py
├── config.py                    # Analysis configuration
├── main.py                      # Main orchestrator
│
├── data_processing/
│   ├── __init__.py
│   ├── loader.py                # Load all JSON/CSV data
│   ├── cleaner.py               # Data cleaning, normalization
│   ├── text_extractor.py        # Extract text from PDFs/OCR
│   ├── schema.py                # Pydantic models for analysis
│   └── ukrainian_nlp.py         # Ukrainian language processing
│
├── analysis/
│   ├── __init__.py
│   ├── statistical/
│   │   ├── descriptive.py       # Basic statistics
│   │   ├── inferential.py       # Hypothesis testing
│   │   ├── correlation.py       # Correlation analysis
│   │   └── regression.py        # Regression models
│   │
│   ├── nlp/
│   │   ├── preprocessing.py     # Tokenization, lemmatization (Ukrainian)
│   │   ├── topic_modeling.py    # LDA, NMF, BERTopic
│   │   ├── embeddings.py        # Word2Vec, FastText, transformers
│   │   ├── similarity.py        # Document/course similarity
│   │   ├── keyword_extraction.py # RAKE, YAKE, KeyBERT
│   │   └── sentiment.py         # Sentiment/tone analysis
│   │
│   ├── network/
│   │   ├── curriculum_graph.py  # Course prerequisite networks
│   │   ├── competency_graph.py  # Competency-course mapping
│   │   ├── institution_network.py # Institution similarity networks
│   │   └── centrality.py        # Network metrics
│   │
│   ├── clustering/
│   │   ├── hierarchical.py      # Hierarchical clustering
│   │   ├── kmeans.py            # K-means, K-medoids
│   │   ├── dbscan.py            # Density-based clustering
│   │   ├── spectral.py          # Spectral clustering
│   │   └── evaluation.py        # Silhouette, Davies-Bouldin
│   │
│   ├── dimensionality/
│   │   ├── pca.py               # Principal Component Analysis
│   │   ├── tsne.py              # t-SNE visualization
│   │   ├── umap.py              # UMAP embeddings
│   │   └── factor_analysis.py   # Factor analysis
│   │
│   ├── deep_learning/
│   │   ├── autoencoders.py      # Curriculum autoencoders
│   │   ├── transformer.py       # Transformer-based analysis
│   │   ├── neural_classifier.py # Program classification
│   │   └── sequence_models.py   # Course sequence analysis
│   │
│   ├── llm/
│   │   ├── claude_analyzer.py   # Claude API integration
│   │   ├── prompt_templates.py  # Structured prompts
│   │   ├── curriculum_critique.py # LLM-based curriculum review
│   │   ├── gap_analysis.py      # AI/modern skills gap detection
│   │   ├── comparative_summary.py # Cross-program comparison
│   │   └── recommendation_engine.py # AI curriculum recommendations
│   │
│   └── comparative/
│       ├── program_comparison.py # Pairwise program comparison
│       ├── benchmarking.py      # Against international standards
│       ├── trend_analysis.py    # Temporal trends
│       └── quality_metrics.py   # Accreditation quality scoring
│
├── synthesis/
│   ├── __init__.py
│   ├── findings_aggregator.py   # Combine all analyses
│   ├── insight_generator.py     # Generate key insights
│   ├── recommendation_synthesizer.py # Final recommendations
│   └── curriculum_designer.py   # Proposed AI-design curriculum
│
├── visualization/
│   ├── __init__.py
│   ├── static_plots.py          # Matplotlib/Seaborn charts
│   ├── interactive.py           # Plotly dashboards
│   ├── network_viz.py           # NetworkX/Pyvis graphs
│   ├── heatmaps.py              # Correlation/similarity matrices
│   ├── word_clouds.py           # Topic word clouds
│   └── latex_figures.py         # LaTeX-ready figure export
│
├── latex_output/
│   ├── __init__.py
│   ├── thesis_generator.py      # Main LaTeX document generator
│   ├── chapter_writers/
│   │   ├── introduction.py
│   │   ├── literature_review.py
│   │   ├── methodology.py
│   │   ├── data_description.py
│   │   ├── statistical_analysis.py
│   │   ├── nlp_analysis.py
│   │   ├── network_analysis.py
│   │   ├── ml_analysis.py
│   │   ├── llm_analysis.py
│   │   ├── comparative_analysis.py
│   │   ├── synthesis.py
│   │   ├── recommendations.py
│   │   └── conclusion.py
│   ├── table_generator.py       # LaTeX tables from DataFrames
│   ├── figure_manager.py        # Figure placement and captions
│   ├── bibliography.py          # BibTeX generation
│   └── templates/
│       ├── thesis_main.tex
│       ├── preamble.tex
│       ├── chapter_template.tex
│       └── table_template.tex
│
├── output/
│   ├── figures/                 # Generated visualizations
│   ├── tables/                  # Generated data tables
│   ├── analysis_results/        # Intermediate analysis outputs
│   ├── latex/                   # Generated LaTeX files
│   │   ├── thesis.tex
│   │   ├── chapters/
│   │   ├── figures/
│   │   └── bibliography.bib
│   └── reports/                 # Summary reports
│
└── tests/
    └── test_*.py                # Unit tests for each module
```

---

## Phase 1: Data Processing Pipeline

### 1.1 Data Loading (`data_processing/loader.py`)

```python
"""
Load and consolidate all scraped NAQA data.

Requirements:
- Load all case_*.json files from data/raw/
- Parse all_programs.json for aggregated view
- Load components_summary.csv for curriculum data
- Extract text from PDFs in data/downloads/
- Handle Ukrainian text encoding properly (UTF-8)
- Create unified DataFrames for analysis

Key DataFrames to produce:
- df_programs: One row per accredited program
- df_components: One row per educational component (course)
- df_tabs: Tab content with program linkage
- df_teachers: Faculty information
- df_files: Downloaded document metadata
"""
```

### 1.2 Ukrainian NLP Setup (`data_processing/ukrainian_nlp.py`)

```python
"""
Ukrainian language processing utilities.

Requirements:
- Install and configure Ukrainian spaCy model (uk_core_news_lg)
- Setup pymorphy2 with Ukrainian dictionary for lemmatization
- Create Ukrainian stopwords list (extended)
- Handle Cyrillic text normalization
- Transliteration utilities for cross-referencing
- Named Entity Recognition for Ukrainian text

Libraries:
- spacy (uk_core_news_lg)
- pymorphy2
- ukrainian-word-stress (optional)
- langdetect for mixed-language handling
"""
```

### 1.3 Data Schema (`data_processing/schema.py`)

```python
"""
Pydantic models for type-safe analysis.

Define models:
- Program: institution, title, degree, specialty, accreditation_date, status
- EducationalComponent: name, credits, hours, type (required/elective), semester
- Competency: code, description, type (general/specific)
- Teacher: name, degree, position, courses
- AccreditationCriteria: criterion_number, score, comments
- CurriculumStructure: total_credits, by_cycle, by_type
"""
```

---

## Phase 2: Statistical Analysis

### 2.1 Descriptive Statistics (`analysis/statistical/descriptive.py`)

```python
"""
Comprehensive descriptive statistics.

Analyses:
1. Program-level statistics:
   - Number of programs by institution type (public/private)
   - Geographic distribution across regions
   - Accreditation status distribution
   - Temporal distribution of accreditation dates

2. Curriculum statistics:
   - Total credits distribution (mean, median, std, range)
   - Number of courses per program
   - Required vs elective ratio
   - Credit distribution by course type
   - Semester load distribution

3. Course-level statistics:
   - Most common course names (with frequency)
   - Credit allocation patterns
   - Course naming variations (clustering similar names)
   - Theory/practice hour ratios

4. Faculty statistics:
   - Faculty size per program
   - Degree distribution (PhD, Dr.Sc., etc.)
   - Student-to-faculty ratios

Output: LaTeX tables, summary statistics JSON
"""
```

### 2.2 Correlation Analysis (`analysis/statistical/correlation.py`)

```python
"""
Correlation and association analysis.

Analyses:
1. Numeric correlations:
   - Credits vs. accreditation score
   - Number of courses vs. elective percentage
   - Faculty size vs. program diversity
   - Use Pearson, Spearman, Kendall as appropriate

2. Categorical associations:
   - Chi-square tests for independence
   - Cramér's V for effect size
   - Institution type vs. curriculum characteristics

3. Correlation matrices:
   - Course credit allocations across programs
   - Competency coverage patterns

Output: Correlation matrices, p-values, effect sizes
"""
```

### 2.3 Regression Analysis (`analysis/statistical/regression.py`)

```python
"""
Regression models for accreditation factors.

Models:
1. Linear regression:
   - Predict accreditation score from curriculum features
   - Identify significant predictors

2. Logistic regression:
   - Predict accreditation outcome (passed/conditional)
   - Feature importance for success factors

3. Mixed-effects models:
   - Account for institution-level clustering
   - Random effects for regional variation

Output: Model coefficients, confidence intervals, diagnostic plots
"""
```

---

## Phase 3: NLP Analysis

### 3.1 Topic Modeling (`analysis/nlp/topic_modeling.py`)

```python
"""
Discover latent topics in curricula and documents.

Methods:
1. LDA (Latent Dirichlet Allocation):
   - Apply to course descriptions
   - Apply to accreditation self-evaluation texts
   - Optimize number of topics (coherence score)

2. NMF (Non-negative Matrix Factorization):
   - Alternative topic extraction
   - Compare with LDA results

3. BERTopic:
   - Use Ukrainian BERT embeddings
   - Hierarchical topic structure
   - Topic evolution across programs

4. Topic Analysis:
   - Identify dominant topics per program
   - Topic distribution comparison
   - Emerging vs. traditional topics

Output: Topic distributions, top words per topic, program-topic matrices
"""
```

### 3.2 Semantic Embeddings (`analysis/nlp/embeddings.py`)

```python
"""
Create and analyze semantic embeddings.

Methods:
1. Word2Vec/FastText:
   - Train on curriculum corpus
   - Course name embeddings
   - Competency description embeddings

2. Sentence Transformers:
   - Use multilingual models (paraphrase-multilingual-mpnet-base-v2)
   - Course description embeddings
   - Program-level document embeddings

3. Ukrainian BERT:
   - Use uk-roberta or similar
   - Contextual embeddings for course analysis

4. Embedding Analysis:
   - Course similarity matrices
   - Find semantically similar courses across programs
   - Identify unique/innovative courses
   - Cluster courses by semantic content

Output: Embedding matrices, similarity scores, cluster assignments
"""
```

### 3.3 Keyword Extraction (`analysis/nlp/keyword_extraction.py`)

```python
"""
Extract key terms and concepts.

Methods:
1. TF-IDF analysis:
   - Distinctive terms per program
   - Common terms across all programs
   - Rare/unique terminology

2. RAKE (Rapid Automatic Keyword Extraction):
   - Multi-word keyword phrases
   - Course description keywords

3. YAKE (Yet Another Keyword Extractor):
   - Unsupervised keyword extraction
   - Ukrainian language support

4. KeyBERT:
   - BERT-based keyword extraction
   - Semantic keyword ranking

5. Analysis:
   - AI/technology-related keyword frequency
   - Traditional vs. modern terminology
   - Competency keyword mapping

Output: Keyword rankings, frequency distributions, temporal trends
"""
```

---

## Phase 4: Network Analysis

### 4.1 Curriculum Network (`analysis/network/curriculum_graph.py`)

```python
"""
Build and analyze curriculum structure networks.

Networks:
1. Course co-occurrence network:
   - Nodes: Courses
   - Edges: Co-occurrence in same program (weighted)
   - Identify course clusters/communities

2. Course sequence network:
   - Directed edges: Prerequisites and course order
   - Critical path analysis
   - Semester dependency structure

3. Program similarity network:
   - Nodes: Programs
   - Edges: Curriculum similarity (Jaccard, cosine)
   - Community detection for program groups

Metrics:
- Degree centrality (core vs. peripheral courses)
- Betweenness centrality (bridging courses)
- Clustering coefficient
- Network density comparison

Output: NetworkX graphs, centrality rankings, community assignments
"""
```

### 4.2 Competency Mapping (`analysis/network/competency_graph.py`)

```python
"""
Competency-curriculum bipartite network analysis.

Networks:
1. Competency-Course bipartite graph:
   - Link courses to competencies they develop
   - Identify competency coverage gaps
   - Over/under-represented competencies

2. Competency co-development network:
   - Project bipartite to competency-competency network
   - Identify competency clusters

3. Course contribution analysis:
   - Which courses contribute to most competencies
   - Specialization vs. generalization patterns

Output: Bipartite graphs, projection networks, coverage matrices
"""
```

---

## Phase 5: Clustering & Dimensionality Reduction

### 5.1 Program Clustering (`analysis/clustering/`)

```python
"""
Cluster programs by curriculum characteristics.

Feature Engineering:
- Course category distribution (percentages)
- Credit allocation patterns
- Competency emphasis
- Faculty characteristics
- Semantic embeddings

Methods:
1. Hierarchical clustering:
   - Dendrogram visualization
   - Optimal cut height
   - Cluster interpretation

2. K-means:
   - Elbow method for k selection
   - Silhouette analysis
   - Cluster profiling

3. DBSCAN:
   - Identify outlier programs
   - Density-based groupings

4. Spectral clustering:
   - Graph-based approach
   - Non-convex cluster detection

Cluster Profiling:
- Characteristic features per cluster
- Representative programs
- Cluster naming/interpretation

Output: Cluster assignments, profiles, dendrograms
"""
```

### 5.2 Dimensionality Reduction (`analysis/dimensionality/`)

```python
"""
Reduce and visualize high-dimensional curriculum data.

Methods:
1. PCA:
   - Identify principal components of curriculum variation
   - Explained variance analysis
   - Component interpretation (loadings)

2. t-SNE:
   - 2D visualization of program similarity
   - Perplexity optimization
   - Interactive plots

3. UMAP:
   - Preserve global structure
   - Faster than t-SNE
   - Hyperparameter tuning

4. Factor Analysis:
   - Identify latent curriculum factors
   - Factor rotation and interpretation
   - Factor scores per program

Output: Reduced representations, loadings, visualizations
"""
```

---

## Phase 6: Deep Learning Analysis

### 6.1 Autoencoders (`analysis/deep_learning/autoencoders.py`)

```python
"""
Learn compressed curriculum representations.

Models:
1. Vanilla Autoencoder:
   - Encode curriculum as dense vector
   - Reconstruct and measure loss
   - Use latent space for clustering

2. Variational Autoencoder (VAE):
   - Probabilistic latent space
   - Generate synthetic curricula
   - Interpolation between programs

3. Denoising Autoencoder:
   - Robust feature learning
   - Handle missing course data

Applications:
- Anomaly detection (unusual curricula)
- Curriculum similarity in latent space
- Generative curriculum suggestions

Output: Latent representations, reconstruction errors, generated samples
"""
```

### 6.2 Transformer Analysis (`analysis/deep_learning/transformer.py`)

```python
"""
Transformer-based curriculum analysis.

Models:
1. Fine-tuned BERT for classification:
   - Classify programs by quality tier
   - Classify courses by category
   - Multi-label competency prediction

2. Sequence modeling:
   - Model curriculum as sequence of courses
   - Predict missing courses
   - Course recommendation

3. Cross-attention analysis:
   - Attention between courses and competencies
   - Visualize what drives classifications

Output: Model weights, attention visualizations, predictions
"""
```

---

## Phase 7: LLM-Powered Analysis (Claude API)

### 7.1 Claude API Integration (`analysis/llm/claude_analyzer.py`)

```python
"""
Integrate Claude API for advanced analysis.

Setup:
- Use anthropic Python SDK
- Rate limiting and retry logic
- Cost tracking
- Response caching (avoid duplicate calls)

Model: claude-sonnet-4-20250514 or claude-opus-4-20250514

Configuration:
ANTHROPIC_API_KEY environment variable
Max tokens, temperature settings per task
"""
```

### 7.2 Curriculum Analysis Prompts (`analysis/llm/prompt_templates.py`)

```python
"""
Structured prompts for curriculum analysis.

Prompt Categories:

1. CURRICULUM_STRUCTURE_ANALYSIS:
   - Analyze overall structure of a program
   - Identify strengths and weaknesses
   - Compare to best practices

2. COURSE_COMPARISON:
   - Compare similar courses across programs
   - Identify innovative approaches
   - Suggest improvements

3. COMPETENCY_ALIGNMENT:
   - Assess competency-course alignment
   - Identify coverage gaps
   - Suggest mapping improvements

4. AI_READINESS_ASSESSMENT:
   - Evaluate AI/digital content presence
   - Identify integration opportunities
   - Benchmark against industry needs

5. MODERN_DESIGN_SKILLS:
   - Assess coverage of modern design tools
   - UX/UI, service design, design thinking
   - Sustainability and ethics

6. SYNTHESIS_AND_RECOMMENDATIONS:
   - Synthesize findings from all analyses
   - Generate actionable recommendations
   - Propose curriculum enhancements

Each prompt should:
- Use structured output (JSON mode where applicable)
- Include relevant context from data
- Request specific, actionable insights
"""
```

### 7.3 Gap Analysis (`analysis/llm/gap_analysis.py`)

```python
"""
LLM-powered gap analysis for modern curriculum needs.

Analyses:
1. AI/ML Skills Gap:
   - Search for AI-related courses
   - Assess depth of coverage
   - Compare to industry requirements
   - Identify missing AI design topics:
     * AI-assisted design tools
     * Generative design
     * Human-AI interaction design
     * Ethical AI in design
     * Prompt engineering for designers

2. Digital Transformation Gap:
   - Digital design tools coverage
   - Motion graphics, 3D, VR/AR
   - Data visualization
   - Design systems and automation

3. Soft Skills Gap:
   - Design thinking methodology
   - Collaboration and teamwork
   - Communication and presentation
   - Project management

4. Industry Alignment:
   - Compare to job market requirements
   - Identify emerging skills
   - Practical vs. theoretical balance

Output: Gap reports, priority rankings, specific recommendations
"""
```

### 7.4 Recommendation Engine (`analysis/llm/recommendation_engine.py`)

```python
"""
Generate data-driven curriculum recommendations.

Recommendation Types:
1. Course additions:
   - New AI/technology courses
   - Modern design methodology courses
   - Industry collaboration opportunities

2. Course modifications:
   - Update outdated content
   - Add AI components to existing courses
   - Increase practical components

3. Structural changes:
   - Semester sequence optimization
   - Elective flexibility
   - Specialization tracks

4. Competency mapping:
   - Enhanced learning outcomes
   - Assessment alignment
   - Portfolio development

5. Implementation roadmap:
   - Phased implementation plan
   - Resource requirements
   - Faculty development needs

Output: Prioritized recommendations with justifications
"""
```

---

## Phase 8: Comparative Analysis

### 8.1 Program Comparison (`analysis/comparative/program_comparison.py`)

```python
"""
Systematic pairwise and group program comparison.

Comparisons:
1. By institution type:
   - Public vs. private universities
   - National vs. regional institutions
   - Arts academies vs. technical universities

2. By accreditation outcome:
   - Fully accredited vs. conditional
   - Identify success factors

3. By geography:
   - Regional curriculum patterns
   - Urban vs. regional differences

4. Curriculum similarity matrix:
   - Jaccard similarity of course sets
   - Semantic similarity of descriptions
   - Competency overlap

Output: Comparison matrices, significant differences, patterns
"""
```

### 8.2 International Benchmarking (`analysis/comparative/benchmarking.py`)

```python
"""
Benchmark against international standards.

Benchmarks:
1. European design education standards:
   - ELIA (European League of Institutes of the Arts)
   - Cumulus Association recommendations
   - Bologna Process alignment

2. Industry frameworks:
   - IDEO design competencies
   - Google UX Design certificate topics
   - Adobe design skills framework

3. Academic frameworks:
   - ACM/IEEE curriculum guidelines
   - Design education research best practices

Analysis:
- Coverage percentage of benchmark competencies
- Gap identification
- Alignment scoring

Output: Benchmark comparison tables, coverage matrices
"""
```

---

## Phase 9: Synthesis & Curriculum Design

### 9.1 Findings Aggregation (`synthesis/findings_aggregator.py`)

```python
"""
Aggregate findings from all analysis streams.

Structure:
1. Key findings by analysis type:
   - Statistical findings
   - NLP insights
   - Network patterns
   - Clustering results
   - Deep learning discoveries
   - LLM-generated insights

2. Cross-validation:
   - Findings supported by multiple methods
   - Contradictions to resolve
   - Confidence scoring

3. Priority ranking:
   - Impact potential
   - Implementation feasibility
   - Evidence strength

Output: Unified findings document, priority matrix
"""
```

### 9.2 AI-Enhanced Curriculum Design (`synthesis/curriculum_designer.py`)

```python
"""
Design proposed AI-integrated design curriculum.

Deliverables:
1. Complete curriculum structure:
   - 240 ECTS (4 years bachelor)
   - Semester-by-semester breakdown
   - Required and elective courses

2. Course specifications:
   - Each course with:
     * Name (Ukrainian and English)
     * Credits and hours
     * Learning outcomes
     * Content outline
     * AI/technology integration points
     * Assessment methods

3. AI-specific courses:
   - "AI Tools for Designers"
   - "Generative Design with AI"
   - "Human-AI Interaction Design"
   - "Ethics of AI in Design"
   - "Data-Driven Design"

4. AI integration in traditional courses:
   - Typography with AI-assisted font generation
   - Color theory with AI palette tools
   - Illustration with generative AI
   - UX with AI prototyping

5. Competency framework:
   - Updated for AI era
   - Mapped to all courses

Output: Complete curriculum document, course syllabi templates
"""
```

---

## Phase 10: LaTeX Thesis Generation

### 10.1 Thesis Structure (`latex_output/thesis_generator.py`)

```python
"""
Generate complete LaTeX thesis document.

Structure:
1. Preamble (Ukrainian academic format)
2. Title page
3. Abstract (Ukrainian and English)
4. Table of contents
5. List of figures and tables
6. List of abbreviations

Chapters:
1. Introduction
   - Research context and motivation
   - Problem statement
   - Research questions
   - Thesis structure

2. Literature Review
   - Design education evolution
   - AI in creative industries
   - Curriculum development theory
   - Ukrainian higher education context

3. Methodology
   - Data collection (NAQA scraper)
   - Analysis methods overview
   - Research design justification

4. Data Description
   - Dataset statistics
   - Data quality assessment
   - Descriptive overview

5. Statistical Analysis
   - Descriptive statistics results
   - Correlation and regression findings
   - Tables and interpretations

6. Natural Language Processing Analysis
   - Topic modeling results
   - Semantic analysis findings
   - Keyword and terminology analysis

7. Network Analysis
   - Curriculum network findings
   - Competency mapping results
   - Community detection outcomes

8. Machine Learning Analysis
   - Clustering results
   - Dimensionality reduction insights
   - Deep learning findings

9. LLM-Enhanced Analysis
   - Curriculum quality assessment
   - Gap analysis results
   - AI integration opportunities

10. Comparative Analysis
    - Program comparisons
    - International benchmarking
    - Best practice identification

11. Synthesis and Recommendations
    - Integrated findings
    - Proposed AI-enhanced curriculum
    - Implementation roadmap

12. Conclusions
    - Summary of contributions
    - Limitations
    - Future research directions

Appendices:
A. Complete curriculum proposal
B. Course syllabi
C. Data codebook
D. Additional tables and figures
E. Code documentation

Bibliography (BibTeX)
"""
```

### 10.2 Table Generator (`latex_output/table_generator.py`)

```python
"""
Generate publication-quality LaTeX tables.

Table Types:
- Descriptive statistics tables
- Correlation matrices
- Regression results
- Topic-word matrices
- Cluster profiles
- Comparison tables
- Curriculum structure tables

Requirements:
- booktabs package styling
- Proper Ukrainian character handling
- Automatic caption and label generation
- Cross-referencing support
- Long table support (longtable)
- Multicolumn and multirow support

Output: .tex files for each table
"""
```

### 10.3 Figure Manager (`latex_output/figure_manager.py`)

```python
"""
Manage thesis figures.

Figure Generation:
- Export all visualizations as PDF/PNG (300 DPI)
- Consistent styling (color scheme, fonts)
- Ukrainian labels where appropriate
- Publication-quality resolution

Figure Types:
- Distribution plots (histograms, box plots)
- Correlation heatmaps
- Network visualizations
- Dimensionality reduction plots (t-SNE, UMAP)
- Topic model visualizations
- Word clouds
- Dendrograms
- Curriculum structure diagrams

LaTeX Integration:
- Figure environments with captions
- Subfigures for related plots
- Cross-referencing

Output: figures/ directory, .tex include files
"""
```

---

## Installation Requirements

```bash
# Core dependencies
pip install pandas numpy scipy scikit-learn statsmodels

# NLP
pip install spacy pymorphy2 gensim nltk
pip install sentence-transformers transformers torch
pip install bertopic yake rake-nltk keybert
python -m spacy download uk_core_news_lg

# Network analysis
pip install networkx pyvis igraph

# Visualization
pip install matplotlib seaborn plotly wordcloud
pip install adjustText  # for label placement

# Deep learning
pip install torch tensorflow keras

# LLM
pip install anthropic

# LaTeX
pip install pylatex jinja2

# Utilities
pip install tqdm pydantic aiofiles python-dotenv
pip install openpyxl xlsxwriter  # Excel support

# Ukrainian specific
pip install pymorphy2-dicts-uk
```

---

## Configuration (`config.py`)

```python
"""
Analysis configuration.

Settings:
- ANTHROPIC_API_KEY: from environment
- DATA_RAW_PATH: "../data/raw/"
- OUTPUT_PATH: "../output/"
- THESIS_OUTPUT_PATH: "./output/latex/"
- FIGURES_PATH: "./output/figures/"
- RANDOM_SEED: 42
- N_TOPICS: 10 (for topic modeling)
- N_CLUSTERS: 5 (for clustering, or auto-detect)
- EMBEDDING_MODEL: "paraphrase-multilingual-mpnet-base-v2"
- LLM_MODEL: "claude-sonnet-4-20250514"
- LLM_MAX_TOKENS: 4096
- LATEX_LANGUAGE: "ukrainian"
"""
```

---

## Execution Order

```bash
# 1. Data loading and preprocessing
python -m thesis_analysis.main --phase data

# 2. Statistical analysis
python -m thesis_analysis.main --phase statistical

# 3. NLP analysis
python -m thesis_analysis.main --phase nlp

# 4. Network analysis
python -m thesis_analysis.main --phase network

# 5. Clustering and dimensionality reduction
python -m thesis_analysis.main --phase clustering

# 6. Deep learning analysis
python -m thesis_analysis.main --phase deep_learning

# 7. LLM analysis (requires API key)
python -m thesis_analysis.main --phase llm

# 8. Comparative analysis
python -m thesis_analysis.main --phase comparative

# 9. Synthesis and curriculum design
python -m thesis_analysis.main --phase synthesis

# 10. Generate LaTeX thesis
python -m thesis_analysis.main --phase latex

# Run all phases
python -m thesis_analysis.main --all

# Generate visualizations only
python -m thesis_analysis.main --phase visualize
```

---

## Output Specifications

### Analysis Results (JSON)
```
output/analysis_results/
├── descriptive_stats.json
├── correlation_matrices.json
├── regression_results.json
├── topic_model.json
├── embeddings_similarity.json
├── network_metrics.json
├── cluster_assignments.json
├── pca_results.json
├── llm_analysis/
│   ├── curriculum_reviews.json
│   ├── gap_analysis.json
│   └── recommendations.json
└── synthesis/
    ├── integrated_findings.json
    └── proposed_curriculum.json
```

### LaTeX Output
```
output/latex/
├── thesis.tex              # Main document
├── preamble.tex            # LaTeX preamble
├── chapters/
│   ├── 01_introduction.tex
│   ├── 02_literature.tex
│   ├── 03_methodology.tex
│   ├── ...
│   └── 12_conclusions.tex
├── figures/
│   ├── fig_*.pdf
│   └── fig_*.tex           # Figure includes
├── tables/
│   └── tab_*.tex
├── appendices/
│   ├── appendix_a.tex
│   └── ...
└── bibliography.bib
```

---

## Quality Requirements

1. **Code Quality**:
   - Type hints on all functions
   - Docstrings for all modules and functions
   - Error handling with informative messages
   - Logging with configurable levels
   - Progress bars for long operations

2. **Analysis Quality**:
   - All statistical tests with proper assumptions checking
   - Effect sizes alongside p-values
   - Multiple comparison corrections where needed
   - Cross-validation for ML models
   - Confidence intervals where applicable

3. **Reproducibility**:
   - Random seeds set consistently
   - All parameters configurable
   - Analysis pipeline fully scripted
   - Version tracking for dependencies

4. **LaTeX Quality**:
   - Proper Ukrainian hyphenation
   - Consistent formatting throughout
   - All figures and tables numbered and referenced
   - Complete bibliography in proper format

---

## Special Considerations

1. **Ukrainian Language**:
   - All course names and descriptions are in Ukrainian
   - Use appropriate NLP tools with Ukrainian support
   - Preserve Cyrillic characters in all outputs
   - Transliteration only where necessary

2. **Data Privacy**:
   - Teacher names may need anonymization
   - Institution names are public record
   - Be cautious with identifying information

3. **Interpretation**:
   - All automated findings need human interpretation
   - LLM outputs should be validated
   - Statistical significance ≠ practical significance

4. **Thesis Format**:
   - Follow Ukrainian academic thesis format
   - Include both Ukrainian and English abstracts
   - Proper citation format (DSTU or institution-specific)

---

Now begin building this system. Start with the data processing module, then proceed through each analysis phase, and finally generate the complete LaTeX thesis. Provide comprehensive code with detailed comments and documentation.
