"""Built-in skills for the orchestrator system."""

from skills.built_in.text_processing import TextProcessingSkill
from skills.built_in.data_analysis import DataAnalysisSkill
from skills.built_in.knowledge_retrieval import KnowledgeRetrievalSkill
from skills.built_in.synthesis import SynthesisSkill

__all__ = [
    "TextProcessingSkill",
    "DataAnalysisSkill",
    "KnowledgeRetrievalSkill",
    "SynthesisSkill",
]
