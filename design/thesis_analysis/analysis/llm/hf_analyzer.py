"""
Hugging Face Inference API client for curriculum analysis.

Uses HF models for text generation, summarization, and
analysis of Ukrainian design education content.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import asyncio

from ...config import settings


@dataclass
class AnalysisResult:
    """Result from LLM analysis."""

    task: str
    input_summary: str
    output: str
    model: str
    tokens_used: int = 0
    success: bool = True
    error: Optional[str] = None


class HFAnalyzer:
    """Hugging Face Inference API client for curriculum analysis."""

    def __init__(
        self,
        token: Optional[str] = None,
        text_model: Optional[str] = None,
        summarization_model: Optional[str] = None,
    ):
        self.token = token or settings.hf_token
        self.text_model = text_model or settings.text_gen_model
        self.summarization_model = summarization_model or settings.summarization_model

        self._client = None

    @property
    def client(self):
        """Lazy load HF Inference Client."""
        if self._client is None:
            try:
                from huggingface_hub import InferenceClient

                self._client = InferenceClient(token=self.token)
            except ImportError:
                raise ImportError(
                    "huggingface-hub not installed. Run: pip install huggingface-hub"
                )
        return self._client

    def analyze_curriculum(
        self,
        program_name: str,
        courses: List[str],
        level: str = "bachelor",
    ) -> AnalysisResult:
        """
        Analyze curriculum structure using LLM.

        Args:
            program_name: Name of the educational program
            courses: List of course names
            level: Degree level (bachelor, master, phd)

        Returns:
            AnalysisResult with curriculum analysis
        """
        prompt = self._build_curriculum_prompt(program_name, courses, level)

        try:
            response = self.client.text_generation(
                prompt,
                model=self.text_model,
                max_new_tokens=512,
                temperature=0.7,
            )

            return AnalysisResult(
                task="curriculum_analysis",
                input_summary=f"{program_name}: {len(courses)} courses",
                output=response,
                model=self.text_model,
                success=True,
            )

        except Exception as e:
            return AnalysisResult(
                task="curriculum_analysis",
                input_summary=f"{program_name}: {len(courses)} courses",
                output="",
                model=self.text_model,
                success=False,
                error=str(e),
            )

    def identify_strengths_weaknesses(
        self,
        courses: List[str],
        competencies: List[str],
    ) -> AnalysisResult:
        """Identify curriculum strengths and weaknesses."""
        prompt = f"""Analyze this Ukrainian design program curriculum.

Courses ({len(courses)} total):
{chr(10).join(f'- {c}' for c in courses[:30])}
{'...' if len(courses) > 30 else ''}

Competencies:
{chr(10).join(f'- {c}' for c in competencies[:15])}

Identify:
1. Key strengths of this curriculum
2. Potential gaps or weaknesses
3. Suggestions for improvement

Focus on modern design education requirements including digital skills and AI tools.
Respond in a structured format."""

        try:
            response = self.client.text_generation(
                prompt,
                model=self.text_model,
                max_new_tokens=768,
                temperature=0.7,
            )

            return AnalysisResult(
                task="strengths_weaknesses",
                input_summary=f"{len(courses)} courses, {len(competencies)} competencies",
                output=response,
                model=self.text_model,
                success=True,
            )

        except Exception as e:
            return AnalysisResult(
                task="strengths_weaknesses",
                input_summary=f"{len(courses)} courses",
                output="",
                model=self.text_model,
                success=False,
                error=str(e),
            )

    def summarize_syllabus(
        self,
        syllabus_text: str,
        max_length: int = 150,
    ) -> AnalysisResult:
        """Summarize syllabus content."""
        # Truncate input if too long
        text = syllabus_text[:3000]

        try:
            response = self.client.summarization(
                text,
                model=self.summarization_model,
                parameters={
                    "max_length": max_length,
                    "min_length": 30,
                }
            )

            summary = response.summary_text if hasattr(response, 'summary_text') else str(response)

            return AnalysisResult(
                task="summarization",
                input_summary=f"{len(syllabus_text)} chars",
                output=summary,
                model=self.summarization_model,
                success=True,
            )

        except Exception as e:
            return AnalysisResult(
                task="summarization",
                input_summary=f"{len(syllabus_text)} chars",
                output="",
                model=self.summarization_model,
                success=False,
                error=str(e),
            )

    def generate_recommendations(
        self,
        gap_analysis: Dict[str, Any],
        current_courses: List[str],
    ) -> AnalysisResult:
        """Generate curriculum improvement recommendations based on gap analysis."""
        missing_skills = gap_analysis.get("missing_skills", [])
        coverage_scores = gap_analysis.get("coverage_scores", {})

        prompt = f"""Based on analysis of a Ukrainian design education program:

Current courses: {len(current_courses)}
Key missing skills identified:
{chr(10).join(f'- {s}' for s in missing_skills[:10])}

AI/Digital coverage score: {coverage_scores.get('ai_digital', 0):.1%}

Generate 5 specific recommendations to modernize this design curriculum.
Focus on:
1. AI and generative design integration
2. Digital tools and technology
3. Industry-relevant skills
4. Balanced traditional and modern approaches

Be specific about what courses or content to add."""

        try:
            response = self.client.text_generation(
                prompt,
                model=self.text_model,
                max_new_tokens=600,
                temperature=0.8,
            )

            return AnalysisResult(
                task="recommendations",
                input_summary=f"{len(missing_skills)} gaps identified",
                output=response,
                model=self.text_model,
                success=True,
            )

        except Exception as e:
            return AnalysisResult(
                task="recommendations",
                input_summary=f"{len(missing_skills)} gaps",
                output="",
                model=self.text_model,
                success=False,
                error=str(e),
            )

    def compare_programs(
        self,
        program1_courses: List[str],
        program2_courses: List[str],
        program1_name: str = "Program A",
        program2_name: str = "Program B",
    ) -> AnalysisResult:
        """Compare two design programs."""
        # Find unique and common courses
        set1 = set(c.lower() for c in program1_courses)
        set2 = set(c.lower() for c in program2_courses)

        common = set1 & set2
        only1 = set1 - set2
        only2 = set2 - set1

        prompt = f"""Compare two Ukrainian design education programs:

{program1_name}: {len(program1_courses)} courses
{program2_name}: {len(program2_courses)} courses

Common courses: {len(common)}
Unique to {program1_name}: {len(only1)}
Unique to {program2_name}: {len(only2)}

Sample unique to {program1_name}:
{chr(10).join(f'- {c}' for c in list(only1)[:10])}

Sample unique to {program2_name}:
{chr(10).join(f'- {c}' for c in list(only2)[:10])}

Analyze the key differences and which program appears more modern/comprehensive."""

        try:
            response = self.client.text_generation(
                prompt,
                model=self.text_model,
                max_new_tokens=500,
                temperature=0.7,
            )

            return AnalysisResult(
                task="program_comparison",
                input_summary=f"{program1_name} vs {program2_name}",
                output=response,
                model=self.text_model,
                success=True,
            )

        except Exception as e:
            return AnalysisResult(
                task="program_comparison",
                input_summary=f"Comparison failed",
                output="",
                model=self.text_model,
                success=False,
                error=str(e),
            )

    def _build_curriculum_prompt(
        self,
        program_name: str,
        courses: List[str],
        level: str,
    ) -> str:
        """Build prompt for curriculum analysis."""
        level_name = {
            "bachelor": "Bachelor's (4 years, 240 ECTS)",
            "master": "Master's (1.5-2 years, 90-120 ECTS)",
            "phd": "PhD (4 years, 60 ECTS + dissertation)",
        }.get(level, level)

        return f"""Analyze this Ukrainian design education program curriculum.

Program: {program_name}
Level: {level_name}
Number of courses: {len(courses)}

Course list:
{chr(10).join(f'{i+1}. {c}' for i, c in enumerate(courses[:40]))}
{'...' if len(courses) > 40 else ''}

Provide a brief analysis covering:
1. Overall curriculum structure and balance
2. Coverage of core design competencies
3. Presence of modern/digital skills
4. Potential areas for improvement

Keep the response concise and actionable."""

    async def batch_analyze(
        self,
        programs: List[Dict[str, Any]],
        analysis_type: str = "curriculum",
    ) -> List[AnalysisResult]:
        """Batch analyze multiple programs."""
        results = []

        for program in programs:
            if analysis_type == "curriculum":
                result = self.analyze_curriculum(
                    program.get("name", "Unknown"),
                    program.get("courses", []),
                    program.get("level", "bachelor"),
                )
            else:
                result = AnalysisResult(
                    task=analysis_type,
                    input_summary="Unknown analysis type",
                    output="",
                    model=self.text_model,
                    success=False,
                    error=f"Unknown analysis type: {analysis_type}",
                )

            results.append(result)

            # Rate limiting
            await asyncio.sleep(1.0)

        return results
